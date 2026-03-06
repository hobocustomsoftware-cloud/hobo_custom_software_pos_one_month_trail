from rest_framework import serializers
from django.db import transaction
from .models import (
    Product, Category, SaleTransaction, SaleItem,
    SerialItem, Location, InventoryMovement, Notification,
    Bundle, BundleItem, BundleComponent, ProductTag, Site,
    ProductSpecification, SerialNumberHistory, Purchase, PurchaseLine, Unit,
    DiscountRule, ModifierGroup, ModifierOption,
)
from core.models import User, Outlet
from drf_spectacular.utils import extend_schema_field

# ----------------------------------------------------
# 1. Basic Serializers
# ----------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    parent_name = serializers.ReadOnlyField(source='parent.name')
    full_path = serializers.ReadOnlyField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'parent', 'parent_name', 'order', 'is_active', 'full_path', 'children']

    def get_children(self, obj):
        """Recursively serialize child categories"""
        children = obj.children.filter(is_active=True).order_by('order', 'name')
        return CategorySerializer(children, many=True).data

class SiteSerializer(serializers.ModelSerializer):
    locations_count = serializers.SerializerMethodField()

    class Meta:
        model = Site
        fields = ['id', 'name', 'address', 'code', 'locations_count']

    def get_locations_count(self, obj):
        return obj.locations.count()


class LocationSerializer(serializers.ModelSerializer):
    staff_assigned = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)
    staff_names = serializers.SerializerMethodField(read_only=True)
    site_name = serializers.ReadOnlyField(source='site.name')

    class Meta:
        model = Location
        fields = [
            'id', 'name', 'address', 'location_type', 'branch_group', 'is_sale_location',
            'site', 'site_name', 'staff_assigned', 'staff_names',
        ]

    def get_staff_names(self, obj):
        return [{'id': u.id, 'username': u.username} for u in obj.staff_assigned.all()]

# ----------------------------------------------------
# 2. Product Serializers
# ----------------------------------------------------
class ProductSpecificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSpecification
        fields = ['id', 'label', 'value', 'order']


