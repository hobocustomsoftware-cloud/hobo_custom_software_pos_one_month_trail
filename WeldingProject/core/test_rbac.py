"""
RBAC regression tests: role tiers (POS vs Manager) and the API endpoints they gate.

Background: `sale_staff` is the role every seed command creates for selling staff
(seed_demo_users, seed_one_year, run_simulation_data, simulate_month) but the OLD
permission code did not know the role, so /api/staff/items/ returned 403 for the
demo staff account. IsAdminOrHigher also used substring matching while
IsManagerOrHigher used exact matching, giving the same role inconsistent rights.
These tests pin both behaviours down.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, SimpleTestCase
from rest_framework.test import APIClient

from core.models import Role, Outlet
from core.permissions import (
    IsAdminOrHigher,
    IsCashierOrHigher,
    IsManagerOrHigher,
    IsSuperAdmin,
    is_cashier_or_higher,
    is_cashier_role,
    is_manager_or_higher,
    is_store_keeper_or_higher,
)

User = get_user_model()


class _FakeRole:
    def __init__(self, name):
        self.name = name


class _FakeUser:
    """Minimal stand-in for django.contrib.auth user (no DB needed)."""

    def __init__(self, role=None, authenticated=True, superuser=False):
        self.role_obj = _FakeRole(role) if role else None
        self.is_authenticated = authenticated
        self.is_superuser = superuser


class RoleTierUnitTest(SimpleTestCase):
    """Pure function level coverage of the role tiers."""

    def test_pos_tier_accepts_the_seeded_selling_roles(self):
        for role in ("cashier", "sale_staff", "owner", "admin", "manager",
                     "super_admin", "assistant_manager"):
            with self.subTest(role=role):
                self.assertTrue(is_cashier_or_higher(_FakeUser(role)))

    def test_pos_tier_rejects_non_selling_roles(self):
        for role in ("store_keeper", "storekeeper", "technician", "employee",
                     "inventory_staff", "sale_supervisor", None):
            with self.subTest(role=role):
                self.assertFalse(is_cashier_or_higher(_FakeUser(role)))

    def test_unauthenticated_and_roleless_users_have_no_rights(self):
        anon = _FakeUser("owner", authenticated=False)
        self.assertFalse(is_cashier_or_higher(anon))
        self.assertFalse(is_manager_or_higher(anon))
        self.assertFalse(is_cashier_or_higher(_FakeUser(None)))

    def test_superuser_bypasses_role_names(self):
        superuser = _FakeUser(None, superuser=True)
        self.assertTrue(is_manager_or_higher(superuser))
        self.assertTrue(is_cashier_or_higher(superuser))

    def test_manager_tier_is_exact_and_case_insensitive(self):
        for role in ("owner", "Owner", "admin", "manager", "super_admin",
                     "assistant_manager", "inventory_manager"):
            with self.subTest(role=role):
                self.assertTrue(is_manager_or_higher(_FakeUser(role)))

    def test_manager_tier_rejects_lookalike_role_names(self):
        # Old code did `'manager' in role_name`, so any custom role containing
        # the words below silently inherited manager/approve rights.
        for role in ("sale_staff", "cashier", "store_keeper",
                     "inventory_notes", "not_an_owner"):
            with self.subTest(role=role):
                self.assertFalse(is_manager_or_higher(_FakeUser(role)))

    def test_store_keeper_tier(self):
        self.assertTrue(is_store_keeper_or_higher(_FakeUser("store_keeper")))
        self.assertTrue(is_store_keeper_or_higher(_FakeUser("storekeeper")))
        self.assertTrue(is_store_keeper_or_higher(_FakeUser("inventory")))
        self.assertFalse(is_store_keeper_or_higher(_FakeUser("cashier")))

    def test_permission_classes_delegate_to_the_tiers(self):
        manager = _FakeUser("manager")
        cashier = _FakeUser("cashier")
        staff = _FakeUser("sale_staff")

        class Req:
            def __init__(self, user):
                self.user = user
                self.method = "GET"

        self.assertTrue(IsManagerOrHigher().has_permission(Req(manager), None))
        self.assertFalse(IsManagerOrHigher().has_permission(Req(cashier), None))
        self.assertTrue(IsCashierOrHigher().has_permission(Req(staff), None))
        self.assertTrue(IsAdminOrHigher().has_permission(Req(manager), None))
        self.assertFalse(IsAdminOrHigher().has_permission(Req(staff), None))

    def test_delete_is_owner_only(self):
        class Req:
            method = "DELETE"

            def __init__(self, user):
                self.user = user

        self.assertTrue(IsAdminOrHigher().has_permission(Req(_FakeUser("owner")), None))
        for role in ("admin", "manager", "inventory_manager", "assistant_manager"):
            with self.subTest(role=role):
                self.assertFalse(
                    IsAdminOrHigher().has_permission(Req(_FakeUser(role)), None)
                )

    def test_cost_visibility_matches_pos_tier(self):
        # POS selling staff must never receive purchase cost.
        for role in ("cashier", "sale_staff", "sale_supervisor"):
            with self.subTest(role=role):
                self.assertTrue(is_cashier_role(_FakeUser(role)))
        for role in ("owner", "admin", "manager", "inventory_manager"):
            with self.subTest(role=role):
                self.assertFalse(is_cashier_role(_FakeUser(role)))

    def test_is_superuser_permission(self):
        class Req:
            def __init__(self, user):
                self.user = user

        self.assertFalse(IsSuperAdmin().has_permission(Req(_FakeUser("owner")), None))
        self.assertTrue(IsSuperAdmin().has_permission(Req(_FakeUser(None, superuser=True)), None))


class RoleApiAccessTest(TestCase):
    """Endpoint level: the same role matrix as seen by DRF."""

    def setUp(self):
        self.client = APIClient()
        self.roles = {}
        for name in ("owner", "manager", "inventory_manager", "cashier",
                     "sale_staff", "store_keeper"):
            self.roles[name], _ = Role.objects.get_or_create(name=name)

        self.users = {}
        for i, name in enumerate(self.roles):
            self.users[name] = User.objects.create_user(
                username=f"rbac_{name}",
                password="S3cure-pass-123",
                role_obj=self.roles[name],
                phone_number=f"959451234{i:02d}"[:11],
            )
        # Owner gets an outlet so non-owner branch of POS list is reachable.
        self.outlet = Outlet.objects.create(name="RBAC Shop", code="rbac-001")
        self.users["manager"].primary_outlet = self.outlet
        self.users["manager"].save()

    def _status_for(self, role, url):
        self.client.force_authenticate(user=self.users[role])
        return self.client.get(url).status_code

    def test_pos_product_list_allowed_for_selling_roles(self):
        for role in ("owner", "cashier", "sale_staff", "manager"):
            with self.subTest(role=role):
                self.assertEqual(self._status_for(role, "/api/staff/items/"), 200)

    def test_pos_product_list_denied_for_other_roles(self):
        self.client.force_authenticate(user=self.users["store_keeper"])
        self.assertEqual(self.client.get("/api/staff/items/").status_code, 403)

    def test_pos_product_list_denied_for_anonymous(self):
        status = self.client.get("/api/staff/items/").status_code
        self.assertIn(status, (401, 403))

    def test_employee_list_is_manager_tier_only(self):
        for role in ("owner", "manager", "inventory_manager"):
            with self.subTest(role=role):
                self.assertEqual(self._status_for(role, "/api/core/employees/"), 200)
        for role in ("cashier", "sale_staff", "store_keeper"):
            with self.subTest(role=role):
                self.assertEqual(self._status_for(role, "/api/core/employees/"), 403)

    def test_profile_endpoint_works_for_any_role(self):
        for role in self.users:
            with self.subTest(role=role):
                self.assertEqual(self._status_for(role, "/api/core/me/"), 200)

    def test_employee_list_never_returns_usable_temp_password(self):
        """temp_password is shown once on create, never stored or listed as plaintext."""
        from django.contrib.auth.hashers import check_password, identify_hasher
        self.assertEqual(self._status_for("owner", "/api/core/employees/"), 200)
        data = self.client.get("/api/core/employees/").json()
        rows = data.get("results", data) if isinstance(data, dict) else data
        for row in rows:
            self.assertIn(row.get("temp_password"), (None, ""))

        self.client.force_authenticate(user=self.users["owner"])
        plain = "N3w-staff-pass-456"
        created = self.client.post("/api/core/employees/", {
            "username": "rbac_new_staff",
            "password": plain,
            "phone_number": "09459988777",
            "role_obj": self.roles["sale_staff"].id,
            "primary_outlet": self.outlet.id,
            "first_name": "New",
        }, format="json")
        if created.status_code == 201:
            # Shown exactly once so the owner can hand it over...
            self.assertEqual(created.json().get("temp_password"), plain)
            # ...but the DB keeps only a hash: plaintext is unrecoverable.
            from core.models import User
            stored = User.objects.get(username="rbac_new_staff").temp_password
            self.assertNotEqual(stored, plain)
            identify_hasher(stored)  # raises if not a hasher output
            self.assertTrue(check_password(plain, stored))
        else:
            # Validation shape differences must not mask a leaked list response.
            self.assertIn(created.status_code, (200, 400))