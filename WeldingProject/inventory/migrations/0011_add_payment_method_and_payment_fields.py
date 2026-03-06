# Generated manually for Payment Method feature

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0010_add_exchange_rate_log'),
    ]

    operations = [
        # Create PaymentMethod model
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='အမည်')),
                ('qr_code_image', models.ImageField(blank=True, null=True, upload_to='payment_qr/', verbose_name='QR Code ပုံ')),
                ('account_name', models.CharField(blank=True, max_length=200, verbose_name='အကောင့်အမည်')),
                ('account_number', models.CharField(blank=True, max_length=100, verbose_name='အကောင့်နံပါတ်/ဖုန်းနံပါတ်')),
                ('is_active', models.BooleanField(default=True, verbose_name='အသုံးပြုနိုင်သည်')),
                ('display_order', models.IntegerField(default=0, verbose_name='ပြသရန် အစဉ်')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'ငွေပေးချေမှု နည်းလမ်း',
                'verbose_name_plural': 'ငွေပေးချေမှု နည်းလမ်းများ',
                'ordering': ['display_order', 'name'],
            },
        ),
        
        # Add payment fields to SaleTransaction
        migrations.AddField(
            model_name='saletransaction',
            name='payment_method',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to='inventory.paymentmethod',
                verbose_name='ငွေပေးချေမှု နည်းလမ်း'
            ),
        ),
        migrations.AddField(
            model_name='saletransaction',
            name='payment_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending Payment (ငွေပေးချေရန် စောင့်ဆိုင်းဆဲ)'),
                    ('paid', 'Paid (ငွေပေးချေပြီး)'),
                    ('failed', 'Payment Failed (ငွေပေးချေမှု မအောင်မြင်)'),
                    ('cash', 'Cash Payment (လက်ငင်း)'),
                ],
                default='pending',
                max_length=20,
                verbose_name='ငွေပေးချေမှု အခြေအနေ'
            ),
        ),
        migrations.AddField(
            model_name='saletransaction',
            name='payment_proof_screenshot',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='payment_proofs/',
                verbose_name='ငွေပေးချေမှု အတည်ပြုပုံ'
            ),
        ),
        migrations.AddField(
            model_name='saletransaction',
            name='payment_proof_uploaded_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
