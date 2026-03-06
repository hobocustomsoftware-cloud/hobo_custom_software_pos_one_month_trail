# Multi-Outlet: scope Expense to Outlet

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_outlet_user_primary_outlet'),
        ('accounting', '0002_rename_accounting__transac_7a8b2c_idx_accounting__transac_01ce29_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='expense',
            name='outlet',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='expenses',
                to='core.outlet',
                verbose_name='Outlet',
            ),
        ),
    ]
