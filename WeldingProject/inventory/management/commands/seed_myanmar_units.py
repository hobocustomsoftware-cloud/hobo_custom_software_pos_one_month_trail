"""
Seed common Myanmar units (Grocery/Chili + general) with Myanmar and English names.
Supports conversion: e.g. 1 Viss = 100 Tical → 50 tical sold = 0.5 viss stock reduction.
Run: python manage.py seed_myanmar_units
Idempotent: uses get_or_create/update_or_create by code; safe to run after migration or anytime.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from inventory.models import Unit


# (code, name_my, name_en, category, order) — base units have no base_unit / factor_to_base=1
SEED_UNITS = [
    # Mass (Grocery/Chili)
    ('VISS', 'ပိဿာ', 'Viss', 'mass', 1),
    ('TICAL', 'ကျပ်သား', 'Tical', 'mass', 2),
    ('GRAM', 'ဂရမ်', 'Gram', 'mass', 3),
    ('KG', 'ကီလိုဂရမ်', 'Kg', 'mass', 4),
    # Packaging (Grocery/Chili)
    ('BAG', 'တစ်အိတ်', 'Bag', 'packaging', 10),
    ('PACK', 'တစ်ထုပ်', 'Pack', 'packaging', 11),
    ('BOX', 'တစ်ဖာ', 'Box', 'packaging', 12),
    ('STRIP', 'တစ်တွဲ', 'Strip', 'packaging', 13),
    # Count
    ('PCS', 'တစ်လုံး', 'Pieces (pcs)', 'count', 20),
    ('DOZEN', 'တစ်ဒါဇင်', 'Dozen', 'count', 21),
    # Length
    ('YARD', 'ကိုက်', 'Yard', 'length', 30),
    ('FEET', 'ပေ', 'Feet', 'length', 31),
    ('INCH', 'လက်မ', 'Inch', 'length', 32),
    # Volume
    ('TIN', 'တစ်ဗူး', 'Tin', 'volume', 40),
    ('GALLON', 'တစ်ဗုံး', 'Gallon', 'volume', 41),
    ('PYI', 'တစ်ပြည်', 'Pyi', 'volume', 42),
]

# Conversions: (unit_code, base_unit_code, factor_to_base) — 1 unit = factor_to_base × base_unit
CONVERSIONS = [
    ('TICAL', 'VISS', Decimal('0.01')),   # 1 Viss = 100 Tical → 1 tical = 0.01 viss
    ('GRAM', 'KG', Decimal('0.001')),    # 1 Kg = 1000 Gram → 1 gram = 0.001 kg
]


class Command(BaseCommand):
    help = 'Seed Myanmar units (Mass, Packaging, Count, Length, Volume) and set conversions (e.g. 1 Viss = 100 Tical)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print what would be created/updated without writing to DB',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write('Dry run: would seed units and set conversions')
        created = 0
        updated = 0

        for code, name_my, name_en, category, order in SEED_UNITS:
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

        for unit_code, base_code, factor in CONVERSIONS:
            if dry_run:
                self.stdout.write(f"  Conversion: 1 {unit_code} = {factor} {base_code}")
                continue
            try:
                unit = Unit.objects.get(code=unit_code)
                base_unit = Unit.objects.get(code=base_code)
                unit.base_unit = base_unit
                unit.factor_to_base = factor
                unit.save(update_fields=['base_unit', 'factor_to_base'])
                self.stdout.write(self.style.SUCCESS(f"Conversion: 1 {unit_code} = {factor} {base_code}"))
            except Unit.DoesNotExist as e:
                self.stdout.write(self.style.WARNING(f"Skip conversion {unit_code}→{base_code}: {e}"))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f"Done. Created {created} new units, updated {updated} existing; conversions applied."
            ))
