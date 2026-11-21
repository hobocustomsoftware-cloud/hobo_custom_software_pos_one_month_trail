from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

# ၁။ User အသစ်ဖန်တီးရာတွင် အသုံးပြုမည့် Form
class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', 'role_obj') # role အစား role_obj ကို သုံးပါ

    def save(self, commit=True):
        from django.contrib.auth.hashers import make_password
        user = super().save(commit=False)
        # Hash only: plaintext is never stored. Shown once via the API create
        # response, never recoverable from the database.
        user.temp_password = make_password(self.cleaned_data["password"])
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
        # temp_password holds only a hash: visible in admin for rotation audits,
        # never a usable password. The clear text is shown once at creation.
        if 'temp_password' in self.fields:
            self.fields['temp_password'].disabled = True
            self.fields['temp_password'].help_text = "Hashed one-time password (unrecoverable). Create a new password to rotate."