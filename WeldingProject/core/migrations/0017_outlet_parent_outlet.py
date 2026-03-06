# Generated for hierarchical outlets: ဆိုင်ချုပ် ၂၀ + တစ်ချုပ်၌ ဆိုင်ခွဲ ၄–၈

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0016_shift'),
    ]

    operations = [
        migrations.AddField(
            model_name='outlet',
            name='parent_outlet',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sub_outlets',
                to='core.outlet',
                verbose_name='ဆိုင်ချုပ် (Parent)',
            ),
        ),
    ]
