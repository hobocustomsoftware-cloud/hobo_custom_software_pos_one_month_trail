# Shared demo server: User.shop and Outlet.shop FK to ShopSettings for tenant isolation

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_outlet_parent_outlet'),
    ]

    operations = [
        migrations.AddField(
            model_name='outlet',
            name='shop',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='outlets',
                to='core.shopsettings',
                verbose_name='Shop (tenant)',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='shop',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='users',
                to='core.shopsettings',
                verbose_name='Shop (tenant)',
            ),
        ),
    ]
