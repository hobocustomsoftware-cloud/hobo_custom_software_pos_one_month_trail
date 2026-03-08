# Pseudo-isolation: add shop FK to Category and Product for request.user.shop filtering

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_add_user_outlet_shop_fk'),
        ('inventory', '0033_serialitem_imei_2'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='shop',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='inventory_categories',
                to='core.shopsettings',
                verbose_name='Shop (tenant)',
            ),
        ),
        migrations.AddField(
            model_name='product',
            name='shop',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='inventory_products',
                to='core.shopsettings',
                verbose_name='Shop (tenant)',
            ),
        ),
    ]
