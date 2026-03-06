from django.shortcuts import render
from rest_framework import generics, permissions, status, filters, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction, models
from django.db.models import Sum, F, Q, Count, Case, When, Value, DecimalField, IntegerField
from django.db.models.functions import Coalesce, TruncDate, TruncWeek, TruncMonth, TruncYear
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from decimal import Decimal, InvalidOperation

from .models import (
    Product, Category, SaleTransaction, SaleItem,
    SerialItem, Location, InventoryMovement, Notification, WarrantyRecord,
    generate_unique_sku, Site, PaymentMethod, ProductSpecification, SerialNumberHistory,
    GlobalSetting, Purchase, PurchaseLine, Unit, DiscountRule, ModifierGroup, ModifierOption,
    Bundle,
)
from .serializers import (
    CategorySerializer, ProductSerializer, ProductListSerializer,
    SaleRequestSerializer, AdminApprovalSerializer, PendingTransactionSerializer,
    StaffSaleHistorySerializer, NotificationSerializer, NotificationReadSerializer,
    LocationSerializer, DailySummarySerializer, InventoryMovementSerializer,
    InvoiceSerializer, SerialItemSerializer, ProductInventorySerializer,
    SiteSerializer, ProductSpecificationSerializer,
    PurchaseSerializer, PurchaseCreateSerializer, UnitSerializer,
    DiscountRuleSerializer, ModifierGroupSerializer, ModifierGroupCreateUpdateSerializer,
    BundleSerializer, BundleListSerializer, BundleWriteSerializer,
)
from .serializers_payment import (
    PaymentMethodSerializer, PaymentProofUploadSerializer, PaymentStatusUpdateSerializer,
)
from core.permissions import (
    IsAdminOrHigher, IsInventoryManagerOrHigher, IsStaffOrHigher,
    IsManagerOrHigher, IsCashierOrHigher, IsStoreKeeperOrHigher,
    is_cashier_role,
)
from core.audit import log_audit
from core.outlet_utils import filter_queryset_by_outlet, is_owner, get_request_outlet_id, user_can_access_location
from rest_framework import serializers
import time
import random
import json
from decimal import Decimal, InvalidOperation
from service.models import *
from django.db.models import Sum, Count


def _parse_quantity(val, default=1):
    """Parse quantity from request (integer only – ဒသမမသုံး)."""
    if val is None:
        return max(1, int(default))
    try:
        return max(1, int(round(float(val))))
    except (TypeError, ValueError):
        return max(1, int(default))


# ----------------------------------------------------
# 1. Category ViewSet
# ----------------------------------------------------
class CategoryViewSet(viewsets.ModelViewSet):
    """Categories: list/retrieve = Cashier+ (POS dropdown), create/update/delete = Inventory Manager+."""
    queryset = Category.objects.all().order_by('name')
    serializer_class = CategorySerializer
    permission_classes = [IsInventoryManagerOrHigher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name', 'id']
    ordering = ['name']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsStaffOrHigher()]  # Role ရှိသူအားလုံး categories ကြည့်နိုင် (POS dropdown)
        return [IsInventoryManagerOrHigher()]

# ----------------------------------------------------
# 2. Product Views
# ----------------------------------------------------
class ProductListAPIView(generics.ListAPIView):
    """POS product list. Cashier+ only; cost hidden for Cashier role."""
    serializer_class = ProductListSerializer
    permission_classes = [IsCashierOrHigher]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        base = Product.objects.select_related('category', 'base_unit', 'purchase_unit')
        if is_owner(user):
            return base.all().order_by('name')

        try:
            outlet_id = getattr(user, "primary_outlet_id", None)
            if not outlet_id:
                return Product.objects.none()
            assigned_locs = getattr(user, "assigned_locations", None)
            if assigned_locs is None:
                return Product.objects.none()
            assigned_locs = assigned_locs.filter(outlet_id=outlet_id)
            if not assigned_locs.exists():
                return Product.objects.none()

            from core.models import StaffSession
            session = getattr(user, "work_sessions", None)
            session = session.filter(is_active=True).first() if session is not None else None
            location = session.location if session else getattr(user, "primary_location", None)
            if location and getattr(location, "outlet_id", None) != outlet_id:
                location = None
            if not location:
                location = assigned_locs.filter(is_sale_location=True).first()
            locs_to_use = [location] if location else list(assigned_locs.filter(is_sale_location=True))
            if not locs_to_use:
                return Product.objects.none()

            qty_zero = Value(0, output_field=IntegerField())
            return base.annotate(
                current_stock=Coalesce(Sum('inventorymovement_set__quantity', filter=Q(inventorymovement_set__to_location__in=locs_to_use)), qty_zero, output_field=IntegerField()) -
                              Coalesce(Sum('inventorymovement_set__quantity', filter=Q(inventorymovement_set__from_location__in=locs_to_use)), qty_zero, output_field=IntegerField())
            ).order_by('name')
        except Exception:
            return Product.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        user = self.request.user
        try:
            from core.models import StaffSession
            session = getattr(user, "work_sessions", None)
            session = session.filter(is_active=True).first() if session is not None else None
            location = session.location if session else getattr(user, "primary_location", None)
            if not location:
                al = getattr(user, "assigned_locations", None)
                location = al.filter(is_sale_location=True).first() if al is not None else None
        except Exception:
            location = None
        context['sale_location'] = location
        context['hide_cost'] = is_cashier_role(user)  # Cashier cannot see purchase costs
        return context

class ProductViewSet(viewsets.ModelViewSet):
    """Inventory products with server-side pagination (PAGE_SIZE from settings)."""
    queryset = Product.objects.all().select_related('category', 'base_unit', 'purchase_unit').order_by('name')
    serializer_class = ProductSerializer
    permission_classes = [IsAdminOrHigher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'model_no', 'category__name']
    ordering_fields = ['name', 'sku', 'retail_price', 'cost_price', 'created_at']
    ordering = ['name']


class ProductLookupBySkuView(APIView):
    """SKU ဖြင့် Product ရှာခြင်း (Barcode/QR scan အတွက်)"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sku = request.query_params.get('sku', '').strip()
        if not sku:
            return Response({'found': False, 'product': None}, status=200)
        try:
            product = Product.objects.select_related('category').get(sku=sku)
            from .serializers import ProductSerializer
            return Response({
                'found': True,
                'product': ProductSerializer(product).data,
            }, status=200)
        except Product.DoesNotExist:
            return Response({'found': False, 'product': None, 'sku': sku}, status=200)


class ProductSearchView(APIView):
    """Search product by code: GET ?q= — tries SKU then serial_number (IMEI/barcode). Same response shape as lookup."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        q = (request.query_params.get('q') or '').strip()
        if not q:
            return Response({'found': False, 'product': None}, status=200)
        from .serializers import ProductSerializer
        # 1) Exact SKU match
        try:
            product = Product.objects.select_related('category').get(sku__iexact=q)
            return Response({'found': True, 'product': ProductSerializer(product).data}, status=200)
        except Product.DoesNotExist:
            pass
        # 2) Serial/IMEI: match serial_number then return that product
        try:
            serial_item = SerialItem.objects.select_related('product', 'product__category').filter(
                serial_number__iexact=q
            ).first()
            if serial_item and serial_item.product_id:
                return Response({
                    'found': True,
                    'product': ProductSerializer(serial_item.product).data,
                }, status=200)
        except Exception:
            pass
        return Response({'found': False, 'product': None, 'q': q}, status=200)


