# Generated manually for Accounting & P&L Module

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('inventory', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExpenseCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='အမျိုးအစားအမည်')),
                ('description', models.TextField(blank=True, null=True, verbose_name='ဖော်ပြချက်')),
            ],
            options={
                'verbose_name': 'ကုန်ကျစရိတ် အမျိုးအစား',
                'verbose_name_plural': 'ကုန်ကျစရိတ် အမျိုးအစားများ',
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=200, verbose_name='ဖော်ပြချက်')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='ငွေပမာဏ (MMK)')),
                ('expense_date', models.DateField(default=django.utils.timezone.now, verbose_name='ကုန်ကျသည့်ရက်စွဲ')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('notes', models.TextField(blank=True, null=True, verbose_name='မှတ်ချက်')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='accounting.expensecategory', verbose_name='အမျိုးအစား')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.user', verbose_name='မှတ်တမ်းတင်သူ')),
            ],
            options={
                'verbose_name': 'ကုန်ကျစရိတ်',
                'verbose_name_plural': 'ကုန်ကျစရိတ်များ',
                'ordering': ['-expense_date', '-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('income', 'Income (ဝင်ငွေ)'), ('expense', 'Expense (ကုန်ကျစရိတ်)')], max_length=10, verbose_name='Transaction Type')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='ငွေပမာဏ')),
                ('transaction_date', models.DateField(db_index=True, default=django.utils.timezone.now, verbose_name='Transaction Date')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expense', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='transactions', to='accounting.expense', verbose_name='ကုန်ကျစရိတ်')),
                ('sale_transaction', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='accounting_transactions', to='inventory.saletransaction', verbose_name='ရောင်းချမှု')),
            ],
            options={
                'verbose_name': 'Transaction',
                'verbose_name_plural': 'Transactions',
                'ordering': ['-transaction_date', '-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_type', 'transaction_date'], name='accounting__transac_7a8b2c_idx'),
        ),
        migrations.AddIndex(
            model_name='transaction',
            index=models.Index(fields=['transaction_date'], name='accounting__transac_8d9e0f_idx'),
        ),
    ]
