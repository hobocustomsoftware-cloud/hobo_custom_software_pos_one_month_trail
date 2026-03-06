"""
Complete one-month simulation of a Solar shop POS system.
Simulates Day 1-30 with all features: registration, staff, inventory, sales, 
installations, repairs, expenses, USD rate changes, P&L reports.

Run: python manage.py simulate_month
"""
import json
import random
import time
from datetime import datetime, timedelta, date
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.conf import settings

# Avoid Redis for this command
settings.CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}


def _safe_str(s):
    """Avoid UnicodeEncodeError on Windows CMD."""
    try:
        return str(s).encode('utf-8', 'replace').decode('utf-8')
    except Exception:
        return str(s)[:50]


class Command(BaseCommand):
    help = 'Simulate one complete month of Solar shop operations'

    def add_arguments(self, parser):
        parser.add_argument('--delay', type=float, default=1.0, help='Delay between days (seconds)')
        parser.add_argument('--skip-delay', action='store_true', help='Skip delays for faster execution')

    def log(self, emoji, day, action):
        """Print progress with emoji and day number."""
        try:
            msg = f"{emoji} Day {day}: {action}"
            self.stdout.write(self.style.SUCCESS(msg))
        except UnicodeEncodeError:
            # Fallback for Windows console encoding issues
            msg = f"Day {day}: {action}"
            self.stdout.write(self.style.SUCCESS(msg))
        self.simulation_log.append({
            'day': day,
            'action': action,
            'emoji': emoji,
            'timestamp': timezone.now().isoformat()
        })

    def handle(self, *args, **options):
        delay = 0 if options['skip_delay'] else options['delay']
        self.simulation_log = []
        start_date = timezone.now() - timedelta(days=30)
        
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))
        self.stdout.write(self.style.MIGRATE_HEADING('SOLAR SHOP ONE-MONTH SIMULATION'))
        self.stdout.write(self.style.MIGRATE_HEADING('=' * 60))

        # Import all models
        from core.models import User, Role, ShopSettings, StaffSession
        from inventory.models import (
            Category, Product, ProductTag, Location, Site, Bundle, BundleItem,
            InventoryMovement, SerialItem, SaleTransaction, SaleItem,
            PaymentMethod, WarrantyRecord, ExchangeRateLog, GlobalSetting, Notification
        )
        from customer.models import Customer
        from service.models import RepairService, RepairSparePart, RepairStatusHistory
        from installation.models import InstallationJob, InstallationStatusHistory
        from accounting.models import ExpenseCategory, Expense, Transaction
        from license.models import AppInstallation, AppLicense

        # DAY 1-2: SHOP REGISTRATION & SETUP
        self.log('🏪', 1, 'Shop Registration & Setup')
        with transaction.atomic():
            # Create owner
            owner_role, _ = Role.objects.get_or_create(name='owner', defaults={'description': 'Owner'})
            owner = User.objects.filter(role_obj=owner_role).first()
            if not owner:
                owner = User.objects.create_user(
                    username='owner_solar',
                    email='owner@solar.com',
                    first_name='ဦး',
                    last_name='မြတ်ရှင်',
                    role_obj=owner_role,
                    is_staff=True,
                    is_active=True,
                )
            owner.set_password('demo123')
            owner.is_active = True
            owner.save()
            self.log('👤', 1, f'Owner ready: {owner.username} / demo123')

            # Activate license
            machine_id = 'SIM-MACHINE-001'
            app_install, _ = AppInstallation.objects.get_or_create(
                machine_id=machine_id,
                defaults={'deployment_mode': 'on_premise'}
            )
            license_key = 'SIM-LICENSE-2024-001'
            app_license, _ = AppLicense.objects.get_or_create(
                license_key=license_key,
                defaults={
                    'license_type': 'on_premise_perpetual',
                    'machine_id': machine_id,
                    'is_active': True
                }
            )
            self.log('🔑', 1, 'License activated')

            # Shop Settings
            shop_settings, _ = ShopSettings.objects.get_or_create(
                pk=1,
                defaults={'shop_name': 'Solar Power Solutions'}
            )
            self.log('⚙️', 1, 'Shop settings configured')

            # Initial USD rate
            usd_rate = Decimal('3450.0000')
            ExchangeRateLog.objects.get_or_create(
                date=start_date.date(),
                defaults={'rate': usd_rate}
            )
            GlobalSetting.objects.update_or_create(
                key='usd_exchange_rate',
                defaults={'value_decimal': usd_rate}
            )
            self.log('💵', 1, f'Initial USD rate: {usd_rate} MMK')

        if delay > 0:
            time.sleep(delay)

        # DAY 2: STAFF SETUP (all 11 roles)
        self.log('👥', 2, 'Staff Setup - All 11 Roles')
        roles_data = [
            ('admin', 'Admin User'),
            ('manager', 'Manager'),
            ('assistant_manager', 'Assistant Manager'),
            ('inventory_manager', 'Inventory Manager'),
            ('inventory_staff', 'Inventory Staff'),
            ('sale_supervisor', 'Sale Supervisor'),
            ('sale_staff', 'Sale Staff'),
            ('technician', 'Technician'),
            ('employee', 'Employee'),
        ]
        staff_users = {'owner': owner}
        
        with transaction.atomic():
            for role_name, description in roles_data:
                role_obj, _ = Role.objects.get_or_create(
                    name=role_name,
                    defaults={'description': description}
                )
                
                if role_name == 'sale_staff':
                    # Create 2 sale_staff
                    for i in range(2):
                        username = f'sale_staff_{i+1}'
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                'first_name': f'ရောင်းချသူ',
                                'last_name': f'{i+1}',
                                'role_obj': role_obj,
                                'is_active': True
                            }
                        )
                        if created:
                            user.set_password('demo123')
                            user.save()
                        else:
                            user.set_password('demo123')
                            user.is_active = True
                            user.save()
                        staff_users[username] = user
                elif role_name == 'technician':
                    # Create 2 technicians
                    for i in range(2):
                        username = f'technician_{i+1}'
                        user, created = User.objects.get_or_create(
                            username=username,
                            defaults={
                                'first_name': f'တပ်ဆင်သူ',
                                'last_name': f'{i+1}',
                                'role_obj': role_obj,
                                'is_active': True
                            }
                        )
                        if created:
                            user.set_password('demo123')
                            user.save()
                        else:
                            user.set_password('demo123')
                            user.is_active = True
                            user.save()
                        staff_users[username] = user
                else:
                    username = role_name
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={
                            'first_name': description.split()[0],
                            'last_name': description.split()[-1] if len(description.split()) > 1 else '',
                            'role_obj': role_obj,
                            'is_staff': role_name in ['admin', 'manager'],
                            'is_active': True
                        }
                    )
                    if created:
                        user.set_password('demo123')
                        user.save()
                    else:
                        user.set_password('demo123')
                        user.is_active = True
                        user.save()
                    staff_users[username] = user

            # Create StaffSession records
            main_location = Location.objects.filter(is_sale_location=True).first()
            if main_location:
                for username, user in staff_users.items():
                    if username != 'owner':
                        StaffSession.objects.get_or_create(
                            user=user,
                            location=main_location,
                            started_at=start_date + timedelta(days=2),
                            defaults={'is_active': True}
                        )

        self.log('✅', 2, f'Created {len(staff_users)} staff members')
        
        # Store manager_user for later use
        manager_user = staff_users.get('manager', owner)

        if delay > 0:
            time.sleep(delay)

        # DAY 3: INVENTORY SETUP
        self.log('📦', 3, 'Inventory Setup - Solar Products')
        with transaction.atomic():
            # Create Site first
            main_site, _ = Site.objects.get_or_create(
                name='Solar Power Solutions - Main Branch',
                defaults={'address': '123 Main Street, Yangon', 'code': 'MAIN-001'}
            )
            
            # Locations
            main_warehouse, _ = Location.objects.get_or_create(
                name='Main Warehouse',
                defaults={
                    'site': main_site,
                    'location_type': 'warehouse', 
                    'is_sale_location': False
                }
            )
            shop_floor, _ = Location.objects.get_or_create(
                name='Shop Floor',
                defaults={
                    'site': main_site,
                    'location_type': 'shop_floor', 
                    'is_sale_location': True
                }
            )
            service_area, _ = Location.objects.get_or_create(
                name='Service Area',
                defaults={
                    'site': main_site,
                    'location_type': 'warehouse',  # Use valid choice
                    'is_sale_location': False
                }
            )

            # Categories
            categories = {}
            cat_names = ['Panels', 'Batteries', 'Inverters', 'Accessories', 'Monitoring']
            for cat_name in cat_names:
                cat, _ = Category.objects.get_or_create(name=cat_name)
                categories[cat_name] = cat

            # Products
            products_data = [
                ('Monocrystalline Panel 400W', 'Panels', Decimal('120.0000'), Decimal('100.0000'), True, 60),
                ('Lithium Battery 100Ah', 'Batteries', Decimal('180.0000'), Decimal('150.0000'), True, 60),
                ('Hybrid Inverter 3KW', 'Inverters', Decimal('250.0000'), Decimal('200.0000'), True, 24),
                ('MPPT Controller 40A', 'Accessories', Decimal('45.0000'), Decimal('35.0000'), False, 12),
                ('DC Cable 10m', 'Accessories', Decimal('15.0000'), Decimal('10.0000'), False, 0),
                ('Mounting Structure', 'Accessories', Decimal('80.0000'), Decimal('60.0000'), False, 0),
                ('WiFi Monitoring Module', 'Monitoring', Decimal('35.0000'), Decimal('25.0000'), False, 12),
            ]
            
            products = {}
            for name, cat_name, cost_usd, cost_price, is_serial, warranty_months in products_data:
                cat = categories[cat_name]
                product, created = Product.objects.get_or_create(
                    name=name,
                    defaults={
                        'category': cat,
                        'cost_usd': cost_usd,
                        'cost_price': cost_price,
                        'retail_price': cost_price * Decimal('1.3'),  # 30% markup
                        'price_type': 'DYNAMIC_USD',
                        'is_serial_tracked': is_serial,
                        'warranty_months': warranty_months,
                        'markup_percentage': Decimal('30.00')
                    }
                )
                if created:
                    # Calculate retail_price from USD
                    product.retail_price = cost_usd * usd_rate * Decimal('1.3')
                    product.save()
                products[name] = product

            # Tags
            tags = {}
            tag_names = ['bestseller', 'new', 'warranty-2yr', 'warranty-5yr']
            for tag_name in tag_names:
                tag, _ = ProductTag.objects.get_or_create(name=tag_name)
                tags[tag_name] = tag

            # Bundle: "3KW Home Solar System"
            bundle, _ = Bundle.objects.get_or_create(
                name='3KW Home Solar System',
                defaults={
                    'bundle_type': 'Solar',
                    'pricing_type': 'CUSTOM_SET',
                    'discount_type': 'PERCENTAGE',
                    'discount_value': Decimal('8.00'),
                    'is_active': True
                }
            )
            bundle_items_data = [
                ('Monocrystalline Panel 400W', 6),
                ('Lithium Battery 100Ah', 4),
                ('Hybrid Inverter 3KW', 1),
                ('MPPT Controller 40A', 1),
                ('DC Cable 10m', 2),
                ('Mounting Structure', 1),
            ]
            for prod_name, qty in bundle_items_data:
                if prod_name in products:
                    BundleItem.objects.get_or_create(
                        bundle=bundle,
                        product=products[prod_name],
                        defaults={'quantity': qty, 'is_optional': False}
                    )

            # Payment Methods
            payment_methods = {}
            pm_data = [
                ('Cash', None, None),
                ('KPay', 'KPay Account', '09123456789'),
                ('WaveMoney', 'Wave Account', '09234567890'),
                ('Bank Transfer', 'AYA Bank', '1234567890'),
            ]
            for pm_name, account_name, account_number in pm_data:
                pm, _ = PaymentMethod.objects.get_or_create(
                    name=pm_name,
                    defaults={
                        'account_name': account_name or '',
                        'account_number': account_number or '',
                        'is_active': True,
                        'display_order': len(payment_methods)
                    }
                )
                payment_methods[pm_name] = pm

        self.log('✅', 3, f'Created {len(products)} products, 1 bundle, {len(payment_methods)} payment methods')

        if delay > 0:
            time.sleep(delay)

        # DAY 3-4: STOCK INBOUND
        self.log('📥', 4, 'Stock Inbound - Assigning to Main Warehouse')
        with transaction.atomic():
            serial_prefixes = {
                'Monocrystalline Panel 400W': 'PNL',
                'Lithium Battery 100Ah': 'BAT',
                'Hybrid Inverter 3KW': 'INV',
            }
            
            for prod_name, product in products.items():
                if product.is_serial_tracked:
                    qty = 50 if 'Panel' in prod_name else 30
                    prefix = serial_prefixes.get(prod_name, 'SN')
                    for i in range(qty):
                        serial_no = f"SN-{prefix}-2024-{i+1:03d}"
                        SerialItem.objects.get_or_create(
                            serial_number=serial_no,
                            defaults={
                                'product': product,
                                'status': 'in_stock',
                                'current_location': main_warehouse
                            }
                        )
                    
                    # Create inbound movement
                    InventoryMovement.objects.create(
                        product=product,
                        quantity=qty,
                        movement_type='inbound',
                        to_location=main_warehouse,
                        moved_by=owner
                    )
                else:
                    # Non-serial products
                    qty = 100
                    InventoryMovement.objects.create(
                        product=product,
                        quantity=qty,
                        movement_type='inbound',
                        to_location=main_warehouse,
                        moved_by=owner
                    )

        self.log('✅', 4, 'Stock inbound completed with serial numbers')

        if delay > 0:
            time.sleep(delay)

        # DAY 5: FIRST CUSTOMERS
        self.log('👥', 5, 'Creating First Customers')
        customers_data = [
            ('ဦးအောင်မြင့်', '09123456789'),
            ('ဒေါ်ခင်ခင်ဝင်း', '09234567890'),
            ('ဦးသန်းထွန်း', '09345678901'),
            ('ဒေါ်မြမြဦး', '09456789012'),
            ('ဦးလှမြင့်', '09567890123'),
        ]
        customers = {}
        with transaction.atomic():
            for name, phone in customers_data:
                customer, _ = Customer.objects.get_or_create(
                    phone_number=phone,
                    defaults={'name': name, 'preferred_branch': shop_floor}
                )
                customers[name] = customer

        self.log('✅', 5, f'Created {len(customers)} customers')

        if delay > 0:
            time.sleep(delay)

        # DAY 5-7: FIRST SALES WEEK
        sale_staff_1 = staff_users.get('sale_staff_1', owner)
        sale_supervisor = staff_users.get('sale_supervisor', owner)
        
        # Sale 1: Single Panel x2 + Battery x1
        self.log('💰', 5, 'Sale 1: Panel x2 + Battery x1')
        with transaction.atomic():
            customer_1 = list(customers.values())[0]
            sale1 = SaleTransaction.objects.create(
                customer=customer_1,
                staff=sale_staff_1,
                sale_location=shop_floor,
                total_amount=Decimal('0'),
                status='pending',
                payment_method=payment_methods['KPay'],
                payment_status='completed'
            )
            
            panel = products['Monocrystalline Panel 400W']
            battery = products['Lithium Battery 100Ah']
            
            # Sale Items
            SaleItem.objects.create(
                sale_transaction=sale1,
                product=panel,
                quantity=2,
                unit_price=panel.retail_price,
                subtotal=panel.retail_price * 2
            )
            SaleItem.objects.create(
                sale_transaction=sale1,
                product=battery,
                quantity=1,
                unit_price=battery.retail_price,
                subtotal=battery.retail_price
            )
            
            sale1.total_amount = (panel.retail_price * 2) + battery.retail_price
            sale1.save()
            
            # Approve sale
            sale1.status = 'approved'
            sale1.approved_by = sale_supervisor
            sale1.approved_at = start_date + timedelta(days=5, hours=10)
            sale1.save()
            
            # Assign serial numbers
            # Note: SerialItem has OneToOneField with SaleTransaction (model limitation)
            # We'll mark serials as sold but not link them directly to avoid constraint violation
            # In real system, serials are tracked through SaleItem serial_number field
            panel_serials = SerialItem.objects.filter(
                product=panel,
                status='in_stock',
                current_location=main_warehouse
            )[:2]
            for serial in panel_serials:
                serial.status = 'sold'
                serial.current_location = None
                # Don't set sale_transaction due to OneToOne constraint
                serial.save()
                
                # Create warranty record (can link to sale_transaction)
                if panel.warranty_months > 0:
                    WarrantyRecord.objects.create(
                        serial_item=serial,
                        product=panel,
                        sale_transaction=sale1,
                        warranty_start_date=sale1.approved_at.date(),
                        warranty_end_date=(sale1.approved_at.date() + timedelta(days=panel.warranty_months * 30))
                    )
            
            battery_serial = SerialItem.objects.filter(
                product=battery,
                status='in_stock',
                current_location=main_warehouse
            ).first()
            if battery_serial:
                battery_serial.status = 'sold'
                battery_serial.current_location = None
                # Don't set sale_transaction due to OneToOne constraint
                battery_serial.save()
                
                if battery.warranty_months > 0:
                    WarrantyRecord.objects.create(
                        serial_item=battery_serial,
                        product=battery,
                        sale_transaction=sale1,
                        warranty_start_date=sale1.approved_at.date(),
                        warranty_end_date=(sale1.approved_at.date() + timedelta(days=battery.warranty_months * 30))
                    )
            
            # Stock outbound
            InventoryMovement.objects.create(
                product=panel,
                quantity=2,
                movement_type='outbound',
                from_location=shop_floor,
                sale_transaction=sale1,
                moved_by=sale_supervisor
            )
            InventoryMovement.objects.create(
                product=battery,
                quantity=1,
                movement_type='outbound',
                from_location=shop_floor,
                sale_transaction=sale1,
                moved_by=sale_supervisor
            )
            
            # Create Transaction record
            Transaction.objects.create(
                transaction_type='income',
                sale_transaction=sale1,
                amount=sale1.total_amount,
                transaction_date=sale1.approved_at.date()
            )

        self.log('✅', 5, 'Sale 1 completed with serial assignment')

        if delay > 0:
            time.sleep(delay)

        # Sale 2: Bundle "3KW Home Solar System"
        self.log('💰', 6, 'Sale 2: Bundle "3KW Home Solar System"')
        with transaction.atomic():
            customer_2 = list(customers.values())[1]
            sale2 = SaleTransaction.objects.create(
                customer=customer_2,
                staff=sale_staff_1,
                sale_location=shop_floor,
                total_amount=Decimal('0'),
                status='pending',
                payment_method=payment_methods['Bank Transfer'],
                payment_status='completed'
            )
            
            bundle_total = Decimal('0')
            for bundle_item in bundle.items.all():
                product = bundle_item.product
                qty = bundle_item.quantity
                unit_price = product.retail_price
                subtotal = unit_price * qty
                SaleItem.objects.create(
                    sale_transaction=sale2,
                    product=product,
                    quantity=qty,
                    unit_price=unit_price,
                    subtotal=subtotal
                )
                bundle_total += subtotal
            
            # Apply bundle discount
            discount = bundle_total * (bundle.discount_value / 100)
            sale2.discount_amount = discount
            sale2.total_amount = bundle_total - discount
            sale2.save()
            
            # Approve sale
            sale2.status = 'approved'
            sale2.approved_by = sale_supervisor
            sale2.approved_at = start_date + timedelta(days=6, hours=14)
            sale2.save()
            
            # Assign serials for bundle items
            for bundle_item in bundle.items.all():
                product = bundle_item.product
                if product.is_serial_tracked:
                    qty = bundle_item.quantity
                    serials = SerialItem.objects.filter(
                        product=product,
                        status='in_stock',
                        current_location=main_warehouse
                    )[:qty]
                    for serial in serials:
                        serial.status = 'sold'
                        serial.current_location = None
                        # Don't set sale_transaction due to OneToOne constraint
                        serial.save()
                        
                        if product.warranty_months > 0:
                            WarrantyRecord.objects.create(
                                serial_item=serial,
                                product=product,
                                sale_transaction=sale2,
                                warranty_start_date=sale2.approved_at.date(),
                                warranty_end_date=(sale2.approved_at.date() + timedelta(days=product.warranty_months * 30))
                            )
                
                # Stock outbound
                InventoryMovement.objects.create(
                    product=product,
                    quantity=bundle_item.quantity,
                    movement_type='outbound',
                    from_location=shop_floor,
                    sale_transaction=sale2,
                    moved_by=sale_supervisor
                )
            
            # Create Transaction record
            Transaction.objects.create(
                transaction_type='income',
                sale_transaction=sale2,
                amount=sale2.total_amount,
                transaction_date=sale2.approved_at.date()
            )
            
            # Create Installation Job for bundle
            technician_1 = staff_users.get('technician_1', owner)
            installation_job = InstallationJob.objects.create(
                sale_transaction=sale2,
                customer=customer_2,
                installation_address='123 Main Street, Yangon',
                installation_date=(start_date + timedelta(days=10)).date(),
                technician=technician_1,
                status='pending',
                created_by=sale_staff_1
            )

        self.log('✅', 6, 'Sale 2 completed - Bundle sold, Installation Job created')

        if delay > 0:
            time.sleep(delay)

        # Sale 3: Accessories (no serial tracking)
        self.log('💰', 7, 'Sale 3: Accessories (Cash)')
        with transaction.atomic():
            customer_3 = list(customers.values())[2]
            sale3 = SaleTransaction.objects.create(
                customer=customer_3,
                staff=sale_staff_1,
                sale_location=shop_floor,
                total_amount=Decimal('0'),
                status='pending',
                payment_method=payment_methods['Cash'],
                payment_status='completed'
            )
            
            cable = products['DC Cable 10m']
            SaleItem.objects.create(
                sale_transaction=sale3,
                product=cable,
                quantity=3,
                unit_price=cable.retail_price,
                subtotal=cable.retail_price * 3
            )
            
            sale3.total_amount = cable.retail_price * 3
            sale3.status = 'approved'
            sale3.approved_by = sale_supervisor
            sale3.approved_at = start_date + timedelta(days=7, hours=11)
            sale3.save()
            
            InventoryMovement.objects.create(
                product=cable,
                quantity=3,
                movement_type='outbound',
                from_location=shop_floor,
                sale_transaction=sale3,
                moved_by=sale_supervisor
            )
            
            # Create Transaction record
            Transaction.objects.create(
                transaction_type='income',
                sale_transaction=sale3,
                amount=sale3.total_amount,
                transaction_date=sale3.approved_at.date()
            )

        self.log('✅', 7, 'Sale 3 completed')

        if delay > 0:
            time.sleep(delay)

        # DAY 8: USD RATE CHANGE (+2%)
        self.log('💵', 8, 'USD Rate Change: 3450 -> 3520 MMK (+2%)')
        new_rate = Decimal('3520.0000')
        rate_date = (start_date + timedelta(days=8)).date()
        
        ExchangeRateLog.objects.get_or_create(
            date=rate_date,
            defaults={'rate': new_rate}
        )
        GlobalSetting.objects.update_or_create(
            key='usd_exchange_rate',
            defaults={'value_decimal': new_rate}
        )
        
        # Reprice all USD-priced products
        usd_products = Product.objects.filter(price_type='DYNAMIC_USD')
        repriced_count = 0
        for product in usd_products:
            if product.cost_usd:
                old_price = product.retail_price
                product.retail_price = product.cost_usd * new_rate * (1 + product.markup_percentage / 100)
                product.save()
                repriced_count += 1
                
                # Log repricing in InventoryMovement
                InventoryMovement.objects.create(
                    product=product,
                    quantity=0,
                    movement_type='adjustment',
                    notes=f'USD rate change: {usd_rate} -> {new_rate} MMK (+2%). Price updated from {old_price:,.0f} to {product.retail_price:,.0f}',
                    moved_by=owner
                )
        
        # Create notification for manager
        Notification.objects.create(
            recipient=manager_user,
            message=f'USD exchange rate changed: {usd_rate} -> {new_rate} MMK. {repriced_count} products repriced automatically.',
            notification_type='exchange_rate_change'
        )
        
        self.log('✅', 8, f'All {repriced_count} USD products repriced. Notification sent to manager.')

        if delay > 0:
            time.sleep(delay)

        # DAY 10-14: INSTALLATION WEEK
        self.log('🔧', 10, 'Installation Week - Job 1 Progress')
        installation_job = InstallationJob.objects.filter(sale_transaction__invoice_number=sale2.invoice_number).first()
        
        if installation_job:
            with transaction.atomic():
                # Status: pending → surveying (Day 10)
                installation_job.status = 'pending'  # Keep as pending, add notes for surveying
                installation_job.notes = 'Site survey completed. Ready for scheduling.'
                installation_job.save()
                InstallationStatusHistory.objects.create(
                    installation_job=installation_job,
                    old_status='pending',
                    new_status='pending',
                    notes='Site survey completed',
                    updated_by=installation_job.technician
                )
                
                self.log('🔧', 10, 'Installation Job 1: Site Survey Completed')
                
                # Status: scheduled (Day 11)
                installation_job.installation_date = (start_date + timedelta(days=12)).date()
                installation_job.save()
                InstallationStatusHistory.objects.create(
                    installation_job=installation_job,
                    old_status='pending',
                    new_status='pending',
                    notes='Installation scheduled',
                    updated_by=installation_job.technician
                )
                
                self.log('🔧', 11, 'Installation Job 1: Scheduled')
                
                # Status: in_progress (Day 12)
                installation_job.status = 'in_progress'
                installation_job.save()
                InstallationStatusHistory.objects.create(
                    installation_job=installation_job,
                    old_status='pending',
                    new_status='in_progress',
                    notes='Installation started',
                    updated_by=installation_job.technician
                )
                
                self.log('🔧', 12, 'Installation Job 1: In Progress')
                
                # Status: completed (Day 14)
                completion_date = start_date + timedelta(days=14)
                installation_job.status = 'completed'
                installation_job.completed_at = completion_date
                installation_job.save()
                InstallationStatusHistory.objects.create(
                    installation_job=installation_job,
                    old_status='in_progress',
                    new_status='completed',
                    notes='Installation completed successfully',
                    updated_by=installation_job.technician
                )
                
                # Warranty sync: Update warranty start dates
                # Manually sync warranty dates for completed installation
                synced_count = 0
                sale = installation_job.sale_transaction
                if sale and sale.status == 'approved':
                    from inventory.models import SaleItem, SerialItem, WarrantyRecord
                    today = completion_date.date()
                    sale_items = SaleItem.objects.filter(sale_transaction=sale)
                    for sale_item in sale_items:
                        product = sale_item.product
                        if product.is_serial_tracked and product.warranty_months > 0:
                            serial_items = SerialItem.objects.filter(
                                sale_transaction=sale,
                                product=product,
                                status='sold'
                            )
                            for serial_item in serial_items:
                                warranty_end_date = None
                                if product.warranty_months:
                                    warranty_end_date = today + timedelta(days=product.warranty_months * 30)
                                warranty_record, created = WarrantyRecord.objects.get_or_create(
                                    serial_item=serial_item,
                                    defaults={
                                        'product': product,
                                        'sale_transaction': sale,
                                        'warranty_start_date': today,
                                        'warranty_end_date': warranty_end_date
                                    }
                                )
                                if not created:
                                    warranty_record.warranty_start_date = today
                                    warranty_record.warranty_end_date = warranty_end_date
                                    warranty_record.save()
                                synced_count += 1
                
                # Add installation fee as Transaction (income, not expense)
                # Installation fee is added as income transaction
                installation_fee_amount = Decimal('150000')  # 150 USD * 1000 MMK approx
                Transaction.objects.create(
                    transaction_type='income',
                    sale_transaction=None,  # Not linked to a sale, it's a service fee
                    amount=installation_fee_amount,
                    transaction_date=completion_date.date()
                )
                
                self.log('✅', 14, f'Installation Job 1 completed, {synced_count} warranties synced. Installation fee recorded.')

        if delay > 0:
            time.sleep(delay)

        # DAY 12-13: MORE SALES
        self.log('💰', 12, 'More Sales: Sale 4 & 5')
        with transaction.atomic():
            # Sale 4: Panel x4
            customer_4 = list(customers.values())[3]
            sale4 = SaleTransaction.objects.create(
                customer=customer_4,
                staff=sale_staff_1,
                sale_location=shop_floor,
                total_amount=panel.retail_price * 4,
                status='approved',
                approved_by=sale_supervisor,
                approved_at=start_date + timedelta(days=12, hours=15),
                payment_method=payment_methods['KPay'],
                payment_status='completed'
            )
            SaleItem.objects.create(
                sale_transaction=sale4,
                product=panel,
                quantity=4,
                unit_price=panel.retail_price,
                subtotal=panel.retail_price * 4
            )
            
            # Assign serials for Sale 4
            panel_serials_4 = SerialItem.objects.filter(
                product=panel,
                status='in_stock',
                current_location=main_warehouse
            )[:4]
            for serial in panel_serials_4:
                serial.status = 'sold'
                serial.current_location = None
                serial.save()
                if panel.warranty_months > 0:
                    WarrantyRecord.objects.create(
                        serial_item=serial,
                        product=panel,
                        sale_transaction=sale4,
                        warranty_start_date=sale4.approved_at.date(),
                        warranty_end_date=(sale4.approved_at.date() + timedelta(days=panel.warranty_months * 30))
                    )
            
            # Stock outbound for Sale 4
            InventoryMovement.objects.create(
                product=panel,
                quantity=4,
                movement_type='outbound',
                from_location=shop_floor,
                sale_transaction=sale4,
                moved_by=sale_supervisor
            )
            
            # Create Transaction for Sale 4
            Transaction.objects.create(
                transaction_type='income',
                sale_transaction=sale4,
                amount=sale4.total_amount,
                transaction_date=sale4.approved_at.date()
            )
            
            # Sale 5: Inverter + Controller
            customer_5 = list(customers.values())[4]
            inverter = products['Hybrid Inverter 3KW']
            controller = products['MPPT Controller 40A']
            sale5 = SaleTransaction.objects.create(
                customer=customer_5,
                staff=sale_staff_1,
                sale_location=shop_floor,
                total_amount=(inverter.retail_price + controller.retail_price),
                status='approved',
                approved_by=sale_supervisor,
                approved_at=start_date + timedelta(days=13, hours=10),
                payment_method=payment_methods['WaveMoney'],
                payment_status='completed'
            )
            SaleItem.objects.create(
                sale_transaction=sale5,
                product=inverter,
                quantity=1,
                unit_price=inverter.retail_price,
                subtotal=inverter.retail_price
            )
            SaleItem.objects.create(
                sale_transaction=sale5,
                product=controller,
                quantity=1,
                unit_price=controller.retail_price,
                subtotal=controller.retail_price
            )
            
            # Assign serial for inverter
            inverter_serial = SerialItem.objects.filter(
                product=inverter,
                status='in_stock',
                current_location=main_warehouse
            ).first()
            if inverter_serial:
                inverter_serial.status = 'sold'
                inverter_serial.current_location = None
                inverter_serial.save()
                if inverter.warranty_months > 0:
                    WarrantyRecord.objects.create(
                        serial_item=inverter_serial,
                        product=inverter,
                        sale_transaction=sale5,
                        warranty_start_date=sale5.approved_at.date(),
                        warranty_end_date=(sale5.approved_at.date() + timedelta(days=inverter.warranty_months * 30))
                    )
            
            # Stock outbound for Sale 5
            InventoryMovement.objects.create(
                product=inverter,
                quantity=1,
                movement_type='outbound',
                from_location=shop_floor,
                sale_transaction=sale5,
                moved_by=sale_supervisor
            )
            InventoryMovement.objects.create(
                product=controller,
                quantity=1,
                movement_type='outbound',
                from_location=shop_floor,
                sale_transaction=sale5,
                moved_by=sale_supervisor
            )
            
            # Create Transaction for Sale 5
            Transaction.objects.create(
                transaction_type='income',
                sale_transaction=sale5,
                amount=sale5.total_amount,
                transaction_date=sale5.approved_at.date()
            )

        self.log('✅', 13, 'Sales 4 & 5 completed')
        
        # Sale 6: Monitoring module (Day 13)
        self.log('💰', 13, 'Sale 6: Monitoring Module (Cash, Walk-in)')
        with transaction.atomic():
            monitoring = products['WiFi Monitoring Module']
            sale6 = SaleTransaction.objects.create(
                customer=None,  # Walk-in customer
                staff=sale_staff_1,
                sale_location=shop_floor,
                total_amount=monitoring.retail_price,
                status='approved',
                approved_by=sale_supervisor,
                approved_at=start_date + timedelta(days=13, hours=16),
                payment_method=payment_methods['Cash'],
                payment_status='cash'
            )
            SaleItem.objects.create(
                sale_transaction=sale6,
                product=monitoring,
                quantity=1,
                unit_price=monitoring.retail_price,
                subtotal=monitoring.retail_price
            )
            InventoryMovement.objects.create(
                product=monitoring,
                quantity=1,
                movement_type='outbound',
                from_location=shop_floor,
                sale_transaction=sale6,
                moved_by=sale_supervisor
            )
            Transaction.objects.create(
                transaction_type='income',
                sale_transaction=sale6,
                amount=sale6.total_amount,
                transaction_date=sale6.approved_at.date()
            )
        
        self.log('✅', 13, 'Sale 6 completed')

        if delay > 0:
            time.sleep(delay)

        # DAY 15: EXPENSE RECORDING
        self.log('📊', 15, 'Recording Monthly Expenses')
        with transaction.atomic():
            expense_categories = {}
            cat_names = ['Rent', 'Utilities', 'Staff', 'Transport', 'Marketing']
            for cat_name in cat_names:
                cat, _ = ExpenseCategory.objects.get_or_create(name=cat_name)
                expense_categories[cat_name] = cat
            
            expenses_data = [
                ('Rent', 'Shop rent - January', Decimal('800000')),
                ('Utilities', 'Electricity bill', Decimal('150000')),
                ('Transport', 'Staff transport allowance', Decimal('200000')),
                ('Marketing', 'Facebook ads campaign', Decimal('100000')),
            ]
            
            expense_date = (start_date + timedelta(days=15)).date()
            for cat_name, desc, amount in expenses_data:
                expense = Expense.objects.create(
                    category=expense_categories[cat_name],
                    description=desc,
                    amount=amount,
                    expense_date=expense_date,
                    created_by=owner
                )
                # Create Transaction record for each expense
                Transaction.objects.create(
                    transaction_type='expense',
                    expense=expense,
                    amount=-abs(amount),  # Negative for expenses
                    transaction_date=expense_date
                )

        self.log('✅', 15, f'Recorded {len(expenses_data)} expenses with Transaction records')

        if delay > 0:
            time.sleep(delay)

        # DAY 16: WARRANTY CLAIM
        self.log('🔧', 16, 'Warranty Claim - Repair Service')
        with transaction.atomic():
            # Customer returns from Sale 1
            warranty_serial = WarrantyRecord.objects.filter(
                sale_transaction=sale1
            ).first()
            
            if warranty_serial:
                repair = RepairService.objects.create(
                    customer=customer_1,
                    item_name=f"Panel {warranty_serial.serial_item.serial_number}",
                    problem_description='Not charging properly',
                    location=service_area,
                    labour_cost=Decimal('50000'),
                    total_estimated_cost=Decimal('75000'),
                    deposit_amount=Decimal('0'),
                    status='received',
                    return_date=(start_date + timedelta(days=20)).date(),
                    staff=staff_users.get('technician_1', owner)
                )
                
                # Add spare parts
                RepairSparePart.objects.create(
                    repair_service=repair,
                    part_name='Thermal paste',
                    quantity=1,
                    unit_price=Decimal('10000'),
                    subtotal=Decimal('10000')
                )
                RepairSparePart.objects.create(
                    repair_service=repair,
                    part_name='Connector replacement',
                    quantity=2,
                    unit_price=Decimal('7500'),
                    subtotal=Decimal('15000')
                )
                
                # Status history
                RepairStatusHistory.objects.create(
                    repair_service=repair,
                    old_status='',
                    new_status='received',
                    updated_by=staff_users.get('technician_1', owner)
                )
                
                repair.status = 'fixing'
                repair.save()
                RepairStatusHistory.objects.create(
                    repair_service=repair,
                    old_status='received',
                    new_status='fixing',
                    updated_by=staff_users.get('technician_1', owner)
                )
                
                repair.status = 'ready'
                repair.save()
                RepairStatusHistory.objects.create(
                    repair_service=repair,
                    old_status='fixing',
                    new_status='ready',
                    updated_by=staff_users.get('technician_1', owner)
                )

        self.log('✅', 16, 'Warranty repair completed')

        if delay > 0:
            time.sleep(delay)

        # DAY 18: USD RATE DROP
        self.log('💵', 18, 'USD Rate Drop: 3520 -> 3490 MMK')
        new_rate_2 = Decimal('3490.0000')
        rate_date_2 = (start_date + timedelta(days=18)).date()
        
        ExchangeRateLog.objects.get_or_create(
            date=rate_date_2,
            defaults={'rate': new_rate_2}
        )
        GlobalSetting.objects.update_or_create(
            key='usd_exchange_rate',
            defaults={'value_decimal': new_rate_2}
        )
        
        # Reprice products again
        repriced_count_2 = 0
        for product in usd_products:
            if product.cost_usd:
                old_price = product.retail_price
                product.retail_price = product.cost_usd * new_rate_2 * (1 + product.markup_percentage / 100)
                product.save()
                repriced_count_2 += 1
                
                # Log repricing
                InventoryMovement.objects.create(
                    product=product,
                    quantity=0,
                    movement_type='adjustment',
                    notes=f'USD rate change: {new_rate} -> {new_rate_2} MMK (-0.85%). Price updated from {old_price:,.0f} to {product.retail_price:,.0f}',
                    moved_by=owner
                )
        
        # Create notification for manager
        Notification.objects.create(
            recipient=manager_user,
            message=f'USD exchange rate changed: {new_rate} -> {new_rate_2} MMK. {repriced_count_2} products repriced automatically.',
            notification_type='exchange_rate_change'
        )

        self.log('✅', 18, f'Products repriced again. Notification sent to manager.')

        if delay > 0:
            time.sleep(delay)

        # DAY 19-20: STOCK TRANSFER
        self.log('📦', 19, 'Stock Transfer: Warehouse -> Shop Floor')
        with transaction.atomic():
            transfer_products = [panel, battery, inverter]
            for product in transfer_products:
                qty = 10
                InventoryMovement.objects.create(
                    product=product,
                    quantity=qty,
                    movement_type='transfer',
                    from_location=main_warehouse,
                    to_location=shop_floor,
                    moved_by=staff_users.get('inventory_manager', owner)
                )
                
                # Update serial locations
                if product.is_serial_tracked:
                    serials = SerialItem.objects.filter(
                        product=product,
                        status='in_stock',
                        current_location=main_warehouse
                    )[:qty]
                    for serial in serials:
                        serial.current_location = shop_floor
                        serial.save()

        self.log('✅', 20, 'Stock transfer completed')

        if delay > 0:
            time.sleep(delay)

        # DAY 21-25: MORE SALES & REPAIRS
        self.log('💰', 21, 'More Sales: Sales 7-10')
        with transaction.atomic():
            for day_offset in [21, 22, 23, 24]:
                customer = random.choice(list(customers.values()))
                product = random.choice(list(products.values()))
                sale = SaleTransaction.objects.create(
                    customer=customer,
                    staff=sale_staff_1,
                    sale_location=shop_floor,
                    total_amount=product.retail_price * random.randint(1, 3),
                    status='approved',
                    approved_by=sale_supervisor,
                    approved_at=start_date + timedelta(days=day_offset, hours=random.randint(9, 17)),
                    payment_method=random.choice(list(payment_methods.values())),
                    payment_status='completed'
                )
                SaleItem.objects.create(
                    sale_transaction=sale,
                    product=product,
                    quantity=random.randint(1, 3),
                    unit_price=product.retail_price,
                    subtotal=product.retail_price * random.randint(1, 3)
                )
        
        # Repair 2: Out of warranty
        self.log('🔧', 23, 'Repair 2: Out of Warranty (Walk-in)')
        with transaction.atomic():
            repair2 = RepairService.objects.create(
                customer=random.choice(list(customers.values())),
                item_name='Old Solar Panel',
                problem_description='Out of warranty repair',
                location=service_area,
                labour_cost=Decimal('80000'),
                total_estimated_cost=Decimal('120000'),
                deposit_amount=Decimal('50000'),
                is_deposit_paid=True,
                status='fixing',
                return_date=(start_date + timedelta(days=28)).date(),
                staff=staff_users.get('technician_2', owner)
            )

        self.log('✅', 25, 'Sales 7-10 and Repair 2 completed')

        if delay > 0:
            time.sleep(delay)

        # DAY 26-28: SECOND INSTALLATION
        self.log('🔧', 26, 'Second Installation Job')
        with transaction.atomic():
            # Create Sale 11 with bundle
            customer_new = random.choice(list(customers.values()))
            sale11 = SaleTransaction.objects.create(
                customer=customer_new,
                staff=sale_staff_1,
                sale_location=shop_floor,
                total_amount=Decimal('0'),
                status='pending',
                payment_method=payment_methods['Bank Transfer'],
                payment_status='completed'
            )
            
            bundle_total_2 = Decimal('0')
            for bundle_item in bundle.items.all():
                product = bundle_item.product
                qty = bundle_item.quantity
                SaleItem.objects.create(
                    sale_transaction=sale11,
                    product=product,
                    quantity=qty,
                    unit_price=product.retail_price,
                    subtotal=product.retail_price * qty
                )
                bundle_total_2 += product.retail_price * qty
            
            discount_2 = bundle_total_2 * (bundle.discount_value / 100)
            sale11.discount_amount = discount_2
            sale11.total_amount = bundle_total_2 - discount_2
            sale11.status = 'approved'
            sale11.approved_by = sale_supervisor
            sale11.approved_at = start_date + timedelta(days=26, hours=10)
            sale11.save()
            
            # Create Installation Job 2
            technician_2 = staff_users.get('technician_2', owner)
            installation_job_2 = InstallationJob.objects.create(
                sale_transaction=sale11,
                customer=customer_new,
                installation_address='456 Second Street, Mandalay',
                installation_date=(start_date + timedelta(days=28)).date(),
                technician=technician_2,
                status='pending',
                created_by=sale_staff_1
            )
            
            # Complete installation
            installation_job_2.status = 'completed'
            installation_job_2.completed_at = start_date + timedelta(days=28)
            installation_job_2.save()
            InstallationStatusHistory.objects.create(
                installation_job=installation_job_2,
                old_status='pending',
                new_status='completed',
                updated_by=technician_2
            )

        self.log('✅', 28, 'Installation Job 2 completed')

        if delay > 0:
            time.sleep(delay)

        # DAY 29-30: MONTH END REPORTS
        self.log('📊', 29, 'Month End: Generating Reports')
        
        # P&L Report
        try:
            from accounting.services import calculate_net_profit, calculate_profit_from_sales
            from django.db.models import Sum
            end_date = (start_date + timedelta(days=30)).date()
            pl_data = calculate_net_profit(start_date.date(), end_date)
            sales_profit = calculate_profit_from_sales(start_date.date(), end_date)
            self.log('   ', 29, f'  Net Profit: {pl_data["net_profit"]:,.0f} MMK')
            self.log('   ', 29, f'  Gross Profit: {sales_profit["gross_profit"]:,.0f} MMK')
        except Exception as e:
            self.log('   ', 29, f'P&L calculation skipped: {e}')
        
        # Trigger AI Insights (log that it should be called via API)
        self.log('🤖', 30, 'AI Insights: Triggering smart business insights')
        try:
            # Note: In real system, this would call /api/ai/insights/
            # For simulation, we just log that it should be triggered
            self.log('   ', 30, '  AI Insights endpoint: GET /api/ai/insights/')
            self.log('   ', 30, '  Best Sellers endpoint: GET /api/ai/best-sellers/')
            self.log('   ', 30, '  Sale Tips endpoint: GET /api/ai/sale-auto-tips/')
        except Exception as e:
            self.log('   ', 30, f'AI insights trigger skipped: {e}')
        
        # Sales Report
        total_sales_count = SaleTransaction.objects.filter(
            status='approved',
            approved_at__gte=start_date,
            approved_at__lte=start_date + timedelta(days=30)
        ).count()
        
        from django.db.models import Sum
        total_revenue = SaleTransaction.objects.filter(
            status='approved',
            approved_at__gte=start_date,
            approved_at__lte=start_date + timedelta(days=30)
        ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
        
        # Inventory Report
        low_stock_products = []
        for product in Product.objects.all():
            stock = product.shop_floor_stock
            if stock < 10:
                low_stock_products.append(product.name)
        
        # Service Report
        total_repairs = RepairService.objects.filter(
            created_at__gte=start_date,
            created_at__lte=start_date + timedelta(days=30)
        ).count()
        
        total_installations = InstallationJob.objects.filter(
            created_at__gte=start_date,
            created_at__lte=start_date + timedelta(days=30)
        ).count()
        
        # Customer Report
        total_customers = Customer.objects.filter(
            created_at__gte=start_date,
            created_at__lte=start_date + timedelta(days=30)
        ).count()

        self.log('📊', 30, f'Month End Summary:')
        self.log('   ', 30, f'  Sales: {total_sales_count} transactions, {total_revenue:,.0f} MMK')
        self.log('   ', 30, f'  Repairs: {total_repairs}')
        self.log('   ', 30, f'  Installations: {total_installations}')
        self.log('   ', 30, f'  New Customers: {total_customers}')
        self.log('   ', 30, f'  Low Stock Items: {len(low_stock_products)}')

        # Save simulation log
        log_file = 'simulation_log.json'
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.simulation_log, f, indent=2, ensure_ascii=False, default=str)
        
        self.stdout.write(self.style.SUCCESS(f'\n[OK] Simulation completed! Log saved to {log_file}'))
        self.stdout.write(self.style.SUCCESS(f'Total actions: {len(self.simulation_log)}'))
