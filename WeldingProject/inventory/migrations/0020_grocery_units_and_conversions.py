# Grocery/Chili: add Mass (gram, kg), Packaging category, set 1 Viss = 100 Tical

from decimal import Decimal
from django.db import migrations


def grocery_units_and_conversions(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')

    # Ensure Mass: ပိဿာ (viss), ကျပ်သား (tical), ဂရမ် (gram), ကီလိုဂရမ် (kg)
    mass_units = [
        ('VISS', 'ပိဿာ', 'Viss', 1),
        ('TICAL', 'ကျပ်သား', 'Tical', 2),
        ('GRAM', 'ဂရမ်', 'Gram', 3),
        ('KG', 'ကီလိုဂရမ်', 'Kg', 4),
    ]
    for code, name_my, name_en, order in mass_units:
        Unit.objects.update_or_create(
            code=code,
            defaults={
                'name_my': name_my,
                'name_en': name_en,
                'category': 'mass',
                'order': order,
            },
        )

    # Packaging: တစ်အိတ် (bag), တစ်ထုပ် (pack), တစ်ဖာ (box), တစ်တွဲ (strip)
    packaging_units = [
        ('BAG', 'တစ်အိတ်', 'Bag', 1),
        ('PACK', 'တစ်ထုပ်', 'Pack', 2),
        ('BOX', 'တစ်ဖာ', 'Box', 3),
        ('STRIP', 'တစ်တွဲ', 'Strip', 4),
    ]
    for code, name_my, name_en, order in packaging_units:
        Unit.objects.update_or_create(
            code=code,
            defaults={
                'name_my': name_my,
                'name_en': name_en,
                'category': 'packaging',
                'order': order,
            },
        )

    # Conversion: 1 Viss = 100 Tical → 1 tical = 0.01 viss (stock: 50 tical = 0.5 viss reduction)
    viss = Unit.objects.get(code='VISS')
    tical = Unit.objects.get(code='TICAL')
    tical.base_unit = viss
    tical.factor_to_base = Decimal('0.01')  # 1 tical = 0.01 viss
    tical.save(update_fields=['base_unit', 'factor_to_base'])

    # Optional: 1 Kg = 1000 Gram (metric mass base = kg)
    kg = Unit.objects.get(code='KG')
    gram = Unit.objects.get(code='GRAM')
    gram.base_unit = kg
    gram.factor_to_base = Decimal('0.001')  # 1 gram = 0.001 kg
    gram.save(update_fields=['base_unit', 'factor_to_base'])


def reverse_app(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    # Clear conversion only; leave units (other migrations may have created them)
    Unit.objects.filter(code='TICAL').update(base_unit_id=None, factor_to_base=Decimal('1'))
    Unit.objects.filter(code='GRAM').update(base_unit_id=None, factor_to_base=Decimal('1'))


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0019_unit_conversion_and_packaging'),
    ]

    operations = [
        migrations.RunPython(grocery_units_and_conversions, reverse_app),
    ]
