"""One-way cleanup: replace any legacy plaintext temp_password with its hash.

Rows written before the hash-only change hold the usable staff password in
clear text: any DB backup leak is a credential leak. Hashing is one-way, so
after this migration the clear text is unrecoverable (by design). Accounts
whose owners still need the password must rotate it via the API.
"""
from django.contrib.auth.hashers import identify_hasher, make_password
from django.db import migrations


def hash_legacy_temp_passwords(apps, schema_editor):
    User = apps.get_model("core", "User")
    for user in User.objects.exclude(temp_password__isnull=True).exclude(temp_password=""):
        value = user.temp_password or ""
        try:
            identify_hasher(value)
            continue  # already a hasher output
        except Exception:
            pass
        user.temp_password = make_password(value)
        user.save(update_fields=["temp_password"])


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0019_alter_outlet_parent_outlet"),
    ]

    operations = [
        migrations.RunPython(hash_legacy_temp_passwords, migrations.RunPython.noop),
    ]
