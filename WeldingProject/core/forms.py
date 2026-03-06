from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

# ၁။ User အသစ်ဖန်တီးရာတွင် အသုံးပြုမည့် Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role_obj') # role အစား role_obj ကို သုံးပါ

    def save(self, commit=True):
        user = super().save(commit=False)
        # Plain password ကို temp_password ထဲတွင် သိမ်းခြင်း (Owner ကြည့်ရန်)
        user.temp_password = self.cleaned_data["password"]
        if commit:
            user.save()
        return user

# ၂။ User အချက်အလက် ပြင်ဆင်ရာတွင် အသုံးပြုမည့် Form
class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role_obj', 'is_active', 'temp_password')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # temp_password ကို Admin panel တွင် ပြင်၍မရဘဲ ကြည့်ရုံသာ (Read-only) လုပ်ထားနိုင်သည်
        if 'temp_password' in self.fields:
            self.fields['temp_password'].disabled = True
            self.fields['temp_password'].help_text = "This is the current plain password for owner reference."