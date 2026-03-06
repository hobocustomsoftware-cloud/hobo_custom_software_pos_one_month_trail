# Loyverse-style registration: business_category, currency, setup_wizard_done

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_unified_login_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopsettings',
            name='business_category',
            field=models.CharField(
                blank=True,
                choices=[
                    ('pharmacy', 'Pharmacy / ဆေးဆိုင်'),
                    ('mobile', 'Mobile / ဖုန်းဆိုင်'),
                    ('electronic_solar', 'Electronic / Solar / လျှပ်စစ်ဆိုင်'),
                    ('general', 'General Retail / အထွေထွေ'),
                ],
                default='general',
                max_length=32,
                verbose_name='Business Category',
            ),
        ),
        migrations.AddField(
            model_name='shopsettings',
            name='currency',
            field=models.CharField(
                blank=True,
                choices=[
                    ('MMK', 'ကျပ် (MMK)'),
                    ('USD', 'US Dollar (USD)'),
                    ('THB', 'ဘတ် (THB)'),
                ],
                default='MMK',
                max_length=8,
                verbose_name='Currency',
            ),
        ),
        migrations.AddField(
            model_name='shopsettings',
            name='setup_wizard_done',
            field=models.BooleanField(
                default=False,
                help_text='True after first-time setup wizard completed (Loyverse-style).',
            ),
        ),
    ]
