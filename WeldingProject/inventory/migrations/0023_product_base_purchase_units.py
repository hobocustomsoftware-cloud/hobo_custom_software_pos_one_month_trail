# Product: base_unit, purchase_unit, purchase_unit_factor for bulk buy / retail sell

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0022_decimal_quantity_for_length'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='base_unit',
            field=models.ForeignKey(
                blank=True,
                help_text='e.g. Viss for chili; Feet for wire. All inventory quantities are in this unit.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products_as_base',
                to='inventory.unit',
                verbose_name='Base unit (stock stored in this unit)',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='purchase_unit',
            field=models.ForeignKey(
                blank=True,
                help_text='e.g. Bag (အိတ်), Roll (ခွေ). Leave blank if same as base.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='products_bought_in',
                to='inventory.unit',
                verbose_name='Purchase unit (ဝယ်ယူသည့်ယူနစ်)',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='purchase_unit_factor',
            field=models.DecimalField(
                decimal_places=6,
                default=1,
                help_text='e.g. 1 Bag = 30 Viss → 30; 1 Roll = 90 Feet → 90.',
                max_digits=20,
                verbose_name='1 Purchase unit = X Base units',
            ),
        ),
    ]
