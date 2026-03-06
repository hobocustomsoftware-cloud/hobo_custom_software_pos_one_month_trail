"""
Database ရှင်းပြီး Demo Trial တစ်လ + ဆိုင်အရေအတွက် စမ်းလို့ရအောင် setup လုပ်ခြင်း။
တစ်ဆိုင်တည်း သို့မဟုတ် ဆိုင်ခွဲ ၃/၄/၅ ဆိုင် စမ်းချင်သလို --outlets နဲ့ ရွေးနိုင်သည်။
ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ဆိုင်ခွဲ ၄–၈ ဆိုရင် --outlets 20 --branches-per-main 6 သုံးပါ။

Usage:
  # တစ်ဆိုင်တည်း (Demo လာစမ်းသူအတွက်)
  python manage.py reset_trial_20_outlets --flush --outlets 1

  # ဆိုင်ခွဲ ၃/၄/၅ ဆိုင် စမ်းမယ်
  python manage.py reset_trial_20_outlets --flush --outlets 3
  python manage.py reset_trial_20_outlets --flush --outlets 5

  # ဆိုင် ၂၀ (အရင် ပုံမှန်: ဆိုင်ချုပ် ၁ + ဆိုင်ခွဲ ၁၉)
  python manage.py reset_trial_20_outlets --flush --outlets 20

  # ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ဆိုင်ခွဲ ၆ ဆိုင် (စုစုပေါင်း ၂၀ + ၁၂၀ = ၁၄၀ ဆိုင်)
  python manage.py reset_trial_20_outlets --flush --outlets 20 --branches-per-main 6

  # ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ဆိုင်ခွဲ ၄/၈ ဆိုင်
  python manage.py reset_trial_20_outlets --flush --outlets 20 --branches-per-main 4
  python manage.py reset_trial_20_outlets --flush --outlets 20 --branches-per-main 8

  # Trial စမ်းချင်ရင်: SKIP_LICENSE=false ထားပြီး run ပါ။
  # ပစ္စည်း/ categories ထည့်ချင်ရင်: python manage.py seed_shop_demo --shop general
"""
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone

from core.models import Outlet, ShopSettings, Role

User = get_user_model()

OUTLET_CHOICES = [1, 3, 4, 5, 20]  # တစ်ဆိုင်တည်း၊ သုံးလေးငါးဆိုင်၊ သို့မဟုတ် ၂၀


def ensure_user(stdout, style):
    user, created = User.objects.get_or_create(
        username='admin',
        defaults={'email': 'admin@example.com', 'is_staff': True, 'is_superuser': True},
    )
    if created or not user.check_password('admin123'):
        user.set_password('admin123')
        user.save()
    if not getattr(user, 'phone_number', None) or not user.phone_number:
        if hasattr(user, 'phone_number'):
            user.phone_number = '09123456789'
            user.save(update_fields=['phone_number'])
    stdout.write(style.SUCCESS("  User: admin / admin123 (သို့) 09123456789"))
    return user


def ensure_roles(stdout, style):
    for name, desc in [
        ('Owner', 'Full access'),
        ('Manager', 'Manage sales & staff'),
        ('Cashier', 'POS only'),
    ]:
        Role.objects.get_or_create(name=name, defaults={'description': desc})
    owner = Role.objects.get(name='Owner')
    stdout.write(style.SUCCESS("  Roles: Owner, Manager, Cashier"))
    return owner


def ensure_shop_settings_trial(stdout, style):
    """ShopSettings ဖန်တီး/ပြင်ပြီး trial တစ်လ စတင်မယ် (trial_start_date = ယနေ့)"""
    obj = ShopSettings.get_settings()
    obj.trial_start_date = timezone.now()
    obj.shop_name = obj.shop_name or 'HoBo POS Trial'
    obj.setup_wizard_done = True
    obj.save()
    stdout.write(style.SUCCESS("  ShopSettings: trial တစ်လ စတင် (trial_start_date = ယနေ့)"))


