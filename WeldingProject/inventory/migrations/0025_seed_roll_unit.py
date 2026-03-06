# Add Unit ROLL (ခွေ) for buying in rolls, selling in feet

from django.db import migrations


def seed_roll(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    Unit.objects.get_or_create(
        code='ROLL',
        defaults={
            'name_my': 'ခွေ',
            'name_en': 'Roll',
            'category': 'packaging',
            'order': 5,
        },
    )


def reverse_roll(apps, schema_editor):
    Unit = apps.get_model('inventory', 'Unit')
    Unit.objects.filter(code='ROLL').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0024_purchase_purchaseline'),
    ]

    operations = [
        migrations.RunPython(seed_roll, reverse_roll),
    ]
