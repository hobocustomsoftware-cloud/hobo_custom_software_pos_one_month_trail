"""
Follow-up Marketing Sync: new user registration → Telegram + Google Sheets.
Uses .env: TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, GOOGLE_SHEETS_*, GOOGLE_SHEETS_JSON (credentials path).
Failures are logged; registration is never blocked.
- Telegram: "New Signup: {name}, Phone: {phone}" (Name + Phone only).
- Google Sheets: one row [Date, Name, Phone] — columns A=Date, B=Name, C=Phone.
"""
import logging
import os
from django.conf import settings

logger = logging.getLogger(__name__)


def _send_telegram(message: str) -> bool:
    """Send message to Telegram. Returns True on success. Logs and returns False on any error."""
    token = (getattr(settings, 'TELEGRAM_BOT_TOKEN', None) or '').strip() or os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = (getattr(settings, 'TELEGRAM_CHAT_ID', None) or '').strip() or os.getenv('TELEGRAM_CHAT_ID', '')
    if not token or not chat_id:
        logger.debug("Telegram skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        r = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10)
        if r.status_code != 200:
            logger.warning("Telegram send failed: status=%s body=%s", r.status_code, r.text[:200])
            return False
        return True
    except requests.RequestException as e:
        logger.warning("Telegram request error: %s", e)
        return False
    except Exception as e:
        logger.warning("Telegram send error: %s", e)
        return False


def _get_credentials_path() -> str:
    """Resolve path to Google service account JSON. Prefer settings, then GOOGLE_SHEETS_JSON env."""
    path = (getattr(settings, 'GOOGLE_SHEETS_CREDENTIALS_JSON', None) or '').strip()
    if not path:
        path = (os.getenv('GOOGLE_SHEETS_JSON') or '').strip()
    return path or ''


def _append_to_google_sheet(row: list) -> bool:
    """
    Append one row to the configured Google Sheet.
    Expected row format: [Date, Name, Phone] → columns A=Date, B=Name, C=Phone.
    Returns True on success. Handles file-not-found and API errors without raising.
    """
    spreadsheet_id = (getattr(settings, 'GOOGLE_SHEETS_SPREADSHEET_ID', None) or '').strip() or os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID', '')
    sheet_name = (getattr(settings, 'GOOGLE_SHEETS_SHEET_NAME', None) or 'Registrations').strip() or 'Registrations'
    creds_path = _get_credentials_path()
    if not spreadsheet_id or not creds_path:
        logger.debug("Google Sheets skipped: GOOGLE_SHEETS_SPREADSHEET_ID or credentials path not set")
        return False
    if not os.path.isfile(creds_path):
        logger.warning("Google Sheets credentials file not found: %s", creds_path)
        return False
    try:
        import json
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        with open(creds_path, 'r', encoding='utf-8') as f:
            info = json.load(f)
        scopes = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = service_account.Credentials.from_service_account_info(info, scopes=scopes)
        service = build('sheets', 'v4', credentials=credentials)
        body = {'values': [row]}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=f"'{sheet_name}'!A:C",
            valueInputOption='USER_ENTERED',
            body=body,
        ).execute()
        logger.debug("Google Sheet append succeeded: 1 row")
        return True
    except FileNotFoundError:
        logger.warning("Google Sheets credentials file not found: %s", creds_path)
        return False
    except PermissionError as e:
        logger.warning("Google Sheets credentials file not readable: %s", e)
        return False
    except ImportError as e:
        logger.warning("Google Sheets sync skipped (missing deps): %s", e)
        return False
    except HttpError as e:
        logger.warning("Google Sheets API error: %s", e)
        return False
    except Exception as e:
        logger.warning("Google Sheet append error: %s", e)
        return False


def sync_new_registration(user, shop_name: str = ''):
    """
    Sync new registration to Telegram and Google Sheets (follow-up marketing).
    - Telegram: "New Signup: {name}, Phone: {phone}" (no shop name).
    - Google Sheets: one row [Date, Name, Phone]; A=Date, B=Name, C=Phone.
    Uses Django timezone for Date. Does not raise; failures are logged.
    """
    full_name = f"{getattr(user, 'first_name', '') or ''} {getattr(user, 'last_name', '') or ''}".strip() or getattr(user, 'username', '')
    phone = getattr(user, 'phone_number', None) or ''

    message = f"New Signup: {full_name}, Phone: {phone}"
    _send_telegram(message)

    from django.utils import timezone
    row = [timezone.now().strftime('%Y-%m-%d %H:%M'), full_name, phone]
    _append_to_google_sheet(row)
