# Generated migration for multi-instance trial

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_remove_user_idx_user_role_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shopsettings',
            name='trial_start_date',
            field=models.DateTimeField(blank=True, help_text='When set, trial expires 30 days after this date.', null=True),
        ),
    ]
