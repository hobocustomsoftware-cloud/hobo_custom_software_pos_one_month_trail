# ဆေးခန်း ကုသမှုမှတ်တမ်း (Clinic Treatment Record) + ဓာတ်မှန်/အယ်ထရာဆောင်း ဖိုင်

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0001_initial'),
        ('service', '0006_alter_repairservice_id_alter_repairservice_location_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TreatmentRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('patient_name', models.CharField(max_length=200, verbose_name='လူနာအမည်')),
                ('age', models.PositiveIntegerField(blank=True, null=True, verbose_name='အသက်')),
                ('condition', models.TextField(blank=True, verbose_name='အခြေအနေ / ရောဂါဖော်ပြချက်')),
                ('drug_allergies', models.TextField(blank=True, help_text='Comma-separated or one per line', verbose_name='မတည့်သောဆေးများ')),
                ('notes', models.TextField(blank=True, verbose_name='မှတ်ချက်')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('customer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='treatment_records', to='customer.customer', verbose_name='ဖောက်သည်မှတ်တမ်း (optional)')),
                ('staff', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'ကုသမှုမှတ်တမ်း',
                'verbose_name_plural': 'ကုသမှုမှတ်တမ်းများ',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TreatmentRecordFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_type', models.CharField(choices=[('xray', 'X-Ray'), ('ultrasound', 'Ultrasound'), ('other', 'Other')], default='other', max_length=20)),
                ('file', models.FileField(upload_to='treatment_files/%Y/%m/', verbose_name='ဖိုင်')),
                ('caption', models.CharField(blank=True, max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('treatment_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='files', to='service.treatmentrecord')),
            ],
            options={
                'verbose_name': 'ကုသမှုဖိုင်',
                'verbose_name_plural': 'ကုသမှုဖိုင်များ',
                'ordering': ['-created_at'],
            },
        ),
    ]