class UnitSerializer(serializers.ModelSerializer):
    """Minimal for dropdowns (purchase unit, base unit)."""
    class Meta:
        model = Unit
        fields = ['id', 'code', 'name_my', 'name_en', 'category']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    current_stock = serializers.SerializerMethodField()
    base_unit_display = serializers.SerializerMethodField()
    base_unit_code = serializers.SerializerMethodField()
    purchase_unit_display = serializers.SerializerMethodField()
    purchase_unit_code = serializers.SerializerMethodField()
    specifications = ProductSpecificationSerializer(many=True, read_only=True)

    def get_base_unit_display(self, obj):
        return f"{obj.base_unit.name_my} / {obj.base_unit.name_en}" if getattr(obj, 'base_unit', None) else None

    def get_base_unit_code(self, obj):
        u = getattr(obj, 'base_unit', None)
        return (u.code or '').lower() if u and getattr(u, 'code', None) else None

    def get_purchase_unit_display(self, obj):
        return f"{obj.purchase_unit.name_my} / {obj.purchase_unit.name_en}" if getattr(obj, 'purchase_unit', None) else None

    def get_purchase_unit_code(self, obj):
        u = getattr(obj, 'purchase_unit', None)
        return (u.code or '').lower() if u and getattr(u, 'code', None) else None

    def get_current_stock(self, obj):
        try:
            return obj.total_stock_qty
        except Exception:
            return 0

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name', 'sku', 'model_no',
            'retail_price', 'cost_price', 'cost_usd', 'markup_percentage', 'price_type', 'selling_price_mmk',
            'is_serial_tracked', 'serial_number_required', 'unit_type',
            'base_unit', 'base_unit_display', 'base_unit_code', 'purchase_unit', 'purchase_unit_display', 'purchase_unit_code', 'purchase_unit_factor',
            'warranty_months', 'expiry_date', 'current_stock', 'tags', 'tag_names', 'specifications',
        ]

    tag_names = serializers.SerializerMethodField(read_only=True)

    def get_tag_names(self, obj):
        return list(obj.tags.values_list('name', flat=True)) if hasattr(obj, 'tags') else []


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.SerializerMethodField()
    total_stock = serializers.SerializerMethodField()
    shop_stock = serializers.SerializerMethodField()
    effective_selling_price_mmk = serializers.SerializerMethodField()
    tag_names = serializers.SerializerMethodField(read_only=True)
    image_url = serializers.SerializerMethodField(read_only=True)
    base_unit_display = serializers.SerializerMethodField(read_only=True)
    base_unit_code = serializers.SerializerMethodField(read_only=True)
    purchase_unit_display = serializers.SerializerMethodField(read_only=True)
    purchase_unit_code = serializers.SerializerMethodField(read_only=True)
    purchase_unit_factor = serializers.DecimalField(max_digits=20, decimal_places=6, read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'category', 'category_name', 'sku', 'model_no', 'retail_price', 'selling_price_mmk',
            'cost_usd', 'price_type', 'effective_selling_price_mmk',
            'is_serial_tracked', 'serial_number_required', 'warranty_months', 'expiry_date',
            'total_stock', 'shop_stock', 'tag_names', 'image_url', 'base_unit_display', 'base_unit_code',
            'purchase_unit', 'purchase_unit_display', 'purchase_unit_code', 'purchase_unit_factor',
        ]

    def get_base_unit_display(self, obj):
        u = getattr(obj, 'base_unit', None)
        if not u:
            return None
        name = getattr(u, 'name_my', None) or getattr(u, 'name_en', None) or str(u)
        if getattr(u, 'name_my', None) and getattr(u, 'name_en', None):
            return f"{u.name_my} / {u.name_en}"
        return name

    def get_base_unit_code(self, obj):
        u = getattr(obj, 'base_unit', None)
        if not u:
            return None
        code = getattr(u, 'code', None)
        return code.lower() if code else None

    def get_purchase_unit_display(self, obj):
        u = getattr(obj, 'purchase_unit', None)
        if not u:
            return None
        if getattr(u, 'name_my', None) and getattr(u, 'name_en', None):
            return f"{u.name_my} / {u.name_en}"
        return getattr(u, 'name_my', None) or getattr(u, 'name_en', None) or str(u)

    def get_purchase_unit_code(self, obj):
        u = getattr(obj, 'purchase_unit', None)
        if not u:
            return None
        code = getattr(u, 'code', None)
        return code.lower() if code else None

    def get_fields(self):
        fields = super().get_fields()
        if self.context.get('hide_cost'):
            fields.pop('cost_usd', None)
        return fields

    def get_category_name(self, obj):
        return obj.category.name if getattr(obj, 'category', None) else None

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        if request:
            url = request.build_absolute_uri(obj.image.url)
            # Fix: Host without port (e.g. localhost) → browser requests port 80 → ERR_CONNECTION_REFUSED. Use MEDIA_BASE_URL in dev.
            import re
            if re.match(r'^https?://localhost(?:/|$)', url):
                from django.conf import settings
                base = getattr(settings, 'MEDIA_BASE_URL', None) or getattr(settings, 'SITE_URL', None)
                if base:
                    path = obj.image.url if obj.image.url.startswith('/') else '/' + obj.image.url
                    url = (base.rstrip('/') + path)
            return url
        return obj.image.url if hasattr(obj.image, 'url') else None

    def get_total_stock(self, obj):
        try:
            return obj.total_stock_qty
        except Exception:
            return 0

    def get_effective_selling_price_mmk(self, obj):
        try:
            val = getattr(obj, 'effective_selling_price_mmk', None)
            return float(val) if val is not None else 0
        except (TypeError, ValueError):
            return 0

    def get_tag_names(self, obj):
        return list(obj.tags.values_list('name', flat=True)) if hasattr(obj, 'tags') else []

    def get_shop_stock(self, obj):
        """ဝန်ထမ်းရဲ့ current_location မှ Stock (မရှိပါက shop_floor_stock)"""
        try:
            location = self.context.get('sale_location')
            if location:
                return obj.get_stock_at_sale_location(location)
            return obj.shop_floor_stock
        except Exception:
            return 0


