"""
License Validation Middleware
- App စတင်တိုင်း license စစ်ဆေးခြင်း
- Blocked/Expired ဖြစ်ရင် 403 ပြန်ခြင်း
"""
import os
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .services import check_license_status

# License စစ်မစစ် လုပ်မလုပ် (SKIP_LICENSE=true သို့မဟုတ် DEBUG မှာ skip)
# Register + Login ကို license မစစ်ပါ - ပထမဆုံး owner ဖန်တီးနိုင်ရန် (EXE + Hosting နှစ်မျိုးလုံး)
SKIP_LICENSE_PATHS = [
    '/admin/',
    '/health/',               # SRE: liveness / readiness
    '/metrics/',              # SRE: Prometheus metrics
    '/api/license/status/',   # status ကိုယ်တိုင် (optional – no key required)
    '/api/license/activate/',
    '/api/license/remote-activate/',  # License server - EXE မှ ခေါ်ခြင်း
    '/api/core/register',     # စာရင်းသွင်းခြင်း - owner ဖန်တီးနိုင်ရန်
    '/api/core/auth/',        # Login – ဝင်ရောက်နိုင်ရန် (401 ကာကွယ်ရန်)
    '/api/core/shop-settings', # Login စာမျက်နှာ shop name/logo ပြရန်
    '/api/token',             # JWT login - ဝင်ရောက်နိုင်ရန်
    '/static/',
    '/media/',
    '/api/schema/',
]


def _license_mode():
    """Resolution order: SKIP_LICENSE > DEPLOYMENT_MODE > DEBUG.

    - SKIP_LICENSE=true: never enforce (local dev, CI, demos).
    - DEPLOYMENT_MODE=hosted: trial middleware owns expiry; license skipped.
    - DEPLOYMENT_MODE=on_premise: enforce even with DEBUG=True so shops can
      rehearse expiry locally (prevents the 'works here, blocked there' gap).
    - unset mode: legacy behaviour, DEBUG=True skips.
    """
    if os.environ.get('SKIP_LICENSE', 'false').lower() in ('true', '1', 'yes'):
        return 'skip'
    mode = os.environ.get('DEPLOYMENT_MODE', '').strip().lower()
    if mode == 'hosted':
        return 'skip'
    if mode == 'on_premise':
        return 'enforce'
    if getattr(settings, 'DEBUG', False):
        return 'skip'  # Development: DEBUG=True မှာ license မစစ်
    return 'enforce'


def _should_skip_license():
    """Dev / hosted မှာ license စစ်ဆေးခြင်း skip လုပ်မလုပ်။ on_premise သတ်မှတ်ထားမှသာ စစ်မည်။"""
    return _license_mode() == 'skip'


def _unified_access_check(path):
    """One gate for license + trial (previously two middlewares disagreed).

    Order: (1) SKIP_LICENSE / DEPLOYMENT_MODE off-switch, (2) always-open
    auth/setup paths, (3) paid license validity, (4) 30-day trial clock.
    Returns None when the request may proceed, else (error, message, status).
    Hosted deployments skip both gates: expiry is handled by subscription
    billing there, not by the on-premise license file.
    """
    if _should_skip_license():
        return None
    for prefix in SKIP_LICENSE_PATHS:
        if path.startswith(prefix):
            return None
    lic = check_license_status()
    if not lic.get('can_use', False):
        return ('license_expired', lic.get('message', 'License သက်တမ်းကုန်ပြီးပါပြီ။'), lic.get('status', 'blocked'))
    from core.trial_middleware import _trial_expired
    if _trial_expired():
        import os
        return ('trial_expired', 'Trial Expired. Contact Admin to Activate.', os.environ.get(
            'TRIAL_EXPIRED_CONTACT',
            'Contact Admin to activate. / သက်တမ်းတိုးချဲ့ရန် အက်ဒ်မင်နှင့် ဆက်သွယ်ပါ။'))
    return None


def _should_skip(request, path):
    if _should_skip_license():
        return True
    for prefix in SKIP_LICENSE_PATHS:
        if path.startswith(prefix):
            return True
    return False


class LicenseCheckMiddleware(MiddlewareMixin):
    """
    Request တိုင်းမှာ license စစ်ဆေးခြင်း
    can_use=False ဖြစ်ရင် 403 ပြန်ခြင်း
    """

    def process_request(self, request):
        path = request.path
        if _should_skip(request, path):
            return None
        verdict = _unified_access_check(path)
        if verdict is None:
            return None
        error, message, status = verdict
        if error == 'trial_expired':
            import os
            if path.startswith('/api/'):
                return JsonResponse({
                    'error': error,
                    'message': 'Trial Expired. Contact Admin to Activate.',
                    'detail': 'This instance has exceeded the 30-day trial period.',
                    'contact': os.environ.get('TRIAL_EXPIRED_CONTACT', message),
                }, status=403)
            return None  # non-API pages stay open; the API gate is enough
        # License gate: expired shops see the banner but keep read-only
        # access; writes are blocked. Trial expiry blocks all business APIs
        # (the old behaviour the tests pin).
        if error == 'license_expired' and path.startswith('/api/') and request.method in ('GET', 'HEAD', 'OPTIONS'):
            return None
        if path.startswith('/api/'):
            return JsonResponse({
                'error': error,
                'message': message,
                'status': status,
            }, status=403)
        from django.shortcuts import render
        return render(request, 'license_expired.html', {
            'message': message,
            'status': status,
        })
