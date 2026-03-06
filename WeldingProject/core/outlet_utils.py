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


def get_shop_outlet_ids(request):
    """Shared demo server: outlet IDs belonging to request.user.shop. None if user has no shop."""
    if not request or not request.user.is_authenticated:
        return None
    shop_id = getattr(request.user, "shop_id", None)
    if shop_id is None:
        return None
    from .models import Outlet
    return list(Outlet.objects.filter(shop_id=shop_id, is_active=True).values_list("pk", flat=True))


def get_request_outlet_id(request):
    """
    Resolve outlet for the current request. Strict isolation: Shop A never sees Shop B.
    When request.user.shop_id is set (shared demo), only outlets in that shop are considered.
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
    shop_outlet_ids = get_shop_outlet_ids(request)
    if is_owner(user):
        # Owner: optional filter by outlet (dashboard switcher); session can hold it
        outlet_id = request.GET.get("outlet_id") or request.session.get("dashboard_outlet_id") or request.session.get("outlet_id")
        if outlet_id is not None:
            try:
                oid = int(outlet_id)
                if shop_outlet_ids is None or oid in shop_outlet_ids:
                    return oid
            except (TypeError, ValueError):
                pass
        # Standalone: default to the single primary outlet so all queries are outlet-scoped
        from django.conf import settings
        if not getattr(settings, "DEMO_MODE", False):
            from .models import Outlet
            outlets = list(Outlet.objects.filter(is_active=True).values_list("pk", flat=True))
            if shop_outlet_ids is not None:
                outlets = [x for x in outlets if x in shop_outlet_ids]
            if len(outlets) == 1:
                return outlets[0]
        return None  # None = all outlets for owner (multi-outlet)
    # Branch lock: staff only see their assigned outlet (must be in user's shop)
    oid = getattr(user, "primary_outlet_id", None)
    if oid is not None and shop_outlet_ids is not None and oid not in shop_outlet_ids:
        return None
    return oid


def filter_queryset_by_outlet(queryset, request, outlet_field="outlet_id"):
    """
    Restrict queryset to the outlet allowed for request.user.
    Shared demo server: when request.user.shop_id is set, only outlets in that shop are included.
    - Owner with no outlet filter: return queryset (scoped to shop outlets when shop_id set).
    - Owner with outlet_id: filter by that outlet.
    - Non-owner: filter by user.primary_outlet_id; if none, return empty.
    """
    shop_outlet_ids = get_shop_outlet_ids(request)
    if shop_outlet_ids is not None:
        if not shop_outlet_ids:
            return queryset.none()
        queryset = queryset.filter(**{f"{outlet_field}__in": shop_outlet_ids})
    outlet_id = get_request_outlet_id(request)
    if outlet_id is None:
        if is_owner(request.user):
            return queryset
        return queryset.none()
    return queryset.filter(**{outlet_field: outlet_id})


def get_visible_outlets(request):
    """Return queryset of outlets the user is allowed to see (for dropdowns). Respects request.user.shop."""
    from .models import Outlet
    if not request or not request.user.is_authenticated:
        return Outlet.objects.none()
    qs = Outlet.objects.filter(is_active=True)
    shop_outlet_ids = get_shop_outlet_ids(request)
    if shop_outlet_ids is not None:
        qs = qs.filter(pk__in=shop_outlet_ids)
    if is_owner(request.user):
        return qs.order_by("-is_main_branch", "name")
    oid = getattr(request.user, "primary_outlet_id", None)
    if not oid:
        return Outlet.objects.none()
    return qs.filter(pk=oid)


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
