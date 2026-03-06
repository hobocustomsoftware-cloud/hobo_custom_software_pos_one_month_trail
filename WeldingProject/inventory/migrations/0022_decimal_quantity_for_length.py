# Support decimal quantities for Length (e.g. 1.5 Feet) and other units.
# InventoryMovement.quantity and SaleItem.quantity: Integer -> Decimal(18,4).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0021_add_missing_units_length_count'),
    ]

    operations = [
        migrations.AlterField(
            model_name='inventorymovement',
            name='quantity',
            field=models.DecimalField(
                decimal_places=4,
                default=1,
                help_text='Supports decimals for length (e.g. 1.5 Feet).',
                max_digits=18,
            ),
        ),
        migrations.AlterField(
            model_name='saleitem',
            name='quantity',
            field=models.DecimalField(
                decimal_places=4,
                default=1,
                help_text='Supports decimals for length (e.g. 1.5 Feet).',
                max_digits=18,
            ),
        ),
    ]
