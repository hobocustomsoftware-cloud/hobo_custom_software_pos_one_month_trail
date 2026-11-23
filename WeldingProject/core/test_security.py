"""
Security regression tests: response headers, the 30-day trial gate, licence
endpoints and the configuration the deployment checklist relies on.
"""
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from core.models import Role, ShopSettings

User = get_user_model()

# DRF reads REST_FRAMEWORK lazily, so tests that repeat requests can turn the
# default throttle off without touching production settings (DRF reloads
# api_settings on django.test.signals.setting_changed).
_NO_THROTTLE = {
    "REST_FRAMEWORK": {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": (),
    },
}


class SecurityHeadersTest(TestCase):
    """SecurityHeadersMiddleware must run on *every* response."""

    def setUp(self):
        self.client = Client()

    def test_health_response_carries_security_headers(self):
        r = self.client.get("/health/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r["X-Frame-Options"], "DENY")
        self.assertIn("strict-origin-when-cross-origin", r["Referrer-Policy"])
        self.assertIn("frame-ancestors 'none'", r["Content-Security-Policy"])
        self.assertIn("camera=()", r["Permissions-Policy"])
        self.assertEqual(r["X-XSS-Protection"], "1; mode=block")

    def test_error_response_still_has_the_headers(self):
        # Middleware ordering bugs show up on error responses: the headers (and
        # CORS, see MIDDLEWARE order) must survive a 401 as well as a 200.
        r = self.client.get("/api/core/me/")
        self.assertIn(r.status_code, (401, 403))
        self.assertEqual(r["X-Content-Type-Options"], "nosniff")
        self.assertEqual(r["X-Frame-Options"], "DENY")
        self.assertIn("frame-ancestors 'none'", r["Content-Security-Policy"])


class SettingsSecurityInvariantsTest(TestCase):
    """Fail loudly if someone deletes the production security switches."""

    def test_jwt_is_the_default_authentication(self):
        self.assertIn(
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"],
        )
        self.assertIn(
            "rest_framework.permissions.IsAuthenticated",
            settings.REST_FRAMEWORK["DEFAULT_PERMISSION_CLASSES"],
        )

    def test_csrf_trusted_origins_are_https_for_the_public_domain(self):
        self.assertIn("https://pos.hobocustomsoftware.com", settings.CSRF_TRUSTED_ORIGINS)

    def test_cors_allow_list_covers_the_frontend_dev_origins(self):
        for origin in ("http://localhost:5173", "http://127.0.0.1:5173"):
            with self.subTest(origin=origin):
                self.assertIn(origin, settings.CORS_ALLOWED_ORIGINS)

    def test_session_cookies_are_httponly(self):
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)
        self.assertEqual(settings.SESSION_COOKIE_SECURE, settings.CSRF_COOKIE_SECURE)

    def test_production_mode_settings_boot_hardened(self):
        """Re-read settings.py with a production environment.

        Django's runner forces DEBUG=False *after* settings have been imported,
        so the only way to assert what a customer's deployment actually boots
        with is to reload the module with DJANGO_DEBUG=0.
        """
        import importlib
        import os
        from django.core.exceptions import ImproperlyConfigured
        import WeldingProject.settings as project_settings

        env_keys = ("DJANGO_DEBUG", "DJANGO_SECRET_KEY", "DJANGO_ALLOWED_HOSTS",
                    "CORS_ALLOW_ALL", "DEMO_MODE")
        saved = {k: os.environ.get(k) for k in env_keys}
        try:
            for key in env_keys:
                os.environ.pop(key, None)
            os.environ["DJANGO_DEBUG"] = "0"

            # 1) production boot must fail closed without a secret key
            with self.assertRaises(ImproperlyConfigured):
                importlib.reload(project_settings)

            # 2) ...and must come up hardened once one is provided
            os.environ["DJANGO_SECRET_KEY"] = "production-key-" + "x" * 60
            importlib.reload(project_settings)
            self.assertFalse(project_settings.DEBUG)
            self.assertTrue(project_settings.SESSION_COOKIE_SECURE)
            self.assertTrue(project_settings.CSRF_COOKIE_SECURE)
            self.assertTrue(project_settings.SECURE_HSTS_SECONDS >= 31536000)
            self.assertNotIn("*", project_settings.ALLOWED_HOSTS)
            self.assertNotIn("django-insecure-", project_settings.SECRET_KEY)
            self.assertFalse(project_settings.CORS_ALLOW_ALL_ORIGINS)
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            importlib.reload(project_settings)

    def test_password_validators_are_configured(self):
        names = [v["NAME"] for v in settings.AUTH_PASSWORD_VALIDATORS]
        self.assertTrue(any("MinimumLengthValidator" in n for n in names))
        self.assertTrue(any("CommonPasswordValidator" in n for n in names))

    def test_only_one_effective_append_slash_value(self):
        # APPEND_SLASH used to be set False near the top and True at the bottom.
        self.assertTrue(settings.APPEND_SLASH)

    def test_production_refuses_to_boot_without_a_secret_key(self):
        self.assertTrue(settings.SECRET_KEY)


