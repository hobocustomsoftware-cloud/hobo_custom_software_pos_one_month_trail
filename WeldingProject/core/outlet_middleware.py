"""
Lightweight multi-tenancy: single backend for all demo shops.
- Subdomain → outlet_id: Nginx passes Host; we resolve subdomain to Outlet (by code) and set request.outlet_id.
- Strict isolation: get_request_outlet_id() uses this so Shop A user never sees Shop B data.
- In DEMO_MODE, owner from subdomain is restricted to that outlet only (no cross-shop access).
"""
import re
from django.utils.deprecation import MiddlewareMixin


def get_subdomain(host, base_domain=None):
    """
    Extract subdomain from host. E.g. shop1.yourdemo.com → shop1.
    If base_domain is None, treat first label as subdomain when there are at least 2 parts.
    """
    if not host:
        return None
    host = host.split(":")[0].strip().lower()
    parts = host.split(".")
    if len(parts) < 2:
        return None
    # Skip www
    if parts[0] == "www":
        if len(parts) < 3:
            return None
        return parts[1] if len(parts) > 2 else None
    # First part is subdomain (e.g. shop1.yourdemo.com)
    sub = parts[0]
    if sub in ("api", "admin", "app", "www", "mail", "ftp", "static"):
        return None
    return sub


class SubdomainOutletMiddleware(MiddlewareMixin):
    """
    Resolve outlet from request subdomain (e.g. shop1.yourdemo.com).
    Outlet.code must match subdomain (e.g. code='shop1').
    Sets request.outlet_id and request.session['outlet_id'] so downstream code
    (get_request_outlet_id) can enforce strict isolation.
    """

    def process_request(self, request):
        request.outlet_id = None
        host = request.get_host()
        subdomain = get_subdomain(host)
        if not subdomain:
            return
        from .models import Outlet
        try:
            outlet = Outlet.objects.filter(code=subdomain, is_active=True).first()
            if outlet:
                request.outlet_id = outlet.id
                if hasattr(request, "session"):
                    request.session["outlet_id"] = outlet.id
        except Exception:
            pass


def is_demo_owner(user):
    """
    True if user is a demo shop owner: has role owner and primary_outlet set.
    In DEMO_MODE such users must not access Master Admin or other shops.
    """
    if not user or not user.is_authenticated:
        return False
    from django.conf import settings
    if not getattr(settings, "DEMO_MODE", False):
        return False
    role_name = (getattr(user, "role", None) or "").lower()
    if role_name != "owner":
        return False
    return getattr(user, "primary_outlet_id", None) is not None


class DemoAdminRestrictMiddleware(MiddlewareMixin):
    """
    In DEMO_MODE: block Master Admin (/admin/) for demo shop owners.
    They must not access the Django admin or other shops' settings.
    """

    def process_request(self, request):
        from django.conf import settings
        if not getattr(settings, "DEMO_MODE", False):
            return
        path = (request.path or "").strip().rstrip("/")
        if not path.startswith("/admin"):
            return
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return
        if not is_demo_owner(user):
            return
        from django.http import HttpResponseForbidden
        request._demo_admin_blocked = True  # for tests
        return HttpResponseForbidden(
            "Demo shop owners cannot access the Master Admin panel."
        )
