"""
Authentication / account-flow tests:
- phone login (UnifiedLoginView) + brute-force lockout
- JWT token endpoint (/api/token/)
- public registration (creates the Owner account + tokens)
- password reset flow
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from core.models import Role, LoginFailAttempt
from core.phone_utils import validate_myanmar_phone

User = get_user_model()

PHONE_INPUT = "0945001122"
PHONE_NORMALIZED = "95945001122"

LOGIN_URL = "/api/core/auth/login/"
TOKEN_URL = "/api/token/"
REGISTER_URL = "/api/core/register/"


class PhoneLoginTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role, _ = Role.objects.get_or_create(name="owner")
        self.user = User.objects.create_user(
            username="login_owner",
            password="Correct-Horse-1",
            phone_number=PHONE_NORMALIZED,
            role_obj=self.role,
        )

    def test_phone_is_normalized_the_way_the_login_lookup_does(self):
        ok, normalized = validate_myanmar_phone(PHONE_INPUT)
        self.assertTrue(ok)
        self.assertEqual(normalized, PHONE_NORMALIZED)

    def test_login_success_returns_tokens_and_profile(self):
        r = self.client.post(LOGIN_URL, {"login": PHONE_INPUT, "password": "Correct-Horse-1"})
        self.assertEqual(r.status_code, 200, r.content)
        body = r.json()
        self.assertIn("access", body)
        self.assertIn("refresh", body)
        self.assertEqual(body["user"]["username"], "login_owner")
        self.assertEqual(body["user"]["role"], "owner")

        # Token must actually authorize a protected endpoint.
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {body["access"]}')
        me = self.client.get("/api/core/me/")
        self.assertEqual(me.status_code, 200, me.content)
        self.assertEqual(me.json()["username"], "login_owner")

    def test_login_rejects_wrong_password(self):
        r = self.client.post(LOGIN_URL, {"login": PHONE_INPUT, "password": "nope"})
        self.assertEqual(r.status_code, 401)

    def test_login_rejects_unknown_phone(self):
        r = self.client.post(LOGIN_URL, {"login": "09999999999", "password": "whatever-1"})
        self.assertEqual(r.status_code, 401)
        # ...and must not tell the caller that the account exists or not.
        self.assertNotIn("phone", r.json().get("detail", "").lower())

    def test_login_requires_password(self):
        r = self.client.post(LOGIN_URL, {"login": PHONE_INPUT})
        self.assertEqual(r.status_code, 400)

    def test_five_failures_lock_the_identifier(self):
        for _ in range(5):
            r = self.client.post(LOGIN_URL, {"login": PHONE_INPUT, "password": "wrong"})
            self.assertEqual(r.status_code, 401)
        r = self.client.post(LOGIN_URL, {"login": PHONE_INPUT, "password": "Correct-Horse-1"})
        self.assertEqual(r.status_code, 403)
        self.assertIn("locked", r.json()["detail"].lower())

        attempt = LoginFailAttempt.objects.get(phone_normalized=PHONE_NORMALIZED)
        self.assertGreaterEqual(attempt.fail_count, 5)
        self.assertIsNotNone(attempt.locked_until)

    def test_successful_login_resets_the_lockout_counter(self):
        self.client.post(LOGIN_URL, {"login": PHONE_INPUT, "password": "wrong"})
        self.client.post(LOGIN_URL, {"login": PHONE_INPUT, "password": "Correct-Horse-1"})
        attempt = LoginFailAttempt.objects.get(phone_normalized=PHONE_NORMALIZED)
        self.assertEqual(attempt.fail_count, 0)
        self.assertIsNone(attempt.locked_until)


class JwtTokenEndpointTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.role, _ = Role.objects.get_or_create(name="cashier")
        self.user = User.objects.create_user(
            username="pos_cashier",
            password="Token-Pass-22",
            phone_number="95945002233",
            role_obj=self.role,
        )

    def test_username_password_grants_access_token(self):
        r = self.client.post(TOKEN_URL, {"username": "pos_cashier", "password": "Token-Pass-22"})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("access", r.json())

    def test_bad_password_is_401(self):
        r = self.client.post(TOKEN_URL, {"username": "pos_cashier", "password": "bad"})
        self.assertEqual(r.status_code, 401)

    def test_phone_login_grants_access_token(self):
        r = self.client.post(TOKEN_URL, {"login": "0945002233", "password": "Token-Pass-22"})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("access", r.json())

    def test_token_refresh_requires_valid_refresh(self):
        r = self.client.post(TOKEN_URL, {"username": "pos_cashier", "password": "Token-Pass-22"})
        refresh = r.json()["refresh"]
        ok = self.client.post("/api/token/refresh/", {"refresh": refresh})
        self.assertEqual(ok.status_code, 200)
        bad = self.client.post("/api/token/refresh/", {"refresh": "garbage"})
        self.assertIn(bad.status_code, (400, 401))

    def test_protected_endpoint_rejects_anonymous(self):
        r = self.client.get("/api/core/me/")
        self.assertIn(r.status_code, (401, 403))

    def test_protected_endpoint_rejects_forged_token(self):
        r = self.client.get("/api/core/me/", HTTP_AUTHORIZATION="Bearer not.a.token")
        self.assertIn(r.status_code, (401, 403))


class RegistrationTest(TestCase):
    """POST /api/core/register/ creates the Owner account of a new shop."""

    def setUp(self):
        self.client = APIClient()
        self.payload = {
            "owner_name": "Daw Khin",
            "phone_number": "09450077881",
            "shop_name": "Khin Welding",
            "password": "Shop-Pass-42",
            "password_confirm": "Shop-Pass-42",
        }

    @staticmethod
    def _norm(phone):
        """The exact form the DB and the login lookup use (core.phone_utils)."""
        ok, value = validate_myanmar_phone(phone)
        assert ok, value
        return value

    def test_register_creates_owner_and_returns_session(self):
        r = self.client.post(REGISTER_URL, self.payload, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        body = r.json()
        self.assertIn("access", body)
        self.assertEqual(body["user"]["role"], "owner")

        user = User.objects.get(phone_number=self._norm(self.payload["phone_number"]))
        self.assertEqual(user.first_name, "Daw Khin")
        self.assertTrue(user.check_password("Shop-Pass-42"))
        self.assertIsNotNone(user.primary_outlet_id)

    def test_register_rejects_mismatched_passwords(self):
        payload = dict(self.payload, password_confirm="Different-42")
        r = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(r.status_code, 400)

    def test_register_rejects_missing_shop_name(self):
        payload = dict(self.payload, shop_name="")
        r = self.client.post(REGISTER_URL, payload, format="json")
        self.assertEqual(r.status_code, 400)

    def _post_register(self):
        # TestCase wraps everything in an atomic block, so on_commit
        # callbacks never fire: capture them and run explicitly.
        from django.test import TestCase as _TC
        with _TC.captureOnCommitCallbacks(execute=True):
            return self.client.post(REGISTER_URL, self.payload, format="json")

    def test_register_dispatches_marketing_via_celery_first(self):
        """Celery .delay() success → inline sync must NOT also run."""
        from unittest.mock import patch
        with patch("core.tasks.sync_new_signup_marketing.delay") as d, \
             patch("core.external_sync.sync_new_registration") as inline:
            r = self._post_register()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(d.called)
        inline.assert_not_called()

    def test_register_falls_back_inline_when_celery_fails(self):
        """Broker down (.delay raises) → exactly one inline sync."""
        from unittest.mock import patch
        with patch("core.tasks.sync_new_signup_marketing.delay",
                    side_effect=ConnectionError("broker down")), \
             patch("core.external_sync.sync_new_registration") as inline:
            r = self._post_register()
        self.assertEqual(r.status_code, 201, r.content)
        self.assertTrue(inline.called)

    def test_register_never_sends_twice(self):
        """Success path sends via Celery OR inline — count total sends == 1."""
        from unittest.mock import patch
        with patch("core.tasks.sync_new_signup_marketing.delay") as d, \
             patch("core.external_sync.sync_new_registration") as inline:
            self._post_register()
        total = int(d.called) + int(inline.called)
        self.assertEqual(total, 1)

    def test_register_rejects_duplicate_phone_regardless_of_spelling(self):
        """The same number typed as 09..., +95... or 95... must not bypass the check."""
        existing = "0950011189"
        User.objects.create_user(
            username="taken", password="x-12345678", phone_number=self._norm(existing),
            role_obj=Role.objects.get_or_create(name="owner")[0],
        )
        raw = self.client.post(REGISTER_URL, dict(self.payload, phone_number=existing),
                               format="json")
        self.assertEqual(raw.status_code, 400, raw.content)

        plus = self.client.post(REGISTER_URL,
                                dict(self.payload, phone_number="+95950011189"),
                                format="json")
        self.assertEqual(plus.status_code, 400, plus.content)


class PasswordResetFlowTest(TestCase):
    """
    Hardened reset flow: only an authenticated Manager+ may request a token
    (this offline POS has no email/SMS channel to verify the caller), and only
    a Manager+ may redeem it. Anonymous callers get 401/403, never a token.
    """

    def setUp(self):
        self.client = APIClient()
        self.manager_role, _ = Role.objects.get_or_create(name="manager")
        self.manager = User.objects.create_user(
            username="reset_manager",
            password="Manager-Pass-1",
            phone_number="95945009911",
            role_obj=self.manager_role,
        )
        self.client.force_authenticate(user=self.manager)
        self.role, _ = Role.objects.get_or_create(name="sale_staff")
        self.user = User.objects.create_user(
            username="reset_user",
            password="Old-Password-1",
            phone_number="95945003344",
            role_obj=self.role,
        )

    def test_reset_round_trip(self):
        from unittest.mock import patch
        from django.core.signing import Signer
        from django.utils import timezone
        from datetime import timedelta
        # Token goes to the owner over Telegram, never back to the requester.
        with patch("core.external_sync._send_telegram", return_value=True):
            forgot = self.client.post("/api/core/forgot-password/", {"username": "reset_user"})
        self.assertEqual(forgot.status_code, 200, forgot.content)
        self.assertTrue(forgot.json().get("delivered"))
        self.assertNotIn("token", forgot.json())
        signer = Signer()
        payload = f'{self.user.id}:{(timezone.now() + timedelta(hours=1)).timestamp()}'
        token = signer.sign(payload)

        reset = self.client.post("/api/core/reset-password/", {
            "token": token, "new_password": "Brand-New-9",
        })
        self.assertEqual(reset.status_code, 200, reset.content)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Brand-New-9"))
        self.assertFalse(self.user.requires_password_change)

        # old password no longer works, new one does (phone login)
        old = self.client.post("/api/core/auth/login/",
                               {"login": "0945003344", "password": "Old-Password-1"})
        self.assertEqual(old.status_code, 401)
        new = self.client.post("/api/core/auth/login/",
                               {"login": "0945003344", "password": "Brand-New-9"})
        self.assertEqual(new.status_code, 200)

    def test_reset_rejects_empty_token(self):
        r = self.client.post("/api/core/reset-password/", {"new_password": "Brand-New-9"})
        self.assertEqual(r.status_code, 400)

    def test_reset_rejects_tampered_token(self):
        r = self.client.post("/api/core/reset-password/", {
            "token": "invalid.token.value", "new_password": "Brand-New-9",
        })
        self.assertEqual(r.status_code, 400)

    def test_reset_requires_reasonable_password_length(self):
        from django.core.signing import Signer
        from django.utils import timezone
        from datetime import timedelta
        signer = Signer()
        payload = f'{self.user.id}:{(timezone.now() + timedelta(hours=1)).timestamp()}'
        token = signer.sign(payload)
        r = self.client.post("/api/core/reset-password/", {"token": token, "new_password": "12"})
        self.assertEqual(r.status_code, 400)

    def test_forgot_password_reports_unknown_account(self):
        r = self.client.post("/api/core/forgot-password/", {"username": "nobody-here"})
        self.assertEqual(r.status_code, 404)

    def test_forgot_password_rejects_anonymous(self):
        anon = APIClient()
        r = anon.post("/api/core/forgot-password/", {"username": "reset_user"})
        self.assertIn(r.status_code, (401, 403))

    def test_reset_rejects_anonymous_even_with_valid_token(self):
        from django.core.signing import Signer
        from django.utils import timezone
        from datetime import timedelta
        signer = Signer()
        payload = f'{self.user.id}:{(timezone.now() + timedelta(hours=1)).timestamp()}'
        token = signer.sign(payload)
        anon = APIClient()
        r = anon.post("/api/core/reset-password/", {
            "token": token, "new_password": "Brand-New-9",
        })
        self.assertIn(r.status_code, (401, 403))

    def test_forgot_password_delivers_over_telegram_not_in_response(self):
        from unittest.mock import patch
        with patch("core.external_sync._send_telegram", return_value=True) as sent:
            r = self.client.post("/api/core/forgot-password/", {"username": "reset_user"})
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(sent.called)
        self.assertNotIn("token", r.json())

    def test_forgot_password_503_without_telegram(self):
        from unittest.mock import patch
        with patch("core.external_sync._send_telegram", return_value=False):
            r = self.client.post("/api/core/forgot-password/", {"username": "reset_user"})
        self.assertEqual(r.status_code, 503)