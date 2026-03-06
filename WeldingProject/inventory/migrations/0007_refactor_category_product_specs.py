# Generated migration for Category hierarchy, ProductSpecification, and unit_type

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0006_add_product_model_no_serial_required'),
    ]

    operations = [
        # Add parent field to Category
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='children',
                to='inventory.category',
                verbose_name='Parent Category'
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='order',
            field=models.IntegerField(default=0, verbose_name='Display Order'),
        ),
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Active'),
        ),
        # Remove unique constraint on name, add unique_together
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, verbose_name='အမျိုးအစားအမည်'),
        ),
        migrations.AlterUniqueTogether(
            name='category',
            unique_together={('name', 'parent')},
        ),
        # Add unit_type to Product
        migrations.AddField(
            model_name='product',
            name='unit_type',
            field=models.CharField(
                choices=[
                    ('PCS', 'Pieces'),
                    ('SET', 'Sets'),
                    ('MTR', 'Meters'),
                    ('ROL', 'Rolls'),
                    ('KG', 'Kilograms'),
                    ('BOX', 'Boxes'),
                    ('PKG', 'Packages'),
                    ('UNT', 'Units'),
                ],
                default='PCS',
                max_length=10,
                verbose_name='Unit Type'
            ),
        ),
        # Create ProductSpecification model
        migrations.CreateModel(
            name='ProductSpecification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('label', models.CharField(max_length=100, verbose_name='Specification Label (e.g., Voltage)')),
                ('value', models.CharField(max_length=200, verbose_name='Specification Value (e.g., 220V)')),
                ('order', models.IntegerField(default=0, verbose_name='Display Order')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('product', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='specifications',
                    to='inventory.product',
                    verbose_name='Product'
                )),
            ],
            options={
                'verbose_name': 'Product Specification',
                'verbose_name_plural': 'Product Specifications',
                'ordering': ['order', 'label'],
                'unique_together': {('product', 'label')},
            },
        ),
        # Create SerialNumberHistory model
        migrations.CreateModel(
            name='SerialNumberHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(
                    choices=[
                        ('purchased', 'Purchased'),
                        ('received', 'Received at Location'),
                        ('transferred', 'Transferred'),
                        ('sold', 'Sold'),
                        ('returned', 'Returned'),
                        ('repair_started', 'Repair Started'),
                        ('repair_completed', 'Repair Completed'),
                        ('defective', 'Marked as Defective'),
                        ('status_changed', 'Status Changed'),
                    ],
                    max_length=20,
                    verbose_name='Action'
                )),
                ('from_status', models.CharField(
                    blank=True,
                    choices=[
                        ('in_stock', 'In Stock'),
                        ('sold', 'Sold'),
                        ('defective', 'Defective'),
                        ('pending_sale', 'Pending Sale Approval'),
                    ],
                    max_length=20,
                    null=True
                )),
                ('to_status', models.CharField(
                    blank=True,
                    choices=[
                        ('in_stock', 'In Stock'),
                        ('sold', 'Sold'),
                        ('defective', 'Defective'),
                        ('pending_sale', 'Pending Sale Approval'),
                    ],
                    max_length=20,
                    null=True
                )),
                ('notes', models.TextField(blank=True, null=True, verbose_name='Notes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='core.user',
                    verbose_name='Created By'
                )),
                ('from_location', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='serial_history_from',
                    to='inventory.location',
                    verbose_name='From Location'
                )),
                ('serial_item', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='history_records',
                    to='inventory.serialitem',
                    verbose_name='Serial Item'
                )),
                ('to_location', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='serial_history_to',
                    to='inventory.location',
                    verbose_name='To Location'
                )),
                ('transaction', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='inventory.saletransaction',
                    verbose_name='Related Transaction'
                )),
            ],
            options={
                'verbose_name': 'Serial Number History',
                'verbose_name_plural': 'Serial Number Histories',
                'ordering': ['-created_at'],
            },
        ),
    ]
