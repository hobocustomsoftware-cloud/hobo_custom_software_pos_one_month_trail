"""Cross-shop isolation: staff of shop A never see shop B's rows."""
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Outlet, Role, ShopSettings, User
from customer.models import Customer
from inventory.models import Location
from service.models import RepairService


def make_user(username, role_name, outlet=None, phone="95945000000"):
    role, _ = Role.objects.get_or_create(name=role_name)
    return User.objects.create_user(
        username=username, password="Pass-1234-x", phone_number=phone,
        role_obj=role, primary_outlet=outlet,
    )


class CrossShopIsolationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.shop_a = ShopSettings.objects.create(shop_name="A")
        self.shop_b = ShopSettings.objects.create(shop_name="B")
        self.outlet_a = Outlet.objects.create(name="A1", shop=self.shop_a, code="a1")
        self.outlet_b = Outlet.objects.create(name="B1", shop=self.shop_b, code="b1")
        self.loc_a = Location.objects.create(name="A-floor", outlet=self.outlet_a)
        self.loc_b = Location.objects.create(name="B-floor", outlet=self.outlet_b)
        self.cust_a = Customer.objects.create(name="CustA", phone_number="0911111111", preferred_branch=self.loc_a)
        self.cust_b = Customer.objects.create(name="CustB", phone_number="0922222222", preferred_branch=self.loc_b)
        from django.utils import timezone
        today = timezone.now().date()
        self.rep_a = RepairService.objects.create(customer=self.cust_a, item_name="Fan", problem_description="x", location=self.loc_a, return_date=today)
        self.rep_b = RepairService.objects.create(customer=self.cust_b, item_name="Fridge", problem_description="y", location=self.loc_b, return_date=today)
        self.staff_a = make_user("staff_a", "sale_staff", self.outlet_a, "95945000001")
        self.staff_b = make_user("staff_b", "sale_staff", self.outlet_b, "95945000002")
        self.client.force_authenticate(user=self.staff_a)

    def _ids(self, url):
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200, r.content)
        data = r.json()
        rows = data.get("results", data) if isinstance(data, dict) else data
        return {row.get("id") for row in rows}

    def test_staff_a_sees_only_shop_a_customers(self):
        ids = self._ids("/api/customers/")
        self.assertIn(self.cust_a.id, ids)
        self.assertNotIn(self.cust_b.id, ids)

    def test_staff_a_sees_only_shop_a_repairs(self):
        ids = self._ids("/api/service/repairs/")
        self.assertIn(self.rep_a.id, ids)
        self.assertNotIn(self.rep_b.id, ids)

    def test_staff_a_cannot_open_shop_b_repair_detail(self):
        r = self.client.get(f"/api/service/repairs/{self.rep_b.id}/")
        self.assertEqual(r.status_code, 404, r.content)

    def test_staff_b_sees_only_shop_b(self):
        self.client.force_authenticate(user=self.staff_b)
        ids = self._ids("/api/customers/")
        self.assertIn(self.cust_b.id, ids)
        self.assertNotIn(self.cust_a.id, ids)
