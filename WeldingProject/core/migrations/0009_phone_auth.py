# Phone-based auth: phone_number, requires_password_change, LoginFailAttempt

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_auditlog_rbac'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, db_index=True, max_length=20, null=True, unique=True, verbose_name='Phone Number'),
        ),
        migrations.AddField(
            model_name='user',
            name='requires_password_change',
            field=models.BooleanField(default=False, verbose_name='Must change password on first login'),
        ),
        migrations.CreateModel(
            name='LoginFailAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_normalized', models.CharField(db_index=True, max_length=20, unique=True)),
                ('fail_count', models.PositiveIntegerField(default=0)),
                ('locked_until', models.DateTimeField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Login Fail Attempt',
                'verbose_name_plural': 'Login Fail Attempts',
            },
        ),
    ]