# ----------------------------------------------------
# 2a. Discount Rule (Promotions)
# ----------------------------------------------------
class DiscountRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiscountRule
        fields = [
            'id', 'name', 'discount_type', 'value', 'min_purchase',
            'start_date', 'end_date', 'is_active', 'created_at',
        ]
        read_only_fields = ['created_at']


class ModifierOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModifierOption
        fields = ['id', 'name', 'price_adjustment', 'display_order', 'is_active']


class ModifierGroupSerializer(serializers.ModelSerializer):
    options = ModifierOptionSerializer(many=True, read_only=True)

    class Meta:
        model = ModifierGroup
        fields = [
            'id', 'name', 'description', 'is_required', 'max_selections',
            'display_order', 'is_active', 'options', 'created_at',
        ]
        read_only_fields = ['created_at']


class ModifierGroupCreateUpdateSerializer(serializers.ModelSerializer):
    """For create/update: accept options as nested list."""
    options = ModifierOptionSerializer(many=True, required=False)

    class Meta:
        model = ModifierGroup
        fields = [
            'id', 'name', 'description', 'is_required', 'max_selections',
            'display_order', 'is_active', 'options',
        ]

    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        group = ModifierGroup.objects.create(**validated_data)
        for i, opt in enumerate(options_data):
            ModifierOption.objects.create(group=group, display_order=i, **opt)
        return group

    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if options_data is not None:
            instance.options.all().delete()
            for i, opt in enumerate(options_data):
                ModifierOption.objects.create(group=instance, display_order=i, **opt)
        return instance


# ----------------------------------------------------
# 2b. Bundle Serializers (Product Bundling)
# ----------------------------------------------------
class BundleItemSerializer(serializers.ModelSerializer):
    """Single item inside a bundle (for list/detail). Frontend uses is_optional to allow deselect before checkout."""
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    unit_price = serializers.DecimalField(
        source='product.retail_price', max_digits=10, decimal_places=2, read_only=True
    )
    subtotal = serializers.SerializerMethodField()
    current_stock = serializers.SerializerMethodField()

    class Meta:
        model = BundleItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'quantity',
            'unit_price', 'subtotal', 'is_optional', 'sort_order', 'current_stock',
        ]
        read_only_fields = ['subtotal', 'current_stock']

    def get_subtotal(self, obj):
        return obj.product.retail_price * obj.quantity

    def get_current_stock(self, obj):
        try:
            return obj.product.total_stock_qty
        except Exception:
            return 0


class BundleItemWriteSerializer(serializers.ModelSerializer):
    """For creating/updating bundle items (admin or bundle edit)."""
    class Meta:
        model = BundleItem
        fields = ['id', 'product', 'quantity', 'is_optional', 'sort_order']


class BundleComponentSerializer(serializers.ModelSerializer):
    """Configurator slot: min/max/default qty, is_required."""
    product_name = serializers.ReadOnlyField(source='product.name')
    product_sku = serializers.ReadOnlyField(source='product.sku')
    product_tag_names = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = BundleComponent
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_tag_names',
            'min_qty', 'max_qty', 'default_qty', 'is_required', 'sort_order',
        ]

    def get_product_tag_names(self, obj):
        return list(obj.product.tags.values_list('name', flat=True)) if obj.product_id else []


