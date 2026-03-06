# Generated migration for Hybrid Exchange Rate System

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0011_add_payment_method_and_payment_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='globalsetting',
            name='is_auto_sync',
            field=models.BooleanField(default=True, help_text='If True, use scraped CBM rate. If False, use manual_usd_rate.', verbose_name='Auto-Sync Enabled'),
        ),
        migrations.AddField(
            model_name='globalsetting',
            name='manual_usd_rate',
            field=models.DecimalField(blank=True, decimal_places=4, help_text='Manual override rate when is_auto_sync=False', max_digits=18, null=True, verbose_name='Manual USD Rate'),
        ),
    ]
