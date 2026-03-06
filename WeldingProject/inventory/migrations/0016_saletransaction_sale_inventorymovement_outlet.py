# Add outlet FK to SaleTransaction, Sale, InventoryMovement for audit and isolation

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_outlet_user_primary_outlet'),
        ('inventory', '0015_outlet_location_outlet_name_constraint'),
    ]

    operations = [
        migrations.AddField(
            model_name='saletransaction',
            name='outlet',
            field=models.ForeignKey(
                blank=True,
                help_text='Outlet where sale occurred (audit + isolation).',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sale_transactions',
                to='core.outlet',
            ),
        ),
        migrations.AddField(
            model_name='sale',
            name='outlet',
            field=models.ForeignKey(
                blank=True,
                help_text='Outlet where sale occurred.',
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='sales',
                to='core.outlet',
            ),
        ),
        migrations.AddField(
            model_name='inventorymovement',
            name='outlet',
            field=models.ForeignKey(
                blank=True,
                help_text='Outlet context (from to_location or from_location).',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='inventory_movements',
                to='core.outlet',
            ),
        ),
    ]
