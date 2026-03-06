# Match model: InventoryMovement.quantity has help_text (state only; DB unchanged).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0030_quantity_integer_only"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventorymovement",
            name="quantity",
            field=models.PositiveIntegerField(
                default=1,
                help_text="အရေအတွက် (ပြည်ပြည်သူသုံး integer ပဲ)",
                verbose_name="အရေအတွက်",
            ),
        ),
    ]