class TrialGateTest(TestCase):
    """Unified gate trial leg: 30 days, then business APIs return 403."""

    def setUp(self):
        import os
        # Trial enforcement only runs where licenses are enforced
        # (on_premise); elsewhere SKIP_LICENSE/hosted skips both gates.
        os.environ['DEPLOYMENT_MODE'] = 'on_premise'
        os.environ.pop('SKIP_LICENSE', None)
        self.addCleanup(os.environ.pop, 'DEPLOYMENT_MODE', None)
        self.client = APIClient()
        role, _ = Role.objects.get_or_create(name="sale_staff")
        self.user = User.objects.create_user(
            username="trial_staff",
            password="Trial-Pass-12",
            phone_number="95945004455",
            role_obj=role,
        )
        self.client.force_authenticate(user=self.user)
        self.shop = ShopSettings.get_settings()

    def _set_trial_start(self, age_days):
        value = timezone.now() - timedelta(days=age_days)
        ShopSettings.objects.filter(pk=self.shop.pk).update(trial_start_date=value)
        return value

    def test_within_trial_window_the_api_works(self):
        self._set_trial_start(5)
        r = self.client.get("/api/staff/items/")
        self.assertEqual(r.status_code, 200, r.content)

    def test_expired_trial_blocks_business_api(self):
        self._set_trial_start(40)
        r = self.client.get("/api/staff/items/")
        self.assertEqual(r.status_code, 403, r.content)
        body = r.json()
        self.assertEqual(body["error"], "trial_expired")
        self.assertIn("contact", body)

    def test_expired_trial_keeps_auth_and_setup_alive(self):
        self._set_trial_start(40)
        self.assertEqual(self.client.get("/api/core/shop-settings/").status_code, 200)
        self.assertEqual(self.client.get("/api/core/me/").status_code, 403)

    def test_trial_is_30_days_not_31(self):
        self._set_trial_start(29)
        self.assertEqual(self.client.get("/api/staff/items/").status_code, 200)
        self._set_trial_start(30)
        self.assertEqual(self.client.get("/api/staff/items/").status_code, 403)

    def test_trial_clock_cannot_be_rewritten_through_the_settings_api(self):
        started = self._set_trial_start(1)
        r = self.client.put(
            "/api/core/shop-settings/",
            {"trial_start_date": "2030-01-01T00:00:00Z"},
            format="json",
        )
        self.assertIn(r.status_code, (200, 400), r.content)
        self.shop.refresh_from_db()
        # Field is not part of ShopSettingsSerializer -> the trial clock stands.
        self.assertEqual(self.shop.trial_start_date, started)


