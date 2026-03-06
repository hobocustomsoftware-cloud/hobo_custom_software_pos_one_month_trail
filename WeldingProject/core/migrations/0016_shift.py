# Shift model for work shifts (CRUD).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_alter_shopsettings_business_category"),
    ]

    operations = [
        migrations.CreateModel(
            name="Shift",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="Shift Name")),
                ("start_time", models.TimeField(verbose_name="စတင်ချိန်")),
                ("end_time", models.TimeField(verbose_name="ပြီးဆုံးချိန်")),
                ("is_active", models.BooleanField(default=True, verbose_name="အသုံးပြုမည်")),
            ],
            options={
                "ordering": ["start_time"],
                "verbose_name": "Shift",
                "verbose_name_plural": "Shifts",
            },
        ),
    ]
