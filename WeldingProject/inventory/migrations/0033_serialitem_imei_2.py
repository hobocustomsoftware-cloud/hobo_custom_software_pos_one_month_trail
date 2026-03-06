# ဖုန်းဆိုင် IMEI ၂ ခု (serial_number = IMEI 1, imei_2 = IMEI 2)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0032_alter_inventorymovement_quantity'),
    ]

    operations = [
        migrations.AddField(
            model_name='serialitem',
            name='imei_2',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True, verbose_name='IMEI 2 (ဖုန်းဆိုင်အတွက် ဒုတိယ IMEI)'),
        ),
    ]
