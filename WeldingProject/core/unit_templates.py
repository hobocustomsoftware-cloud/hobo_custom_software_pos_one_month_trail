"""
Loyverse-style unit templates: seed default units when a user registers by business category.
- Pharmacy: တစ်လုံး (Tablet), တစ်ကတ် (Strip), တစ်ဗူး (Bottle), တစ်ဖာ (Box).
- Electronic/Solar: ပေ (Feet), လက်မ (Inch), တစ်ချောင်း (Pcs), တစ်ခွေ (Roll).
"""
from decimal import Decimal


# (code, name_my, name_en, category, order)
PHARMACY_UNITS = [
    ('TABLET', 'တစ်လုံး', 'Tablet', 'count', 1),
    ('STRIP', 'တစ်ကတ်', 'Strip', 'packaging', 2),
    ('CARD', 'ကဒ်', 'Card', 'packaging', 3),
    ('BOTTLE', 'တစ်ဗူး', 'Bottle', 'volume', 4),
    ('BOX', 'တစ်ဖာ', 'Box', 'packaging', 5),
]

ELECTRONIC_SOLAR_UNITS = [
    ('FEET', 'ပေ', 'Feet', 'length', 1),
    ('INCH', 'လက်မ', 'Inch', 'length', 2),
    ('PCS', 'တစ်ချောင်း', 'Pcs', 'count', 3),
    ('CARD', 'ကဒ်', 'Card', 'packaging', 4),
    ('ROLL', 'တစ်ခွေ', 'Roll', 'packaging', 5),
]

# General/Mobile: minimal count + packaging so product form has something
GENERAL_UNITS = [
    ('PCS', 'တစ်ခု', 'Pcs', 'count', 1),
    ('CARD', 'ကဒ်', 'Card', 'packaging', 2),
    ('BOX', 'ဘူး/ဖာ', 'Box', 'packaging', 3),
]

# Hardware / building materials (အိမ်ဆောက်ပစ္စည်း): ပေ, မီတာ, ဒါဇင်, ဖာ
HARDWARE_UNITS = [
    ('PCS', 'တစ်ချောင်း/ခု', 'Pcs', 'count', 1),
    ('FEET', 'ပေ', 'Feet', 'length', 2),
    ('MTR', 'မီတာ', 'Meter', 'length', 3),
    ('DOZEN', 'ဒါဇင်', 'Dozen', 'count', 4),
    ('BOX', 'ဖာ/ဘူး', 'Box', 'packaging', 5),
    ('ROL', 'ခွေ', 'Roll', 'packaging', 6),
]

# Liquor store: ပုလင်း, ခွက်, ဒါဇင်, ဘူး
LIQUOR_UNITS = [
    ('PCS', 'ခွက်/ပုလင်း', 'Pcs', 'count', 1),
    ('BOTTLE', 'ပုလင်း', 'Bottle', 'volume', 2),
    ('CASE', 'ဘူးစင်', 'Case', 'packaging', 3),
    ('BOX', 'ဘူး/ဖာ', 'Box', 'packaging', 4),
    ('DOZEN', 'ဒါဇင်', 'Dozen', 'count', 5),
]

# Grocery / ကုန်မာဆိုင်: ပြည်, ပိဿာ, ပုလင်း, အိတ်
GROCERY_UNITS = [
    ('PCS', 'ခု', 'Pcs', 'count', 1),
    ('KG', 'ကီလို', 'Kg', 'mass', 2),
    ('VISS', 'ပိဿာ', 'Viss', 'mass', 3),
    ('BAG', 'အိတ်', 'Bag', 'packaging', 4),
    ('BOTTLE', 'ပုလင်း', 'Bottle', 'volume', 5),
    ('BOX', 'ဘူး/ဖာ', 'Box', 'packaging', 6),
]


def get_unit_codes_for_business_category(category):
    """Return list of unit codes for the given business category (for filtering unit list)."""
    if category in ('pharmacy', 'pharmacy_clinic'):
        return [c[0] for c in PHARMACY_UNITS]
    if category in ('electronic_solar', 'electronic', 'solar'):
        return [c[0] for c in ELECTRONIC_SOLAR_UNITS]
    if category in ('hardware', 'hardware_store'):
        return [c[0] for c in HARDWARE_UNITS]
    if category in ('mobile', 'computer'):
        return [c[0] for c in GENERAL_UNITS]
    return [c[0] for c in GENERAL_UNITS]


def seed_units_for_business_category(category):
    """
    Create Unit records for the given business_category if they don't exist.
    category: 'pharmacy' | 'pharmacy_clinic' | 'electronic_solar' | 'mobile' | 'hardware' | 'general'
    Returns number of units created.
    """
    from inventory.models import Unit

    if category in ('pharmacy', 'pharmacy_clinic'):
        templates = PHARMACY_UNITS
    elif category in ('electronic_solar', 'electronic', 'solar'):
        templates = ELECTRONIC_SOLAR_UNITS
    elif category in ('hardware', 'hardware_store'):
        templates = HARDWARE_UNITS
    elif category in ('mobile', 'computer'):
        templates = GENERAL_UNITS
    elif category in ('liquor', 'liquor_store'):
        templates = LIQUOR_UNITS
    elif category in ('grocery', 'grocery_store'):
        templates = GROCERY_UNITS
    else:
        templates = GENERAL_UNITS

    created = 0
    for code, name_my, name_en, unit_category, order in templates:
        _, was_created = Unit.objects.get_or_create(
            code=code,
            defaults={
                'name_my': name_my,
                'name_en': name_en,
                'category': unit_category,
                'order': order,
                'factor_to_base': Decimal('1'),
            },
        )
        if was_created:
            created += 1
    return created
