# Add missing units: Length (မီတာ Meter, တစ်ချောင် Custom/Inches)
# Ensures requested list: Length ပေ/လက်မ/ကိုက်/မီတာ/တစ်ချောင်; Mass and Count already present from 0018/0020.

from django.db import migrations


def add_missing_units(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    # Length: add Meter, တစ်ချောင် (Custom/Inches) — ပေ/လက်မ/ကိုက် already in 0018
    new_units = [
        ('METER', 'မီတာ', 'Meter', 'length', 23),
        ('CUSTOM_INCH', 'တစ်ချောင်', 'Custom/Inches', 'length', 24),
    ]
    for code, name_my, name_en, category, order in new_units:
        Unit.objects.get_or_create(
            code=code,
            defaults={
                'name_my': name_my,
                'name_en': name_en,
                'category': category,
                'order': order,
            },
        )


def reverse_add(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    Unit.objects.filter(code__in=['METER', 'CUSTOM_INCH']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0020_grocery_units_and_conversions'),
    ]

    operations = [
        migrations.RunPython(add_missing_units, reverse_add),
    ]