class BundleComponentWriteSerializer(serializers.ModelSerializer):
    """For creating/updating bundle components."""
    class Meta:
        model = BundleComponent
        fields = ['id', 'product', 'min_qty', 'max_qty', 'default_qty', 'is_required', 'sort_order']


class BundleWriteSerializer(serializers.ModelSerializer):
    """Create/update bundle with nested items and components."""
    items = BundleItemWriteSerializer(many=True, required=False)
    components = BundleComponentWriteSerializer(many=True, required=False)

    class Meta:
        model = Bundle
        fields = [
            'id', 'name', 'description', 'sku', 'bundle_type', 'bundle_price',
            'pricing_type', 'discount_type', 'discount_value', 'is_active',
            'items', 'components',
        ]

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        components_data = validated_data.pop('components', [])
        bundle = Bundle.objects.create(**validated_data)
        for i, item_data in enumerate(items_data):
            BundleItem.objects.create(bundle=bundle, sort_order=i, **item_data)
        for i, comp_data in enumerate(components_data):
            BundleComponent.objects.create(bundle=bundle, sort_order=i, **comp_data)
        return bundle

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        components_data = validated_data.pop('components', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if items_data is not None:
            instance.items.all().delete()
            for i, item_data in enumerate(items_data):
                BundleItem.objects.create(bundle=instance, sort_order=i, **item_data)
        if components_data is not None:
            instance.components.all().delete()
            for i, comp_data in enumerate(components_data):
                BundleComponent.objects.create(bundle=instance, sort_order=i, **comp_data)
        return instance


class BundleSerializer(serializers.ModelSerializer):
    """Bundle detail with all items. Frontend lists items; if is_optional=True user can deselect before checkout."""
    items = BundleItemSerializer(many=True, read_only=True)
    components = BundleComponentSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField()
    items_count = serializers.SerializerMethodField()

    class Meta:
        model = Bundle
        fields = [
            'id', 'name', 'description', 'sku', 'bundle_type', 'bundle_price',
            'pricing_type', 'discount_type', 'discount_value', 'is_active',
            'items', 'components', 'total_price', 'items_count',
        ]
        read_only_fields = ['total_price', 'items_count']

    def get_total_price(self, obj):
        """If bundle_price set, return it; else sum of (product.retail_price * quantity) for all items."""
        if obj.bundle_price is not None:
            return obj.bundle_price
        total = sum(
            item.product.retail_price * item.quantity
            for item in obj.items.select_related('product').all()
        )
        return total

    def get_items_count(self, obj):
        return obj.items.count()


class BundleListSerializer(serializers.ModelSerializer):
    """Light list for dropdown/selector (e.g. POS bundle picker)."""
    items_count = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()

    class Meta:
        model = Bundle
        fields = [
            'id', 'name', 'sku', 'bundle_type', 'bundle_price', 'pricing_type',
            'discount_type', 'discount_value', 'is_active', 'items_count', 'total_price',
        ]

    def get_items_count(self, obj):
        return obj.items.count()

    def get_total_price(self, obj):
        if obj.bundle_price is not None:
            return obj.bundle_price
        total = sum(
            item.product.retail_price * item.quantity
            for item in obj.items.select_related('product').all()
        )
        return total


# ----------------------------------------------------
# 3. Sale & Transaction Serializers (ဒီမှာ အမှားပြင်ထားပါတယ်)
# ----------------------------------------------------


class SaleItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    serial_number = serializers.CharField(source='serial_item.serial_number', read_only=True)
    
    
    
    class Meta:
        model = SaleItem
        fields = ['id', 'product', 'product_name', 'quantity', 'unit_price', 'subtotal', 'serial_number']
        read_only_fields = ['subtotal']

class SaleRequestSerializer(serializers.ModelSerializer):
    sale_items = SaleItemSerializer(many=True)
    sale_location = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.filter(is_sale_location=True),
        required=False, allow_null=True
    )
    invoice_number = serializers.ReadOnlyField()
    auto_approve = serializers.BooleanField(required=False, default=False, write_only=True)

    class Meta:
        model = SaleTransaction
        fields = ['customer', 'sale_items', 'sale_location', 'discount_amount', 'payment_method', 'invoice_number', 'auto_approve']

    def create(self, validated_data):
        items_data = validated_data.pop('sale_items')
        sale_location = validated_data.pop('sale_location', None)
        auto_approve = validated_data.pop('auto_approve', False)
        user = self.context['request'].user

        # Location ရွေးချယ်မှု: API မှ ပို့ထား → StaffSession → primary_location → assigned_locations
        location = sale_location
        if not location:
            from core.models import StaffSession
            session = user.work_sessions.filter(is_active=True).first()
            if session:
                location = session.location
        if not location and user.primary_location:
            location = user.primary_location
        if not location:
            location = user.assigned_locations.filter(is_sale_location=True).first()
        if not location:
            raise serializers.ValidationError({"error": "Location သတ်မှတ်ထားခြင်း မရှိပါ။ sale_location ပို့ပါ သို့မဟုတ် select-location ခေါ်ပါ။"})
        if location not in user.assigned_locations.all() and user.role_obj and user.role_obj.name.lower() not in ['admin', 'owner', 'super_admin']:
            raise serializers.ValidationError({"error": "ဤဆိုင်တွင် တာဝန်မကျထားပါ။"})

        with transaction.atomic():
            from django.utils import timezone
            # ၁။ အရင်ဆုံး Transaction ကို Create လုပ်ပါ (Settings မှာ Sale Approve ပိတ်ထားရင် auto_approve=True ဖြင့် ချက်ချင်းအတည်ပြု)
            payment_method = validated_data.pop('payment_method', None)
            pm_id = getattr(payment_method, 'pk', payment_method) if payment_method else None
            status = 'approved' if auto_approve else 'pending'
            approved_by = user if auto_approve else None
            approved_at = timezone.now() if auto_approve else None
            sale = SaleTransaction.objects.create(
                staff=user,
                sale_location=location,
                status=status,
                approved_by=approved_by,
                approved_at=approved_at,
                payment_method_id=pm_id,
                payment_status='cash' if payment_method else 'pending',  # Auto-set cash if no payment method, else pending
                **validated_data
            )
            
            # ✅ ၂။ total_amount ကို 0 လို့ အရင် ကြေညာပေးရပါမယ် (ဒါမှ Error မတက်မှာပါ)
            total_amount = 0 
            
            for item in items_data:
                # ၃။ SaleItem တစ်ခုချင်းစီ ဆောက်ပါ (only allowed fields; client may send serial_number etc.)
                product = item.get('product')
                quantity = item.get('quantity', 1)
                unit_price = item.get('unit_price')
                if product is None or unit_price is None:
                    raise serializers.ValidationError({"sale_items": "product and unit_price are required."})
                s_item = SaleItem.objects.create(
                    sale_transaction=sale,
                    product=product,
                    quantity=int(quantity),
                    unit_price=unit_price,
                )
                
                # ၄။ total_amount ထဲကို ပေါင်းထည့်ပါ
                # s_item.subtotal က SaleItem model ရဲ့ save() မှာ auto တွက်ထားပြီးသားဖြစ်ရပါမယ်
                total_amount += s_item.subtotal
            
            # ၅။ နောက်ဆုံးရလာတဲ့ စုစုပေါင်းကို Transaction မှာ ပြန်သိမ်းပါ
            sale.total_amount = total_amount
            sale.save()
            # Audit: who created the sale request
            from core.audit import log_audit
            log_audit(user, 'sale_request', 'SaleTransaction', sale.id, outlet_id=location.outlet_id, details={'invoice_number': sale.invoice_number, 'total_amount': str(total_amount)})
            return sale
        
