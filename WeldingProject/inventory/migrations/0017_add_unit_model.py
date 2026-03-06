# Unit model for common Myanmar/English units (mass, count, length, volume)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0016_saletransaction_sale_inventorymovement_outlet'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_my', models.CharField(max_length=80, verbose_name='Myanmar name (မြန်မာအမည်)')),
                ('name_en', models.CharField(max_length=80, verbose_name='English name')),
                ('code', models.CharField(db_index=True, max_length=20, unique=True, verbose_name='Short code (e.g. VISS, PCS)')),
                ('category', models.CharField(choices=[('mass', 'Mass'), ('count', 'Count'), ('length', 'Length'), ('volume', 'Volume')], db_index=True, max_length=20)),
                ('order', models.PositiveIntegerField(default=0, verbose_name='Display order')),
            ],
            options={
                'verbose_name': 'ယူနစ် (Unit)',
                'verbose_name_plural': 'ယူနစ်များ (Units)',
                'ordering': ['category', 'order', 'name_en'],
            },
        ),
    ]
