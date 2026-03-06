from django.contrib.auth.models import UserManager

class CustomUserManager(UserManager):
    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError('The given username must be set')
        
        email = self.normalize_email(email)
        # is_staff ကို ဖယ်ထုတ်စရာမလိုတော့ပါ (Model ရဲ့ save() ထဲမှာ logic ရေးထားပြီးသားမို့လို့ပါ)
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        
        # password ကို temp_password ထဲမှာပါ သိမ်းပေးထားခြင်း (Owner ကြည့်ရန်)
        user.temp_password = password
        
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True) # Superuser အတွက် staff access လိုအပ်ပါသည်

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        # Database ထဲတွင် super_admin ဆိုသော Role ရှိမရှိ စစ်ဆေးပြီး ချိတ်ပေးခြင်း
        from core.models import Role # Circular import ရှောင်ရန် ဒီမှာ import လုပ်ပါ
        super_admin_role, _ = Role.objects.get_or_create(name='super_admin')
        extra_fields.setdefault('role_obj', super_admin_role)

        return self._create_user(username, email, password, **extra_fields)