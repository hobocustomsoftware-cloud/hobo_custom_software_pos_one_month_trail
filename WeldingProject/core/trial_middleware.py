"""
Trial expiry middleware for multi-instance deployment.
If trial_start_date + 30 days < now, block POS/Inventory APIs and return 403.
When SKIP_LICENSE=true or DEPLOYMENT_MODE=hosted: trial check is skipped (demo တစ်လလောက် သုံးနိုင်ရန်).
"""
import os
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from datetime import timedelta

# Paths that are always allowed during trial (login, register, license, shop-settings)
TRIAL_ALLOW_PATHS = (
    '/admin/',
    '/health/',
    '/metrics/',
    '/api/token/',
    '/api/core/register',
    '/api/core/shop-settings',
    '/api/license/',
    '/static/',
    '/media/',
    '/api/schema/',
    '/api/docs/',
)


def _trial_expired():
    """Return True if this instance's trial has expired (trial_start_date + 30 days < now)."""
    from core.models import ShopSettings
    try:
        settings_obj = ShopSettings.objects.get(pk=1)
    except ShopSettings.DoesNotExist:
        return False  # No shop yet, allow (e.g. first request before register)
    start = getattr(settings_obj, 'trial_start_date', None)
    if not start:
        return False
    # Make start timezone-aware if naive
    if timezone.is_naive(start):
        start = timezone.make_aware(start)
    expiry = start + timedelta(days=30)
    return timezone.now() > expiry


def _should_skip_trial_check(path):
    for prefix in TRIAL_ALLOW_PATHS:
        if path.startswith(prefix):
            return True
    return False


class TrialExpiryMiddleware(MiddlewareMixin):
    """Legacy entry point: the real check now lives in
    license.middleware._unified_access_check so license + trial can never
    disagree (previously only one of the two middlewares could be active and
    each had its own skip rules). Kept as a no-op for MIDDLEWARE lists that
    still reference it; remove it from settings once deployed.
    """

    def process_request(self, request):
        return None
