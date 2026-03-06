# Generated manually for pharmacy expiry

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0028_add_modifier_group_option'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='expiry_date',
            field=models.DateField(blank=True, null=True, verbose_name='သက်တမ်းကုန်ရက် (ဆေး)'),
        ),
    ]
