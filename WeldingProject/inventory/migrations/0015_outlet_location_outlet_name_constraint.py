# Multi-Outlet: Link Location to Outlet; unique (outlet, name) when outlet is set

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_outlet_user_primary_outlet'),
        ('inventory', '0014_alter_category_options_alter_exchangeratelog_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='outlet',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='locations',
                to='core.outlet',
                verbose_name='Outlet',
            ),
        ),
        migrations.AlterField(
            model_name='location',
            name='name',
            field=models.CharField(max_length=100),
        ),
        migrations.AddConstraint(
            model_name='location',
            constraint=models.UniqueConstraint(
                condition=models.Q(outlet__isnull=False),
                fields=('outlet', 'name'),
                name='inventory_location_outlet_name_uniq',
            ),
        ),
    ]
