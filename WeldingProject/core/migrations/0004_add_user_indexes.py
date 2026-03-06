"""
Add database indexes for User model performance optimization.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('core', '0003_shop_settings'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['role_obj'], name='idx_user_role'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['primary_location'], name='idx_user_location'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active', 'is_staff'], name='idx_user_active_staff'),
        ),
    ]
