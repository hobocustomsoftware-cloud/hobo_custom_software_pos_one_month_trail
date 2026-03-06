# Purchase module: bulk buy with purchase unit → stock in base unit

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_outlet_user_primary_outlet'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('inventory', '0023_product_base_purchase_units'),
    ]

    operations = [
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reference', models.CharField(blank=True, max_length=80, verbose_name='အမှတ်အသား/ဖောင်နံပါတ်')),
                ('purchase_date', models.DateField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='purchases_created', to=settings.AUTH_USER_MODEL)),
                ('outlet', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='purchases', to='core.outlet', verbose_name='ဆိုင်ခွဲ')),
            ],
            options={
                'verbose_name': 'ဝယ်ယူမှု',
                'verbose_name_plural': 'ဝယ်ယူမှုများ',
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='PurchaseLine',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=4, default=1, max_digits=18, verbose_name='အရေအတွက် (ယူနစ်အလိုက်)')),
                ('unit_cost', models.DecimalField(decimal_places=2, default=0, max_digits=14, verbose_name='ယူနစ်ဈေး (MMK)')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='inventory.product')),
                ('purchase', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='inventory.purchase')),
                ('purchase_unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='purchase_lines', to='inventory.unit', verbose_name='ဝယ်ယူသည့်ယူနစ်')),
                ('to_location', models.ForeignKey(blank=True, help_text='Stock received to this location', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='purchase_lines', to='inventory.location')),
            ],
            options={
                'verbose_name': 'ဝယ်ယူမှု လိုင်း',
                'verbose_name_plural': 'ဝယ်ယူမှု လိုင်းများ',
            },
        ),
    ]
