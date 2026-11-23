"""
Unit and integration tests (Task C - A to K recommendation).
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from .throttling import ApiUserThrottle, AuthThrottle, _get_ip

User = get_user_model()


class HealthEndpointsTest(TestCase):
    """Integration: Health check endpoints for SRE."""

    def setUp(self):
        self.client = Client()

    def test_health_liveness(self):
        r = self.client.get("/health/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "hobopos")

    def test_health_ready(self):
        r = self.client.get("/health/ready/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data.get("status"), "ready")
        self.assertEqual(data.get("db"), "ok")


class ThrottlingUnitTest(TestCase):
    """Unit: Rate limit cache keys."""

    def test_get_ip_uses_last_forwarded_hop(self):
        # Proxy-appended hop is the trustworthy one; left entries are client's.
        class Req:
            META = {"HTTP_X_FORWARDED_FOR": " 1.2.3.4 , 10.0.0.1 "}
        self.assertEqual(_get_ip(Req()), "10.0.0.1")

    def test_get_ip_forwarded_is_spoof_stable(self):
        # Rotating only the client-controlled part must not change the key,
        # otherwise every rate limit (login / license) can be bypassed.
        real = {"HTTP_X_FORWARDED_FOR": "9.9.9.9, 203.0.113.7"}
        spoofed = {"HTTP_X_FORWARDED_FOR": "8.8.8.8, 203.0.113.7"}

        class A:
            META = real

        class B:
            META = spoofed
        self.assertEqual(_get_ip(A()), _get_ip(B()))

    def test_get_ip_fallback(self):
        class Req:
            META = {"REMOTE_ADDR": "127.0.0.1"}
        self.assertEqual(_get_ip(Req()), "127.0.0.1")

    def test_api_user_throttle_anon(self):
        class Req:
            user = None
            META = {"REMOTE_ADDR": "1.2.3.4"}
        t = ApiUserThrottle()
        key = t.get_cache_key(Req(), None)
        self.assertTrue(key.startswith("api_anon_"))
        self.assertIn("1.2.3.4", key)
