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
