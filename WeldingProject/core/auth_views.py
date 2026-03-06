"""
Unified login: single input accepts Phone or Email + Password.
Phone: input starts with '09' or '+95'. Email: otherwise.
5 failed attempts per identifier (phone or email) → lockout. Returns JWT and user/outlet.
"""
from __future__ import annotations

import os
import re
from typing import Tuple, Optional
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.conf import settings as django_settings
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, LoginFailAttempt
from .phone_utils import validate_myanmar_phone
from .throttling import AuthThrottle

# Lockout after 5 failures for 15 minutes
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# Store lockout key as normalized phone (11 chars) or "e:" + lowercase email (max 256)
LOGIN_IDENTIFIER_MAX_LENGTH = 320


def _is_phone_input(login: str) -> bool:
    """If input starts with 09 or +95 (after strip), treat as phone."""
    s = (login or "").strip()
    if not s:
        return False
    if s.startswith("+95") or s.startswith("09"):
        return True
    # Allow 9xxxxxxxx (9 digits) as Myanmar without leading 0
    digits = re.sub(r"\D", "", s)
    if len(digits) >= 9 and digits.startswith("9"):
        return True
    return False


def _normalize_login_identifier(login: str, country_code: str = "+95") -> Tuple[Optional[str], Optional[str], str]:
    """
    Returns (lockout_key, normalized_phone_or_none, error_message).
    lockout_key: for LoginFailAttempt (normalized phone or "e:"+email.lower()).
    normalized_phone_or_none: if phone path, the normalized phone; else None.
    error_message: non-empty only on validation error.
    """
    s = (login or "").strip()
    if not s:
        return None, None, "Login (phone or email) is required."
    if _is_phone_input(s):
        is_valid, normalized_or_error = validate_myanmar_phone(s, country_code)
        if not is_valid:
            return None, None, normalized_or_error
        return normalized_or_error, normalized_or_error, ""
    # Email path
    if "@" not in s or len(s) > 254:
        return None, None, "Enter a valid email address."
    email_lower = s.lower().strip()
    if len(email_lower) > 254:
        return None, None, "Enter a valid email address."
    return "e:" + email_lower, None, ""


def get_tokens_for_user(user):
    """JWT tokens for login response. Uses user.pk so custom User is fine."""
    try:
        refresh = RefreshToken.for_user(user)
        return {"refresh": str(refresh), "access": str(refresh.access_token)}
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("get_tokens_for_user failed for user_id=%s: %s", getattr(user, "pk", None), e)
        raise


def _build_user_payload(user):
    """Build login response user/outlet dicts; never raise (safe for 500 avoidance)."""
    try:
        role_obj = getattr(user, "role_obj", None)
        role_name = (getattr(role_obj, "name", None) or "") if role_obj else ""
    except Exception:
        role_name = ""
    payload = {
        "id": getattr(user, "id", None) or getattr(user, "pk", None),
        "username": getattr(user, "username", "") or "",
        "phone_number": getattr(user, "phone_number", "") or "",
        "email": getattr(user, "email", "") or "",
        "first_name": getattr(user, "first_name", "") or "",
        "last_name": getattr(user, "last_name", "") or "",
        "role": role_name,
        "requires_password_change": getattr(user, "requires_password_change", False),
    }
    outlet = None
    try:
        if getattr(user, "primary_outlet_id", None):
            po = getattr(user, "primary_outlet", None)
            if po is not None:
                outlet = {
                    "id": getattr(po, "id", None),
                    "name": getattr(po, "name", "") or "",
                    "code": getattr(po, "code", "") or "",
                }
    except Exception:
        pass
    return payload, outlet


