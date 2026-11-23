"""
License API: status, activate, remote-activate (license server)
"""
import os
import requests
from rest_framework.views import APIView
from core.throttling import LicenseActivateThrottle, RemoteLicenseThrottle
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils import timezone
from .services import check_license_status, get_or_create_installation
from .models import AppLicense, BackupAddOn, LicenseType, SubscriptionPlan
from .utils import get_machine_id, save_license_to_file


class LicenseStatusView(APIView):
    """License status စစ်ဆေးခြင်း - Public (login မလို). Optional: no key required; returns trial/licensed/expired."""
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            result = check_license_status()
        except Exception:
            # Optional: when license check fails (e.g. no DB), return can_use True so app does not block
            result = {
                'status': 'trial',
                'can_use': True,
                'message': 'License check skipped.',
            }
        result['machine_id'] = get_machine_id()
        return Response(result)


class LicenseActivateView(APIView):
    """License key ထည့်ပြီး Activate လုပ်ခြင်း (Local DB သို့မဟုတ် License Server)"""
    permission_classes = [AllowAny]
    throttle_classes = [LicenseActivateThrottle]

    def post(self, request):
        license_key = request.data.get('license_key', '').strip()
        if not license_key:
            return Response(
                {'error': 'license_key လိုအပ်ပါသည်။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        machine_id = get_machine_id()
        server_url = os.environ.get('LICENSE_SERVER_URL', '').rstrip('/')

        # EXE: License Server မှ validate လုပ်ခြင်း
        if server_url:
            try:
                r = requests.post(
                    f'{server_url}/api/license/remote-activate/',
                    json={'license_key': license_key, 'machine_id': machine_id},
                    timeout=15,
                )
                data = r.json() if r.ok else {}
                if r.ok and data.get('success'):
                    save_license_to_file(
                        license_key=license_key,
                        machine_id=machine_id,
                        license_type=data.get('license_type', 'on_premise_perpetual'),
                        expires_at=data.get('expires_at'),
                    )
                    return Response({
                        'message': 'License Activate အောင်မြင်ပါပြီ။',
                        'license_type': data.get('license_type'),
                        'expires_at': data.get('expires_at'),
                    }, status=status.HTTP_200_OK)
                return Response(
                    {'error': data.get('error', 'License Server နှင့် ချိတ်ဆက်မရပါ။')},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except requests.RequestException as e:
                return Response(
                    {'error': f'License Server နှင့် ချိတ်ဆက်မရပါ။ ({str(e)[:50]})'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        # Local DB မှာ license ရှိလား
        lic = AppLicense.objects.filter(
            license_key=license_key,
            is_active=True
        ).first()

        if not lic:
            return Response(
                {'error': 'License key မမှန်ကန်ပါ သို့မဟုတ် သက်တမ်းကုန်ပြီးပါပြီ။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if lic.is_expired:
            return Response(
                {'error': 'License သက်တမ်းကုန်ပြီးပါပြီ။ Renewal လုပ်ပါ။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if lic.machine_id and lic.machine_id != machine_id:
            return Response(
                {'error': 'ဤ License ကို အခြားစက်တွင် သုံးပြီးပါပြီ။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lic.machine_id = machine_id
        lic.save()

        save_license_to_file(
            license_key=license_key,
            machine_id=machine_id,
            license_type=lic.license_type,
            expires_at=lic.expires_at,
        )

        return Response({
            'message': 'License Activate အောင်မြင်ပါပြီ။',
            'license_type': lic.license_type,
            'expires_at': lic.expires_at.isoformat() if lic.expires_at else None,
        }, status=status.HTTP_200_OK)


class RemoteLicenseActivateView(APIView):
    """
    License Server endpoint - EXE မှ ခေါ်ခြင်း
    Receives license_key + machine_id, validates, binds, returns license data.
    """
    permission_classes = [AllowAny]
    throttle_classes = [RemoteLicenseThrottle]

    def post(self, request):
        license_key = request.data.get('license_key', '').strip()
        machine_id = request.data.get('machine_id', '').strip()
        if not license_key or not machine_id:
            return Response(
                {'error': 'license_key နှင့် machine_id လိုအပ်ပါသည်။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lic = AppLicense.objects.filter(
            license_key=license_key,
            is_active=True
        ).first()

        if not lic:
            return Response(
                {'error': 'License key မမှန်ကန်ပါ သို့မဟုတ် သက်တမ်းကုန်ပြီးပါပြီ။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if lic.is_expired:
            return Response(
                {'error': 'License သက်တမ်းကုန်ပြီးပါပြီ။ Renewal လုပ်ပါ။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if lic.machine_id and lic.machine_id != machine_id:
            return Response(
                {'error': 'ဤ License ကို အခြားစက်တွင် သုံးပြီးပါပြီ။'},
                status=status.HTTP_400_BAD_REQUEST
            )

        lic.machine_id = machine_id
        lic.save()

        return Response({
            'success': True,
            'license_type': lic.license_type,
            'expires_at': lic.expires_at.isoformat() if lic.expires_at else None,
        }, status=status.HTTP_200_OK)


DEFAULT_PLANS = [
    {'code': 'sub_basic', 'name': 'Basic', 'price_mmk': 15000, 'billing_cycle': 'monthly',
     'features': ['1 shop', 'POS + inventory', 'Local backup export'], 'sort_order': 1},
    {'code': 'sub_standard', 'name': 'Standard', 'price_mmk': 30000, 'billing_cycle': 'monthly',
     'features': ['Up to 3 outlets', 'POS + inventory + services', 'Local backup export'], 'sort_order': 2},
    {'code': 'sub_premium', 'name': 'Premium', 'price_mmk': 50000, 'billing_cycle': 'monthly',
     'features': ['Unlimited outlets', 'All modules', 'Cloud backup add-on eligible'], 'sort_order': 3},
]


def _plan_payload(plan):
    features = list(plan.features or [])
    extra = [f.label for f in plan.plan_features.filter(included=True).order_by('sort_order', 'id')]
    return {
        'code': plan.code, 'name': plan.name, 'price_mmk': plan.price_mmk,
        'billing_cycle': plan.billing_cycle, 'features': features + [f for f in extra if f not in features],
    }


class SubscriptionPlanListView(APIView):
    """Public dynamic pricing: ChatGPT/Google-AI style plan cards, served as data.

    Seeded from DEFAULT_PLANS on first call so a fresh install shows pricing
    with zero admin work; owners edit plans in admin afterwards.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        for defaults in DEFAULT_PLANS:
            SubscriptionPlan.objects.get_or_create(code=defaults['code'], defaults=defaults)
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('sort_order', 'id')
        current = check_license_status().get('license_type')
        return Response({
            'plans': [_plan_payload(p) for p in plans],
            'current_plan': current,
            'backup_addon_available': True,
        })


class BackupStatusView(APIView):
    """Per-shop backup state: local export always allowed; cloud needs add-on."""

    def get(self, request):
        from django.conf import settings
        machine_id = get_machine_id()
        shop_id = getattr(getattr(request.user, 'shop', None), 'id', None) or getattr(request.user, 'shop_id', None)
        addon = BackupAddOn.objects.filter(machine_id=machine_id, is_active=True).first()
        if not addon and shop_id:
            addon = BackupAddOn.objects.filter(shop_id=shop_id, is_active=True).first()
        valid = bool(addon and addon.is_valid)
        expired = bool(addon and addon.expires_at and timezone.now() > addon.expires_at)
        return Response({
            'local_export': True,
            'cloud_backup': valid,
            'addon_expired': expired,
            'addon_expires_at': addon.expires_at.isoformat() if addon and addon.expires_at else None,
            'machine_id': machine_id,
        })


class BackupActivateView(APIView):
    """Activate the sellable cloud-backup add-on with a key (Owner/Manager)."""

    def post(self, request):
        from core.permissions import is_manager_or_higher
        if not is_manager_or_higher(request.user):
            return Response({'error': 'Owner/Manager only.'}, status=status.HTTP_403_FORBIDDEN)
        key = (request.data.get('backup_key') or '').strip()
        if not key:
            return Response({'error': 'backup_key required.'}, status=status.HTTP_400_BAD_REQUEST)
        addon = BackupAddOn.objects.filter(license_key=key, is_active=True).first()
        if not addon:
            return Response({'error': 'Invalid backup key.'}, status=status.HTTP_400_BAD_REQUEST)
        if addon.expires_at and timezone.now() > addon.expires_at:
            return Response({'error': 'Backup key expired. Renew the add-on.'}, status=status.HTTP_400_BAD_REQUEST)
        machine_id = get_machine_id()
        shop = getattr(request.user, 'shop', None)
        if not addon.machine_id:
            addon.machine_id = machine_id
        if shop is not None and addon.shop_id is None:
            addon.shop = shop
        addon.save()
        return Response({'message': 'Cloud backup activated.', 'cloud_backup': True})
