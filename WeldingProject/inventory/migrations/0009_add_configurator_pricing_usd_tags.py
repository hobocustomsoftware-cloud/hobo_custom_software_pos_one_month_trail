# Generated manually for configurator, pricing, USD, tags

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0008_add_site_and_location_site_fk'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProductTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=80, unique=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='GlobalSetting',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=100, unique=True)),
                ('value', models.CharField(blank=True, max_length=500)),
                ('value_decimal', models.DecimalField(blank=True, decimal_places=6, max_digits=18, null=True)),
            ],
            options={
                'ordering': ['key'],
            },
        ),
        migrations.AddField(
            model_name='product',
            name='cost_usd',
            field=models.DecimalField(blank=True, decimal_places=4, max_digits=12, null=True, verbose_name='Cost (USD)'),
        ),
        migrations.AddField(
            model_name='product',
            name='markup_percentage',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=6, verbose_name='Markup %'),
        ),
        migrations.AddField(
            model_name='product',
            name='price_type',
            field=models.CharField(
                choices=[('FIXED_MMK', 'Fixed MMK'), ('DYNAMIC_USD', 'Dynamic (USD + rate)')],
                default='FIXED_MMK',
                max_length=20,
                verbose_name='Price type',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='selling_price_mmk',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                verbose_name='Selling price (MMK) – set manually or synced from USD',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='products', to='inventory.producttag', verbose_name='Compatibility tags'),
        ),
        migrations.AddField(
            model_name='bundle',
            name='bundle_type',
            field=models.CharField(
                choices=[
                    ('PC', 'PC Building'),
                    ('Solar', 'Solar Set'),
                    ('Machine', 'Machinery Package'),
                    ('Fixed', 'Fixed Bundle'),
                ],
                default='Fixed',
                max_length=20,
                verbose_name='Bundle type (PC / Solar / Machine / Fixed)',
            ),
        ),
        migrations.AddField(
            model_name='bundle',
            name='pricing_type',
            field=models.CharField(
                choices=[
                    ('FIXED_BUNDLE', 'Fixed Bundle – total price constant'),
                    ('CUSTOM_SET', 'Custom Set – sum(item_price × qty)'),
                ],
                default='CUSTOM_SET',
                max_length=20,
                verbose_name='Pricing: fixed total vs custom sum',
            ),
        ),
        migrations.AddField(
            model_name='bundle',
            name='discount_type',
            field=models.CharField(
                blank=True,
                choices=[('PERCENTAGE', 'Percentage'), ('FIXED_AMOUNT', 'Fixed amount')],
                max_length=20,
                null=True,
                verbose_name='Global bundle discount type',
            ),
        ),
        migrations.AddField(
            model_name='bundle',
            name='discount_value',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=12,
                null=True,
                default=0,
                verbose_name='Discount (percent or fixed MMK)',
            ),
        ),
        migrations.CreateModel(
            name='BundleComponent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('min_qty', models.PositiveIntegerField(default=0, verbose_name='Min quantity')),
                ('max_qty', models.PositiveIntegerField(default=1, verbose_name='Max quantity')),
                ('default_qty', models.PositiveIntegerField(default=1, verbose_name='Default quantity')),
                ('is_required', models.BooleanField(default=False, verbose_name='Required (e.g. CPU)')),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('bundle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='components', to='inventory.bundle')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bundle_components', to='inventory.product')),
            ],
            options={
                'ordering': ['bundle', 'sort_order', 'id'],
                'unique_together': {('bundle', 'product')},
            },
        ),
    ]
