# Add Unit CARD (ကဒ်) for product base/purchase unit options

from decimal import Decimal

from django.db import migrations


def seed_card(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    Unit.objects.get_or_create(
        code='CARD',
        defaults={
            'name_my': 'ကဒ်',
            'name_en': 'Card',
            'category': 'packaging',
            'order': 3,
            'factor_to_base': Decimal('1'),
        },
    )


def reverse_card(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    Unit.objects.filter(code='CARD').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0025_seed_roll_unit'),
    ]

    operations = [
        migrations.RunPython(seed_card, reverse_card),
    ]
