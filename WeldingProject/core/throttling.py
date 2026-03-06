"""
Rate limiting for sensitive endpoints - brute force / abuse ကာကွယ်ခြင်း
"""
from rest_framework.throttling import SimpleRateThrottle


def _get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


class LicenseActivateThrottle(SimpleRateThrottle):
    """License activate - 10/min per IP"""
    scope = 'license_activate'
    rate = '10/min'

    def get_cache_key(self, request, view):
        return f'license_activate_{_get_ip(request)}'


class RemoteLicenseThrottle(SimpleRateThrottle):
    """Remote license (EXE) - 30/min per IP"""
    scope = 'remote_license'
    rate = '30/min'

    def get_cache_key(self, request, view):
        return f'remote_license_{_get_ip(request)}'


class AuthThrottle(SimpleRateThrottle):
    """Login / token - 20/min per IP"""
    scope = 'auth'
    rate = '20/min'

    def get_cache_key(self, request, view):
        return f'auth_{_get_ip(request)}'


class ApiUserThrottle(SimpleRateThrottle):
    """General API - 200/min per user (authenticated) or per IP (anonymous). ဆိုင်ခွဲ/အသုံးပြုသူများ တစ်ပြိုင်တည်းသုံးစွဲမှု ထိန်းချုပ်ရန်"""
    scope = 'api_user'
    rate = '200/min'

    def get_cache_key(self, request, view):
        if request.user and request.user.is_authenticated:
            return f'api_user_{request.user.id}'
        return f'api_anon_{_get_ip(request)}'
