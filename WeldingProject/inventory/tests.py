"""
Integration tests for inventory API (Task C - A to K recommendation).
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.models import Role

User = get_user_model()


class StaffItemsAPITest(TestCase):
    """Integration: Staff items list requires auth and returns 200 when allowed."""

    def setUp(self):
        self.client = APIClient()
        role = Role.objects.create(name="sale_staff", description="Staff")
        self.user = User.objects.create_user(
            username="teststaff",
            password="testpass123",
            role_obj=role,
        )

    def test_staff_items_unauthorized(self):
        r = self.client.get("/api/staff/items/")
        self.assertIn(r.status_code, (401, 403))

    def test_staff_items_authorized(self):
        self.client.force_authenticate(user=self.user)
        r = self.client.get("/api/staff/items/")
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(r.json(), list)


class DashboardOutletIsolationTest(TestCase):
    """Staff see only their own outlet's repairs/activities, never other shops'."""

    def setUp(self):
        from core.models import Outlet, ShopSettings
        self.client = APIClient()
        self.shop = ShopSettings.objects.create(shop_name="Shop A")
        self.outlet_a = Outlet.objects.create(name="A", shop=self.shop)
        self.outlet_b = Outlet.objects.create(name="B", shop=self.shop)
        role_staff, _ = Role.objects.get_or_create(name="sale_staff")
        role_owner, _ = Role.objects.get_or_create(name="owner")
        self.staff_a = User.objects.create_user(
            username="staff_a", password="Staff-A-12", role_obj=role_staff,
            primary_outlet=self.outlet_a,
        )
        self.owner = User.objects.create_user(
            username="iso_owner", password="Owner-12-x", role_obj=role_owner,
        )

    def test_staff_pinned_to_own_outlet_param_ignored(self):
        from inventory.views import DashboardAnalyticsView
        self.client.force_authenticate(user=self.staff_a)
        r = self.client.get("/api/dashboard/analytics/?outlet_id=%s" % self.outlet_b.id)
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertEqual(body["user_info"]["role"], "sale_staff")

    def test_owner_sees_shop_wide(self):
        self.client.force_authenticate(user=self.owner)
        r = self.client.get("/api/dashboard/analytics/")
        self.assertEqual(r.status_code, 200, r.content)


class BulkImportThresholdTest(TestCase):
    """<=500 rows inline; 501+ → Celery 202 + task_id; dispatch failure → inline."""

    def setUp(self):
        import io
        self.client = APIClient()
        role, _ = Role.objects.get_or_create(name="inventory_manager")
        self.mgr = User.objects.create_user(
            username="bulk_mgr", password="Bulk-Pass-1", role_obj=role,
        )
        self.client.force_authenticate(user=self.mgr)

    def _csv(self, n):
        import io
        lines = ["model_no,name,quantity"]
        for i in range(n):
            lines.append(f"M{i},Item {i},1")
        return io.BytesIO(("\n".join(lines)).encode())

    def _post(self, n):
        from django.core.files.uploadedfile import SimpleUploadedFile
        buf = self._csv(n)
        f = SimpleUploadedFile("items.csv", buf.read(), content_type="text/csv")
        mapping = '{"model_no": "model_no", "name": "name", "quantity": "quantity"}'
        return self.client.post("/api/products/import/", {"file": f, "mapping": mapping}, format="multipart")

    def test_500_rows_stays_inline(self):
        r = self._post(500)
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertIn("imported", r.json())

    def test_501_rows_dispatches_celery_with_task_id(self):
        from unittest.mock import patch, MagicMock
        fake = MagicMock(); fake.id = "task-123"
        with patch("inventory.tasks.bulk_import_products.delay", return_value=fake) as d:
            r = self._post(501)
        self.assertEqual(r.status_code, 202, r.content[:300])
        self.assertEqual(r.json()["task_id"], "task-123")
        self.assertTrue(d.called)

    def test_501_rows_falls_back_inline_when_dispatch_fails(self):
        from unittest.mock import patch
        with patch("inventory.tasks.bulk_import_products.delay",
                    side_effect=ConnectionError("broker down")):
            r = self._post(501)
        self.assertEqual(r.status_code, 200, r.content[:300])
        self.assertIn("imported", r.json())

    def test_public_lookup_throttle_rate_is_30_per_minute(self):
        from core.throttling import PublicLookupThrottle
        self.assertEqual(PublicLookupThrottle.rate, "30/min")
