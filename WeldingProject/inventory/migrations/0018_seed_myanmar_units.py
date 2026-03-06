# Seed common Myanmar units (Mass, Count, Length, Volume) with Myanmar + English names

from django.db import migrations


def seed_units(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    # (code, name_my, name_en, category, order)
    units = [
        # Mass
        ('VISS', 'ပိဿာ', 'Viss', 'mass', 1),
        ('TICAL', 'ကျပ်သား', 'Tical', 'mass', 2),
        ('BAG', 'တစ်အိတ်', 'Bag', 'mass', 3),
        ('BOX', 'တစ်ဖာ', 'Box', 'mass', 4),
        # Count
        ('PCS', 'တစ်လုံး', 'Pieces (pcs)', 'count', 10),
        ('PACK', 'တစ်ထုတ်', 'Pack', 'count', 11),
        ('STRIP', 'တစ်တွဲ', 'Strip', 'count', 12),
        ('DOZEN', 'တစ်ဒါဇင်', 'Dozen', 'count', 13),
        # Length
        ('YARD', 'ကိုက်', 'Yard', 'length', 20),
        ('FEET', 'ပေ', 'Feet', 'length', 21),
        ('INCH', 'လက်မ', 'Inch', 'length', 22),
        # Volume
        ('TIN', 'တစ်ဗူး', 'Tin', 'volume', 30),
        ('GALLON', 'တစ်ဗုံး', 'Gallon', 'volume', 31),
        ('PYI', 'တစ်ပြည်', 'Pyi', 'volume', 32),
    ]
    for code, name_my, name_en, category, order in units:
        Unit.objects.get_or_create(
            code=code,
            defaults={
                'name_my': name_my,
                'name_en': name_en,
                'category': category,
                'order': order,
            },
        )


def reverse_seed(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    codes = [
        'VISS', 'TICAL', 'BAG', 'BOX',
        'PCS', 'PACK', 'STRIP', 'DOZEN',
        'YARD', 'FEET', 'INCH',
        'TIN', 'GALLON', 'PYI',
    ]
    Unit.objects.filter(code__in=codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0017_add_unit_model'),
    ]

    operations = [
        migrations.RunPython(seed_units, reverse_seed),
    ]
