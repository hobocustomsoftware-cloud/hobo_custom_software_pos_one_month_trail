"""
Myanmar phone number normalization and validation.
Formats: 09xxxxxxxx, +959xxxxxxxx, 959xxxxxxxx (9-11 digits after country code).
"""
import re

# Myanmar country code without +
MYANMAR_COUNTRY_CODE = "95"
MYANMAR_COUNTRY_CODE_PLUS = "+95"

# After normalization we store: 959xxxxxxxx (9 digits after 95 = 11 total)
# Valid: 09xxxxxxxx (9 digits), +959xxxxxxxx, 959xxxxxxxx
PHONE_REGEX = re.compile(r"^\+?9?5?9\d{7,9}$")


def normalize_phone_for_db(phone: str, country_code: str = "+95") -> str:
    """
    Normalize to digits only, Myanmar format: 959xxxxxxxx (11 chars).
    Accepts: 09xxxxxxxx, 9xxxxxxxx, +959xxxxxxxx, 959xxxxxxxx.
    """
    if not phone:
        return ""
    digits = re.sub(r"\D", "", str(phone).strip())
    # Strip leading 0
    if digits.startswith("0"):
        digits = digits[1:]
    # Ensure Myanmar: 95 then 9 then 7-9 more digits
    if digits.startswith("959"):
        return digits[:11]  # 959 + up to 8 digits
    if digits.startswith("95") and len(digits) >= 10:
        return digits[:11]
    if digits.startswith("9") and len(digits) >= 9:
        return "95" + digits[:9]
    return "95" + digits[-9:] if len(digits) >= 9 else "95" + digits.zfill(9)


def validate_myanmar_phone(phone: str, country_code: str = "+95"):
    # Returns (is_valid, normalized_or_error_message)
    """
    Validate Myanmar phone. Returns (is_valid, normalized_or_error_message).
    """
    if not phone or not str(phone).strip():
        return False, "Phone number is required."
    normalized = normalize_phone_for_db(phone, country_code)
    if len(normalized) != 11 or not normalized.startswith("959"):
        return False, "Invalid Myanmar phone. Use 09xxxxxxxx or +959xxxxxxxx."
    return True, normalized


def display_phone(normalized: str, with_plus: bool = True) -> str:
    """Convert stored 959xxxxxxxx to display format +95 9 xxx xxx xxx or 09xxxxxxxx."""
    if not normalized:
        return ""
    digits = re.sub(r"\D", "", normalized)
    if len(digits) >= 11 and digits.startswith("959"):
        local = "0" + digits[2:]  # 09xxxxxxxx
        return "+95 " + digits[2:] if with_plus else local
    return normalized
