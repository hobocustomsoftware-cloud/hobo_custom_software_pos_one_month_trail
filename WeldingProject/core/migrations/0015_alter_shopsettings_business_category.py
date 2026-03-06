# Sync business_category choices with model (added pharmacy_clinic, hardware, liquor, grocery).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0014_sync_index_state"),
    ]

    operations = [
        migrations.AlterField(
            model_name="shopsettings",
            name="business_category",
            field=models.CharField(
                blank=True,
                choices=[
                    ("pharmacy", "Pharmacy / ဆေးဆိုင်"),
                    ("pharmacy_clinic", "Pharmacy + Clinic / ဆေးခန်းတွဲ ဆေးဆိုင်"),
                    ("mobile", "Mobile / ဖုန်းဆိုင်"),
                    ("electronic_solar", "Electronic / Solar / လျှပ်စစ်ဆိုင်"),
                    ("hardware", "Hardware / အိမ်ဆောက်ပစ္စည်းဆိုင်"),
                    ("liquor", "Liquor Store / အရက်ဆိုင်"),
                    ("grocery", "Grocery / ကုန်မာဆိုင်"),
                    ("general", "General Retail / အထွေထွေ"),
                ],
                default="general",
                max_length=32,
                verbose_name="Business Category",
            ),
        ),
    ]
