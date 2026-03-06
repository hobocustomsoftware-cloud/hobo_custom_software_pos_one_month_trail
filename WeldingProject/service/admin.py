from django.contrib import admin
from django.utils.html import format_html
from .models import RepairService, RepairSparePart, RepairStatusHistory


class RepairSparePartInline(admin.TabularInline):
    model = RepairSparePart
    extra = 1
    fields = ('product', 'part_name', 'quantity', 'unit_price', 'subtotal')
    readonly_fields = ('subtotal',)


class RepairStatusHistoryInline(admin.TabularInline):
    model = RepairStatusHistory
    extra = 0
    readonly_fields = ('old_status', 'new_status', 'notes', 'created_at', 'updated_by')
    can_delete = False


@admin.register(RepairService)
class RepairServiceAdmin(admin.ModelAdmin):
    # စာရင်းတွင် ပြသမည့် Column များ
    list_display = (
        'repair_no', 
        'customer_link', 
        'item_name', 
        'return_date', 
        'status_color', 
        'total_estimated_cost', 
        'deposit_amount',
        'balance_display',
        'is_customer_notified',
        'created_at', 
        'updated_at'
    )
    
    # ဘေးဘက်တွင် စစ်ထုတ်နိုင်မည့် Filter များ
    list_filter = ('status', 'received_date', 'return_date', 'is_customer_notified', 'staff', )
    
    # ရှာဖွေနိုင်မည့် Field များ
    search_fields = ('repair_no', 'item_name', 'customer__name', 'customer__phone_number')
    
    # ရက်စွဲအလိုက် အစီအစဉ်ချခြင်း
    date_hierarchy = 'received_date'
    
    # ပြင်ဆင်ရလွယ်အောင် ပုံစံချခြင်း
    readonly_fields = ('repair_no', 'received_date', 'balance_display')
    
    inlines = [RepairSparePartInline, RepairStatusHistoryInline]

    fieldsets = (
        ('အခြေခံအချက်အလက်', {
            'fields': (('repair_no', 'status'), 'customer', 'item_name', 'problem_description')
        }),
        ('ငွေကြေးပိုင်းဆိုင်ရာ', {
            'fields': (('labour_cost', 'total_estimated_cost', 'deposit_amount'), 'is_deposit_paid', 'balance_display')
        }),
        ('ရက်စွဲနှင့် ဝန်ထမ်း', {
            'fields': (('return_date', 'received_date'), 'staff', 'is_customer_notified')
        }),
    )

    # Customer Name ကို နှိပ်ရင် Customer Detail ဆီ သွားနိုင်အောင် Link လုပ်ခြင်း
    def customer_link(self, obj):
        return obj.customer.name
    customer_link.short_description = 'ဝယ်ယူသူ'

    # ကျန်ငွေကို အရောင်နဲ့ ပြသခြင်း
    def balance_display(self, obj):
        amount = obj.balance_amount
        # ကိန်းဂဏန်းကို format အရင်လုပ်ပါ (ဥပမာ - 1,500.00)
        formatted_amount = "{:,.2f}".format(amount)
        
        color = "red" if amount > 0 else "green"
        
        # format_html ထဲမှာ format code (f) ကို မသုံးဘဲ variable ကိုပဲ ထည့်ပါ
        return format_html(
            '<b style="color: {}; font-family: monospace;">{} Ks</b>', 
            color, 
            formatted_amount
        )
    balance_display.short_description = 'ကျန်ငွေ'

    # Status ကို အရောင်လေးတွေနဲ့ ခွဲခြားပြသခြင်း
    def status_color(self, obj):
        colors = {
            'received': '#f39c12',  # Orange
            'fixing': '#3498db',    # Blue
            'ready': '#2ecc71',     # Green
            'completed': '#27ae60', # Dark Green
            'cancelled': '#e74c3c', # Red
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.get_status_display()
        )
    status_color.short_description = 'အခြေအနေ'


@admin.register(RepairSparePart)
class RepairSparePartAdmin(admin.ModelAdmin):
    list_display = ('repair_service', 'part_name', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('repair_service',)


@admin.register(RepairStatusHistory)
class RepairStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ('repair_service', 'old_status', 'new_status', 'notes', 'created_at', 'updated_by')
    list_filter = ('new_status',)
    readonly_fields = ('repair_service', 'old_status', 'new_status', 'notes', 'created_at', 'updated_by')