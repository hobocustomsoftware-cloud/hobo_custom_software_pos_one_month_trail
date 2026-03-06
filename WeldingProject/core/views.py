from django.core.signing import Signer, BadSignature
from django.utils import timezone
from django.db import connection
from urllib.parse import quote
from datetime import timedelta
from rest_framework import generics, viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
from .models import User, Role, StaffSession, ShopSettings, Outlet, Shift
from .serializers import UserSerializer, EmployeeSerializer, RoleSerializer, RegisterSerializer, ShopSettingsSerializer, ShiftSerializer
from .permissions import IsAdminOrHigher, IsOwner, IsStaffOrHigher
from .outlet_utils import get_visible_outlets, is_owner
from .auth_views import get_tokens_for_user, _build_user_payload

class RegisterView(generics.CreateAPIView):
    """ဝန်ထမ်း စာရင်းသွင်းခြင်း (Public - Login မလိုပါ) - EXE + Hosting နှစ်မျိုးလုံး"""
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        from django.db import IntegrityError
        import logging
        logger = logging.getLogger(__name__)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            logger.warning("Register validation failed: data=%s errors=%s", request.data, serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = serializer.save()
        except IntegrityError as e:
            err_msg = str(e)
            if 'unique' in err_msg.lower() or 'duplicate' in err_msg.lower():
                return Response({
                    'phone_number': ['This phone number is already registered. Please login.'],
                }, status=status.HTTP_400_BAD_REQUEST)
            raise
        except Exception as e:
            logger.exception("Register failed: %s", e)
            raise
        shop_name = (request.data.get('shop_name') or '').strip()
        # Marketing: Telegram + Google Sheet. Run sync in request so it works without Celery worker.
        try:
            from .external_sync import sync_new_registration
            sync_new_registration(user, shop_name=shop_name)
        except Exception as e2:
            logging.getLogger(__name__).warning("Registration marketing sync failed: %s", e2)
        # Optional: also queue for Celery if worker is running (no duplicate send; task is idempotent by design)
        try:
            from .tasks import sync_new_signup_marketing
            sync_new_signup_marketing.delay(user.id, shop_name)
        except Exception as e:
            pass  # already synced above; worker optional
        # စာရင်းသွင်းသူတိုင်း သူ့ဆိုင်ရဲ့ Owner ဖြစ်သွားပြီး ချက်ချင်း ဝင်လို့ရသည်။
        can_login_now = True
        msg = 'Registration successful. You can sign in now.'
        payload = {
            'message': msg,
            'phone_number': getattr(user, 'phone_number', None) or '',
            'username': user.username,
            'can_login_now': can_login_now,
        }
        tokens = get_tokens_for_user(user)
        user_payload, outlet = _build_user_payload(user)
        payload['access'] = tokens['access']
        payload['refresh'] = tokens.get('refresh', '')
        payload['user'] = user_payload
        payload['outlet'] = outlet
        return Response(payload, status=status.HTTP_201_CREATED)


class RoleViewSet(viewsets.ModelViewSet):
    """Owner စိတ်ကြိုက် Role များ CRUD လုပ်ရန် API – Admin+ only. Shared demo: filter by request.user.shop."""
    serializer_class = RoleSerializer
    permission_classes = [IsAdminOrHigher]
    pagination_class = None

    def get_queryset(self):
        qs = Role.objects.all().order_by('id')
        shop_id = getattr(self.request.user, 'shop_id', None)
        if shop_id is not None:
            qs = qs.filter(users__shop_id=shop_id).distinct()
        return qs


class UserDetailView(generics.RetrieveAPIView):
    """လက်ရှိ Login ဝင်ထားသူ၏ Profile ကို ပြန်ပေးမည်"""
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class EmployeeViewSet(viewsets.ModelViewSet):
    """User အားလုံးကို စီမံခန့်ခွဲရန် (Owner Only). Shared demo: filter by request.user.shop."""
    serializer_class = EmployeeSerializer
    permission_classes = [IsAdminOrHigher]
    pagination_class = None

    def get_queryset(self):
        qs = User.objects.select_related(
            'role_obj', 'primary_outlet', 'primary_location', 'shop'
        ).prefetch_related(
            'assigned_locations', 'work_sessions'
        )
        shop_id = getattr(self.request.user, 'shop_id', None)
        if shop_id is not None:
            qs = qs.filter(shop_id=shop_id)
        return qs


class ShiftViewSet(viewsets.ModelViewSet):
    """Shift (အလုပ်ချိန်) CRUD – Manager+. Shared demo: no shop on Shift; visible to all in same app."""
    serializer_class = ShiftSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Shift.objects.all().order_by('start_time')


class ForgotPasswordView(APIView):
    """စကားဝှက် မေ့သွားပါက - Username သို့မဟုတ် Phone Number ဖြင့် Reset Token ရယူခြင်း"""
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        phone_raw = request.data.get('phone_number', '').strip()
        country_code = (request.data.get('country_code') or '+95').strip()
        if not username and not phone_raw:
            return Response({'error': 'Username သို့မဟုတ် Phone Number လိုအပ်ပါသည်။'}, status=status.HTTP_400_BAD_REQUEST)
        user = None
        if phone_raw:
            from .phone_utils import validate_myanmar_phone
            ok, norm = validate_myanmar_phone(phone_raw, country_code)
            if ok:
                user = User.objects.filter(phone_number=norm, is_active=True).first()
            if not user:
                return Response({'error': 'ဤ ဖုန်းနံပါတ် မရှိပါ။'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                user = User.objects.get(username=username, is_active=True)
            except User.DoesNotExist:
                return Response({'error': 'ဤ Username မရှိပါ။'}, status=status.HTTP_404_NOT_FOUND)
        signer = Signer()
        payload = f'{user.id}:{(timezone.now() + timedelta(hours=1)).timestamp()}'
        token = signer.sign(payload)
        return Response({
            'token': token,
            'reset_url': f'/app/reset-password?token={quote(token)}',
            'message': 'စကားဝှက် ပြန်လည်သတ်မှတ်ရန် အောက်ပါ link ကို သုံးပါ။ (၁ နာရီအတွင်း အသုံးပြုရမည်)',
        }, status=status.HTTP_200_OK)




class ResetPasswordView(APIView):
    """Token ဖြင့် စကားဝှက် ပြန်သတ်မှတ်ခြင်း"""
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('token', '').strip()
        new_password = request.data.get('new_password', '')
        if not token:
            return Response({'error': 'Token လိုအပ်ပါသည်။'}, status=status.HTTP_400_BAD_REQUEST)
        if not new_password or len(new_password) < 6:
            return Response({'error': 'စကားဝှက် အနည်းဆုံး ၆ လုံး ရှိရပါမည်။'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            signer = Signer()
            payload = signer.unsign(token)
            user_id, exp_ts = payload.split(':')
            if timezone.now().timestamp() > float(exp_ts):
                return Response({'error': 'Token သက်တမ်းကုန်ပါပြီ။ ထပ်မံတောင်းခံပါ။'}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(id=int(user_id), is_active=True)
            user.set_password(new_password)
            user.requires_password_change = False
            user.save()
            return Response({'message': 'စကားဝှက် ပြောင်းလဲပြီးပါပြီ။ ဝင်ရောက်နိုင်ပါပြီ။'}, status=status.HTTP_200_OK)
        except (BadSignature, ValueError, User.DoesNotExist):
            return Response({'error': 'Token မမှန်ကန်ပါ သို့မဟုတ် သက်တမ်းကုန်ပါပြီ။'}, status=status.HTTP_400_BAD_REQUEST)


class ShopSettingsView(APIView):
    """ဆိုင်ချိန်ညှိချက် - GET (အားလုံး)၊ PUT (Owner သို့မဟုတ် ပထမဆုံး user – Setup Wizard အတွက်)"""
    def get_permissions(self):
        if self.request.method == 'GET':
            return [AllowAny()]
        # PUT: require auth; view checks Owner or first user
        return [IsAuthenticated()]

    def check_put_allowed(self, request):
        """Allow PUT for Owner, Manager, first user, or any authenticated user when setup not done yet (Loyverse-style)."""
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        role_name = (getattr(getattr(request.user, 'role_obj', None), 'name', None) or '').lower()
        if role_name in ('owner', 'admin', 'manager', 'super_admin'):
            return True
        if User.objects.count() == 1:
            return True
        # Loyverse-style: allow any logged-in user to complete setup wizard when not done yet
        try:
            settings_obj = ShopSettings.get_settings()
            if not getattr(settings_obj, 'setup_wizard_done', True):
                return True
        except Exception:
            pass
        return False

    def get(self, request):
        try:
            settings_obj = ShopSettings.get_settings()
            serializer = ShopSettingsSerializer(settings_obj, context={'request': request})
            return Response(serializer.data)
        except Exception as e:
            # DB မပြည့်စုံရင် / migration မပြေးရင် default ပြန်မယ် - 404 မပြန်စေရန်
            return Response({
                'shop_name': 'HoBo POS',
                'logo': None,
                'logo_url': None,
                'updated_at': None,
            })

    def put(self, request):
        if not self.check_put_allowed(request):
            return Response({'detail': 'Only the owner can update shop settings.'}, status=status.HTTP_403_FORBIDDEN)
        import logging
        logger = logging.getLogger(__name__)
        try:
            from .unit_templates import seed_units_for_business_category
            settings_obj = ShopSettings.get_settings()
            serializer = ShopSettingsSerializer(settings_obj, data=request.data, partial=True, context={'request': request})
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if request.data.get('business_category'):
                seed_units_for_business_category(request.data.get('business_category'))
            return Response(serializer.data)
        except Exception as e:
            logger.exception('ShopSettings PUT failed')
            return Response(
                {'detail': str(e) or 'Failed to update shop settings.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DatabaseStatsView(APIView):
    """SRE: Database size and table row counts (Task E recommendation - DB monitoring). Staff only."""
    permission_classes = [IsAuthenticated, IsStaffOrHigher]

    def get(self, request):
        vendor = connection.vendor
        size_bytes = None
        tables = []
        try:
            with connection.cursor() as c:
                if vendor == 'postgresql':
                    c.execute("SELECT pg_database_size(current_database())")
                    size_bytes = c.fetchone()[0]
                    c.execute("""
                        SELECT relname, n_live_tup FROM pg_stat_user_tables
                        ORDER BY n_live_tup DESC LIMIT 30
                    """)
                    tables = [{'table': r[0], 'rows': r[1]} for r in c.fetchall()]
                elif vendor == 'sqlite':
                    c.execute("SELECT (SELECT page_count FROM pragma_page_count()) * (SELECT page_size FROM pragma_page_size())")
                    row = c.fetchone()
                    size_bytes = row[0] if row else 0
                    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    for (name,) in c.fetchall():
                        # Use quote_name to avoid SQL injection (Pentester/Security)
                        quoted = connection.ops.quote_name(name)
                        c.execute(f"SELECT COUNT(*) FROM {quoted}")
                        tables.append({'table': name, 'rows': c.fetchone()[0]})
                    tables.sort(key=lambda x: x['rows'], reverse=True)
                    tables = tables[:30]
        except Exception as e:
            # Log full error; return generic message in production (Security: no internal detail exposure)
            import logging
            logging.getLogger(__name__).exception("DatabaseStatsView error")
            err_msg = str(e)[:200] if settings.DEBUG else "Database error"
            return Response({'error': err_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        size_mb = round(size_bytes / (1024 * 1024), 2) if size_bytes else None
        return Response({
            'database': vendor,
            'size_bytes': size_bytes,
            'size_mb': size_mb,
            'tables': tables,
        })


class SelectLocationView(APIView):
    """ယနေ့အလုပ်လုပ်မည့်ဆိုင် ရွေးချယ်ခြင်း (အလှည့်ကျ ဝန်ထမ်းများအတွက်)"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        location_id = request.data.get('location_id')
        if not location_id:
            return Response({'error': 'location_id လိုအပ်ပါသည်။'}, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        from inventory.models import Location
        from .outlet_utils import is_owner, user_can_access_location
        try:
            location = Location.objects.get(id=location_id, is_sale_location=True)
        except Location.DoesNotExist:
            return Response({'error': 'Location ရှာမတွေ့ပါ သို့မဟုတ် ရောင်းချရန်နေရာ မဟုတ်ပါ။'}, status=status.HTTP_400_BAD_REQUEST)
        if not is_owner(user) and not user_can_access_location(user, location):
            return Response({'error': 'ဤဆိုင်တွင် တာဝန်မကျထားပါ သို့မဟုတ် ဤ Outlet အတွက် ရွေးချယ်၍မရပါ။'}, status=status.HTTP_403_FORBIDDEN)
        allowed = user.assigned_locations.filter(is_sale_location=True)
        if location not in allowed and user.role_obj and user.role_obj.name.lower() not in ['admin', 'owner', 'super_admin']:
            return Response({'error': 'ဤဆိုင်တွင် တာဝန်မကျထားပါ။'}, status=status.HTTP_403_FORBIDDEN)
        # ယခင် Session များကို ပိတ်ပါ
        StaffSession.objects.filter(user=user, is_active=True).update(is_active=False)
        # အသစ် ဖန်တီးပါ
        session = StaffSession.objects.create(user=user, location=location)
        return Response({
            'message': f'ယနေ့အလုပ်လုပ်မည့်ဆိုင်: {location.name}',
            'current_location': {'id': location.id, 'name': location.name}
        }, status=status.HTTP_200_OK)


class OutletListView(APIView):
    """GET: List outlets visible to current user (for Owner dashboard switcher; staff see only their outlet)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        outlets = get_visible_outlets(request)
        data = [{"id": o.id, "name": o.name, "code": o.code, "is_main_branch": o.is_main_branch} for o in outlets]
        return Response(data, status=status.HTTP_200_OK)


class SetDashboardOutletView(APIView):
    """
    POST: Owner မှ လက်ရှိ ကြည့်မည့်ဆိုင်ကို ရွေးချယ်ခြင်း (Demo မှာ ဆိုင်ပြောင်းကြည့်ရန်)。
    Body: { "outlet_id": 2 }. Session ထဲ သတ်မှတ်ပြီး နောက် API တွေက ဒီ ဆိုင်အလိုက် ပဲ ပြန်မယ်။
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not is_owner(request.user):
            return Response(
                {"detail": "Only owner can switch dashboard outlet."},
                status=status.HTTP_403_FORBIDDEN,
            )
        outlet_id = request.data.get("outlet_id")
        if outlet_id is None:
            # Clear selection = show all outlets again
            if hasattr(request, "session"):
                request.session.pop("dashboard_outlet_id", None)
                request.session.pop("outlet_id", None)
            return Response({"detail": "Outlet filter cleared. Showing all outlets."}, status=status.HTTP_200_OK)
        try:
            outlet_id = int(outlet_id)
        except (TypeError, ValueError):
            return Response({"detail": "Invalid outlet_id."}, status=status.HTTP_400_BAD_REQUEST)
        outlets = get_visible_outlets(request)
        if not any(o.id == outlet_id for o in outlets):
            return Response({"detail": "Outlet not found or access denied."}, status=status.HTTP_404_NOT_FOUND)
        if hasattr(request, "session"):
            request.session["dashboard_outlet_id"] = outlet_id
            request.session["outlet_id"] = outlet_id
        return Response({"detail": "Outlet set.", "outlet_id": outlet_id}, status=status.HTTP_200_OK)