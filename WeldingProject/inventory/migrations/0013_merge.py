# Merge migration for conflicting branches

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_add_hybrid_exchange_rate_fields'),
        ('inventory', '0008_enhance_exchange_rate_log'),
    ]

    operations = [
    ]
