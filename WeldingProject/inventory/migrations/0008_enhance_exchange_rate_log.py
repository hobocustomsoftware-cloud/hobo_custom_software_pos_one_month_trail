# Migration to enhance ExchangeRateLog for multiple currencies and add manual adjustment fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_add_exchange_rate_log'),
        ('inventory', '0007_refactor_category_product_specs'),
    ]

    operations = [
        # Update ExchangeRateLog to support multiple currencies
        migrations.AddField(
            model_name='exchangeratelog',
            name='currency',
            field=models.CharField(
                choices=[('USD', 'US Dollar'), ('THB', 'Thai Baht'), ('SGD', 'Singapore Dollar')],
                default='USD',
                max_length=3
            ),
        ),
        migrations.AddField(
            model_name='exchangeratelog',
            name='source',
            field=models.CharField(default='CBM', max_length=50, verbose_name='Source (CBM/Manual)'),
        ),
        # Remove unique constraint on date, add unique_together
        migrations.AlterUniqueTogether(
            name='exchangeratelog',
            unique_together={('date', 'currency')},
        ),
        # Add manual adjustment fields to GlobalSetting
        migrations.AddField(
            model_name='globalsetting',
            name='market_premium_percentage',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text='Percentage to add to CBM rate (e.g., 10 = +10%)',
                max_digits=6,
                null=True,
                verbose_name='Market Premium % (e.g., +10 for 10% markup)'
            ),
        ),
        migrations.AddField(
            model_name='globalsetting',
            name='manual_fixed_rate',
            field=models.DecimalField(
                blank=True,
                decimal_places=4,
                help_text='If set, this rate will be used instead of CBM rate',
                max_digits=18,
                null=True,
                verbose_name='Manual Fixed Rate (overrides CBM rate)'
            ),
        ),
    ]
