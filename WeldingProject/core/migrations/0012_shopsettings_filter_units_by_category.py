# Toggle: show only units for business category (on) or all units (off)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_shopsettings_loyverse_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopsettings',
            name='filter_units_by_business_category',
            field=models.BooleanField(
                default=True,
                help_text='On: only units for selected business type. Off: show all units.',
                verbose_name='ဆိုင်အမျိုးအစားအလိုက် unit ပဲပြမယ်',
            ),
        ),
    ]
