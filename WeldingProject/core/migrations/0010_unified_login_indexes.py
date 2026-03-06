# Unified login: longer lockout identifier (phone or email), index on User.email for fast login

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_phone_auth'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loginfailattempt',
            name='phone_normalized',
            field=models.CharField(db_index=True, max_length=320, unique=True),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='core_user_email_idx'),
        ),
    ]
