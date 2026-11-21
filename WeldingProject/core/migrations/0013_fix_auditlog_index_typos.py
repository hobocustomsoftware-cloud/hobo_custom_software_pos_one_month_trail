# Fix typo in index names from 0008; use names <=30 chars (Oracle/Django E034).
# Safe to run: drops old indexes only if they exist, then adds correct ones.

from django.db import migrations, models


def drop_old_audit_indexes(apps, schema_editor):
    """Drop indexes that may have typo/long names (if they exist)."""
    connection = schema_editor.connection
    # SQLite does not understand `DROP INDEX ... CASCADE` (and index names are
    # only quoted in mixin/PG), so branch on the DB vendor and use proper
    # identifier quoting. See ticket: `manage.py test` crashed on SQLite.
    is_sqlite = connection.vendor == "sqlite"
    with connection.cursor() as cursor:
        for name in [
            "core_auditl_action_0a1b0d_idx",
            "core_auditl_outlet__8c2e4f_idx",
            "core_auditlog_action_0a1b0d_idx",
            "core_auditlog_outlet__8c2e4f_idx",
        ]:
            quoted = connection.ops.quote_name(name)
            if is_sqlite:
                cursor.execute('DROP INDEX IF EXISTS "%s"' % name)
            else:
                cursor.execute("DROP INDEX IF EXISTS %s CASCADE" % quoted)


def reverse_drop(apps, schema_editor):
    """Re-add old typo indexes (for reverse migrate)."""
    # Recreate the indexes as in 0008 so reverse is possible
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS core_auditl_action_0a1b0d_idx
            ON core_auditlog (action, created_at)
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS core_auditl_outlet__8c2e4f_idx
            ON core_auditlog (outlet_id, created_at)
            """
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0012_shopsettings_filter_units_by_category"),
    ]

    operations = [
        migrations.RunPython(drop_old_audit_indexes, reverse_drop),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["action", "created_at"],
                name="core_audit_act_0a1b0d_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="auditlog",
            index=models.Index(
                fields=["outlet", "created_at"],
                name="core_audit_out_8c2e4f_idx",
            ),
        ),
    ]
