# Sync migration state with DB. 0013 already dropped typo-named audit indexes and added short names.
# This removes the old index names from Django's state only (no DROP in DB).
# core_user_email_idx: remove from state so model and state match (index stays in DB for performance).

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0013_fix_auditlog_index_typos"),
    ]

    operations = [
        # AuditLog: remove old typo index names from state only (0013 already dropped them in DB)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveIndex(
                    model_name="auditlog",
                    name="core_auditl_action_0a1b0d_idx",
                ),
                migrations.RemoveIndex(
                    model_name="auditlog",
                    name="core_auditl_outlet__8c2e4f_idx",
                ),
            ],
            database_operations=[],
        ),
        # User: remove email index from state (keep in DB for fast login by email)
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveIndex(
                    model_name="user",
                    name="core_user_email_idx",
                ),
            ],
            database_operations=[],
        ),
    ]