def ensure_outlets(stdout, style, num_outlets, branches_per_main=0):
    """
    branches_per_main=0 (default): ဆိုင်ချုပ် ၁ + ဆိုင်ခွဲ (num_outlets - 1) ခု ဖန်တီး (အရင် ပုံမှန်)။
    branches_per_main=4 to 8: ဆိုင်ချုပ် num_outlets ခု ဖန်တီး၊ တစ်ချုပ်၌ ဆိုင်ခွဲ branches_per_main ခု။
    """
    if branches_per_main and num_outlets >= 2:
        # ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ဆိုင်ခွဲ ၄–၈
        mains = []
        for i in range(1, num_outlets + 1):
            code = f"MAIN_{i:02d}"
            o = Outlet.objects.filter(code=code).first()
            if not o:
                o = Outlet.objects.create(
                    name=f"ဆိုင်ချုပ် {i}",
                    code=code,
                    is_main_branch=(i == 1),
                    parent_outlet=None,
                )
            mains.append(o)
        for main in mains:
            for j in range(1, branches_per_main + 1):
                sub_code = f"{main.code}_BRANCH_{j:02d}"
                if Outlet.objects.filter(code=sub_code).exists():
                    continue
                Outlet.objects.create(
                    name=f"{main.name} - ခွဲ {j}",
                    code=sub_code,
                    is_main_branch=False,
                    parent_outlet=main,
                )
        for o in Outlet.objects.all():
            o.get_warehouse_location()
            o.get_shopfloor_location()
        total = Outlet.objects.count()
        stdout.write(style.SUCCESS(
            f"  Outlets: ဆိုင်ချုပ် {num_outlets} + တစ်ချုပ်၌ ခွဲ {branches_per_main} = စုစုပေါင်း {total} ဆိုင်"
        ))
        return mains[0] if mains else None
    # ပုံမှန်: ဆိုင်ချုပ် ၁ + ဆိုင်ခွဲ (num_outlets - 1)
    main = Outlet.objects.filter(code='MAIN').first()
    if not main:
        main = Outlet.objects.create(
            name="ဆိုင်ချုပ် (Main)",
            code="MAIN",
            is_main_branch=True,
            parent_outlet=None,
        )
    num_branches = max(0, int(num_outlets) - 1)
    for i in range(1, num_branches + 1):
        code = f"BRANCH_{i:02d}"
        if Outlet.objects.filter(code=code).exists():
            continue
        Outlet.objects.create(
            name=f"ဆိုင်ခွဲ {i}",
            code=code,
            is_main_branch=False,
            parent_outlet=None,
        )
    for o in Outlet.objects.all():
        o.get_warehouse_location()
        o.get_shopfloor_location()
    count = Outlet.objects.count()
    if num_outlets == 1:
        stdout.write(style.SUCCESS("  Outlets: တစ်ဆိုင်တည်း (ဆိုင်ချုပ် ပဲ)"))
    else:
        stdout.write(style.SUCCESS(f"  Outlets: စုစုပေါင်း {count} ဆိုင် (ဆိုင်ချုပ် + ဆိုင်ခွဲ {num_branches})"))
    return main


class Command(BaseCommand):
    help = 'Database ရှင်းပြီး Demo Trial တစ်လ + ဆိုင်အရေအတွက် (၁/၃/၄/၅/၂၀) စမ်းလို့ရအောင် setup လုပ်ပါ။'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='DB flush + migrate + seed_base_units ပြီးမှ trial နဲ့ ဆိုင်များ ထည့်မည်။',
        )
        parser.add_argument(
            '--outlets',
            type=int,
            default=1,
            choices=OUTLET_CHOICES,
            metavar='N',
            help='ဆိုင်အရေအတွက်: 1=တစ်ဆိုင်တည်း, 3/4/5=ဆိုင်ခွဲ သုံးလေးငါး, 20=ဆိုင်၂၀ (default: 1)',
        )
        parser.add_argument(
            '--branches-per-main',
            type=int,
            default=0,
            metavar='K',
            help='ဆိုင်ချုပ် တစ်ချုပ်၌ ဆိုင်ခွဲ အရေအတွက် (၄–၈)。 --outlets 20 နဲ့ သုံးရင် ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ခွဲ K ဆိုင် ဖန်တီးမယ်။',
        )

    def handle(self, *args, **options):
        style = self.style
        do_flush = options.get('flush', False)
        num_outlets = options.get('outlets', 1)
        branches_per_main = max(0, min(8, options.get('branches_per_main', 0)))

        if branches_per_main and num_outlets >= 2:
            self.stdout.write(style.SUCCESS(
                f"\n=== Demo Trial တစ်လ + ဆိုင်ချုပ် {num_outlets} × ခွဲ {branches_per_main} ===\n"
            ))
        else:
            self.stdout.write(style.SUCCESS(f"\n=== Demo Trial တစ်လ + ဆိုင် {num_outlets} ===\n"))

        if do_flush:
            self.stdout.write("DB ရှင်းနေပါတယ် (flush)...")
            call_command('flush', '--noinput')
            call_command('migrate', '--noinput')
            self.stdout.write("Base units ထည့်နေပါတယ်...")
            call_command('seed_base_units')

        with transaction.atomic():
            user = ensure_user(self.stdout, style)
            owner_role = ensure_roles(self.stdout, style)
            ensure_shop_settings_trial(self.stdout, style)
            main = ensure_outlets(self.stdout, style, num_outlets, branches_per_main=branches_per_main)

            if not getattr(user, 'role_obj_id', None):
                user.role_obj = owner_role
                user.save(update_fields=['role_obj'])
            if not getattr(user, 'primary_outlet_id', None):
                user.primary_outlet = main
                user.save(update_fields=['primary_outlet'])

        if branches_per_main and num_outlets >= 2:
            total = num_outlets + num_outlets * branches_per_main
            self.stdout.write(style.SUCCESS(f"\nပြီးပါပြီ။ Trial တစ်လ + ဆိုင် စုစုပေါင်း {total} စမ်းလို့ရပါပြီ။"))
        else:
            self.stdout.write(style.SUCCESS(f"\nပြီးပါပြီ။ Trial တစ်လ စတင်ပြီး ဆိုင် {num_outlets} စမ်းလို့ရပါပြီ။"))
        self.stdout.write("  Login: admin / admin123")
        self.stdout.write("  ပစ္စည်း/ categories ထည့်ချင်ရင်: python manage.py seed_shop_demo --shop general")
