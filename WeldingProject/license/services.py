"""
License validation service (single-tenant POS).

EXE Version (standalone): Set DEPLOYMENT_MODE=on_premise; license from license.lic or DB.
  Optional LICENSE_SERVER_URL for remote activate only.
Server Version: Same; set LICENSE_SERVER_URL if using a license server for updates/activation.
"""
from django.utils import timezone
from .models import AppInstallation, AppLicense, LicenseType
from .utils import get_machine_id, load_license_from_file


# Trial: ၃၀ ရက်, Grace: ၅ ရက်
TRIAL_DAYS = 30
GRACE_DAYS = 5


def get_or_create_installation(machine_id=None):
    """Installation record ရှာခြင်း သို့မဟုတ် ဖန်တီးခြင်း"""
    mid = machine_id or get_machine_id()
    inst, created = AppInstallation.objects.get_or_create(
        machine_id=mid,
        defaults={'deployment_mode': _get_deployment_mode()}
    )
    return inst


def _get_deployment_mode():
    """env မှ deployment mode ဖတ်ခြင်း"""
    import os
    return os.environ.get('DEPLOYMENT_MODE', 'on_premise')


def check_license_status(machine_id=None):
    """
    License status စစ်ဆေးခြင်း
    Returns: dict with status, message, can_use, days_remaining, etc.
    """
    mid = machine_id or get_machine_id()
    deployment = _get_deployment_mode()

    # 1. ဝယ်ပြီး license ရှိလား (DB သို့မဟုတ် license.lic)
    db_license = AppLicense.objects.filter(
        machine_id=mid, is_active=True
    ).order_by('-activated_at').first()

    if not db_license:
        # license.lic ဖိုင်မှ စစ်ဆေးခြင်း (offline - DB မလိုပါ)
        file_data = load_license_from_file()
        if file_data:
            file_mid = file_data.get('machine_id')
            file_type = file_data.get('license_type')
            expires_str = file_data.get('expires_at')
            if file_mid == mid:
                from datetime import datetime
                is_perpetual = file_type == LicenseType.ON_PREMISE_PERPETUAL
                expired = False
                if not is_perpetual and expires_str:
                    try:
                        exp = datetime.fromisoformat(expires_str.replace('Z', '+00:00'))
                        if timezone.is_naive(exp):
                            exp = timezone.make_aware(exp)
                        if timezone.now() > exp:
                            expired = True
                    except Exception:
                        expired = True  # parse မရရင် ကုန်ပြီးလို့ ယူဆ
                if not expired:
                    return {
                        'status': 'licensed',
                        'license_type': file_type or 'on_premise_perpetual',
                        'can_use': True,
                        'message': 'License မှန်ကန်ပါသည်။ (Offline)',
                        'expires_at': expires_str,
                    }

    if db_license and db_license.is_valid:
        return {
            'status': 'licensed',
            'license_type': db_license.license_type,
            'can_use': True,
            'message': 'License မှန်ကန်ပါသည်။',
            'expires_at': db_license.expires_at.isoformat() if db_license.expires_at else None,
        }

    if db_license and db_license.is_expired:
        return {
            'status': 'expired',
            'can_use': False,
            'message': 'License သက်တမ်းကုန်ပြီးပါပြီ။ Renewal လုပ်ပါ။',
        }

    # 2. Trial စစ်ဆေးခြင်း
    inst = get_or_create_installation(mid)

    if inst.is_grace_expired:
        return {
            'status': 'blocked',
            'can_use': False,
            'message': f'Trial နှင့် Grace period ကုန်ဆုံးပြီးပါပြီ။ License ဝယ်ယူပါ။',
            'first_run_at': inst.first_run_at.isoformat(),
            'grace_expires_at': inst.grace_expires_at.isoformat(),
        }

    if inst.is_trial_expired:
        # Grace period ထဲမှာ
        days = inst.days_remaining_in_grace
        return {
            'status': 'grace',
            'can_use': True,
            'message': f'Trial ကုန်ပြီး Grace period ထဲရှိပါသည်။ {days} ရက်အတွင်း License ဝယ်ပါ။',
            'days_remaining': days,
            'first_run_at': inst.first_run_at.isoformat(),
            'grace_expires_at': inst.grace_expires_at.isoformat(),
        }

    # Trial ထဲမှာ
    days = inst.days_remaining_in_trial
    return {
        'status': 'trial',
        'can_use': True,
        'message': f'Trial သုံးနေပါသည်။ {days} ရက် ကျန်ပါသေးသည်။',
        'days_remaining': days,
        'first_run_at': inst.first_run_at.isoformat(),
        'trial_expires_at': inst.trial_expires_at.isoformat(),
    }