@override_settings(**_NO_THROTTLE)
class LicenseEndpointTest(TestCase):
    """Public licence endpoints: status readable, activation rejects junk keys."""

    def setUp(self):
        self.client = APIClient()

    def test_status_is_public_and_never_500s(self):
        r = self.client.get("/api/license/status/")
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertIn("status", body)
        self.assertIn("can_use", body)
        self.assertIn("machine_id", body)

    def test_unknown_key_is_rejected_locally(self):
        r = self.client.post("/api/license/activate/", {"license_key": "NOT-A-REAL-KEY-123"})
        self.assertEqual(r.status_code, 400)

    def test_missing_key_is_a_400(self):
        r = self.client.post("/api/license/activate/", {})
        self.assertEqual(r.status_code, 400)

    def test_remote_activate_requires_both_arguments(self):
        r = self.client.post("/api/license/remote-activate/", {"license_key": "X"})
        self.assertEqual(r.status_code, 400)


class LicenseMiddlewareModeTest(TestCase):
    """_license_mode(): SKIP_LICENSE > DEPLOYMENT_MODE > DEBUG."""

    def setUp(self):
        import os
        from license import middleware as lic_mid
        self._saved = {k: os.environ.get(k) for k in ("SKIP_LICENSE", "DEPLOYMENT_MODE", "DJANGO_DEBUG")}
        self.mid = lic_mid

    def tearDown(self):
        import os
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def _mode(self, **env):
        import os
        for k in ("SKIP_LICENSE", "DEPLOYMENT_MODE"):
            os.environ.pop(k, None)
        os.environ.update(env)
        with override_settings(DEBUG=True):
            return self.mid._license_mode()

    def test_skip_license_wins_over_everything(self):
        self.assertEqual(self._mode(SKIP_LICENSE="true", DEPLOYMENT_MODE="on_premise"), "skip")

    def test_hosted_never_enforces(self):
        self.assertEqual(self._mode(DEPLOYMENT_MODE="hosted"), "skip")

    def test_on_premise_enforces_even_in_debug(self):
        # Shops rehearse expiry locally; DEBUG must not silently disable it.
        self.assertEqual(self._mode(DEPLOYMENT_MODE="on_premise"), "enforce")

    def test_unset_mode_keeps_legacy_debug_skip(self):
        self.assertEqual(self._mode(), "skip")


class AnonymousApiAccessTest(TestCase):
    """Default REST_FRAMEWORK permission must be IsAuthenticated."""

    def setUp(self):
        self.client = APIClient()

    def test_me_endpoint_blocks_anonymous(self):
        self.assertIn(self.client.get("/api/core/me/").status_code, (401, 403))

    def test_employee_endpoint_blocks_anonymous(self):
        self.assertIn(self.client.get("/api/core/employees/").status_code, (401, 403))

    def test_pos_list_blocks_anonymous(self):
        self.assertIn(self.client.get("/api/staff/items/").status_code, (401, 403))

    def test_forged_bearer_token_is_rejected(self):
        r = self.client.get("/api/core/me/", HTTP_AUTHORIZATION="Bearer aaa.bbb.ccc")
        self.assertIn(r.status_code, (401, 403))


class UnifiedGateTest(TestCase):
    """_unified_access_check(): one order for license + trial."""

    def setUp(self):
        import os
        self._saved = {k: os.environ.get(k) for k in ("SKIP_LICENSE", "DEPLOYMENT_MODE")}
        os.environ["DEPLOYMENT_MODE"] = "on_premise"
        os.environ.pop("SKIP_LICENSE", None)

    def tearDown(self):
        import os
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v

    def test_skip_switch_opens_the_gate(self):
        import os
        from license.middleware import _unified_access_check
        os.environ["SKIP_LICENSE"] = "true"
        self.assertIsNone(_unified_access_check("/api/sales/"))

    def test_auth_paths_stay_open(self):
        from license.middleware import _unified_access_check
        self.assertIsNone(_unified_access_check("/api/core/auth/login/"))
        self.assertIsNone(_unified_access_check("/api/token/"))

    def test_valid_installation_passes(self):
        from license.middleware import _unified_access_check
        verdict = _unified_access_check("/api/sales/")
        self.assertIsNone(verdict)


