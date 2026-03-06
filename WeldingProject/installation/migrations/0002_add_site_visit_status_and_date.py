# Generated manually for site_visit status and site_visit_date

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('installation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='installationjob',
            name='site_visit_date',
            field=models.DateField(blank=True, null=True, verbose_name='သွားတိုင်းရမည့်ရက်'),
        ),
        migrations.AlterField(
            model_name='installationjob',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending (စောင့်ဆိုင်းဆဲ)'),
                    ('site_visit', 'Site visit (သွားတိုင်းရမည်)'),
                    ('in_progress', 'In Progress (တပ်ဆင်ဆဲ)'),
                    ('completed', 'Completed (ပြီးစီးပြီး)'),
                    ('signed_off', 'Signed Off (လက်မှတ်ရေးထိုးပြီး)'),
                    ('cancelled', 'Cancelled (ပယ်ဖျက်)'),
                ],
                default='pending',
                max_length=20,
                verbose_name='အခြေအနေ',
            ),
        ),
    ]