# ----------------------------------------------------
# 4. Admin Serializers
# ----------------------------------------------------

class AdminApprovalSerializer(serializers.ModelSerializer):
    """Admin မှ Approve/Reject လုပ်ရန် (ImportError တက်နေတဲ့နေရာ)"""
    class Meta:
        model = SaleTransaction
        fields = ['status', 'reject_reason']

    def validate(self, data):
        if data.get('status') == 'rejected' and not data.get('reject_reason'):
            raise serializers.ValidationError("ငြင်းပယ်ရသည့် အကြောင်းပြချက် ထည့်သွင်းပေးပါ။")
        return data

class PendingTransactionSerializer(serializers.ModelSerializer):
    """Admin Dashboard မှာ Pending စာရင်းပြရန်"""
    staff_name = serializers.ReadOnlyField(source='staff.username')
    location_name = serializers.ReadOnlyField(source='sale_location.name')
    customer_name = serializers.ReadOnlyField(source='customer.name')
    
    # ပစ္စည်းစာရင်းကို အကျဉ်းချုပ်ပြရန် (ဥပမာ - Cutter x 2, Pump x 1)
    items_summary = serializers.SerializerMethodField()

    class Meta:
        model = SaleTransaction
        fields = [
            'id', 'invoice_number', 'customer_name', 'items_summary', 
            'total_amount', 'staff_name', 'location_name', 'created_at'
        ]

    def get_items_summary(self, obj):
        # Voucher အောက်မှာရှိတဲ့ ပစ္စည်းတွေကို စာသားအဖြစ် စုစည်းပြခြင်း
        items = obj.sale_items.all()
        return ", ".join([f"{item.product.name} (x{item.quantity})" for item in items])
    
    @extend_schema_field(serializers.CharField())
    def get_items_summary(self, obj):
        return obj.get_items_summary()

