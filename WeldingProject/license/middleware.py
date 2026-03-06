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


def _should_skip_license():
    """Dev / hosted မှာ license စစ်ဆေးခြင်း skip လုပ်မလုပ်။ on_premise သတ်မှတ်ထားမှသာ စစ်မည်။"""
    if os.environ.get('SKIP_LICENSE', 'false').lower() in ('true', '1', 'yes'):
        return True
    if getattr(settings, 'DEBUG', False):
        return True  # Development: DEBUG=True မှာ license မစစ်
    # Only enforce license when explicitly on_premise (EXE/standalone)
    mode = os.environ.get('DEPLOYMENT_MODE', '').strip().lower()
    if mode != 'on_premise':
        return True  # hosted, empty, or other => skip so /api/staff/items/, dashboard, ai work
    return False


def _should_skip(request, path):
    if _should_skip_license():
        return True
    # Localhost / 127.0.0.1 => skip so dev and Docker (user hits localhost) work without license
    try:
        host = (request.get_host().split(':')[0] or '').lower()
        if host in ('localhost', '127.0.0.1', 'backend', 'frontend'):
            return True
    except Exception:
        pass
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
        # Never block /api/ with license – let DRF handle auth/permission (avoids 403 for staff/items, payment-methods, etc.)
        if path.startswith('/api/'):
            return None
        if _should_skip(request, path):
            return None

        result = check_license_status()
        if not result.get('can_use', False):
            # API request ဖြစ်ရင် JSON ပြန်မည်
            if path.startswith('/api/'):
                return JsonResponse({
                    'error': 'license_expired',
                    'message': result.get('message', 'License သက်တမ်းကုန်ပြီးပါပြီ။'),
                    'status': result.get('status', 'blocked'),
                }, status=403)
            # Page request ဖြစ်ရင် license-expired page ပြမည်
            from django.shortcuts import render
            return render(request, 'license_expired.html', {
                'message': result.get('message', ''),
                'status': result.get('status', 'blocked'),
            })
        return None
