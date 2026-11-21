"""
Myanmar phone number normalization and validation.
Accepted input shapes: 09xxxxxxxx, 9xxxxxxxx, +959xxxxxxxx, 959xxxxxxxx, 959xxxxxxxxx.

History (important for reads):
  The old normalizer returned `'95' + digits[:9]`, which silently DROPPED the last
  digit of every standard 11-digit number: `09451234567` -> `95945123456`.
  Two numbers differing only in the last digit therefore mapped to the same
  row (registration lockout + ambiguous login lookup), and the digit is not
  recoverable from the stored value.
  The canonical form below keeps every digit (`09451234567` -> `959451234567`)
  while reads still accept the legacy 11-char values through
  `phone_lookup_variants()`.
"""
import re

# Myanmar country code without +
MYANMAR_COUNTRY_CODE = "95"
MYANMAR_COUNTRY_CODE_PLUS = "+95"

# Legacy rows are 11 chars (95 + first nine local digits); new rows keep the
# full local part: 95 + 9 digits = 11, or 95 + 10 digits = 12.
LEGACY_LENGTH = 11

# Kept for backward-compatible imports (format hint: optional +, optional 95, then national number)
PHONE_REGEX = re.compile(r"^\+?(95)?9\d{8,9}$")

LOCAL_MIN_LEN = 9
LOCAL_MAX_LEN = 10


def _national_digits(digits: str) -> str:
    """Strip every country/leading-0 decoration, leaving the national number."""
    if not digits:
        return ""
    if digits.startswith("0"):
        return digits[1:]
    if digits.startswith("95"):
        # '+'+95 / 95 / 959... all start with the country code here
        return digits[2:]
    return digits


def normalize_phone_for_db(phone: str, country_code: str = "+95") -> str:
    """
    Canonical storage form: '95' + national number (9 or 10 digits, no truncation).
    Accepts: 09xxxxxxxx, 9xxxxxxxx, +959xxxxxxxx, 959xxxxxxxx.
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone).strip())
    if digits.startswith("0"):
        # Local form 09...: drop the trunk 0, the rest is already national.
        # A 9-digit national starting with "95" (e.g. 0950011189) is not a
        # +95 number, so strip the leading 0 here and stop.
        national = digits[1:]
    elif digits.startswith("959") and len(digits) in (LOCAL_MIN_LEN + 2, LOCAL_MAX_LEN + 2):
        # Country-code form (+95.../95...): the digits after 95 have exactly the
        # length of a national number, so 95 is really the country code.
        national = digits[2:]
    else:
        national = digits
    return "95" + national


def phone_lookup_variants(normalized: str) -> list:
    """
    Values to try when reading `User.phone_number` / checking uniqueness.

    Ordered: canonical first, then the legacy 11-char form still seen in rows
    written before the truncation bug was fixed. Deduplicated, never empty.
    """
    values = []
    if normalized:
        values.append(normalized)
        if len(normalized) > LEGACY_LENGTH and normalized.startswith("95"):
            values.append(normalized[:LEGACY_LENGTH])
    seen, out = set(), []
    for v in values:
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out or [""]


def find_user_by_phone(qs, phone, **filters):
    """
    Look a user up by phone: canonical value first, legacy 11-char form second.

    Keeps accounts written by the old truncating normalizer loggable while new
    accounts always store the full, unambiguous number.
    """
    for value in phone_lookup_variants(phone):
        user = qs.filter(phone_number=value, **filters).first()
        if user is not None:
            return user
    return None


def validate_myanmar_phone(phone: str, country_code: str = "+95"):
    """
    Validate a Myanmar phone number.
    Returns (is_valid, canonical_number_or_error_message).
    """
    if not phone or not str(phone).strip():
        return False, "Phone number is required."
    normalized = normalize_phone_for_db(phone, country_code)
    national = normalized[2:] if normalized.startswith("95") else ""
    if not normalized.startswith("959"):
        return False, "Invalid Myanmar phone. Use 09xxxxxxxx or +959xxxxxxxx."
    if not (LOCAL_MIN_LEN <= len(national) <= LOCAL_MAX_LEN):
        return False, "Invalid Myanmar phone. Use 09xxxxxxxx or +959xxxxxxxx."
    if not national.isdigit():
        return False, "Invalid Myanmar phone. Use 09xxxxxxxx or +959xxxxxxxx."
    return True, normalized


def display_phone(normalized: str, with_plus: bool = True) -> str:
    """Convert a stored 959xxxxxxxx (11 or 12 chars) to 09xxxxxxxx / +95 ... form."""
    if not normalized:
        return ""
    digits = re.sub(r"\D", "", normalized)
    if len(digits) >= 11 and digits.startswith("959"):
        local = "0" + digits[2:]  # 09xxxxxxxx
        return "+95 " + digits[2:] if with_plus else local
    return normalized