#-------------------------------------------------
# 5. Staff Serializers
#-------------------------------------------------

class StaffSaleHistorySerializer(serializers.ModelSerializer):
    items_summary = serializers.SerializerMethodField()
    customer_name = serializers.ReadOnlyField(source='customer.name')
    customer_phone = serializers.ReadOnlyField(source='customer.phone_number')

    class Meta:
        model = SaleTransaction
        fields = [
            'id', 'invoice_number', 'customer_name', 'customer_phone', 'items_summary',
            'status', 'total_amount', 'created_at',
        ]

    def get_items_summary(self, obj):
        items = obj.sale_items.all()
        if not items.exists():
            return "No items"
        return ", ".join([f"{item.product.name} (x{item.quantity})" for item in items])



# ----------------------------------------------------
# 4. Inventory & Movement Serializers
# ----------------------------------------------------
class InventoryMovementSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    product_unit = serializers.SerializerMethodField()
    from_location_name = serializers.SerializerMethodField()
    to_location_name = serializers.SerializerMethodField()
    moved_by_name = serializers.ReadOnlyField(source='moved_by.username')

    def get_product_unit(self, obj):
        u = getattr(obj.product, 'base_unit', None) if obj.product else None
        if u:
            return getattr(u, 'name_en', None) or getattr(u, 'name_my', None) or str(u)
        return getattr(obj.product, 'unit_type', None) or '—'

    def get_from_location_name(self, obj):
        return obj.from_location.name if obj.from_location else None

    def get_to_location_name(self, obj):
        return obj.to_location.name if obj.to_location else None
    movement_type_display = serializers.CharField(source='get_movement_type_display', read_only=True)

    class Meta:
        model = InventoryMovement
        fields = [
            'id', 'product', 'product_name', 'product_unit', 'from_location', 'from_location_name',
            'to_location', 'to_location_name', 'quantity', 'movement_type',
            'movement_type_display', 'moved_by_name', 'created_at', 'notes'
        ]


class PurchaseLineSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    purchase_unit_display = serializers.SerializerMethodField()
    quantity_in_base = serializers.SerializerMethodField()
    cost_per_base = serializers.SerializerMethodField()
    total_cost = serializers.ReadOnlyField()

    def get_purchase_unit_display(self, obj):
        u = obj.purchase_unit
        return f"{u.name_my} / {u.name_en}" if u else None

    def get_quantity_in_base(self, obj):
        return obj.quantity_in_base_unit()

    def get_cost_per_base(self, obj):
        return obj.cost_per_base_unit()

    class Meta:
        model = PurchaseLine
        fields = [
            'id', 'product', 'product_name', 'purchase_unit', 'purchase_unit_display',
            'quantity', 'unit_cost', 'total_cost', 'to_location',
            'quantity_in_base', 'cost_per_base',
        ]


class PurchaseSerializer(serializers.ModelSerializer):
    lines = PurchaseLineSerializer(many=True, read_only=True)
    outlet_name = serializers.ReadOnlyField(source='outlet.name', default=None)
    created_by_name = serializers.ReadOnlyField(source='created_by.username', default=None)

    class Meta:
        model = Purchase
        fields = [
            'id', 'outlet', 'outlet_name', 'reference', 'purchase_date', 'notes',
            'created_at', 'created_by', 'created_by_name', 'lines',
        ]
        read_only_fields = ['created_at']


class PurchaseCreateSerializer(serializers.Serializer):
    """POST body: outlet_id, to_location_id (default for all lines), reference, purchase_date, notes, lines[]."""
    outlet = serializers.PrimaryKeyRelatedField(queryset=Outlet.objects.all(), required=False, allow_null=True)
    to_location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), required=False, allow_null=True)
    reference = serializers.CharField(required=False, allow_blank=True, default='')
    purchase_date = serializers.DateField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default='')
    lines = serializers.ListField(child=serializers.DictField(), min_length=1)

    def validate_lines(self, value):
        for i, row in enumerate(value):
            if not row.get('product'):
                raise serializers.ValidationError(f"Line {i+1}: product is required.")
            qty = row.get('quantity', 1)
            if qty is None or (hasattr(qty, '__le__') and qty <= 0):
                raise serializers.ValidationError(f"Line {i+1}: quantity must be positive.")
        return value

# ----------------------------------------------------
# 5. Notification Serializers
# ----------------------------------------------------
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

class NotificationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['is_read']

# ----------------------------------------------------
# 6. Report & Invoice Serializers
# ----------------------------------------------------
class DailySummarySerializer(serializers.Serializer):
    date = serializers.DateField()
    total_sales_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_items_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)

class InvoiceSerializer(serializers.ModelSerializer):
    staff_name = serializers.ReadOnlyField(source='staff.username')
    location_name = serializers.ReadOnlyField(source='sale_location.name')
    customer_name = serializers.ReadOnlyField(source='customer.name')
    sale_items = SaleItemSerializer(many=True, read_only=True) # ပစ္စည်းစာရင်းအသေးစိတ်ပြရန်

    class Meta:
        model = SaleTransaction
        fields = [
            'id', 'invoice_number', 'customer_name', 'staff_name', 
            'location_name', 'discount_amount', 'total_amount',
            'status', 'created_at', 'sale_items'
        ]


# ----------------------------------------------------
# 7. SerialItem Serializers
# ----------------------------------------------------



class SerialItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source='product.name')
    location_name = serializers.ReadOnlyField(source='current_location.name')
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SerialItem
        fields = [
            'id', 'product', 'product_name', 'serial_number', 'imei_2',
            'status', 'status_display', 'current_location', 'location_name'
        ]




class ProductInventorySerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    current_stock = serializers.ReadOnlyField(source='total_stock_qty')
    stock_status = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'model_no', 'category_name', 'current_stock',
            'retail_price', 'stock_status',
        ]

    def get_stock_status(self, obj):
        qty = obj.total_stock_qty
        if qty <= 0: return "Out of Stock"
        if qty <= 5: return "Low Stock"
        return "In Stock"