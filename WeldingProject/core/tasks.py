"""
Celery tasks for core app. Follow-up marketing sync (Telegram + Google Sheets) runs in background
so the main request-response cycle is not blocked.
Trial version: uses this project's database (get_user_model()) so Main and Trial stay isolated.
"""
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(name='core.sync_new_signup_marketing', bind=True)
def sync_new_signup_marketing(self, user_id: int, shop_name: str = ''):
    """
    Background task: sync new registration to Telegram and Google Sheets (follow-up marketing).
    - Telegram: "New Signup: {name}, Phone: {phone}" (Name + Phone only).
    - Google Sheets: one row [Date, Name, Phone]; A=Date, B=Name, C=Phone.
    Uses this project's database (get_user_model()); failures are logged and do not crash the worker.
    """
    from django.contrib.auth import get_user_model
    from .external_sync import _send_telegram, _append_to_google_sheet
    from django.utils import timezone

    User = get_user_model()
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        logger.warning("sync_new_signup_marketing: user_id=%s not found", user_id)
        return

    name = f"{getattr(user, 'first_name', '') or ''} {getattr(user, 'last_name', '') or ''}".strip() or user.username
    phone = getattr(user, 'phone_number', None) or ''
    message = f"New Signup: {name}, Phone: {phone}"
    row = [timezone.now().strftime('%Y-%m-%d %H:%M'), name, phone]

    try:
        _send_telegram(message)
    except Exception as e:
        logger.warning("sync_new_signup_marketing: Telegram failed for user_id=%s: %s", user_id, e)

    try:
        _append_to_google_sheet(row)
    except Exception as e:
        logger.warning("sync_new_signup_marketing: Google Sheet failed for user_id=%s: %s", user_id, e)
