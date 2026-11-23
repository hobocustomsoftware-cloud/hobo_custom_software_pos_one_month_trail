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
        lic = check_license_status()
        return Response({
            'plans': [_plan_payload(p) for p in plans],
            'current_plan': lic.get('license_type'),
            # Trial → paid handoff: the app shows this CTA when the clock runs out.
            'trial': {
                'status': lic.get('status'),
                'days_remaining': lic.get('days_remaining', 0),
                'trial_expires_at': lic.get('trial_expires_at'),
                'grace_expires_at': lic.get('grace_expires_at'),
                'upgrade_required': lic.get('status') in ('grace', 'blocked', 'expired'),
                'upgrade_message': 'Trial ကုန်ပါပြီ။ ဆက်သုံးရန် plan ရွေးပြီး payment လုပ်ပါ။' if lic.get('status') in ('grace', 'blocked', 'expired') else None,
            },
            'backup_addon_available': True,
        })


class TrialCheckoutView(APIView):
    """Trial → paid: pick a plan, prove payment, get a license.

    Flow (manual transfer until Dinger lands):
    1. POST {plan_code} → order with amount + transfer instructions (KPay/Wave to shop owner account).
    2. Customer pays, POST {order_id, payment_proof} → pending review.
    3. Owner approves → AppLicense issued (subscription expiry set), app unlocks.
    Dinger will replace steps 1-2 with a payment link + webhook.
    """
    permission_classes = [AllowAny]
    throttle_classes = [LicenseActivateThrottle]

    def post(self, request):
        from .models import TrialOrder
        plan_code = (request.data.get('plan_code') or '').strip()
        phone = (request.data.get('phone_number') or '').strip()
        if not plan_code or not phone:
            return Response({'error': 'plan_code + phone_number required.'}, status=status.HTTP_400_BAD_REQUEST)
        for defaults in DEFAULT_PLANS:
            SubscriptionPlan.objects.get_or_create(code=defaults['code'], defaults=defaults)
        try:
            plan = SubscriptionPlan.objects.get(code=plan_code, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Unknown plan.'}, status=status.HTTP_400_BAD_REQUEST)
        order = TrialOrder.objects.create(
            plan=plan, phone_number=phone, amount_mmk=plan.price_mmk,
            machine_id=get_machine_id(), status='pending_payment',
        )
        return Response({
            'order_id': order.id,
            'plan': _plan_payload(plan),
            'amount_mmk': order.amount_mmk,
            'pay_to': {
                'kpay': '0979-XXX-XXXX (HoBo)', 'wave': '0979-XXX-XXXX (HoBo)',
                'note': f'Order #{order.id} {phone}',
            },
            'next': f'Pay, then POST /api/license/checkout/{order.id}/proof/ with payment screenshot.',
        }, status=status.HTTP_201_CREATED)


class TrialCheckoutProofView(APIView):
    """Attach payment proof to a trial order (customer side)."""
    permission_classes = [AllowAny]
    throttle_classes = [LicenseActivateThrottle]

    def post(self, request, order_id):
        from .models import TrialOrder
        try:
            order = TrialOrder.objects.get(pk=order_id, status='pending_payment')
        except TrialOrder.DoesNotExist:
            return Response({'error': 'Order not found or already submitted.'}, status=status.HTTP_404_NOT_FOUND)
        proof = request.FILES.get('payment_proof') or request.data.get('payment_proof')
        txn = (request.data.get('transaction_id') or '').strip()
        if not proof and not txn:
            return Response({'error': 'payment_proof file or transaction_id required.'}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(proof, 'size') and proof.size > 5 * 1024 * 1024:
            return Response({'error': 'File must be less than 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
        if hasattr(proof, 'read'):
            from django.core.files.storage import default_storage
            path = default_storage.save(f'trial_orders/{order.id}_{proof.name}', proof)
            order.payment_proof = path
        order.transaction_id = txn
        order.status = 'pending_review'
        order.save()
        try:
            from core.external_sync import _send_telegram
            _send_telegram(f'New trial payment: Order #{order.id} {order.plan.code} {order.amount_mmk}Ks {order.phone_number}')
        except Exception:
            pass
        return Response({'message': 'Proof received. We will activate within 24h.', 'order_id': order.id})


class TrialCheckoutApproveView(APIView):
    """Owner approves a paid order → license issued (Manager+)."""

    def post(self, request, order_id):
        from datetime import timedelta
        from core.permissions import is_manager_or_higher
        from .models import TrialOrder
        if not is_manager_or_higher(request.user):
            return Response({'error': 'Owner/Manager only.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            order = TrialOrder.objects.get(pk=order_id, status='pending_review')
        except TrialOrder.DoesNotExist:
            return Response({'error': 'Order not found or not ready.'}, status=status.HTTP_404_NOT_FOUND)
        months = 1
        lic = AppLicense.objects.create(
            license_type=order.plan.code, machine_id=order.machine_id or get_machine_id(),
            is_active=True, expires_at=timezone.now() + timedelta(days=30 * months),
            notes=f'trial order #{order.id} {order.phone_number}',
        )
        order.status = 'approved'
        order.save()
        return Response({'message': 'License activated.', 'license_type': lic.license_type, 'expires_at': lic.expires_at.isoformat()})


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