class UnifiedLoginView(APIView):
    """
    POST: Login with Phone Number + Password (phone-only).
    Body: { "login": "09xxxxxxxx or +959xxxxxxxx", "password": "...", "country_code": "+95" (optional) }
    Returns: { "access", "refresh", "user": {...}, "outlet": {...} or null }
    After 5 failed attempts per phone, returns 403 locked.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        login_raw = (request.data.get("login") or "").strip()
        country_code = (request.data.get("country_code") or "+95").strip()
        if not country_code.startswith("+"):
            country_code = "+" + country_code
        password = request.data.get("password", "")

        if not password:
            return Response(
                {"detail": "Password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        lockout_key, normalized_phone, err_msg = _normalize_login_identifier(login_raw, country_code)
        if err_msg or lockout_key is None:
            return Response(
                {"detail": err_msg or "Login (phone or email) is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Phone-only: disallow email login
        if not normalized_phone:
            return Response(
                {"detail": "Phone number is required. / ဖုန်းနံပါတ် ထည့်ပါ။"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check lockout (same table: phone_normalized stores lockout_key)
        now = timezone.now()
        try:
            attempt = LoginFailAttempt.objects.get(phone_normalized=lockout_key)
            if attempt.locked_until and attempt.locked_until > now:
                return Response(
                    {
                        "detail": "Too many failed attempts. Account temporarily locked. Try again later.",
                        "locked_until": attempt.locked_until.isoformat(),
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )
        except LoginFailAttempt.DoesNotExist:
            attempt = None

        # Find user by phone or email (indexed for performance); select_related to avoid 500 on role/outlet access
        qs = User.objects.filter(is_active=True).select_related("role_obj", "primary_outlet")
        user = qs.filter(phone_number=normalized_phone).first()
        not_found_detail = "No active account found with this phone number."

        if not user:
            self._record_failure(lockout_key, attempt)
            return Response({"detail": not_found_detail}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(password):
            self._record_failure(lockout_key, attempt)
            return Response(
                {"detail": "Invalid login or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Success: reset fail count
        if attempt:
            attempt.fail_count = 0
            attempt.locked_until = None
            attempt.save()

        try:
            # JWT အတွက် pk သက်သက်သုံး (relation များ lazy load မဖြစ်အောင်)
            user_for_token = User.objects.filter(pk=user.pk).only("pk").first()
            tokens = get_tokens_for_user(user_for_token or user)
            user_payload, outlet = _build_user_payload(user)
            return Response({
                "access": tokens["access"],
                "refresh": tokens["refresh"],
                "user": user_payload,
                "outlet": outlet,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            log = logging.getLogger(__name__)
            log.exception("Login response build failed: %s", e)
            # Server မတင်ခင်စစ်တဲ့အခါ error မြင်ရအောင် DEBUG သို့မဟုတ် SHOW_LOGIN_ERROR ဖွင့်ထားရင် detail ပြမယ်
            show_error = (
                getattr(django_settings, "DEBUG", False)
                or os.environ.get("HOBOPOS_SHOW_LOGIN_ERROR", "").lower() in ("1", "true", "yes")
            )
            detail = str(e) if show_error else "Internal server error."
            return Response(
                {"detail": detail},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _record_failure(self, lockout_key: str, attempt):
        if attempt is None:
            attempt = LoginFailAttempt(phone_normalized=lockout_key[:LOGIN_IDENTIFIER_MAX_LENGTH], fail_count=0)
        attempt.fail_count += 1
        if attempt.fail_count >= MAX_FAILED_ATTEMPTS:
            attempt.locked_until = timezone.now() + timedelta(minutes=LOCKOUT_MINUTES)
        attempt.save()


class PhoneLoginView(APIView):
    """
    POST: Login with Phone Number + Password (legacy).
    Body: { "phone_number": "09xxxxxxxx", "country_code": "+95", "password": "..." }
    Prefer UnifiedLoginView with "login" field for new clients.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone_raw = (request.data.get("phone_number") or "").strip()
        country_code = (request.data.get("country_code") or "+95").strip()
        if not country_code.startswith("+"):
            country_code = "+" + country_code
        password = request.data.get("password", "")
        from rest_framework.request import Request
        merged = {**request.data, "login": phone_raw, "password": password, "country_code": country_code}
        new_request = Request(request._request, data=merged)
        return UnifiedLoginView().post(new_request)


class CustomTokenObtainView(APIView):
    """
    JWT token endpoint compatible with both:
    - Standard: { "username", "password" } → same as TokenObtainPairView.
    - Loyverse: { "login" (phone or email), "password", "country_code" (optional) } → same user lookup as UnifiedLoginView.
    Returns: { "access", "refresh" } so Swagger/Postman and any client using /api/token/ work with phone/email.
    """
    permission_classes = [AllowAny]
    throttle_classes = [AuthThrottle]

    def post(self, request):
        login_raw = (request.data.get("login") or "").strip()
        username = (request.data.get("username") or "").strip()
        password = request.data.get("password", "")
        country_code = (request.data.get("country_code") or "+95").strip()
        if not country_code.startswith("+"):
            country_code = "+" + country_code

        if not password:
            return Response(
                {"detail": "Password is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = None
        if login_raw:
            lockout_key, normalized_phone, err_msg = _normalize_login_identifier(login_raw, country_code)
            if err_msg or lockout_key is None:
                return Response({"detail": err_msg or "Login (phone or email) is required."}, status=status.HTTP_400_BAD_REQUEST)
            # Phone-only: disallow email login
            if not normalized_phone:
                return Response(
                    {"detail": "Phone number is required. / ဖုန်းနံပါတ် ထည့်ပါ။"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user = User.objects.filter(phone_number=normalized_phone, is_active=True).first()
            if user and not user.check_password(password):
                user = None
        elif username:
            user = User.objects.filter(username=username, is_active=True).first()
            if user and not user.check_password(password):
                user = None

        if not user:
            return Response(
                {"detail": "No active account found with the given credentials."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            tokens = get_tokens_for_user(user)
            return Response({"access": tokens["access"], "refresh": tokens["refresh"]}, status=status.HTTP_200_OK)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Token creation failed for user_id=%s: %s", getattr(user, 'pk', None), e)
            return Response(
                {"detail": "Unable to issue token. Try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
