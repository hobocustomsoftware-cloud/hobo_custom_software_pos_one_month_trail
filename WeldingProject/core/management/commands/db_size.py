"""
Database size monitoring (Task E - A to K recommendation).
Run: python manage.py db_size
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Print database size and table row counts (SRE / Task E)."

    def handle(self, *args, **options):
        vendor = connection.vendor
        with connection.cursor() as c:
            if vendor == 'postgresql':
                c.execute("SELECT pg_database_size(current_database())")
                size_bytes = c.fetchone()[0]
                self.stdout.write(f"Database size: {size_bytes / (1024*1024):.2f} MB")
                c.execute("""
                    SELECT relname, n_live_tup FROM pg_stat_user_tables
                    ORDER BY n_live_tup DESC LIMIT 20
                """)
                for name, rows in c.fetchall():
                    self.stdout.write(f"  {name}: {rows} rows")
            elif vendor == 'sqlite':
                c.execute("SELECT (SELECT page_count FROM pragma_page_count()) * (SELECT page_size FROM pragma_page_size())")
                size_bytes = c.fetchone()[0] or 0
                self.stdout.write(f"Database size: {size_bytes / (1024*1024):.2f} MB")
                c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                for (name,) in c.fetchall():
                    quoted = connection.ops.quote_name(name)
                    c.execute(f"SELECT COUNT(*) FROM {quoted}")
                    self.stdout.write(f"  {name}: {c.fetchone()[0]} rows")
            else:
                self.stdout.write(self.style.WARNING(f"Unknown vendor: {vendor}"))
