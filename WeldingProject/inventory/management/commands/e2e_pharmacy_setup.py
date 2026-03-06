"""
E2E Pharmacy Demo: DB reset, migrate, seed units (Box, Strip), admin user, 2 outlets (Main + Branch A).
Run before E2E browser test. Usage: python manage.py e2e_pharmacy_setup
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model
from core.models import Outlet
from inventory.models import Unit, Category

User = get_user_model()


class Command(BaseCommand):
    help = "Reset DB, migrate, seed Box/Strip, create admin + 2 outlets (Main, Branch A)"

    def add_arguments(self, parser):
        parser.add_argument('--no-flush', action='store_true', help='Skip flush (e.g. already clean)')
        parser.add_argument('--no-migrate', action='store_true', help='Skip migrate')

    def handle(self, *args, **options):
        style = self.style
        self.stdout.write(style.SUCCESS("\n=== E2E Pharmacy Setup ===\n"))

        if not options.get('no_flush'):
            self.stdout.write("  Flushing database...")
            call_command('flush', '--noinput')
            self.stdout.write(style.SUCCESS("  Flush done."))

        if not options.get('no_migrate'):
            self.stdout.write("  Running migrations...")
            call_command('migrate', '--noinput')
            self.stdout.write(style.SUCCESS("  Migrate done."))

        with transaction.atomic():
            # Admin user
            user, created = User.objects.get_or_create(
                username='admin',
                defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True},
            )
            if created or not user.check_password('admin123'):
                user.set_password('admin123')
                user.save()
            self.stdout.write(style.SUCCESS("  User: admin / admin123"))

            # Units: Box, Strip (Pharmacy)
            Unit.objects.update_or_create(
                code='STRIP',
                defaults={'name_my': 'ကတ်', 'name_en': 'Strip', 'category': 'count', 'order': 1},
            )
            Unit.objects.update_or_create(
                code='BOX',
                defaults={'name_my': 'ဗူး/ဘူး', 'name_en': 'Box', 'category': 'packaging', 'order': 2},
            )
            self.stdout.write(style.SUCCESS("  Units: Box, Strip"))

            # 2 Outlets: Main (Warehouse + Shopfloor), Branch A (Warehouse + Shopfloor)
            main = Outlet.objects.filter(code='MAIN').first()
            if not main:
                main = Outlet.objects.create(name="Main Warehouse", code="MAIN", is_main_branch=True)
            branch_a = Outlet.objects.filter(code='BRANCH_A').first()
            if not branch_a:
                branch_a = Outlet.objects.create(name="Branch A", code="BRANCH_A", is_main_branch=False)
            self.stdout.write(style.SUCCESS("  Outlets: Main, Branch A (each has Warehouse + Shopfloor)"))

            # Category for Pharmacy (product create needs category)
            Category.objects.get_or_create(name="Pharmacy (ဆေးဆိုင်)", defaults={'order': 0})

            # Optional: ensure Owner role so admin can access all
            from core.models import Role
            Role.objects.get_or_create(name='Owner', defaults={'description': 'Full access'})
            owner_role = Role.objects.get(name='Owner')
            if not user.role_obj_id:
                user.role_obj = owner_role
                user.save(update_fields=['role_obj'])

        self.stdout.write(style.SUCCESS("\n  Setup complete. Start server and run E2E script.\n"))
