"""
အခြေခံယူနစ်များ ထည့်သွင်းခြင်း။ လုံး, ကဒ်, ပုလင်း, လက်မ, ပေ, ကိုက်, ပိဿာ, ကျပ်သား, ပုံး, တန်, ကျင်း, ဒါဇင်, ထုတ်, အိတ်, ဆွဲ, ဖာ, ခု, လိပ်, ဗူး စသည့် ယူနစ်အားလုံး။
Run: python manage.py seed_base_units
Idempotent: update_or_create by code.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from inventory.models import Unit


# (code, name_my, name_en, category, order)
# Unit.UNIT_CATEGORY_CHOICES: mass, packaging, count, length, volume
BASE_UNITS = [
    # Count
    ('PCS', 'တစ်လုံး', 'Pieces', 'count', 1),
    ('ITEM', 'ခု', 'Item (တစ်ခု၊ နှစ်ခု)', 'count', 2),
    ('DOZEN', 'ဒါဇင်', 'Dozen', 'count', 3),
    ('CARD', 'ကဒ်', 'Card', 'count', 4),
    # Length
    ('INCH', 'လက်မ', 'Inch', 'length', 10),
    ('FEET', 'ပေ', 'Feet', 'length', 11),
    ('YARD', 'ကိုက်', 'Yard', 'length', 12),
    ('MTR', 'မီတာ', 'Meter', 'length', 13),
    # Mass
    ('TICAL', 'ကျပ်သား', 'Tical', 'mass', 20),
    ('VISS', 'ပိဿာ', 'Viss', 'mass', 21),
    ('GRAM', 'ဂရမ်', 'Gram', 'mass', 22),
    ('KG', 'ကီလိုဂရမ်', 'Kg', 'mass', 23),
    ('TON', 'တန်', 'Ton', 'mass', 24),
    # Packaging
    ('PACK', 'ထုတ်', 'Pack (တစ်ထုတ်)', 'packaging', 30),
    ('BAG', 'အိတ်', 'Bag (တစ်အိတ်)', 'packaging', 31),
    ('SWE', 'ဆွဲ', 'Bundle (တစ်ဆွဲ)', 'packaging', 32),
    ('CARTON', 'ဖာ', 'Carton (တစ်ဖာ)', 'packaging', 33),
    ('BOX', 'ဖာ/ဘူး', 'Box', 'packaging', 34),
    ('BUCKET', 'ပုံး', 'Bucket (တစ်ပုံး)', 'packaging', 35),
    ('STRIP', 'တစ်ကတ်', 'Strip', 'packaging', 36),
    ('ROLL', 'လိပ်', 'Roll (တစ်လိပ်၊ နှစ်လိပ်)', 'packaging', 37),
    ('JINE', 'ကျင်း', 'Jine (basket)', 'packaging', 38),
    # Volume
    ('BOTTLE', 'ပုလင်း', 'Bottle (တစ်ပုလင်း)', 'volume', 40),
    ('TIN', 'ဗူး', 'Tin/Bottle (တစ်ဗူး၊ နှစ်ဗူး)', 'volume', 41),
    ('GALLON', 'ဗုံး', 'Gallon', 'volume', 42),
    ('PYI', 'ပြည်', 'Pyi', 'volume', 43),
]


class Command(BaseCommand):
    help = 'Seed all base units (လုံး, ကဒ်, ပုလင်း, လက်မ, ပေ, ကိုက်, ပိဿာ, ကျပ်သား, ပုံး, တန်, ကျင်း, ဒါဇင်, ထုတ်, အိတ်, ဆွဲ, ဖာ, ခု, လိပ်, ဗူး)'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Print only, do not write DB')

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        created = 0
        updated = 0
        for code, name_my, name_en, category, order in BASE_UNITS:
            if dry_run:
                self.stdout.write(f"  {code}: {name_my} / {name_en} ({category})")
                continue
            obj, was_created = Unit.objects.update_or_create(
                code=code,
                defaults={
                    'name_my': name_my,
                    'name_en': name_en,
                    'category': category,
                    'order': order,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"Created: {obj}"))
            else:
                updated += 1
        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"Done. Created {created}, updated {updated} units."
            ))
