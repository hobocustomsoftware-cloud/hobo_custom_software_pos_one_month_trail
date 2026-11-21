from rest_framework import permissions


def _role_name(user):
    """Safe role name; does not raise when role_obj missing or deleted."""
    if not user:
        return ""
    try:
        ro = getattr(user, "role_obj", None)
        if not ro:
            return ""
        return (getattr(ro, "name", None) or "").lower()
    except Exception:
        return ""


def is_cashier_role(user):
    """POS selling staff who must NOT see purchase cost.

    'sale_staff' / 'sale_supervisor' are the roles created by the seed
    (seed_demo_users, seed_one_year, run_simulation_data, simulate_month) for
    selling staff, so they get the same cost-hiding as 'cashier'.
    """
    return _role_name(user) in ("cashier", "sale_staff", "sale_supervisor")


def is_store_keeper_role(user):
    """Store Keeper: Inbound, Outbound, Internal Transfers within outlet only."""
    r = _role_name(user)
    return r in ("store_keeper", "storekeeper", "store keeper")


# --- Role tiers (single source of truth, exact + case-insensitive matching) ---
# Manager tier: approve sales, admin & reports (docs/RBAC_STAFF_ACCESS_CONTROL.md
# + the manager-suffixed roles created by seed / simulate data).
MANAGER_ROLE_NAMES = (
    "owner",
    "admin",
    "manager",
    "super_admin",
    "assistant_manager",
    "inventory_manager",
)

# POS tier: product list, sale request, locations, own sales.
POS_ROLE_NAMES = ("cashier", "sale_staff")


def is_manager_or_higher(user):
    """Manager, Admin, Owner: can approve sales, access admin/reports."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return _role_name(user) in MANAGER_ROLE_NAMES


def is_cashier_or_higher(user):
    """Cashier and above: can use POS and create Sale Requests."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    r = _role_name(user)
    return r in ("owner", "admin", "manager", "super_admin", "assistant_manager") + POS_ROLE_NAMES


def is_store_keeper_or_higher(user):
    """Store Keeper and above: can manage Inbound, Outbound, Transfers."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    r = _role_name(user)
    return r in ("owner", "admin", "manager", "super_admin", "store_keeper", "storekeeper", "inventory")


class IsSuperAdmin(permissions.BasePermission):
    """Superuser သာ ခွင့်ပြုသည်"""
    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsOwner(permissions.BasePermission):
    """Owner Role ပါဝင်သူ သို့မဟုတ် Superuser သာ ခွင့်ပြုသည်"""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        
        # role_obj ရှိမရှိနှင့် နာမည်ထဲတွင် 'owner' ပါမပါ စစ်ဆေးခြင်း (safe when role_obj deleted)
        try:
            ro = getattr(user, "role_obj", None)
            return ro is not None and 'owner' in (getattr(ro, "name", None) or "").lower()
        except Exception:
            return False

class IsAdminOrHigher(permissions.BasePermission):
    """Approval ပေးနိုင်သည့် Role များ (Manager tier).

    NOTE: this used substring matching (`'manager' in role_name`) while
    IsManagerOrHigher matched exactly, so a role like `inventory_manager` could
    approve sales but got 403 on the dashboard. Both now share
    MANAGER_ROLE_NAMES (exact, case-insensitive), and DELETE stays owner-only.
    """
    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False

        # Superuser က အကုန်လုပ်ခွင့်ရှိသည်
        if user.is_superuser:
            return True

        role_name = _role_name(user)
        if not role_name:
            return False
        if request.method == 'DELETE':
            return role_name == 'owner'
        return role_name in MANAGER_ROLE_NAMES

class IsInventoryManagerOrHigher(permissions.BasePermission):
    """Inventory ဆိုင်ရာ လုပ်ပိုင်ခွင့် (Manager, Inventory, Admin, Owner)"""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        
        try:
            ro = getattr(user, "role_obj", None)
            if ro:
                role_name = (getattr(ro, "name", None) or "").lower()
                if request.method == 'DELETE':
                    return role_name == 'owner' or user.is_superuser
                # Manager tier + every `inventory*` role (inventory, inventory_staff, ...).
                # Previously substring-matched, which also matched unrelated names like
                # `owner_notes` -> keep only the grants that existed for real roles.
                return role_name in MANAGER_ROLE_NAMES or role_name.startswith('inventory')
        except Exception:
            pass
        return False

class IsStaffOrHigher(permissions.BasePermission):
    """အခြေခံ ဝန်ထမ်းနှင့် အထက် (Login ဝင်နိုင်သူ အားလုံးနီးပါး)"""
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated or not user.is_active:
            return False
        try:
            return user.is_superuser or getattr(user, "role_obj", None) is not None
        except Exception:
            return False


class IsManagerOrHigher(permissions.BasePermission):
    """Manager, Admin, Owner: full outlet access, approve Sale Requests, admin & reports. Cashier/Store Keeper get 403."""
    def has_permission(self, request, view):
        return is_manager_or_higher(request.user)


class IsCashierOrHigher(permissions.BasePermission):
    """Cashier and above: POS screen, create Sale Requests. Used for staff/items, sales/request, locations."""
    def has_permission(self, request, view):
        return is_cashier_or_higher(request.user)


class IsStoreKeeperOrHigher(permissions.BasePermission):
    """Store Keeper and above: Inbound, Outbound, Internal Transfers within assigned outlet."""
    def has_permission(self, request, view):
        return is_store_keeper_or_higher(request.user)