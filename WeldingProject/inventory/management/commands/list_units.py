"""
List all Units in the database as a table: Unit Name (MM), Unit Name (EN), Category.
Usage: python manage.py list_units
"""
from django.core.management.base import BaseCommand

from inventory.models import Unit


class Command(BaseCommand):
    help = "List all units: Name (MM), Name (EN), Category"

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv',
            action='store_true',
            help='Output as CSV',
        )

    def handle(self, *args, **options):
        units = Unit.objects.all().order_by('category', 'order', 'name_en')
        if not units.exists():
            self.stdout.write("No units in database. Run migrations that seed units.")
            return

        if options.get('csv'):
            self.stdout.write("code,name_my,name_en,category,order")
            for u in units:
                self.stdout.write(f"{u.code},{u.name_my},{u.name_en},{u.category},{u.order}")
            return

        # Table: max widths
        max_my = max(len(u.name_my) for u in units)
        max_en = max(len(u.name_en) for u in units)
        max_cat = max(len(u.get_category_display() or u.category) for u in units)
        max_my = max(max_my, 16)
        max_en = max(max_en, 16)
        max_cat = max(max_cat, 10)

        sep = " | "
        header = (
            "Code".ljust(14) + sep +
            ("Unit Name (MM)").ljust(max_my) + sep +
            ("Unit Name (EN)").ljust(max_en) + sep +
            "Category".ljust(max_cat)
        )
        self.stdout.write(header)
        self.stdout.write("-" * len(header))
        for u in units:
            cat = u.get_category_display() or u.category
            row = (
                (u.code or "").ljust(14) + sep +
                (u.name_my or "").ljust(max_my) + sep +
                (u.name_en or "").ljust(max_en) + sep +
                cat.ljust(max_cat)
            )
            self.stdout.write(row)
        self.stdout.write("")
        self.stdout.write(f"Total: {units.count()} unit(s)")
