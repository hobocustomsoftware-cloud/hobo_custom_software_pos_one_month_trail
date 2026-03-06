# Add conversion fields to Unit (base_unit, factor_to_base) and support packaging category

from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0018_seed_myanmar_units'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='base_unit',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='converted_units',
                to='inventory.unit',
                verbose_name='Base unit for conversion',
            ),
        ),
        migrations.AddField(
            model_name='unit',
            name='factor_to_base',
            field=models.DecimalField(
                decimal_places=10,
                default=Decimal('1'),
                help_text='How many base units per 1 of this unit. E.g. 1 tical = 0.01 viss.',
                max_digits=20,
                verbose_name='Factor to base unit',
            ),
        ),
        migrations.AlterField(
            model_name='unit',
            name='category',
            field=models.CharField(
                choices=[
                    ('mass', 'Mass'),
                    ('packaging', 'Packaging'),
                    ('count', 'Count'),
                    ('length', 'Length'),
                    ('volume', 'Volume'),
                ],
                db_index=True,
                max_length=20,
            ),
        ),
    ]