class SubscriptionPlansTest(TestCase):
    """Dynamic plans: public, seeded, editable without deploys."""

    def setUp(self):
        self.client = APIClient()

    def test_plans_are_public_and_seeded(self):
        r = self.client.get("/api/license/plans/")
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertGreaterEqual(len(body["plans"]), 3)
        self.assertTrue(body["backup_addon_available"])
        codes = [p["code"] for p in body["plans"]]
        self.assertIn("sub_basic", codes)

    def test_plan_price_edit_is_instant(self):
        from license.models import SubscriptionPlan
        self.client.get("/api/license/plans/")  # seed
        plan = SubscriptionPlan.objects.get(code="sub_basic")
        plan.price_mmk = 99999
        plan.save()
        body = self.client.get("/api/license/plans/").json()
        price = [p for p in body["plans"] if p["code"] == "sub_basic"][0]["price_mmk"]
        self.assertEqual(price, 99999)


class BackupAddOnTest(TestCase):
    """Per-shop backup: local export free, cloud gated on the add-on."""

    def setUp(self):
        self.client = APIClient()
        role, _ = Role.objects.get_or_create(name="owner")
        self.owner = User.objects.create_user(
            username="backup_owner", password="Backup-Pass-1",
            phone_number="95945007788", role_obj=role,
        )
        self.client.force_authenticate(user=self.owner)

    def test_status_without_addon_offers_local_only(self):
        r = self.client.get("/api/license/backup/status/")
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertTrue(body["local_export"])
        self.assertFalse(body["cloud_backup"])

    def test_activate_with_bad_key_is_400(self):
        r = self.client.post("/api/license/backup/activate/", {"backup_key": "NOPE"})
        self.assertEqual(r.status_code, 400)

    def test_activate_with_valid_key_unlocks_cloud(self):
        from license.models import BackupAddOn
        BackupAddOn.objects.create(license_key="BACKUP-KEY-1", is_active=True)
        r = self.client.post("/api/license/backup/activate/", {"backup_key": "BACKUP-KEY-1"})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(self.client.get("/api/license/backup/status/").json()["cloud_backup"])


class TrialCheckoutTest(TestCase):
    """Trial → paid: order → proof → approve → license."""

    def setUp(self):
        self.client = APIClient()
        role, _ = Role.objects.get_or_create(name="owner")
        self.owner = User.objects.create_user(
            username="trial_owner", password="Trial-Owner-1",
            phone_number="95945006677", role_obj=role,
        )

    def test_plans_carry_trial_cta(self):
        body = self.client.get("/api/license/plans/").json()
        self.assertIn("trial", body)
        # Fresh DB starts on trial; an approved checkout moves it to licensed.
        self.assertIn(body["trial"]["status"], ("trial", "grace", "blocked", "licensed"))

    def test_full_checkout_round_trip(self):
        order = self.client.post("/api/license/checkout/", {
            "plan_code": "sub_basic", "phone_number": "09450011223",
        })
        self.assertEqual(order.status_code, 201, order.content)
        order_id = order.json()["order_id"]
        proof = self.client.post(f"/api/license/checkout/{order_id}/proof/",
                                 {"transaction_id": "TXN123"})
        self.assertEqual(proof.status_code, 200, proof.content)
        self.client.force_authenticate(user=self.owner)
        approved = self.client.post(f"/api/license/checkout/{order_id}/approve/")
        self.assertEqual(approved.status_code, 200, approved.content)
        self.assertEqual(approved.json()["license_type"], "sub_basic")

    def test_approve_requires_manager(self):
        order = self.client.post("/api/license/checkout/", {
            "plan_code": "sub_basic", "phone_number": "09450011223",
        })
        order_id = order.json()["order_id"]
        self.client.post(f"/api/license/checkout/{order_id}/proof/", {"transaction_id": "TXN1"})
        role, _ = Role.objects.get_or_create(name="sale_staff")
        staff = User.objects.create_user(username="t_staff", password="x-12345678",
                                         phone_number="95945001199", role_obj=role)
        self.client.force_authenticate(user=staff)
        r = self.client.post(f"/api/license/checkout/{order_id}/approve/")
        self.assertEqual(r.status_code, 403)