class ProductImportPreviewView(APIView):
    """
    POST: multipart/form-data with `file` (Excel or CSV) only.
    Returns: { "columns": ["Col1", "Col2", ...], "sample": [first row values] } for column mapping UI.
    """
    permission_classes = [IsInventoryManagerOrHigher]

    def post(self, request):
        import math
        import pandas as pd

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'Missing file. Send "file" (Excel or CSV).'}, status=status.HTTP_400_BAD_REQUEST)

        name = (file_obj.name or '').lower()
        try:
            if name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_obj)
            else:
                df = pd.read_csv(file_obj)
        except Exception as e:
            return Response({'error': f'Could not read file: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        if df.empty:
            return Response({'columns': [], 'sample': []}, status=status.HTTP_200_OK)

        columns = [str(c).strip() for c in df.columns.tolist()]
        first = df.iloc[0]
        sample = []
        for v in first.tolist():
            if v is None or (isinstance(v, float) and math.isnan(v)):
                sample.append('')
            else:
                sample.append(str(v).strip()[:100])

        return Response({'columns': columns, 'sample': sample}, status=status.HTTP_200_OK)


class ProductBulkImportView(APIView):
    """
    Bulk import products from Excel/CSV.
    TODO: Implement Celery background tasks for massive Excel imports to avoid blocking
    the main thread and prevent server crashes (SRE: non-blocking bulk import).
    POST: multipart/form-data with `file` (Excel or CSV) and `mapping` (JSON string).
    mapping example: {"Model": "model_no", "Product Name": "name", "SKU": "sku", "Price": "retail_price", "Qty": "quantity"}
    - If model_no exists: update stock (inbound movement). Requires optional `location_id` for stock.
    - If model_no does not exist: create new product (name, sku mandatory).
    Returns: { "imported", "updated", "failed", "errors": [{"row", "reason"}] }
    """
    permission_classes = [IsInventoryManagerOrHigher]

    def _safe_decimal(self, val, default=None):
        if val is None or (isinstance(val, float) and __import__('math').isnan(val)):
            return default
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        try:
            return Decimal(str(val).strip())
        except (InvalidOperation, ValueError):
            return default

    def _safe_int(self, val, default=0):
        if val is None or (isinstance(val, float) and __import__('math').isnan(val)):
            return default
        try:
            return int(float(val))
        except (ValueError, TypeError):
            return default

    def _safe_str(self, val, max_len=500):
        if val is None or (isinstance(val, float) and __import__('math').isnan(val)):
            return None
        s = str(val).strip()
        return s[:max_len] if s else None

    def post(self, request):
        import pandas as pd

        file_obj = request.FILES.get('file')
        mapping_raw = request.data.get('mapping') or request.POST.get('mapping')
        location_id = request.data.get('location_id') or request.POST.get('location_id')

        if not file_obj:
            return Response(
                {'error': 'Missing file. Send "file" (Excel/CSV) and "mapping" (JSON).'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if not mapping_raw:
            return Response(
                {'error': 'Missing mapping. Example: {"Column A": "model_no", "Column B": "name", "SKU": "sku"}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            mapping = json.loads(mapping_raw) if isinstance(mapping_raw, str) else mapping_raw
        except json.JSONDecodeError as e:
            return Response({'error': f'Invalid mapping JSON: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        if not mapping or not isinstance(mapping, dict):
            return Response({'error': 'mapping must be a non-empty object.'}, status=status.HTTP_400_BAD_REQUEST)

        location = None
        if location_id:
            try:
                location = Location.objects.get(pk=int(location_id))
            except (Location.DoesNotExist, ValueError):
                pass
        if not location:
            location = Location.objects.filter(is_sale_location=True).first()

        name = (file_obj.name or '').lower()
        try:
            if name.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_obj)
            else:
                df = pd.read_csv(file_obj)
        except Exception as e:
            return Response({'error': f'Could not read file: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        if df.empty:
            return Response({
                'imported': 0, 'updated': 0, 'failed': 0,
                'errors': [{'row': 0, 'reason': 'File has no rows.'}],
            }, status=status.HTTP_200_OK)

        # Rename columns by mapping (excel_col -> our field name)
        rename = {}
        for col in df.columns:
            col_str = str(col).strip()
            if col_str in mapping:
                rename[col] = mapping[col_str]
        df = df.rename(columns=rename)

        imported = 0
        updated = 0
        failed = 0
        errors = []

        for idx, row in df.iterrows():
            row_num = int(idx) + 2  # 1-based + header
            row_errors = []

            def get(field):
                if field not in df.columns:
                    return None
                val = row.get(field)
                if val is None or (isinstance(val, float) and __import__('math').isnan(val)):
                    return None
                return val

            model_no = self._safe_str(get('model_no'), 100)
            name_val = self._safe_str(get('name'), 200)
            sku_val = self._safe_str(get('sku'), 50)
            quantity_val = self._safe_decimal(get('quantity'), None)
            if quantity_val is not None and quantity_val < 0:
                quantity_val = Decimal('0')

            existing = None
            if model_no:
                existing = Product.objects.filter(model_no=model_no).first()

            if existing:
                if quantity_val is not None and quantity_val > 0 and location:
                    try:
                        with transaction.atomic():
                            InventoryMovement.objects.create(
                                product=existing,
                                quantity=quantity_val,
                                movement_type='inbound',
                                to_location=location,
                                from_location=None,
                                moved_by=request.user,
                                notes='Bulk import stock',
                                outlet_id=location.outlet_id,
                            )
                        updated += 1
                    except Exception as e:
                        row_errors.append(str(e))
                        failed += 1
                        errors.append({'row': row_num, 'reason': f'Stock update failed: {e}'})
                else:
                    updated += 1
                continue

            if not name_val:
                failed += 1
                errors.append({
                    'row': row_num,
                    'reason': 'Missing mandatory field: name required for new product.',
                })
                continue

            # SKU မပါရင် သို့မဟုတ် ထပ်နေရင် product name ကနေ auto-generate (barcode/scanner နဲ့ အဆင်ပြေ)
            if not sku_val or Product.objects.filter(sku=sku_val).exists():
                sku_val = generate_unique_sku(name_val)

            category = None
            cat_name = self._safe_str(get('category_name'), 100)
            if cat_name:
                category = Category.objects.filter(name__iexact=cat_name).first()

            retail_price = self._safe_decimal(get('retail_price'), Decimal('0'))
            cost_price = self._safe_decimal(get('cost_price'), Decimal('0'))
            warranty_months = self._safe_int(get('warranty_months'), 0)
            is_serial = bool(get('is_serial_tracked'))
            serial_required = bool(get('serial_number_required'))

            try:
                with transaction.atomic():
                    product = Product.objects.create(
                        name=name_val,
                        sku=sku_val,
                        model_no=model_no or None,
                        category=category,
                        retail_price=retail_price or Decimal('0'),
                        cost_price=cost_price or Decimal('0'),
                        warranty_months=max(0, warranty_months),
                        is_serial_tracked=is_serial,
                        serial_number_required=serial_required,
                    )
                    if quantity_val is not None and quantity_val > 0 and location:
                        InventoryMovement.objects.create(
                            product=product,
                            quantity=quantity_val,
                            movement_type='inbound',
                            to_location=location,
                            from_location=None,
                            moved_by=request.user,
                            notes='Bulk import',
                            outlet_id=location.outlet_id,
                        )
                    imported += 1
            except Exception as e:
                failed += 1
                errors.append({'row': row_num, 'reason': str(e)})

        return Response({
            'imported': imported,
            'updated': updated,
            'failed': failed,
            'errors': errors,
        }, status=status.HTTP_200_OK)


class SyncPricesView(APIView):
    """
    POST: body { "exchange_rate": 2100 } (optional "round_base": 100).
    Runs sync_all_prices(exchange_rate) and returns { "updated_count", "exchange_rate" }.
    """
    permission_classes = [IsAdminOrHigher]

    def post(self, request):
        rate = request.data.get('exchange_rate')
        if rate is None:
            from .services import get_usd_exchange_rate
            rate = get_usd_exchange_rate()
            if rate is None:
                return Response(
                    {'error': 'exchange_rate required in body or set in GlobalSetting'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        try:
            rate = Decimal(str(rate))
        except Exception:
            return Response({'error': 'Invalid exchange_rate'}, status=status.HTTP_400_BAD_REQUEST)
        round_base = request.data.get('round_base', 100)
        from .services import sync_all_prices
        updated = sync_all_prices(rate, round_base=int(round_base))
        return Response({
            'updated_count': updated,
            'exchange_rate': str(rate),
        }, status=status.HTTP_200_OK)


class GlobalSettingExchangeRateView(APIView):
    """GET/PATCH usd_exchange_rate for POS header and frontend recalc.
    Owner/Admin/Manager can always edit. When DEBUG (testing), any staff can edit."""

    def get_permissions(self):
        if self.request.method == 'PATCH':
            from django.conf import settings
            if getattr(settings, 'DEBUG', False):
                return [IsStaffOrHigher()]
            return [IsAdminOrHigher()]
        return [IsStaffOrHigher()]

    def get(self, request):
        from .models import GlobalSetting, ExchangeRateLog
        from django.utils import timezone

        row = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
        rate = None
        is_auto_sync = True
        if row:
            rate = row.get_active_usd_rate
            if rate:
                rate = str(rate)
            is_auto_sync = row.is_auto_sync if row.is_auto_sync is not None else True
        else:
            # No GlobalSetting yet: use latest from ExchangeRateLog if any
            latest = ExchangeRateLog.objects.filter(currency='USD').order_by('-date', '-id').first()
            if latest and latest.rate:
                rate = str(latest.rate)

        # Lazy init: if still no rate, try web scraping once so "–" မပြတော့ဘူး
        if not rate and request.user and getattr(request.user, 'is_authenticated', True):
            try:
                from .scraper_service import scrape_cbm_usd_rate
                scraped = scrape_cbm_usd_rate()
                if scraped is not None:
                    gs, _ = GlobalSetting.objects.get_or_create(
                        key='usd_exchange_rate',
                        defaults={'value_decimal': scraped, 'is_auto_sync': True}
                    )
                    if not gs.value_decimal:
                        gs.value_decimal = scraped
                        gs.save(update_fields=['value_decimal'])
                    today = timezone.now().date()
                    ExchangeRateLog.objects.update_or_create(
                        date=today, currency='USD',
                        defaults={'rate': scraped, 'source': 'Scraped'}
                    )
                    rate = str(scraped)
            except Exception:
                pass

        manual = str(row.manual_usd_rate) if row and getattr(row, 'manual_usd_rate', None) else None
        return Response({
            'usd_exchange_rate': rate,
            'is_auto_sync': is_auto_sync,
            'manual_usd_rate': manual,
        })

    def patch(self, request):
        gs, _ = GlobalSetting.objects.get_or_create(
            key='usd_exchange_rate',
            defaults={'is_auto_sync': True}
        )
        
        # Handle hybrid system fields
        is_auto_sync = request.data.get('is_auto_sync')
        manual_usd_rate = request.data.get('manual_usd_rate')
        legacy_rate = request.data.get('usd_exchange_rate')  # Legacy support
        
        # Update is_auto_sync
        if is_auto_sync is not None:
            gs.is_auto_sync = bool(is_auto_sync)
        
        # Update manual_usd_rate
        if manual_usd_rate is not None:
            try:
                gs.manual_usd_rate = Decimal(str(manual_usd_rate))
            except (ValueError, InvalidOperation):
                return Response({'error': 'Invalid manual_usd_rate'}, status=status.HTTP_400_BAD_REQUEST)
        elif manual_usd_rate is None and not gs.is_auto_sync:
            # If switching to manual but no rate provided, keep existing
            pass
        
        # Legacy support: if usd_exchange_rate is provided, update value_decimal
        if legacy_rate is not None:
            try:
                rate = Decimal(str(legacy_rate))
                gs.value_decimal = rate
            except (ValueError, InvalidOperation):
                return Response({'error': 'Invalid usd_exchange_rate'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_rate = gs.get_active_usd_rate
        gs.save()
        
        # Get new active rate
        new_rate = gs.get_active_usd_rate
        # Log rate for Smart Business Insight trend (one per day)
        if new_rate:
            from django.utils import timezone
            from .models import ExchangeRateLog
            today = timezone.now().date()
            source = 'Manual' if not gs.is_auto_sync else 'CBM'
            ExchangeRateLog.objects.update_or_create(
                date=today,
                currency='USD',
                defaults={'rate': new_rate, 'source': source}
            )
            # Auto-adjust: ဒေါ်လာဈေးပြောင်းတိုင်း DYNAMIC_USD ပစ္စည်းဈေးများ DB ထဲ ပြန်တင်
            from .services import sync_all_prices
            round_base = request.data.get('round_base', 100)
            prices_synced_count = sync_all_prices(new_rate, round_base=int(round_base))
        else:
            prices_synced_count = 0
        
        # AI Insight: Check for >1% change and notify Owner
        if old_rate and new_rate:
            rate_change_percent = abs((float(new_rate) - float(old_rate)) / float(old_rate)) * 100
            if rate_change_percent > 1.0:
                from core.models import User, Role
                owner_role = Role.objects.filter(name__iexact='owner').first()
                if owner_role:
                    owners = User.objects.filter(role_obj=owner_role)
                    trend = 'increased' if new_rate > old_rate else 'decreased'
                    trend_icon = '📈' if new_rate > old_rate else '📉'
                    message = (
                        f"{trend_icon} USD Exchange Rate {trend} by {rate_change_percent:.2f}%: "
                        f"{old_rate:,.2f} → {new_rate:,.2f} MMK. "
                        f"DYNAMIC_USD product prices have been auto-synced. "
                        f"Consider reviewing pricing strategy."
                    )
                    for owner in owners:
                        Notification.objects.create(
                            recipient=owner,
                            notification_type='rate_change',
                            message=message,
                            is_read=False,
                        )
        
        return Response({
            'usd_exchange_rate': str(new_rate) if new_rate else None,
            'prices_synced_count': prices_synced_count,
            'is_auto_sync': gs.is_auto_sync if gs.is_auto_sync is not None else True,
            'manual_usd_rate': str(gs.manual_usd_rate) if gs.manual_usd_rate else None,
        })


BUSINESS_TYPE_CHOICES = [
    ('phone_electronics', 'Phone/Electronics'),
    ('pharmacy_clinic', 'Pharmacy/Clinic'),
    ('hardware_store', 'Hardware Store'),
    ('solar_aircon', 'Solar/Air-con'),
    ('general_retail', 'General Retail'),
]


class BusinessTypeSettingView(APIView):
    """GET/PATCH business_type for Industry Engine. Values: phone_electronics, pharmacy_clinic, hardware_store, solar_aircon, general_retail."""

    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAdminOrHigher()]
        return [IsStaffOrHigher()]

    def get(self, request):
        gs = GlobalSetting.objects.filter(key='business_type').first()
        value = (gs.value or '').strip() if gs else ''
        if value not in [c[0] for c in BUSINESS_TYPE_CHOICES]:
            value = 'general_retail'
        return Response({'business_type': value})

    def patch(self, request):
        value = (request.data.get('business_type') or '').strip()
        if value not in [c[0] for c in BUSINESS_TYPE_CHOICES]:
            return Response({'error': 'Invalid business_type'}, status=status.HTTP_400_BAD_REQUEST)
        gs, _ = GlobalSetting.objects.get_or_create(key='business_type', defaults={'value': value})
        gs.value = value
        gs.save()
        return Response({'business_type': gs.value})


class ServiceInstallationSettingView(APIView):
    """GET/PATCH enable_service, enable_installation, enable_treatment_records. When false, hide from UI."""
    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAdminOrHigher()]
        return [IsStaffOrHigher()]

    def _get_bool(self, key, default=True):
        gs = GlobalSetting.objects.filter(key=key).first()
        if not gs or not gs.value:
            return default
        return (gs.value or '').strip().lower() in ('1', 'true', 'yes')

    def get(self, request):
        return Response({
            'enable_service': self._get_bool('enable_service', True),
            'enable_installation': self._get_bool('enable_installation', True),
            'enable_treatment_records': self._get_bool('enable_treatment_records', True),
        })

    def patch(self, request):
        enable_service = request.data.get('enable_service')
        enable_installation = request.data.get('enable_installation')
        enable_treatment_records = request.data.get('enable_treatment_records')
        if enable_service is not None:
            gs, _ = GlobalSetting.objects.get_or_create(key='enable_service', defaults={'value': 'true'})
            gs.value = 'true' if enable_service else 'false'
            gs.save()
        if enable_installation is not None:
            gs, _ = GlobalSetting.objects.get_or_create(key='enable_installation', defaults={'value': 'true'})
            gs.value = 'true' if enable_installation else 'false'
            gs.save()
        if enable_treatment_records is not None:
            gs, _ = GlobalSetting.objects.get_or_create(key='enable_treatment_records', defaults={'value': 'true'})
            gs.value = 'true' if enable_treatment_records else 'false'
            gs.save()
        return Response({
            'enable_service': self._get_bool('enable_service', True),
            'enable_installation': self._get_bool('enable_installation', True),
            'enable_treatment_records': self._get_bool('enable_treatment_records', True),
        })


class ProductFieldSettingsView(APIView):
    """GET/PATCH product creation toggles: show_warranty, show_expiry_date, show_model_number, enabled_unit_ids (list)."""
    def get_permissions(self):
        if self.request.method == 'PATCH':
            return [IsAdminOrHigher()]
        return [IsStaffOrHigher()]

    def _get_json(self, key, default):
        gs = GlobalSetting.objects.filter(key=key).first()
        if not gs or not gs.value:
            return default
        try:
            import json
            return json.loads(gs.value)
        except Exception:
            return default

    def _set_json(self, key, value):
        import json
        gs, _ = GlobalSetting.objects.get_or_create(key=key, defaults={'value': '{}'})
        gs.value = json.dumps(value)
        gs.save()

    def get(self, request):
        data = self._get_json('product_field_settings', {})
        return Response({
            'show_warranty': data.get('show_warranty', True),
            'show_expiry_date': data.get('show_expiry_date', True),
            'show_model_number': data.get('show_model_number', True),
            'enabled_unit_ids': data.get('enabled_unit_ids', []),
        })

    def patch(self, request):
        data = self._get_json('product_field_settings', {})
        if request.data.get('show_warranty') is not None:
            data['show_warranty'] = bool(request.data.get('show_warranty'))
        if request.data.get('show_expiry_date') is not None:
            data['show_expiry_date'] = bool(request.data.get('show_expiry_date'))
        if request.data.get('show_model_number') is not None:
            data['show_model_number'] = bool(request.data.get('show_model_number'))
        if 'enabled_unit_ids' in request.data:
            ids = request.data.get('enabled_unit_ids')
            data['enabled_unit_ids'] = [int(x) for x in ids] if isinstance(ids, (list, tuple)) else []
        self._set_json('product_field_settings', data)
        return Response({
            'show_warranty': data.get('show_warranty', True),
            'show_expiry_date': data.get('show_expiry_date', True),
            'show_model_number': data.get('show_model_number', True),
            'enabled_unit_ids': data.get('enabled_unit_ids', []),
        })


class ExchangeRateHistoryView(APIView):
    """Get exchange rate history"""
    permission_classes = [IsStaffOrHigher]

    def get(self, request):
        from .models import ExchangeRateLog
        from django.utils import timezone
        from datetime import timedelta

        days = int(request.query_params.get('days', 7))
        limit = int(request.query_params.get('limit', 10))

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        # Get latest rates for each currency
        latest_rates = {}
        for currency in ['USD', 'THB', 'SGD']:
            latest = ExchangeRateLog.objects.filter(
                currency=currency,
                date__lte=end_date
            ).order_by('-date').first()
            if latest:
                latest_rates[currency] = {
                    'rate': float(latest.rate),
                    'date': latest.date.strftime('%Y-%m-%d'),
                    'source': latest.source,
                }

        # Get history
        history = ExchangeRateLog.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('-date', 'currency')[:limit]

        history_list = [
            {
                'currency': h.currency,
                'rate': float(h.rate),
                'date': h.date.strftime('%Y-%m-%d'),
                'source': h.source,
            }
            for h in history
        ]

        return Response({
            'rates': latest_rates,
            'history': history_list,
        })


class ExchangeRateFetchView(APIView):
    """Manually trigger exchange rate fetch and auto-sync DYNAMIC_USD prices.
    When DEBUG (testing), any staff can run."""
    def get_permissions(self):
        from django.conf import settings
        if getattr(settings, 'DEBUG', False):
            return [IsStaffOrHigher()]
        return [IsAdminOrHigher()]

    def post(self, request):
        from django.core.management import call_command
        from .services import sync_all_prices, get_usd_exchange_rate
        try:
            # Fetch rates from CBM API
            call_command('fetch_exchange_rates', '--force')
            
            # Auto-sync DYNAMIC_USD product prices
            rate = get_usd_exchange_rate()
            synced_count = 0
            if rate:
                synced_count = sync_all_prices(rate, round_base=100)
            
            return Response({
                'message': 'Exchange rates fetched and prices synced successfully',
                'prices_synced': synced_count,
            })
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExchangeRateAdjustmentsView(APIView):
    """Get/Set manual rate adjustments (Market Premium % and Manual Fixed Rate).
    When DEBUG (testing), any staff can get/post."""
    def get_permissions(self):
        from django.conf import settings
        if getattr(settings, 'DEBUG', False):
            return [IsStaffOrHigher()]
        return [IsAdminOrHigher()]

    def get(self, request):
        from .models import GlobalSetting
        adjustments = {}
        for currency in ['USD', 'THB', 'SGD']:
            key = f'{currency.lower()}_exchange_rate'
            gs = GlobalSetting.objects.filter(key=key).first()
            if not gs and currency == 'USD':
                gs = GlobalSetting.objects.filter(key='usd_exchange_rate').first()
            if gs:
                adjustments[currency.lower()] = {
                    'market_premium_percentage': float(gs.market_premium_percentage) if gs.market_premium_percentage else None,
                    'manual_fixed_rate': float(gs.manual_fixed_rate) if gs.manual_fixed_rate else None,
                }
            else:
                adjustments[currency.lower()] = {
                    'market_premium_percentage': None,
                    'manual_fixed_rate': None,
                }
        return Response({'adjustments': adjustments})

    def post(self, request):
        from .models import GlobalSetting
        adjustments = request.data

        for currency in ['USD', 'THB', 'SGD']:
            key = f'{currency.lower()}_exchange_rate'
            if currency == 'USD':
                # Also check usd_exchange_rate for backward compatibility
                key = 'usd_exchange_rate'

            currency_data = adjustments.get(currency.lower(), {})
            premium = currency_data.get('market_premium_percentage')
            fixed = currency_data.get('manual_fixed_rate')

            gs, _ = GlobalSetting.objects.get_or_create(key=key)
            gs.market_premium_percentage = Decimal(str(premium)) if premium is not None else None
            gs.manual_fixed_rate = Decimal(str(fixed)) if fixed is not None else None
            gs.save()

        return Response({'message': 'Adjustments saved successfully'})


class ValidateBundleView(APIView):
    """POST: body { bundle_id, selected_items: [{ product_id, quantity }] }. Returns validation result."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        from .models import Bundle
        from .services import validate_bundle
        bundle_id = request.data.get('bundle_id')
        selected_items = request.data.get('selected_items', [])
        if not bundle_id:
            return Response({'error': 'bundle_id required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            bundle = Bundle.objects.get(pk=bundle_id)
        except Bundle.DoesNotExist:
            return Response({'error': 'Bundle not found'}, status=status.HTTP_404_NOT_FOUND)
        result = validate_bundle(bundle, selected_items)
        return Response(result, status=status.HTTP_200_OK)


# ----------------------------------------------------
# 3. Sale Transaction & Approval Views
# ----------------------------------------------------
class SaleRequestCreateView(generics.CreateAPIView):
    serializer_class = SaleRequestSerializer
    permission_classes = [IsCashierOrHigher]

    # def perform_create(self, serializer):
    #     serializer.save(staff=self.request.user, status='pending')

class AdminApprovalView(generics.UpdateAPIView):
    serializer_class = AdminApprovalSerializer
    permission_classes = [IsManagerOrHigher]

    def get_queryset(self):
        return filter_queryset_by_outlet(
            SaleTransaction.objects.filter(status='pending').order_by('-created_at'),
            self.request,
        )

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.save(approved_by=self.request.user, approved_at=timezone.now())
        action = 'sale_approve' if instance.status == 'approved' else 'sale_reject'
        outlet_id = getattr(instance, 'outlet_id', None) or (instance.sale_location.outlet_id if instance.sale_location else None)
        log_audit(self.request.user, action, 'SaleTransaction', instance.id, outlet_id=outlet_id, details={'invoice_number': instance.invoice_number, 'status': instance.status})
        if instance.status == 'approved':
            location = instance.sale_location
            if not location:
                raise serializers.ValidationError("Location မပါဝင်ပါ။")

            # ၂။ ဘောက်ချာထဲက ပစ္စည်းတစ်ခုချင်းစီကို Loop ပတ်သည်
            for item in instance.sale_items.all():
                product = item.product
                
                # Stock စစ်ခြင်း
                available = product.get_stock_by_location(location)
                if available < item.quantity:
                    raise serializers.ValidationError(f"{product.name} လက်ကျန်မလောက်ပါ။")

                # Stock Out မှတ်တမ်းသွင်းခြင်း (outbound from Shopfloor of sale outlet)
                outlet = getattr(instance, 'outlet_id', None) or (location.outlet_id if location else None)
                InventoryMovement.objects.create(
                    product=product,
                    quantity=item.quantity,
                    movement_type='outbound',
                    from_location=location,
                    sale_transaction=instance,
                    moved_by=self.request.user,
                    outlet_id=outlet,
                )

                # ၃။ ✅ Serial Number Logic ကို ပြုပြင်ခြင်း
                # SaleItem model မှာ serial_number ဆိုတဲ့ field ရှိမရှိ သေချာစစ်ပါ
                # မရှိလျှင် AttributeError မတက်အောင် getattr ကို သုံးထားသည်
                if product.is_serial_tracked:
                    serial_val = getattr(item, 'serial_number', None) 
                    
                    if serial_val:
                        for serial_item in SerialItem.objects.filter(
                            product=product, 
                            serial_number=serial_val,
                            current_location=location
                        ):
                            serial_item.status = 'sold'
                            serial_item.sale_transaction = instance
                            serial_item.current_location = None
                            serial_item.save()
                            # Warranty Record ဖန်တီးခြင်း
                            if product.warranty_months > 0:
                                start_date = instance.approved_at.date()
                                end_date = serial_item._add_months(instance.approved_at, product.warranty_months)
                                WarrantyRecord.objects.get_or_create(
                                    serial_item=serial_item,
                                    defaults={
                                        'product': product,
                                        'sale_transaction': instance,
                                        'warranty_start_date': start_date,
                                        'warranty_end_date': end_date
                                    }
                                )
                    else:
                        pass
            

            

class PendingApprovalListView(generics.ListAPIView):
    serializer_class = PendingTransactionSerializer
    permission_classes = [IsManagerOrHigher]

    def get_queryset(self):
        return filter_queryset_by_outlet(
            SaleTransaction.objects.filter(status='pending').order_by('-created_at'),
            self.request,
        )

# ----------------------------------------------------
# 4. Dashboard & Reporting Views (Manager+ only; Cashier/Store Keeper get 403)
# ----------------------------------------------------
class DailySalesSummaryView(APIView):
    permission_classes = [IsManagerOrHigher]
    # FIX: Serializer class ကို instance မဟုတ်ဘဲ class အနေဖြင့်ပေးရမည်
    serializer_class = DailySummarySerializer 
    
    def get(self, request):
        today = timezone.now().date()
        user = request.user

        if is_owner(user):
            outlet_id = get_request_outlet_id(request)
            sales = SaleTransaction.objects.filter(created_at__date=today, status='approved')
            if outlet_id is not None:
                sales = sales.filter(outlet_id=outlet_id)
            history_base = SaleTransaction.objects.filter(status='approved')
            if outlet_id is not None:
                history_base = history_base.filter(outlet_id=outlet_id)
            daily_history = history_base.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                total_sales=Sum('total_amount'),
                count=Count('id')
            ).order_by('-date')[:7]
            return Response({
                "total_revenue": sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
                "total_vouchers": sales.count(),
                "daily_history": list(daily_history),
                "role": user.role_obj.name if user.role_obj else "Owner/Admin"
            })
        else:
            outlet_id = getattr(user, "primary_outlet_id", None)
            if not outlet_id:
                return Response({"total": 0, "count": 0, "role": getattr(user.role_obj, "name", "No Role")})
            staff_sales = SaleTransaction.objects.filter(
                staff=user, outlet_id=outlet_id, created_at__date=today, status='approved'
            )
            return Response({
                "total": staff_sales.aggregate(Sum('total_amount'))['total_amount__sum'] or 0,
                "count": staff_sales.count(),
                "role": user.role_obj.name if user.role_obj else "No Role"
            })

# ----------------------------------------------------
# 5. Inventory Movement Views
# ----------------------------------------------------
# class InventoryMovementCreateView(generics.CreateAPIView):
#     serializer_class = InventoryMovementSerializer
#     permission_classes = [IsInventoryManagerOrHigher]

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)

class InventoryMovementListView(generics.ListAPIView):
    """Store Keeper+ only. Cashier cannot see movements."""
    serializer_class = InventoryMovementSerializer
    permission_classes = [IsStoreKeeperOrHigher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['product__name', 'notes']
    ordering_fields = ['created_at', 'quantity', 'movement_type']
    ordering = ['-created_at']
    filterset_fields = ['product', 'from_location', 'to_location', 'product__category']

    def get_queryset(self):
        return filter_queryset_by_outlet(
            InventoryMovement.objects.all().select_related('product', 'product__base_unit', 'from_location', 'to_location', 'moved_by').order_by('-created_at'),
            self.request,
        )


# ----------------------------------------------------
# Owner Super-Admin Dashboard (Multi-Outlet)
# ----------------------------------------------------
class OwnerDashboardView(APIView):
    """
    GET: Global dashboard. Manager+ (Owner/Admin/Manager). Cashier/Store Keeper get 403.
    Query params: outlet_id, days=30, movement_limit=50.
    """
    permission_classes = [IsManagerOrHigher]

    def get(self, request):
        from core.outlet_utils import is_owner, get_request_outlet_id
        from core.models import Outlet

        if not is_owner(request.user):
            return Response({"detail": "Owner access required."}, status=status.HTTP_403_FORBIDDEN)

        outlet_id = get_request_outlet_id(request)
        days = max(1, min(365, int(request.GET.get('days', 30))))
        movement_limit = max(1, min(200, int(request.GET.get('movement_limit', 50))))
        period_end = timezone.now().date()
        period_start = period_end - timezone.timedelta(days=days)

        outlets_qs = Outlet.objects.filter(is_active=True).order_by('-is_main_branch', 'name')
        outlets = [{"id": o.id, "name": o.name, "code": o.code, "is_main_branch": o.is_main_branch} for o in outlets_qs]
        if outlet_id is not None:
            outlets_qs = outlets_qs.filter(pk=outlet_id)
            if not outlets_qs.exists():
                return Response({"detail": "Outlet not found."}, status=status.HTTP_404_NOT_FOUND)

        # Stock per outlet: Warehouse and Shopfloor (product-level)
        stock_by_outlet = []
        for outlet in outlets_qs:
            wh = outlet.get_warehouse_location()
            sf = outlet.get_shopfloor_location()
            warehouse_stock = []
            shopfloor_stock = []
            for loc, label in [(wh, warehouse_stock), (sf, shopfloor_stock)]:
                if not loc:
                    continue
                _zero = Value(0, output_field=IntegerField())
                qs = InventoryMovement.objects.filter(
                    Q(to_location=loc) | Q(from_location=loc)
                ).values('product_id', 'product__name').annotate(
                    in_q=Coalesce(Sum(Case(When(to_location=loc, then=F('quantity')), default=Value(0, output_field=IntegerField())), output_field=IntegerField()), _zero, output_field=IntegerField()),
                    out_q=Coalesce(Sum(Case(When(from_location=loc, then=F('quantity')), default=Value(0, output_field=IntegerField())), output_field=IntegerField()), _zero, output_field=IntegerField()),
                ).annotate(stock=F('in_q') - F('out_q')).filter(stock__gt=0)
                for row in qs:
                    label.append({
                        "product_id": row['product_id'],
                        "product_name": row.get('product__name') or '',
                        "quantity": row['stock'],
                    })
            stock_by_outlet.append({
                "outlet_id": outlet.id,
                "outlet_name": outlet.name,
                "warehouse": warehouse_stock,
                "shopfloor": shopfloor_stock,
            })

        # Sales: combined and by outlet
        sales_qs = SaleTransaction.objects.filter(
            status='approved',
            created_at__date__gte=period_start,
            created_at__date__lte=period_end,
        )
        if outlet_id is not None:
            sales_qs = sales_qs.filter(outlet_id=outlet_id)
        sales_combined = sales_qs.aggregate(
            total_amount=Coalesce(Sum('total_amount'), 0),
            count=Count('id'),
        )
        sales_by_outlet = list(
            SaleTransaction.objects.filter(
                status='approved',
                created_at__date__gte=period_start,
                created_at__date__lte=period_end,
            )
            .filter(outlet_id__isnull=False)
            .values('outlet_id', 'outlet__name')
            .annotate(total_amount=Coalesce(Sum('total_amount'), 0), count=Count('id'))
            .order_by('-total_amount')
        )
        if outlet_id is not None:
            sales_by_outlet = [x for x in sales_by_outlet if x['outlet_id'] == outlet_id]

        # Recent movements (Inbound/Outbound) with user and outlet
        movements_qs = InventoryMovement.objects.filter(
            movement_type__in=('inbound', 'outbound', 'transfer')
        ).select_related('product', 'from_location', 'to_location', 'moved_by', 'outlet').order_by('-created_at')[:movement_limit]
        if outlet_id is not None:
            movements_qs = movements_qs.filter(outlet_id=outlet_id)
        movements = [
            {
                "id": m.id,
                "created_at": m.created_at.isoformat() if m.created_at else None,
                "movement_type": m.movement_type,
                "product_id": m.product_id,
                "product_name": m.product.name if m.product_id else None,
                "quantity": m.quantity,
                "from_location": m.from_location.name if m.from_location_id else None,
                "to_location": m.to_location.name if m.to_location_id else None,
                "moved_by_id": m.moved_by_id,
                "moved_by_username": m.moved_by.username if m.moved_by_id else None,
                "outlet_id": m.outlet_id,
                "outlet_name": m.outlet.name if m.outlet_id else None,
            }
            for m in movements_qs
        ]

        return Response({
            "outlets": outlets,
            "current_outlet_id": outlet_id,
            "stock_by_outlet": stock_by_outlet,
            "sales_combined": {
                "total_amount": str(sales_combined['total_amount']),
                "count": sales_combined['count'],
                "period_start": str(period_start),
                "period_end": str(period_end),
            },
            "sales_by_outlet": sales_by_outlet,
            "movements": movements,
        }, status=status.HTTP_200_OK)


class InventoryInboundView(APIView):
    """Store Keeper+ only. Inbound to outlet's locations."""
    permission_classes = [IsStoreKeeperOrHigher]

    @transaction.atomic
    def post(self, request):
        try:
            raw_product = request.data.get('product')
            raw_to_loc = request.data.get('to_location')
            if raw_product is None or raw_product == '':
                return Response({"error": "product is required."}, status=400)
            if raw_to_loc is None or raw_to_loc == '':
                return Response({"error": "to_location is required."}, status=400)
            try:
                product_id = int(raw_product)
                to_loc_id = int(raw_to_loc)
            except (TypeError, ValueError):
                return Response({"error": "product and to_location must be valid ids."}, status=400)

            qty = _parse_quantity(request.data.get('quantity'), 1)
            unit_id = request.data.get('unit')
            notes = request.data.get('notes', 'Initial Inbound')

            try:
                product = Product.objects.select_related('base_unit', 'purchase_unit').get(id=product_id)
            except Product.DoesNotExist:
                return Response({"error": "Product ရှာမတွေ့ပါ"}, status=400)
            try:
                to_loc = Location.objects.get(id=to_loc_id)
            except Location.DoesNotExist:
                return Response({"error": "တည်နေရာ ရှာမတွေ့ပါ"}, status=400)
            if not user_can_access_location(request.user, to_loc):
                return Response({"error": "ဤတည်နေရာသို့ အဝင်မှတ်ပုံတင်ရန် ခွင့်ပြုချက်မရှိပါ။"}, status=403)

            # Convert quantity to base unit if unit_id is product's purchase_unit
            quantity_in_base = qty
            if unit_id is not None and unit_id != '':
                try:
                    uid = int(unit_id)
                    if product.purchase_unit_id and uid == product.purchase_unit_id and (product.purchase_unit_factor or 0) > 0:
                        quantity_in_base = int(Decimal(str(qty)) * (product.purchase_unit_factor or 1))
                except (TypeError, ValueError):
                    pass

            # ၁။ Movement Record ကို အဝင် (Inbound) အဖြစ် မှတ်တမ်းတင်ခြင်း (outlet = to_location's outlet)
            movement = InventoryMovement.objects.create(
                product=product,
                from_location=None,  # Inbound ဖြစ်၍ မူရင်းနေရာ မရှိပါ
                to_location=to_loc,
                quantity=quantity_in_base,
                movement_type='inbound',
                moved_by=request.user,
                notes=notes,
                outlet_id=to_loc.outlet_id,
            )

            # ၂။ Serial Tracking ရှိပါက SerialItem များကို အလိုအလျောက် Create လုပ်ခြင်း (decimal qty → int count)
            if product.is_serial_tracked:
                for _ in range(int(quantity_in_base)):
                    # serial_number မပို့ဘဲ save လုပ်လိုက်လျှင် Model save() က Auto Generate လုပ်ပေးမည်
                    SerialItem.objects.create(
                        product=product,
                        current_location=to_loc,
                        status='in_stock'
                    )

            log_audit(request.user, 'movement_inbound', 'InventoryMovement', movement.id, outlet_id=to_loc.outlet_id, details={'product_id': product_id, 'quantity': int(quantity_in_base)})
            return Response({
                "message": "Stock အသစ်ထည့်သွင်းခြင်း အောင်မြင်ပါသည်",
                "movement_id": movement.id
            }, status=201)

        except Exception as e:
            return Response({"error": str(e)}, status=400)


class StockCountSubmitView(APIView):
    """Store Keeper+ only. Submit stock count: adjust stock at a location to counted quantity."""
    permission_classes = [IsStoreKeeperOrHigher]

    @transaction.atomic
    def post(self, request):
        try:
            location_id = request.data.get('location')
            lines = request.data.get('lines') or []
            if not location_id:
                return Response({"error": "location is required."}, status=400)
            if not lines:
                return Response({"error": "lines (product, counted_quantity) are required."}, status=400)
            try:
                to_loc = Location.objects.get(id=location_id)
            except Location.DoesNotExist:
                return Response({"error": "တည်နေရာ ရှာမတွေ့ပါ"}, status=400)
            if not user_can_access_location(request.user, to_loc):
                return Response({"error": "ဤတည်နေရာသို့ ခွင့်ပြုချက်မရှိပါ။"}, status=403)

            created = []
            for i, row in enumerate(lines):
                product_id = row.get('product') or row.get('product_id')
                counted = _parse_quantity(row.get('counted_quantity'), 0)
                if not product_id:
                    continue
                try:
                    product = Product.objects.get(id=product_id)
                except Product.DoesNotExist:
                    continue
                current = product.get_stock_by_location(to_loc) or 0
                current = int(current)
                diff = counted - current
                if diff == 0:
                    continue
                outlet_id = getattr(to_loc, 'outlet_id', None)
                if diff > 0:
                    movement = InventoryMovement.objects.create(
                        product=product,
                        from_location=None,
                        to_location=to_loc,
                        quantity=diff,
                        movement_type='adjustment',
                        moved_by=request.user,
                        outlet_id=outlet_id,
                        notes=f"Stock count: set to {counted}",
                    )
                else:
                    movement = InventoryMovement.objects.create(
                        product=product,
                        from_location=to_loc,
                        to_location=None,
                        quantity=abs(diff),
                        movement_type='adjustment',
                        moved_by=request.user,
                        outlet_id=outlet_id,
                        notes=f"Stock count: set to {counted}",
                    )
                created.append({"product_id": product.id, "movement_id": movement.id})
            return Response({"message": "Stock count သိမ်းပြီးပါပြီ။", "created": created}, status=201)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class UnitListView(generics.ListAPIView):
    """List units for dropdowns. Optional ?business_category=pharmacy|solar|... to show only that type's units."""
    permission_classes = [IsAuthenticated]
    serializer_class = UnitSerializer
    queryset = Unit.objects.all().order_by('category', 'order', 'name_en')

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('business_category', '').strip().lower()
        if category:
            from core.unit_templates import get_unit_codes_for_business_category
            codes = get_unit_codes_for_business_category(category)
            if codes:
                qs = qs.filter(code__in=codes)
        return qs


class PurchaseListView(generics.ListAPIView):
    """List purchases (Store Keeper+). Filter by outlet via query param."""
    permission_classes = [IsStoreKeeperOrHigher]
    serializer_class = PurchaseSerializer
    queryset = Purchase.objects.all().prefetch_related('lines', 'lines__product', 'lines__purchase_unit')

    def get_queryset(self):
        qs = super().get_queryset()
        outlet_id = get_request_outlet_id(self.request) or self.request.query_params.get('outlet')
        if outlet_id is not None:
            qs = qs.filter(outlet_id=outlet_id)
        return qs.order_by('-created_at')


class PurchaseCreateView(APIView):
    """
    Create a purchase: bulk buy with purchase unit → stock in base unit, unit cost calculated.
    POST body: outlet (id), to_location (id, default for all lines), reference, purchase_date, notes,
    lines: [ { product, purchase_unit, quantity, unit_cost [, to_location] }, ... ]
    """
    permission_classes = [IsStoreKeeperOrHigher]

    @transaction.atomic
    def post(self, request):
        ser = PurchaseCreateSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        data = ser.validated_data
        outlet = data.get('outlet')
        default_to_location = data.get('to_location')
        reference = data.get('reference') or ''
        purchase_date = data.get('purchase_date')
        notes = data.get('notes') or ''
        lines_data = data['lines']

        purchase = Purchase.objects.create(
            outlet=outlet,
            reference=reference,
            purchase_date=purchase_date,
            notes=notes,
            created_by=request.user,
        )
        created_lines = []
        for row in lines_data:
            product_id = row.get('product') or row.get('product_id')
            if isinstance(product_id, dict):
                product_id = product_id.get('id')
            product = Product.objects.get(id=product_id)
            purchase_unit_id = row.get('purchase_unit')
            purchase_unit = Unit.objects.filter(id=purchase_unit_id).first() if purchase_unit_id else None
            to_loc_raw = row.get('to_location') or default_to_location
            if to_loc_raw is None:
                return Response(
                    {"error": "to_location is required (per line or in body)."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            to_loc = to_loc_raw if hasattr(to_loc_raw, 'outlet_id') else Location.objects.get(id=to_loc_raw)
            if not user_can_access_location(request.user, to_loc):
                return Response({"error": "ဤတည်နေရာသို့ ခွင့်ပြုချက်မရှိပါ။"}, status=403)
            quantity = _parse_quantity(row.get('quantity'), 1)
            unit_cost = Decimal(str(row.get('unit_cost', 0)))
            base_qty = product.get_purchase_to_base_quantity(purchase_unit, quantity)
            cost_per_base = product.cost_per_base_unit(unit_cost, purchase_unit)

            line = PurchaseLine.objects.create(
                purchase=purchase,
                product=product,
                purchase_unit=purchase_unit,
                quantity=quantity,
                unit_cost=unit_cost,
                to_location=to_loc,
            )
            created_lines.append(line)
            InventoryMovement.objects.create(
                product=product,
                from_location=None,
                to_location=to_loc,
                quantity=base_qty,
                movement_type='inbound',
                moved_by=request.user,
                outlet_id=to_loc.outlet_id,
                notes=f"Purchase #{purchase.id} ({quantity} {getattr(purchase_unit, 'name_en', '')} = {base_qty} base)",
            )
            product.cost_price = cost_per_base
            product.save(update_fields=['cost_price'])
        return Response(
            PurchaseSerializer(purchase).data,
            status=status.HTTP_201_CREATED,
        )


class InventoryTransferView(APIView):
    """Store Keeper+ only. Transfer within or between outlet locations."""
    permission_classes = [IsStoreKeeperOrHigher]
    @transaction.atomic
    def post(self, request):
        try:
            product_id = request.data.get('product')
            to_loc_id = request.data.get('to_location')
            from_loc_id = request.data.get('from_location')  # Inbound ဆိုရင် null လာမယ်
            qty = _parse_quantity(request.data.get('quantity'), 1)
            unit_id = request.data.get('unit')

            product = Product.objects.select_related('base_unit', 'purchase_unit').get(id=product_id)
            try:
                to_loc = Location.objects.get(id=to_loc_id)
            except Location.DoesNotExist:
                return Response({"error": "ပစ်မှတ်တည်နေရာကို ရှာမတွေ့ပါ။"}, status=400)
            if not user_can_access_location(request.user, to_loc):
                return Response({"error": "ပစ်မှတ်တည်နေရာသို့ ခွင့်ပြုချက်မရှိပါ။"}, status=403)

            from_loc = None
            if from_loc_id:
                try:
                    from_loc = Location.objects.get(id=from_loc_id)
                except Location.DoesNotExist:
                    return Response({"error": "မူရင်းတည်နေရာကို ရှာမတွေ့ပါ"}, status=400)
                if not user_can_access_location(request.user, from_loc):
                    return Response({"error": "မူရင်းတည်နေရာသို့ ခွင့်ပြုချက်မရှိပါ။"}, status=403)

            # Convert quantity to base unit if unit_id is product's purchase_unit
            quantity_in_base = qty
            if unit_id is not None and unit_id != '':
                try:
                    uid = int(unit_id)
                    if product.purchase_unit_id and uid == product.purchase_unit_id and (product.purchase_unit_factor or 0) > 0:
                        quantity_in_base = int(Decimal(str(qty)) * (product.purchase_unit_factor or 1))
                except (TypeError, ValueError):
                    pass

            # ၁။ Movement Record ကို သိမ်းဆည်းခြင်း (outlet for audit)
            outlet_id = (to_loc.outlet_id or (from_loc.outlet_id if from_loc else None))
            movement = InventoryMovement.objects.create(
                product=product,
                from_location=from_loc,
                to_location=to_loc,
                quantity=quantity_in_base,
                movement_type='inbound' if not from_loc else 'transfer',
                moved_by=request.user,
                notes=request.data.get('notes', 'Stock Update'),
                outlet_id=outlet_id,
            )

            # ၂။ SerialTrack လုပ်ထားသော ပစ္စည်းဖြစ်ပါက SerialItems များ ထည့်သွင်းခြင်း
            if product.is_serial_tracked:
                if not from_loc:  # Inbound (အသစ်အဝင်)
                    for _ in range(int(quantity_in_base)):
                        # serial_number ကို model ရဲ့ save() method က auto generate လုပ်ပေးပါလိမ့်မယ်
                        SerialItem.objects.create(
                            product=product,
                            current_location=to_loc,
                            status='in_stock'
                        )
                else: # Transfer (လွှဲပြောင်းခြင်း)
                    # Frontend က ပို့ပေးတဲ့ Serial list ကို နေရာပြောင်းပေးမည်
                    serial_nums = request.data.get('serial_numbers', [])
                    if serial_nums:
                        SerialItem.objects.filter(
                            product=product, 
                            serial_number__in=serial_nums
                        ).update(current_location=to_loc)

            log_audit(request.user, 'movement_transfer', 'InventoryMovement', movement.id, outlet_id=outlet_id, details={'product_id': product_id, 'quantity': int(quantity_in_base)})
            return Response({"message": "လုပ်ဆောင်ချက် အောင်မြင်ပါသည်"}, status=201)

        except Product.DoesNotExist:
            return Response({"error": "Product မရှိပါ"}, status=400)
        except Exception as e:
            return Response({"error": str(e)}, status=400)


class FullInventoryReportView(generics.ListAPIView):
    permission_classes = [IsManagerOrHigher]
    serializer_class = ProductSerializer
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['name', 'sku']
    filterset_fields = ['category']

    def get_queryset(self):
        if is_owner(self.request.user):
            return Product.objects.all().order_by('name')
        outlet_id = getattr(self.request.user, "primary_outlet_id", None)
        if not outlet_id:
            return Product.objects.none()
        _zero = Value(0, output_field=IntegerField())
        return Product.objects.annotate(
            total_in=Coalesce(Sum('inventorymovement__quantity', filter=Q(inventorymovement__to_location__outlet_id=outlet_id)), _zero, output_field=IntegerField()),
            total_out=Coalesce(Sum('inventorymovement__quantity', filter=Q(inventorymovement__from_location__outlet_id=outlet_id)), _zero, output_field=IntegerField()),
        ).annotate(
            current_stock=F('total_in') - F('total_out')
        ).order_by('name')

class SalesSummaryReportView(generics.ListAPIView):
    serializer_class = DailySummarySerializer
    permission_classes = [IsManagerOrHigher]

    def get_queryset(self):
        period = self.request.query_params.get('period', 'day').lower()
        if period == 'week':
            truncate_func = TruncWeek
        elif period == 'month':
            truncate_func = TruncMonth
        elif period == 'year':
            truncate_func = TruncYear
        else:
            truncate_func = TruncDate
        base = SaleTransaction.objects.filter(status='approved')
        base = filter_queryset_by_outlet(base, self.request)
        return base.annotate(
            report_date=truncate_func('created_at', output_field=models.DateField())
        ).values('report_date').annotate(
            total_sales_amount=Sum('total_amount'),
            total_items_sold=Count('id'),
            total_revenue=Sum('total_amount')
        ).order_by('-report_date')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        results = [{
            'date': item['report_date'],
            'total_sales_amount': item['total_sales_amount'],
            'total_items_sold': item['total_items_sold'],
            'total_revenue': item['total_revenue']
        } for item in queryset]
        return Response(results)

# ----------------------------------------------------
# 6. Notification Views
# ----------------------------------------------------
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).order_by('-created_at')

class UnreadNotificationCountView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        count = Notification.objects.filter(recipient=request.user, is_read=False).count()
        return Response({'unread_count': count})

class MarkAllAsReadView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return Response({'message': 'All notifications marked as read'})

class NotificationMarkAsReadView(generics.UpdateAPIView):
    queryset = Notification.objects.all()
    serializer_class = NotificationReadSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'pk'

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user)

    def perform_update(self, serializer):
        serializer.save(is_read=True)

# ----------------------------------------------------
# 7. Invoice & History Views
# ----------------------------------------------------
class InvoiceDetailView(generics.RetrieveAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [IsCashierOrHigher]

    def get_queryset(self):
        return filter_queryset_by_outlet(SaleTransaction.objects.all(), self.request)


class InvoicePDFView(generics.RetrieveAPIView):
    """Digital Receipt PDF. Cashier+ (reprint for own outlet)."""
    permission_classes = [IsCashierOrHigher]

    def get_queryset(self):
        return filter_queryset_by_outlet(
            SaleTransaction.objects.filter(status='approved'), self.request
        )

    def retrieve(self, request, *args, **kwargs):
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from django.http import HttpResponse

        instance = self.get_object()
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Invoice-{instance.invoice_number}.pdf"'

        doc = SimpleDocTemplate(response, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        elements.append(Paragraph(f"<b>HoBo Custom Software - Invoice</b>", styles['Title']))
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(f"Invoice No: {instance.invoice_number}", styles['Normal']))
        elements.append(Paragraph(f"Date: {instance.created_at.strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        elements.append(Paragraph(f"Customer: {instance.customer.name if instance.customer else 'Walk-in'}", styles['Normal']))
        elements.append(Paragraph(f"Location: {instance.sale_location.name if instance.sale_location else '-'}", styles['Normal']))
        elements.append(Spacer(1, 20))

        data = [['Product', 'Qty', 'Unit Price', 'Subtotal']]
        for item in instance.sale_items.select_related('product').all():
            data.append([
                item.product.name,
                str(item.quantity),
                f"{item.unit_price:,.0f} MMK",
                f"{item.subtotal:,.0f} MMK"
            ])
        data.append(['', '', 'Total:', f"{instance.total_amount:,.0f} MMK"])
        if instance.discount_amount and instance.discount_amount > 0:
            data.append(['', '', 'Discount:', f"-{instance.discount_amount:,.0f} MMK"])
            data.append(['', '', 'Grand Total:', f"{instance.total_amount - instance.discount_amount:,.0f} MMK"])

        t = Table(data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Thank you for your business!", styles['Normal']))

        doc.build(elements)
        return response


class StaffSaleHistoryListView(generics.ListAPIView):
    serializer_class = StaffSaleHistorySerializer
    permission_classes = [IsCashierOrHigher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['invoice_number', 'customer__name', 'customer__phone_number']
    ordering_fields = ['created_at', 'invoice_number', 'total_amount']
    ordering = ['-created_at']

    def get_queryset(self):
        qs = SaleTransaction.objects.exclude(status='pending').select_related('staff', 'customer', 'sale_location', 'outlet').order_by('-created_at')
        qs = filter_queryset_by_outlet(qs, self.request)
        user = self.request.user
        privileged = user.role_obj and user.role_obj.name.lower() in ['owner', 'admin', 'super_admin', 'manager', 'assistant_manager']
        if not privileged:
            qs = qs.filter(staff=user)
        return qs

class InvoiceListView(generics.ListAPIView):
    """Cashier+ can list receipts/invoices (Cashier sees own outlet; Manager+ sees outlet scope).
    Query params: date_from (YYYY-MM-DD), date_to (YYYY-MM-DD), outlet_id, status – for Sales Summary / Receipts / Shift."""
    serializer_class = InvoiceSerializer
    permission_classes = [IsCashierOrHigher]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['invoice_number', 'customer__name', 'customer__phone_number']
    ordering_fields = ['created_at', 'invoice_number', 'total_amount']
    ordering = ['-created_at']
    filterset_fields = ['status', 'sale_location']

    def get_queryset(self):
        qs = SaleTransaction.objects.exclude(status='pending').select_related('staff', 'customer', 'sale_location', 'outlet').order_by('-created_at')
        qs = filter_queryset_by_outlet(qs, self.request)
        user = self.request.user
        role_name = (getattr(user, 'role_obj', None) and getattr(user.role_obj, 'name', '') or '').lower()
        if role_name not in ['owner', 'admin', 'super_admin', 'manager', 'assistant_manager']:
            qs = qs.filter(staff=user)
        params = self.request.query_params
        date_from = params.get('date_from')
        date_to = params.get('date_to')
        outlet_id = params.get('outlet_id')
        if date_from:
            qs = qs.filter(created_at__date__gte=date_from)
        if date_to:
            qs = qs.filter(created_at__date__lte=date_to)
        if outlet_id:
            try:
                qs = qs.filter(outlet_id=int(outlet_id))
            except (ValueError, TypeError):
                pass
        return qs

class InvoiceCancelView(generics.UpdateAPIView):
    """Manager+ only. Cancel voucher and return stock."""
    serializer_class = AdminApprovalSerializer
    permission_classes = [IsManagerOrHigher]

    def get_queryset(self):
        return filter_queryset_by_outlet(SaleTransaction.objects.all(), self.request)

    @transaction.atomic
    def perform_update(self, serializer):
        instance = serializer.save(status='cancelled')
        
        # Serial Items များကို ပြန်လည်သတ်မှတ်ခြင်း
        SerialItem.objects.filter(sale_transaction=instance).update(
            status='in_stock', sale_transaction=None, current_location=instance.sale_location
        )

        # ✅ Voucher အောက်က ပစ္စည်းအားလုံးကို Loop ပတ်ပြီး Stock ပြန်သွင်းရမယ်
        outlet_id = getattr(instance, 'outlet_id', None) or (instance.sale_location.outlet_id if instance.sale_location else None)
        for item in instance.sale_items.all():
            product = item.product
            InventoryMovement.objects.create(
                product=product,
                quantity=item.quantity,
                movement_type='inbound',
                to_location=instance.sale_location,
                moved_by=self.request.user,
                notes=f"Invoice Cancelled: {instance.invoice_number}",
                outlet_id=outlet_id,
            )
        log_audit(self.request.user, 'invoice_cancel', 'SaleTransaction', instance.id, outlet_id=outlet_id, details={'invoice_number': instance.invoice_number})

class LowStockReportView(generics.ListAPIView):
    serializer_class = ProductListSerializer
    permission_classes = [IsManagerOrHigher]

    def get_queryset(self):
        user = self.request.user
        if is_owner(user):
            _zero = Value(0, output_field=IntegerField())
            return Product.objects.annotate(
                total_in=Coalesce(Sum('inventorymovement__quantity', filter=Q(inventorymovement__to_location__isnull=False)), _zero, output_field=IntegerField()),
                total_out=Coalesce(Sum('inventorymovement__quantity', filter=Q(inventorymovement__from_location__isnull=False)), _zero, output_field=IntegerField()),
            ).annotate(
                current_stock=F('total_in') - F('total_out')
            ).filter(current_stock__lte=5).order_by('current_stock')
        outlet_id = getattr(user, "primary_outlet_id", None)
        if not outlet_id:
            return Product.objects.none()
        _zero = Value(0, output_field=IntegerField())
        return Product.objects.annotate(
            total_in=Coalesce(Sum('inventorymovement__quantity', filter=Q(inventorymovement__to_location__outlet_id=outlet_id)), _zero, output_field=IntegerField()),
            total_out=Coalesce(Sum('inventorymovement__quantity', filter=Q(inventorymovement__from_location__outlet_id=outlet_id)), _zero, output_field=IntegerField()),
        ).annotate(
            current_stock=F('total_in') - F('total_out')
        ).filter(current_stock__lte=5).order_by('current_stock')

class SiteViewSet(viewsets.ModelViewSet):
    """ဆိုင်များ/ဆိုင်ခွဲများ။ create_sales_and_warehouse=true ပို့ရင် အရောင်းဆိုင် + ဂိုထောင် Location နှစ်ခု တွဲဖန်တီးမည်။"""
    queryset = Site.objects.all().order_by('name')
    serializer_class = SiteSerializer
    permission_classes = [IsAdminOrHigher]
    pagination_class = None

    def perform_create(self, serializer):
        site = serializer.save()
        if self.request.data.get('create_sales_and_warehouse'):
            base = site.name.strip()
            sales_name = f"{base} - Sales"
            wh_name = f"{base} - Warehouse"
            n = 0
            while Location.objects.filter(name=sales_name).exists():
                n += 1
                sales_name = f"{base} - Sales {n}"
            n = 0
            while Location.objects.filter(name=wh_name).exists():
                n += 1
                wh_name = f"{base} - Warehouse {n}"
            Location.objects.create(
                site=site, name=sales_name, location_type='shop_floor', is_sale_location=True,
            )
            Location.objects.create(
                site=site, name=wh_name, location_type='warehouse', is_sale_location=False,
            )


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [IsAdminOrHigher]
    pagination_class = None
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'site__name', 'outlet__name']
    ordering_fields = ['name', 'location_type']
    ordering = ['name']
    filterset_fields = ['site', 'outlet', 'location_type', 'is_sale_location']

    def get_queryset(self):
        qs = Location.objects.all().order_by('name').select_related('site', 'outlet').prefetch_related('staff_assigned')
        from core.outlet_utils import get_request_outlet_id, is_owner
        outlet_id = get_request_outlet_id(self.request)
        if outlet_id is not None:
            qs = qs.filter(outlet_id=outlet_id)
        elif not is_owner(self.request.user):
            qs = qs.none()
        return qs


class LocationListAPIView(generics.ListAPIView):
    """POS dropdown: Cashier+ see only their outlet's locations."""
    serializer_class = LocationSerializer
    permission_classes = [IsCashierOrHigher]

    def get_queryset(self):
        user = self.request.user
        from core.outlet_utils import is_owner
        if is_owner(user):
            return Location.objects.all().select_related('outlet', 'site').order_by('name')
        outlet_id = getattr(user, 'primary_outlet_id', None)
        if outlet_id is not None:
            return Location.objects.filter(outlet_id=outlet_id).select_related('outlet', 'site').order_by('name')
        if hasattr(user, 'assigned_locations'):
            return user.assigned_locations.all().select_related('outlet', 'site').order_by('name')
        return Location.objects.none()

class StaffSalesSummaryView(APIView):
    permission_classes = [IsCashierOrHigher]

    def get(self, request):
        today = timezone.now().date()
        qs = SaleTransaction.objects.filter(
            staff=request.user,
            created_at__date=today,
            status='approved'
        )
        if not is_owner(request.user):
            oid = getattr(request.user, "primary_outlet_id", None)
            if oid is not None:
                qs = qs.filter(outlet_id=oid)
        summary = qs.aggregate(count=Count('id'), total=Sum('total_amount'))
        return Response({
            "count": summary['count'] or 0,
            "total": summary['total'] or 0,
            "username": request.user.username,
            "date": today
        })



class InventoryTransferView(APIView):
    """Store Keeper+ only. Warehouse to branch transfer."""
    permission_classes = [IsStoreKeeperOrHigher]

    @transaction.atomic
    def post(self, request):
        product_id = request.data.get('product')
        from_loc_id = request.data.get('from_location')
        to_loc_id = request.data.get('to_location')
        qty = _parse_quantity(request.data.get('quantity'), 0)
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"error": "Product ရှာမတွေ့ပါ"}, status=400)
        try:
            from_loc = Location.objects.get(id=from_loc_id)
        except Location.DoesNotExist:
            return Response({"error": "မူရင်းတည်နေရာကို ရှာမတွေ့ပါ"}, status=400)
        try:
            to_loc = Location.objects.get(id=to_loc_id)
        except Location.DoesNotExist:
            return Response({"error": "ပစ်မှတ်တည်နေရာကို ရှာမတွေ့ပါ"}, status=400)
        if not user_can_access_location(request.user, from_loc):
            return Response({"error": "မူရင်းတည်နေရာသို့ ခွင့်ပြုချက်မရှိပါ။"}, status=403)
        if not user_can_access_location(request.user, to_loc):
            return Response({"error": "ပစ်မှတ်တည်နေရာသို့ ခွင့်ပြုချက်မရှိပါ။"}, status=403)
        if product.get_stock_by_location(from_loc) < qty:
            return Response({"error": "မူရင်းနေရာတွင် လက်ကျန်မလုံလောက်ပါ"}, status=400)

        outlet_id = to_loc.outlet_id or getattr(from_loc, 'outlet_id', None)
        InventoryMovement.objects.create(
            product=product,
            from_location_id=from_loc_id,
            to_location_id=to_loc_id,
            quantity=qty,
            movement_type='transfer',
            moved_by=request.user,
            notes=request.data.get('notes', 'Internal Transfer'),
            outlet_id=outlet_id,
        )
        log_audit(request.user, 'movement_transfer', 'InventoryMovement', None, outlet_id=outlet_id, details={'product_id': product_id, 'quantity': int(qty), 'from_location_id': from_loc_id, 'to_location_id': to_loc_id})
        return Response({"message": "Transfer Successful"})


class SerialItemLookupView(generics.ListAPIView):
    serializer_class = SerialItemSerializer
    permission_classes = [IsStaffOrHigher]

    def get_queryset(self):
        product_id = self.request.query_params.get('product')
        location_id = self.request.query_params.get('location')
        return SerialItem.objects.filter(
            product_id=product_id, 
            current_location_id=location_id, 
            status='in_stock'
        )


class SerialItemUpdateView(generics.UpdateAPIView):
    """Serial Number ပြင်ဆင်ခြင်း (Auto-generate ပြင်ချင်လည်းပြင်လို့ရသည်)"""
    queryset = SerialItem.objects.filter(status='in_stock')
    serializer_class = SerialItemSerializer
    permission_classes = [IsInventoryManagerOrHigher]
    http_method_names = ['patch', 'put']

    def get_serializer_class(self):
        from rest_framework import serializers as rf_serializers
        class SerialItemPatchSerializer(rf_serializers.ModelSerializer):
            class Meta:
                model = SerialItem
                fields = ['serial_number']
        return SerialItemPatchSerializer


# ----------------------------------------------------
# 8. Warranty Views
# ----------------------------------------------------
class WarrantyCheckView(APIView):
    """Serial Number ဖြင့် Warranty စစ်ဆေးခြင်း - GET /api/warranty/check/?serial_number=SN-xxx (Public)"""
    permission_classes = [permissions.AllowAny]  # Customer များ စစ်ဆေးနိုင်ရန်

    def get(self, request):
        serial_number = request.query_params.get('serial_number', '').strip()
        if not serial_number:
            return Response({'error': 'serial_number parameter လိုအပ်ပါသည်။'}, status=400)
        try:
            serial_item = SerialItem.objects.select_related('product', 'sale_transaction').get(
                serial_number__iexact=serial_number, status='sold'
            )
        except SerialItem.DoesNotExist:
            return Response({
                'found': False,
                'message': f'Serial No. {serial_number} ရှာမတွေ့ပါ သို့မဟုတ် ရောင်းချပြီးမဟုတ်ပါ။'
            }, status=404)
        try:
            wr = serial_item.warranty_record
            return Response({
                'found': True,
                'serial_number': serial_item.serial_number,
                'product_name': serial_item.product.name,
                'warranty_start_date': wr.warranty_start_date,
                'warranty_end_date': wr.warranty_end_date,
                'is_warranty_active': serial_item.is_warranty_active,
                'invoice_number': serial_item.sale_transaction.invoice_number if serial_item.sale_transaction else None
            })
        except WarrantyRecord.DoesNotExist:
            return Response({
                'found': True,
                'serial_number': serial_item.serial_number,
                'product_name': serial_item.product.name,
                'warranty_start_date': None,
                'warranty_end_date': None,
                'is_warranty_active': False,
                'message': 'Warranty မှတ်တမ်းမရှိပါ (ပစ္စည်းတွင် warranty_months သတ်မှတ်မထားပါ)။'
            })


class WarrantyExpiringSoonView(generics.ListAPIView):
    """သက်တမ်းမကုန်မီ ၃၀ ရက်အတွင်း Warranty ပစ္စည်းများ"""
    permission_classes = [IsInventoryManagerOrHigher]

    def list(self, request, *args, **kwargs):
        from datetime import timedelta
        today = timezone.now().date()
        end_date = today + timedelta(days=30)
        records = WarrantyRecord.objects.filter(
            warranty_end_date__gte=today,
            warranty_end_date__lte=end_date
        ).select_related('serial_item', 'product', 'sale_transaction').order_by('warranty_end_date')
        data = [{
            'serial_number': r.serial_item.serial_number,
            'product_name': r.product.name,
            'warranty_end_date': r.warranty_end_date,
            'days_remaining': (r.warranty_end_date - today).days,
            'invoice_number': r.sale_transaction.invoice_number if r.sale_transaction else None
        } for r in records]
        return Response(data)

#----------------------------------------------------------------
#               Dashboard Views
#-----------------------------------------------------------------
class DashboardAnalyticsView(APIView):
    """Dashboard: Role ရှိသူအားလုံး ကြည့်နိုင် (role အလိုက် stats/charts ပြမည်)."""
    permission_classes = [IsStaffOrHigher]

    def get(self, request):
        try:
            user = request.user
            role_name = (getattr(user.role_obj, 'name', None) or 'staff').lower() if user.role_obj else "staff"

            # Vue ကပို့လိုက်တဲ့ ?period=monthly (သို့) daily, weekly, yearly ကိုယူမယ်
            period = request.query_params.get('period', 'daily').lower()
            date_param = request.query_params.get('date', '').strip()  # optional YYYY-MM-DD for daily
            # ၁။ Date Range သတ်မှတ်ခြင်း
            start_date, single_day = self.get_start_date(period, date_param)

            # Low-stock count: DB annotation (SRE-safe). Fallback to 0 on any query error.
            low_stock_count = 0
            try:
                from django.db.models import IntegerField
                _zero = Value(0, output_field=IntegerField())
                low_stock_count = Product.objects.annotate(
                    inbound=Coalesce(Sum('inventorymovement_set__quantity', filter=Q(inventorymovement_set__to_location__isnull=False)), _zero, output_field=IntegerField()),
                    outbound=Coalesce(Sum('inventorymovement_set__quantity', filter=Q(inventorymovement_set__from_location__isnull=False)), _zero, output_field=IntegerField()),
                ).annotate(total=F('inbound') - F('outbound')).filter(total__lte=5).count()
            except Exception:
                pass

            outlet_id = get_request_outlet_id(request)
            try:
                charts = self.get_charts_by_role(user, role_name, start_date, single_day, outlet_id)
            except Exception:
                charts = {"top_selling": {"labels": [], "values": []}, "service_analytics": {}, "channel_performance": []}
            if is_owner(user):
                try:
                    from accounting.services import get_pnl_by_outlet
                    end_dt = timezone.now().date()
                    pl = get_pnl_by_outlet(start_date, end_dt)
                    charts["pl_by_outlet"] = [
                        {"outlet_name": o["outlet_name"], "net_profit": str(o["net_profit"]), "total_income": str(o["total_income"]), "total_expenses": str(o["total_expenses"])}
                        for o in pl
                    ]
                except Exception:
                    charts["pl_by_outlet"] = []
            try:
                stats = self.get_stats_by_role(user, role_name, low_stock_count, start_date, single_day, outlet_id)
            except Exception:
                stats = {"total_revenue": 0, "active_services": 0, "low_stock_count": low_stock_count, "revenue_growth": "0%", "installation_jobs_count": 0, "today_pl": None}
            try:
                activities = self.get_recent_activities(user, role_name, outlet_id)
            except Exception:
                activities = []
            data = {
                "user_info": {"username": user.username, "role": role_name},
                "stats": stats,
                "charts": charts,
                "recent_activities": activities,
            }
            return Response(data)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Dashboard analytics error")
            # Never return 500: frontend gets 200 with safe defaults so role-based login never sees error
            return Response({
                "user_info": {"username": getattr(request.user, "username", ""), "role": "staff"},
                "stats": {
                    "total_revenue": 0, "active_services": 0, "low_stock_count": 0,
                    "revenue_growth": "0%", "installation_jobs_count": 0, "today_pl": None,
                },
                "charts": {"top_selling": {"labels": [], "values": []}, "service_analytics": {}, "channel_performance": [], "pl_by_outlet": []},
                "recent_activities": [],
            }, status=200)

    def get_start_date(self, period, date_param=''):
        """Period အလိုက် စမှတ် Date ကို တွက်ပေးသော Helper function. date_param=YYYY-MM-DD for daily single-day view."""
        now = timezone.now()
        single_day = False
        if period == 'daily' and date_param:
            try:
                from datetime import datetime
                d = datetime.strptime(date_param, '%Y-%m-%d').date()
                return d, True
            except ValueError:
                pass
        if period == 'daily':
            return now.date(), False
        elif period == 'weekly':
            return (now - timezone.timedelta(days=7)).date(), False
        elif period == 'monthly':
            return (now - timezone.timedelta(days=30)).date(), False
        elif period == 'yearly':
            return (now - timezone.timedelta(days=365)).date(), False
        return None, False

    def get_stats_by_role(self, user, role_name, low_stock_count, start_date, single_day=False, outlet_id=None):
        # Outlet isolation: non-owner must have outlet_id from primary_outlet; owner may filter by outlet_id
        if not is_owner(user):
            outlet_id = getattr(user, "primary_outlet_id", None)
        sales_qs = SaleTransaction.objects.filter(status='approved')
        if outlet_id is not None:
            sales_qs = sales_qs.filter(outlet_id=outlet_id)
        if start_date:
            if single_day:
                sales_qs = sales_qs.filter(created_at__date=start_date)
            else:
                sales_qs = sales_qs.filter(created_at__date__gte=start_date)
        privileged_roles = ['admin', 'owner', 'super_admin', 'manager']
        if role_name not in privileged_roles:
            sales_qs = sales_qs.filter(staff=user)
        total_revenue = sales_qs.aggregate(Sum('total_amount'))['total_amount__sum'] or 0

        # Active services & installation count: only when Settings toggles are on
        enable_service = True
        enable_installation = True
        gs_s = GlobalSetting.objects.filter(key='enable_service').first()
        if gs_s and (gs_s.value or '').strip().lower() in ('0', 'false', 'no'):
            enable_service = False
        gs_i = GlobalSetting.objects.filter(key='enable_installation').first()
        if gs_i and (gs_i.value or '').strip().lower() in ('0', 'false', 'no'):
            enable_installation = False
        active_repairs = RepairService.objects.exclude(status__in=['completed', 'cancelled']).count() if enable_service else 0
        installation_jobs_count = 0
        if enable_installation:
            try:
                from installation.models import InstallationJob
                installation_jobs_count = InstallationJob.objects.count()
            except Exception:
                pass

        stats = {
            "total_revenue": total_revenue,
            "active_services": active_repairs,
            "low_stock_count": low_stock_count,
            "revenue_growth": "12%",
            "installation_jobs_count": installation_jobs_count,
        }

        # ဒီနေ့အရောင်း / P&L — Owner, Manager နှင့် Cashier အားလုံးမှာ အချိန်နဲ့အမျှ ပြရန်
        today = timezone.now().date()
        if role_name in privileged_roles:
            try:
                from accounting.services import calculate_net_profit, calculate_profit_from_sales
                pnl_today = calculate_net_profit(today, today)
                sales_today = calculate_profit_from_sales(today, today)
                stats["today_pl"] = {
                    "total_income": str(pnl_today["total_income"]),
                    "total_expenses": str(pnl_today["total_expenses"]),
                    "net_profit": str(pnl_today["net_profit"]),
                    "profit_margin_percent": str(pnl_today["profit_margin_percent"]),
                    "total_revenue": str(sales_today["total_revenue"]),
                    "total_cost": str(sales_today["total_cost"]),
                    "gross_profit": str(sales_today["gross_profit"]),
                    "gross_profit_margin_percent": str(sales_today["gross_profit_margin_percent"]),
                }
            except Exception:
                stats["today_pl"] = None
        else:
            # Cashier: ဒီနေ့ မိမိရောင်းချထားသော စုစုပေါင်း (အမြတ်/ကုန်ကျ မပါသော simplified)
            rev = total_revenue
            stats["today_pl"] = {
                "total_income": str(rev),
                "total_expenses": "0",
                "net_profit": str(rev),
                "profit_margin_percent": "100",
                "total_revenue": str(rev),
                "total_cost": "0",
                "gross_profit": str(rev),
                "gross_profit_margin_percent": "100",
            }

        return stats

    

    def get_charts_by_role(self, user, role_name, start_date=None, single_day=False, outlet_id=None):
        if not is_owner(user):
            outlet_id = getattr(user, "primary_outlet_id", None)
        sales_f = Q(status='approved')
        if outlet_id is not None:
            sales_f &= Q(outlet_id=outlet_id)
        service_f = Q()
        # Location reverse: SaleTransaction.sale_location → Location.saletransaction_set (Django default)
        loc_sales_f = Q(saletransaction_set__status='approved')
        if outlet_id is not None:
            loc_sales_f &= Q(saletransaction_set__outlet_id=outlet_id)
        loc_service_f = Q(repairs__status='completed')

        if start_date:
            if single_day:
                sales_f &= Q(created_at__date=start_date)
                service_f &= Q(created_at__date=start_date)
                loc_sales_f &= Q(saletransaction_set__created_at__date=start_date)
                loc_service_f &= Q(repairs__created_at__date=start_date)
            else:
                sales_f &= Q(created_at__date__gte=start_date)
                service_f &= Q(created_at__date__gte=start_date)
                loc_sales_f &= Q(saletransaction_set__created_at__date__gte=start_date)
                loc_service_f &= Q(repairs__created_at__date=start_date)

        approved_sales = SaleTransaction.objects.filter(sales_f).count()
        pending_qs = SaleTransaction.objects.filter(status='pending')
        if outlet_id is not None:
            pending_qs = pending_qs.filter(outlet_id=outlet_id)
        pending_sales = pending_qs.count()
        all_services = RepairService.objects.filter(service_f)
        cancelled_qs = SaleTransaction.objects.filter(status='cancelled')
        if outlet_id is not None:
            cancelled_qs = cancelled_qs.filter(outlet_id=outlet_id)
        analytics = {
            "total_count": approved_sales + all_services.count(),
            "completed": approved_sales + all_services.filter(status='completed').count(),
            "processing": pending_sales + all_services.filter(status__in=['received', 'fixing']).count(),
            "cancelled": cancelled_qs.count() + all_services.filter(status='cancelled').count(),
            "active_services": all_services.filter(status__in=['received', 'fixing']).count()
        }

        locs_qs = Location.objects.all()
        if outlet_id is not None:
            locs_qs = locs_qs.filter(outlet_id=outlet_id)
        branch_performance = locs_qs.annotate(
            s_rev=Coalesce(Sum('saletransaction_set__total_amount', filter=loc_sales_f), 0.0, output_field=models.FloatField()),
            sv_rev=Coalesce(Sum('repairs__total_estimated_cost', filter=loc_service_f), 0.0, output_field=models.FloatField()),
            s_cnt=Count('saletransaction_set', filter=loc_sales_f),
            sv_cnt=Count('repairs', filter=loc_service_f)
        ).annotate(
            total_rev_sum=F('s_rev') + F('sv_rev'),
            total_qty_sum=F('s_cnt') + F('sv_cnt')
        ).values('name', 'total_rev_sum', 'total_qty_sum').order_by('-total_rev_sum')[:4]

        # ၄။ Vue Format သို့ ပြောင်းခြင်း
        formatted_performance = [
            {
                "name": item['name'],
                "location_revenue": item['total_rev_sum'],
                "order_count": item['total_qty_sum']
            } for item in branch_performance
        ]

        top_base = SaleItem.objects.filter(sale_transaction__status='approved')
        if outlet_id is not None:
            top_base = top_base.filter(sale_transaction__outlet_id=outlet_id)
        top_products = top_base.values('product__name').annotate(total_qty=Sum('quantity')).order_by('-total_qty')[:5]

        return {
            "top_selling": {
                "labels": [p['product__name'] for p in top_products],
                "values": [p['total_qty'] for p in top_products]
            },
            "service_analytics": analytics,
            "channel_performance": formatted_performance
        }

    def get_recent_activities(self, user, role_name, outlet_id=None):
        """Table အတွက် Activities (outlet-scoped for non-owner). created_at + sale_id for frontend link."""
        if not is_owner(user):
            outlet_id = getattr(user, "primary_outlet_id", None)
        activities = []
        sales_qs = SaleTransaction.objects.all().select_related('staff').order_by('-created_at')[:5]
        if outlet_id is not None:
            sales_qs = sales_qs.filter(outlet_id=outlet_id)
        for s in sales_qs:
            activities.append({
                "id": s.id,
                "sale_id": s.id,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "time": s.created_at,
                "category": "Sales",
                "message": f"Sales #{s.invoice_number or s.id} is {s.status}",
                "user": s.staff.username if s.staff else "System",
                "status": s.status.capitalize(),
            })

        repairs = RepairService.objects.all().select_related('staff').order_by('-created_at')[:5]
        for r in repairs:
            activities.append({
                "id": f"repair-{r.id}",
                "sale_id": None,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "time": r.created_at,
                "category": "Service",
                "message": f"Repair {getattr(r, 'repair_no', r.id)} is {r.status}",
                "user": r.staff.username if r.staff else "Technician",
                "status": r.status.capitalize(),
            })

        activities.sort(key=lambda x: x['time'] or timezone.now(), reverse=True)
        return activities[:10]


# --------------------------------------------------------
# Inventory Dashboard
# --------------------------------------------------------
class InventoryManagementAPIView(generics.ListAPIView):
    serializer_class = ProductInventorySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'sku', 'category__name']

    def get_queryset(self):
        # select_related သုံးထားတာ ကောင်းပါတယ်။ prefetch_related ပါ ထပ်ထည့်နိုင်ပါတယ်
        return Product.objects.all().select_related('category')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        # Paginate first (SRE: never load full table into memory)
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page if page is not None else queryset, many=True)
        # Lightweight stats: today_sales only; total_value/low_stock from dedicated endpoint if needed
        return Response({
            "cards": {
                "total_value": 0,
                "low_stock_alert": 0,
                "today_sales": self.get_today_sales()
            },
            "inventory_list": serializer.data
        })

    def get_today_sales(self):
        return SaleTransaction.objects.filter(
            status='approved', 
            created_at__date=timezone.now().date()
        ).aggregate(s=Sum('total_amount'))['s'] or 0


# ----------------------------------------------------
# Payment Method Views
# ----------------------------------------------------
class DiscountRuleViewSet(viewsets.ModelViewSet):
    """Discount rules / promotions CRUD - Admin+ """
    queryset = DiscountRule.objects.all().order_by('-created_at')
    serializer_class = DiscountRuleSerializer
    permission_classes = [IsAdminOrHigher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'discount_type']
    search_fields = ['name']


class ModifierGroupViewSet(viewsets.ModelViewSet):
    """Modifier groups and options CRUD - Admin+ """
    queryset = ModifierGroup.objects.prefetch_related('options').order_by('display_order', 'name')
    permission_classes = [IsAdminOrHigher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ModifierGroupCreateUpdateSerializer
        return ModifierGroupSerializer


class BundleViewSet(viewsets.ModelViewSet):
    """အတွဲ (Set/Bundle) CRUD - အတွဲလိုက်ရောင်းချရန် ဖန်တီး/ပြင်ဆင်/ဖျက်။"""
    queryset = Bundle.objects.prefetch_related('items__product', 'components__product').order_by('name')
    permission_classes = [IsAdminOrHigher]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active', 'bundle_type']
    search_fields = ['name', 'sku', 'description']

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return BundleWriteSerializer
        if self.action == 'list':
            return BundleListSerializer
        return BundleSerializer


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """Payment Method: list/retrieve = Cashier+ (POS အတွက်), create/update/delete = Admin+ only."""
    queryset = PaymentMethod.objects.all().order_by('display_order', 'name')
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAdminOrHigher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [IsStaffOrHigher()]  # Role ရှိသူအားလုံး POS/Settings မှ ငွေပေးနည်းစာရင်း ကြည့်နိုင်
        return [IsAdminOrHigher()]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PaymentMethodListAPIView(generics.ListAPIView):
    """List active payment methods for POS. Staff and Admin both see all active methods (no per-user filter)."""
    queryset = PaymentMethod.objects.filter(is_active=True).order_by('display_order', 'name')
    serializer_class = PaymentMethodSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class PaymentProofUploadView(generics.UpdateAPIView):
    """Upload payment proof screenshot for a sale - Sale Staff can upload"""
    queryset = SaleTransaction.objects.all()
    serializer_class = PaymentProofUploadSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        sale = self.get_object()
        
        # Sale staff who created the sale can upload, or admin/manager
        if sale.staff != request.user:
            # Check if user is admin/manager
            if request.user.role_obj:
                role_name = request.user.role_obj.name.lower()
                if role_name not in ['admin', 'owner', 'super_admin', 'manager', 'assistant_manager']:
                    return Response(
                        {'error': 'Permission denied. Only the sale creator or admin can upload payment proof.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            else:
                return Response(
                    {'error': 'Permission denied. Only the sale creator can upload payment proof.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Upload payment proof
        payment_proof = serializer.validated_data['payment_proof']
        payment_status = serializer.validated_data.get('payment_status', 'paid')
        
        # Validate file size (max 5MB)
        if payment_proof.size > 5 * 1024 * 1024:
            return Response(
                {'error': 'File size must be less than 5MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/webp', 'image/jpg']
        if payment_proof.content_type not in allowed_types:
            return Response(
                {'error': 'Only image files (JPEG, PNG, WebP) are allowed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        sale.payment_proof_screenshot = payment_proof
        sale.payment_status = payment_status
        sale.payment_proof_uploaded_at = timezone.now()
        sale.save()
        
        return Response({
            'message': 'Payment proof uploaded successfully',
            'payment_status': sale.payment_status,
            'payment_proof_url': request.build_absolute_uri(sale.payment_proof_screenshot.url) if sale.payment_proof_screenshot else None,
        })


class PaymentStatusUpdateView(generics.UpdateAPIView):
    """Update payment status for a sale"""
    queryset = SaleTransaction.objects.all()
    serializer_class = PaymentStatusUpdateSerializer
    permission_classes = [IsAdminOrHigher]
    
    def update(self, request, *args, **kwargs):
        sale = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        payment_status = serializer.validated_data['payment_status']
        sale.payment_status = payment_status
        
        # If setting to cash, clear payment proof
        if payment_status == 'cash':
            sale.payment_proof_screenshot = None
            sale.payment_proof_uploaded_at = None
        
        sale.save()
        
        return Response({
            'message': 'Payment status updated successfully',
            'payment_status': sale.payment_status,
        })


# ----------------------------------------------------
# AI Suggestion Engine Views
# ----------------------------------------------------
class CrossSellSuggestionView(APIView):
    """
    Cross-sell suggestions based on ProductTag and ProductSpecification compatibility.
    When a product is added to cart, suggest compatible items.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_ids = request.data.get('product_ids', [])  # List of products in cart
        max_results = int(request.data.get('max_results', 5))

        if not product_ids:
            return Response({'suggestions': []})

        # Get products in cart
        cart_products = Product.objects.filter(id__in=product_ids).prefetch_related('tags', 'specifications')

        suggestions = []
        seen_product_ids = set(product_ids)

        for cart_product in cart_products:
            # 1. Find products with matching tags (compatibility)
            matching_tags = cart_product.tags.all()
            if matching_tags.exists():
                tag_products = Product.objects.filter(
                    tags__in=matching_tags,
                    is_serial_tracked=cart_product.is_serial_tracked,  # Similar tracking requirement
                ).exclude(id__in=seen_product_ids).distinct()

                for product in tag_products[:3]:
                    score = self._calculate_compatibility_score(cart_product, product)
                    if score > 0:
                        suggestions.append({
                            'product': ProductSerializer(product).data,
                            'score': score,
                            'reason': f'Compatible tags: {", ".join([t.name for t in matching_tags[:2]])}',
                            'type': 'tag_match',
                        })
                        seen_product_ids.add(product.id)

            # 2. Find products with matching specifications (e.g., Voltage, Amperage)
            cart_specs = {s.label.lower(): s.value.lower() for s in cart_product.specifications.all()}
            if cart_specs:
                # Find products with similar specs
                compatible_products = Product.objects.exclude(id__in=seen_product_ids).prefetch_related('specifications')
                
                for product in compatible_products:
                    product_specs = {s.label.lower(): s.value.lower() for s in product.specifications.all()}
                    matching_specs = {}
                    for key in ['voltage', 'volt', 'v', 'amperage', 'amp', 'a', 'power', 'watt', 'w']:
                        if key in cart_specs and key in product_specs:
                            if cart_specs[key] == product_specs[key]:
                                matching_specs[key] = product_specs[key]

                    if matching_specs:
                        score = len(matching_specs) * 10
                        suggestions.append({
                            'product': ProductSerializer(product).data,
                            'score': score,
                            'reason': f'Matching specs: {", ".join([f"{k}={v}" for k, v in list(matching_specs.items())[:2]])}',
                            'type': 'spec_match',
                        })
                        seen_product_ids.add(product.id)

        # Sort by score and return top results
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        result_suggestions = suggestions[:max_results]

        # Fallback: ဆက်စပ်ပစ္စည်း (tag/spec) မရှိရင် အရောင်းရဆုံးစာရင်းမှ "ဒါလေးရောမလိုဘူးလား" ပြမယ်
        if not result_suggestions:
            best = (
                SaleItem.objects.filter(sale_transaction__status='approved')
                .values('product_id')
                .annotate(total_qty=Sum('quantity'))
                .order_by('-total_qty')[:max_results + len(product_ids)]
            )
            seen = set(product_ids)
            for b in best:
                if b['product_id'] in seen:
                    continue
                try:
                    p = Product.objects.get(pk=b['product_id'])
                except Product.DoesNotExist:
                    continue
                seen.add(p.id)
                result_suggestions.append({
                    'product': ProductSerializer(p).data,
                    'score': 1,
                    'reason': 'ဒါလေးရောမလိုဘူးလား — အရောင်းရဆုံး စာရင်းမှ',
                    'type': 'best_seller',
                })
                if len(result_suggestions) >= max_results:
                    break

        return Response({
            'suggestions': result_suggestions,
            'cart_product_count': len(product_ids),
        })

    def _calculate_compatibility_score(self, product1, product2):
        """Calculate compatibility score between two products"""
        score = 0
        # Same category
        if product1.category == product2.category:
            score += 5
        # Same tags
        common_tags = product1.tags.filter(id__in=product2.tags.all())
        score += common_tags.count() * 3
        return score


class BusinessInsightView(APIView):
    """
    Smart Business Insight: Analyze ExchangeRateLog trends and recommend price adjustments.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        days = int(request.query_params.get('days', 30))
        
        from django.utils import timezone
        from datetime import timedelta
        from .models import ExchangeRateLog, GlobalSetting
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get exchange rate history
        rate_logs = ExchangeRateLog.objects.filter(
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        if rate_logs.count() < 2:
            return Response({
                'insights': [],
                'message': 'Insufficient exchange rate data for analysis',
            })

        rates = [float(log.rate) for log in rate_logs]
        current_rate = rates[-1]
        avg_rate = sum(rates) / len(rates)
        rate_change = ((current_rate - rates[0]) / rates[0]) * 100
        rate_trend = 'increasing' if rate_change > 0 else 'decreasing'

        # Get products with DYNAMIC_USD pricing
        dynamic_products = Product.objects.filter(price_type='DYNAMIC_USD')
        
        insights = []
        recommendations = []

        # Analyze each product
        for product in dynamic_products:
            if not product.cost_usd:
                continue

            # Calculate expected selling price at current rate
            expected_price = float(product.cost_usd) * current_rate * (1 + float(product.markup_percentage or 0) / 100)
            current_selling_price = float(product.selling_price_mmk or product.retail_price or 0)

            if current_selling_price == 0:
                continue

            price_diff_percent = ((expected_price - current_selling_price) / current_selling_price) * 100

            # Recommend adjustment if difference is significant (>5%)
            if abs(price_diff_percent) > 5:
                action = 'increase' if price_diff_percent > 0 else 'decrease'
                recommendations.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_price': current_selling_price,
                    'recommended_price': round(expected_price, 2),
                    'difference_percent': round(price_diff_percent, 2),
                    'action': action,
                    'reason': f'Exchange rate {rate_trend} by {abs(rate_change):.2f}%',
                })

        insights.append({
            'type': 'exchange_rate_analysis',
            'current_rate': float(current_rate),
            'average_rate': round(avg_rate, 4),
            'rate_change_percent': round(rate_change, 2),
            'trend': rate_trend,
            'days_analyzed': days,
            'recommendations': recommendations[:10],  # Top 10 recommendations
        })

        return Response({
            'insights': insights,
            'summary': {
                'products_need_adjustment': len(recommendations),
                'rate_trend': rate_trend,
                'rate_change': round(rate_change, 2),
            },
        })


class StockPredictionView(APIView):
    """
    Stock Prediction: Predict out-of-stock dates based on InventoryMovement history.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        product_id = request.query_params.get('product_id')
        location_id = request.query_params.get('location_id')
        days_to_predict = int(request.query_params.get('days', 90))
        limit = min(int(request.query_params.get('limit', 10)), 50)
        offset = max(0, int(request.query_params.get('offset', 0)))

        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Sum, Avg, Q
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)  # Analyze last 30 days

        if product_id:
            products = Product.objects.filter(id=product_id)
        else:
            # Limit products analyzed for performance (SRE: avoid full table scan)
            products = Product.objects.all()[:200]

        predictions = []

        for product in products:
            # Get movements for this product
            movements_query = InventoryMovement.objects.filter(
                product=product,
                created_at__gte=start_date,
            )

            if location_id:
                movements_query = movements_query.filter(
                    Q(to_location_id=location_id) | Q(from_location_id=location_id)
                )

            movements = movements_query.order_by('created_at')

            # Current stock (for low/out-of-stock display even without enough movements)
            if location_id:
                from .models import Location
                try:
                    location = Location.objects.get(id=location_id)
                    current_stock = product.get_stock_by_location(location)
                except Exception:
                    current_stock = product.total_stock_qty
            else:
                current_stock = product.total_stock_qty

            if movements.count() < 5:  # Need at least 5 movements for prediction
                if current_stock <= 10:  # Still show low/out so card has data
                    predictions.append({
                        'product_id': product.id,
                        'product_name': product.name,
                        'current_stock': current_stock,
                        'predicted_out_of_stock_date': None,
                        'days_until_out_of_stock': 0 if current_stock <= 0 else None,
                        'status': 'out_of_stock' if current_stock <= 0 else 'low_stock',
                        'daily_avg_consumption': 0,
                        'confidence': 'low',
                    })
                continue

            # Calculate daily average outbound (sales/withdrawals)
            outbound_movements = movements.filter(movement_type='outbound')
            if not outbound_movements.exists():
                continue

            total_outbound = outbound_movements.aggregate(Sum('quantity'))['quantity__sum'] or 0
            days_with_movements = (end_date - outbound_movements.first().created_at).days or 1
            daily_avg_outbound = total_outbound / days_with_movements if days_with_movements > 0 else 0

            if daily_avg_outbound <= 0:
                continue

            if current_stock <= 0:
                predictions.append({
                    'product_id': product.id,
                    'product_name': product.name,
                    'current_stock': current_stock,
                    'predicted_out_of_stock_date': None,
                    'days_until_out_of_stock': 0,
                    'status': 'out_of_stock',
                    'daily_avg_consumption': round(daily_avg_outbound, 2),
                    'confidence': 'high',
                })
                continue

            # Predict out-of-stock date
            days_until_out = int(current_stock / daily_avg_outbound) if daily_avg_outbound > 0 else None
            predicted_date = (end_date + timedelta(days=days_until_out)).date() if days_until_out else None

            predictions.append({
                'product_id': product.id,
                'product_name': product.name,
                'current_stock': current_stock,
                'predicted_out_of_stock_date': predicted_date.strftime('%Y-%m-%d') if predicted_date else None,
                'days_until_out_of_stock': days_until_out,
                'status': 'low_stock' if days_until_out and days_until_out <= 7 else 'normal',
                'daily_avg_consumption': round(daily_avg_outbound, 2),
                'confidence': 'high' if movements.count() >= 10 else 'medium',
            })

        # Sort by days until out of stock (urgent first)
        predictions.sort(key=lambda x: (x['days_until_out_of_stock'] is None, x['days_until_out_of_stock'] or 999))
        total = len(predictions)
        page = predictions[offset:offset + limit]

        return Response({
            'predictions': page,
            'total': total,
            'limit': limit,
            'offset': offset,
            'analyzed_period_days': 30,
            'prediction_horizon_days': days_to_predict,
        })


# ----------------------------------------------------
# Product Specification Views (EAV Pattern)
# ----------------------------------------------------
class ProductSpecificationViewSet(viewsets.ModelViewSet):
    """CRUD for Product Specifications"""
    serializer_class = ProductSpecificationSerializer
    permission_classes = [IsInventoryManagerOrHigher]

    def get_queryset(self):
        product_id = self.request.query_params.get('product_id')
        if product_id:
            return ProductSpecification.objects.filter(product_id=product_id).order_by('order', 'label')
        return ProductSpecification.objects.all().order_by('order', 'label')

    def perform_create(self, serializer):
        serializer.save()


class ProductCloneView(APIView):
    """Clone a product with all its specifications"""
    permission_classes = [IsInventoryManagerOrHigher]

    def post(self, request, pk):
        try:
            original = Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=404)

        # Clone product
        cloned = Product.objects.create(
            name=f"{original.name} (Copy)",
            category=original.category,
            sku=generate_unique_sku(f"{original.name} Copy"),
            model_no=original.model_no,
            retail_price=original.retail_price,
            cost_price=original.cost_price,
            cost_usd=original.cost_usd,
            markup_percentage=original.markup_percentage,
            price_type=original.price_type,
            selling_price_mmk=original.selling_price_mmk,
            is_serial_tracked=original.is_serial_tracked,
            serial_number_required=original.serial_number_required,
            unit_type=original.unit_type,
            warranty_months=original.warranty_months,
        )

        # Clone specifications
        for spec in original.specifications.all():
            ProductSpecification.objects.create(
                product=cloned,
                label=spec.label,
                value=spec.value,
                order=spec.order,
            )

        # Clone tags
        cloned.tags.set(original.tags.all())

        return Response({
            'message': 'Product cloned successfully',
            'product': ProductSerializer(cloned).data,
        }, status=201)


class SerialNumberHistoryView(generics.ListAPIView):
    """Get history for a serial number"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        serial_id = self.kwargs.get('serial_id')
        return SerialNumberHistory.objects.filter(serial_item_id=serial_id).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        history = []
        for record in queryset:
            history.append({
                'id': record.id,
                'action': record.action,
                'action_display': record.get_action_display(),
                'from_location': record.from_location.name if record.from_location else None,
                'to_location': record.to_location.name if record.to_location else None,
                'from_status': record.from_status,
                'to_status': record.to_status,
                'notes': record.notes,
                'created_by': record.created_by.username if record.created_by else None,
                'created_at': record.created_at,
            })
        return Response({'history': history})


class AIProductSuggestionView(APIView):
    """
    AI-powered product suggestions for sales.
    Analyzes customer needs and suggests products/bundles.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        query = request.data.get('query', '').strip()
        use_case = request.data.get('use_case', '').strip()
        category_id = request.data.get('category_id')
        max_results = int(request.data.get('max_results', 5))

        if not query and not use_case:
            return Response({'error': 'Query or use_case required'}, status=400)

        # Simple keyword-based matching (can be enhanced with AI/ML)
        products = Product.objects.all()
        
        if category_id:
            products = products.filter(category_id=category_id)

        # Search in name, model_no, and specifications
        search_terms = (query + ' ' + use_case).lower().split()
        
        results = []
        for product in products[:50]:  # Limit initial search
            score = 0
            product_text = f"{product.name} {product.model_no or ''}".lower()
            
            # Check specifications
            specs_text = ' '.join([
                f"{s.label} {s.value}" for s in product.specifications.all()
            ]).lower()

            full_text = f"{product_text} {specs_text}"
            
            # Score based on keyword matches
            for term in search_terms:
                if term in product_text:
                    score += 3
                if term in specs_text:
                    score += 2
                if term in full_text:
                    score += 1

            if score > 0:
                results.append({
                    'product': ProductSerializer(product).data,
                    'score': score,
                    'match_reason': self._get_match_reason(product, query, use_case),
                })

        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        results = results[:max_results]

        # Add bundle suggestions if applicable
        bundle_suggestions = self._suggest_bundles(query, use_case, category_id)
        
        return Response({
            'suggestions': results,
            'bundles': bundle_suggestions,
            'query': query,
            'use_case': use_case,
        })

    def _get_match_reason(self, product, query, use_case):
        """Generate human-readable match reason"""
        reasons = []
        if query:
            if query.lower() in product.name.lower():
                reasons.append(f"Name matches '{query}'")
        if use_case:
            reasons.append(f"Suitable for: {use_case}")
        if product.specifications.exists():
            reasons.append(f"{product.specifications.count()} specifications available")
        return '; '.join(reasons) if reasons else 'General match'

    def _suggest_bundles(self, query, use_case, category_id):
        """Suggest product bundles based on query"""
        # This can be enhanced with actual bundle logic
        from .models import Bundle
        bundles = Bundle.objects.filter(is_active=True)
        if category_id:
            bundles = bundles.filter(items__product__category_id=category_id).distinct()
        return [{'id': b.id, 'name': b.name, 'description': b.description} for b in bundles[:3]]