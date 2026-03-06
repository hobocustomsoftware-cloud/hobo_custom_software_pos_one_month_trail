"""
Demo သုံးသူများအတွက် အကောင့်များ ဖန်တီးခြင်း
Run: python manage.py seed_demo_users
"""
from django.core.management.base import BaseCommand
from core.models import User, Role


DEMO_USERS = [
    {
        'username': 'owner',
        'password': 'demo123',
        'first_name': 'Demo',
        'last_name': 'Owner',
        'role_name': 'owner',
        'description': 'ပိုင်ရှင် (အကောင့်အားလုံး ကြည့်နိုင်)',
    },
    {
        'username': 'manager',
        'password': 'demo123',
        'first_name': 'Demo',
        'last_name': 'Manager',
        'role_name': 'manager',
        'description': 'မန်နေဂျာ',
    },
    {
        'username': 'staff',
        'password': 'demo123',
        'first_name': 'Demo',
        'last_name': 'Staff',
        'role_name': 'sale_staff',
        'description': 'ရောင်းချရေး ဝန်ထမ်း',
    },
]


class Command(BaseCommand):
    help = 'Demo သုံးသူများအတွက် အကောင့်များ ဖန်တီးခြင်း'

    def handle(self, *args, **options):
        created = 0
        for data in DEMO_USERS:
            role_name = data.pop('role_name')
            description = data.pop('description', '')
            password = data.pop('password')

            role, _ = Role.objects.get_or_create(
                name=role_name,
                defaults={'description': description}
            )
            is_staff = role_name in ('owner', 'manager', 'super_admin')

            user, created_user = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    **data,
                    'role_obj': role,
                    'is_active': True,
                    'is_staff': is_staff,
                }
            )
            # Demo အကောင့်များ password ကို အမြဲ demo123 ထားခြင်း
            user.set_password(password)
            user.save()
            if created_user:
                created += 1
            self.stdout.write(self.style.SUCCESS(f'  [OK] {user.username} / {password}'))

        if created:
            self.stdout.write(self.style.SUCCESS(f'\nDemo accounts: {created} created.'))
        else:
            self.stdout.write('Demo accounts ready.')
