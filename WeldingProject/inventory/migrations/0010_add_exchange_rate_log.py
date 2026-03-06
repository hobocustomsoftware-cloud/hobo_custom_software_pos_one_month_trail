# Smart Business Insight: USD rate history for trend analysis

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0009_add_configurator_pricing_usd_tags'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExchangeRateLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(unique=True)),
                ('rate', models.DecimalField(decimal_places=4, max_digits=18)),
            ],
            options={
                'ordering': ['-date'],
                'verbose_name': 'USD rate log',
                'verbose_name_plural': 'USD rate logs',
            },
        ),
    ]
