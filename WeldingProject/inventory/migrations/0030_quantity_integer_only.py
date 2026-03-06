# Product/item quantities: integer only (no decimals). Myanmar locale convention.

from django.db import migrations, models


def alter_quantity_to_integer(apps, schema_editor):
    """PostgreSQL: convert decimal quantity columns to integer with ROUND."""
    if schema_editor.connection.vendor != 'postgresql':
        return
    schema_editor.execute(
        "ALTER TABLE inventory_inventorymovement "
        "ALTER COLUMN quantity TYPE integer USING ROUND(quantity)::integer;"
    )
    schema_editor.execute(
        "ALTER TABLE inventory_purchaseline "
        "ALTER COLUMN quantity TYPE integer USING ROUND(quantity)::integer;"
    )
    schema_editor.execute(
        "ALTER TABLE inventory_saleitem "
        "ALTER COLUMN quantity TYPE integer USING ROUND(quantity)::integer;"
    )


def noop_reverse(apps, schema_editor):
    """Reverse: back to decimal. Optional; not used if you never need to revert."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0029_add_product_expiry_date'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(alter_quantity_to_integer, noop_reverse),
            ],
            state_operations=[
                migrations.AlterField(
                    model_name='inventorymovement',
                    name='quantity',
                    field=models.PositiveIntegerField(default=1, verbose_name='အရေအတွက်'),
                ),
                migrations.AlterField(
                    model_name='purchaseline',
                    name='quantity',
                    field=models.PositiveIntegerField(default=1, verbose_name='အရေအတွက် (ယူနစ်အလိုက်)'),
                ),
                migrations.AlterField(
                    model_name='saleitem',
                    name='quantity',
                    field=models.PositiveIntegerField(default=1, verbose_name='အရေအတွက်'),
                ),
            ],
        ),
    ]
