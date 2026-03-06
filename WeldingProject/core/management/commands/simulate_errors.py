"""
Error simulation for testing: license expired (403), etc.
Run: python manage.py simulate_errors --license-expired   (then open app to see 403 -> license-activate)
     python manage.py simulate_errors --reset-license     (restore)
     python manage.py simulate_errors --list              (list options)
"""
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = 'Simulate errors for testing (e.g. license expired 403). Use --list to see options.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--license-expired',
            action='store_true',
            help='Make license appear expired (trial+grace over). Next API call returns 403.',
        )
        parser.add_argument(
            '--reset-license',
            action='store_true',
            help='Restore after --license-expired (trial from now, restore license.lic if backed up).',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List available error simulations.',
        )

    def handle(self, *args, **options):
        if options['list']:
            self._list()
            return
        if options['license_expired']:
            self._simulate_license_expired()
            return
        if options['reset_license']:
            self._reset_license()
            return
        self.stdout.write(self.style.WARNING('Use --list, --license-expired, or --reset-license.'))

    def _list(self):
        self.stdout.write(self.style.MIGRATE_HEADING('Available error simulations:'))
        self.stdout.write('  --license-expired   Simulate 403 (trial+grace expired). Open app to see redirect to /license-activate.')
        self.stdout.write('  --reset-license     Restore after --license-expired.')
        self.stdout.write('')
        self.stdout.write('Other errors (manual): 401 = remove access_token in localStorage; 404/offline = stop backend.')

    def _simulate_license_expired(self):
        from license.utils import get_machine_id, get_license_file_path
        from license.services import get_or_create_installation

        mid = get_machine_id()
        inst = get_or_create_installation(mid)
        # Trial 30 + Grace 5 = 35 days. Set first_run_at to 40 days ago so grace_expired.
        old_first = timezone.now() - timedelta(days=40)
        inst.first_run_at = old_first
        inst.save(update_fields=['first_run_at'])

        # Hide license.lic so check_license_status does not use it (backup and remove)
        path = get_license_file_path()
        backup = path.parent / (path.name + '.simulate_bak')
        if path.exists():
            backup.write_bytes(path.read_bytes())
            path.unlink()
            self.stdout.write(self.style.SUCCESS('Backed up license.lic to license.lic.simulate_bak and removed.'))
        else:
            self.stdout.write('No license.lic to backup.')

        self.stdout.write(self.style.SUCCESS(
            'License expired simulated. Next API request will get 403 -> redirect to /license-activate.'
        ))
        self.stdout.write('To restore: python manage.py simulate_errors --reset-license')

    def _reset_license(self):
        from license.utils import get_machine_id, get_license_file_path
        from license.services import get_or_create_installation

        mid = get_machine_id()
        inst = get_or_create_installation(mid)
        inst.first_run_at = timezone.now()
        inst.save(update_fields=['first_run_at'])

        path = get_license_file_path()
        backup = path.parent / (path.name + '.simulate_bak')
        if backup.exists():
            path.write_bytes(backup.read_bytes())
            backup.unlink()
            self.stdout.write(self.style.SUCCESS('Restored license.lic from license.lic.simulate_bak.'))
        else:
            self.stdout.write('No license.lic.simulate_bak to restore.')

        self.stdout.write(self.style.SUCCESS('License reset. Trial starts from now.'))
