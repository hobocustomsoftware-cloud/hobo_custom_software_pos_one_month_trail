"""
Multi-Outlet: access control and outlet scoping.
- Owner: primary_outlet is null → full access; may filter by outlet via request.
- Manager/Cashier: primary_outlet set → see only that outlet's data.
"""
from django.db.models import Q


def is_owner(user):
    """True if user has Owner (or equivalent) role and thus can see all outlets. Safe when role_obj missing/deleted."""
    if not user or not getattr(user, "is_authenticated", False):
        return False
    try:
        ro = getattr(user, "role_obj", None)
        role_name = (getattr(ro, "name", None) or "").lower() if ro else ""
        return role_name in ("owner", "admin", "super", "superuser")
    except Exception:
        return False


def get_request_outlet_id(request):
    """
    Resolve outlet for the current request. Strict isolation: Shop A never sees Shop B.
    - Subdomain binding: if request.outlet_id is set (from SubdomainOutletMiddleware), use it for everyone.
    - Standalone (single shop): when DEMO_MODE is False and there is exactly one active outlet, owner
      defaults to that outlet_id so all Sale/Inventory queries are filtered to the primary outlet.
    - Owner: may pass ?outlet_id=X or session; otherwise None = all (or single-outlet default in Standalone).
    - Non-owner: must use user.primary_outlet_id (enforced).
    """
    # Subdomain binding (demo / multi-tenant): one outlet per request
    if request and getattr(request, "outlet_id", None) is not None:
        return request.outlet_id
    if not request or not request.user.is_authenticated:
        return None
    user = request.user
    if is_owner(user):
        # Owner: optional filter by outlet (dashboard switcher); session can hold it
        outlet_id = request.GET.get("outlet_id") or request.session.get("dashboard_outlet_id") or request.session.get("outlet_id")
        if outlet_id is not None:
            try:
                return int(outlet_id)
            except (TypeError, ValueError):
                pass
        # Standalone: default to the single primary outlet so all queries are outlet-scoped
        from django.conf import settings
        if not getattr(settings, "DEMO_MODE", False):
            from .models import Outlet
            outlets = list(Outlet.objects.filter(is_active=True).values_list("pk", flat=True))
            if len(outlets) == 1:
                return outlets[0]
        return None  # None = all outlets for owner (multi-outlet)
    # Branch lock: staff only see their assigned outlet
    return getattr(user, "primary_outlet_id", None)


def filter_queryset_by_outlet(queryset, request, outlet_field="outlet_id"):
    """
    Restrict queryset to the outlet allowed for request.user.
    - Owner with no outlet filter: return queryset unchanged.
    - Owner with outlet_id: filter by that outlet.
    - Non-owner: filter by user.primary_outlet_id; if none, return empty.
    """
    outlet_id = get_request_outlet_id(request)
    if outlet_id is None:
        if is_owner(request.user):
            return queryset
        # Staff with no assigned outlet see nothing
        return queryset.none()
    filter_kw = {outlet_field: outlet_id}
    return queryset.filter(**filter_kw)


def get_visible_outlets(request):
    """Return queryset of outlets the user is allowed to see (for dropdowns)."""
    from .models import Outlet
    if not request or not request.user.is_authenticated:
        return Outlet.objects.none()
    if is_owner(request.user):
        return Outlet.objects.filter(is_active=True).order_by("-is_main_branch", "name")
    oid = getattr(request.user, "primary_outlet_id", None)
    if not oid:
        return Outlet.objects.none()
    return Outlet.objects.filter(pk=oid, is_active=True)


def user_can_access_location(user, location):
    """True if user is allowed to use this location (inbound/transfer/select). Owner: any; Staff: location must belong to primary_outlet."""
    if not location:
        return False
    if is_owner(user):
        return True
    oid = getattr(user, "primary_outlet_id", None)
    if not oid:
        return False
    return getattr(location, "outlet_id", None) == oid
