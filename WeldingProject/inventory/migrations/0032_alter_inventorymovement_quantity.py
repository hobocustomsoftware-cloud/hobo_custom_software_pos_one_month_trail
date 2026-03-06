# Match model: quantity has help_text only (no verbose_name).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0031_inventorymovement_quantity_help_text"),
    ]

    operations = [
        migrations.AlterField(
            model_name="inventorymovement",
            name="quantity",
            field=models.PositiveIntegerField(
                default=1,
                help_text="အရေအတွက် (ပြည်ပြည်သူသုံး integer ပဲ)",
            ),
        ),
    ]
