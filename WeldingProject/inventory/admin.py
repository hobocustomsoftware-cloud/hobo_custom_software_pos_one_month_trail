from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import *

# ----------------------------------------------------
# 1. Category Admin (အသစ်ထည့်သွင်းသည်)
# ----------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'get_product_count')
    search_fields = ('name',)

    def get_product_count(self, obj):
        return obj.products.count()
    get_product_count.short_description = 'ပစ္စည်းအရေအတွက်'

# ----------------------------------------------------
# 2. Inline Models
# ----------------------------------------------------
class SerialItemInline(admin.TabularInline):
    model = SerialItem
    extra = 0
    readonly_fields = ('status',)  # serial_number ကို ပြင်လို့ရအောင် editable ထားသည်
    fields = ('serial_number', 'status', 'current_location')

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 1
    fields = ['product', 'quantity', 'unit_price', 'subtotal']
    readonly_fields = ['subtotal']

# ----------------------------------------------------
# 3. Product Admin (Category Filter ထည့်ထားသည်)
# ----------------------------------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'sku', 'model_no', 'stock_display', 'retail_price',
        'price_type', 'selling_price_mmk', 'base_unit', 'purchase_unit', 'purchase_unit_factor',
        'is_serial_tracked', 'serial_number_required', 'warranty_months',
    )
    search_fields = ('name', 'sku', 'model_no')
    list_filter = ('category', 'price_type', 'is_serial_tracked', 'serial_number_required')
    autocomplete_fields = ['category', 'base_unit', 'purchase_unit']
    filter_horizontal = ['tags']

    def stock_display(self, obj):
        return format_html(
            "<b>Total:</b> {} <br/> <small style='color:blue;'>Shop: {}</small>",
            obj.total_stock_qty,
            obj.shop_floor_stock
        )
    stock_display.short_description = 'လက်ကျန် (Total/Shop)'

    def get_inlines(self, request, obj=None):
        if obj and (obj.is_serial_tracked or obj.serial_number_required):
            return [SerialItemInline]
        return []

# ----------------------------------------------------
# 4. Sale Transaction Admin
# ----------------------------------------------------
@admin.register(SaleTransaction)
class SaleTransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'sale_location', 'customer', 'staff', 'get_total_display', 'status')
    list_filter = ('status', 'sale_location', 'created_at')
    inlines = [SaleItemInline] # ပစ္စည်းများကို Inline ပြရန်
    
    fieldsets = (
        ('Header Info', {
            'fields': ('invoice_number', 'sale_location', 'customer', 'staff')
        }),
        ('Financials', {
            'fields': ('total_amount', 'discount_amount')
        }),
        ('Approval Status', {
            'fields': ('status', 'reject_reason', 'approved_by', 'approved_at')
        }),
        ('Payment', {
            'fields': ('payment_method', 'payment_status', 'payment_proof_screenshot', 'payment_proof_uploaded_at')
        }),
    )
    readonly_fields = ('invoice_number', 'approved_by', 'approved_at', 'payment_proof_uploaded_at')

    def get_total_display(self, obj):
        return f"{obj.total_amount:,.0f} MMK"
    get_total_display.short_description = 'စုစုပေါင်း'

# ----------------------------------------------------
# 5. Serial Item Admin
# ----------------------------------------------------
@admin.register(SerialItem)
class SerialItemAdmin(admin.ModelAdmin):
    list_display = ('serial_number', 'product', 'status', 'sale_info_link')
    list_filter = ('status', 'product__category', 'product')
    search_fields = ('serial_number', 'product__name')
    readonly_fields = ('sale_transaction',)  # serial_number ပြင်လို့ရသည် (Auto-generate ပြင်ချင်လည်းပြင်လို့ရသည်)
    autocomplete_fields = ['product']

    def sale_info_link(self, obj):
        if obj.sale_transaction:
            try:
                url = reverse("admin:inventory_saletransaction_change", args=[obj.sale_transaction.id])
                return format_html('<a href="{}">{}</a>', url, obj.sale_transaction.invoice_number)
            except:
                return "Link Error"
        return "Available"
    sale_info_link.short_description = 'Voucher'

# ----------------------------------------------------
# 6. Core Inventory Admins
# ----------------------------------------------------
class LocationInline(admin.TabularInline):
    model = Location
    extra = 0
    fields = ('name', 'location_type', 'is_sale_location')


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'address')
    search_fields = ('name', 'code')
    inlines = [LocationInline]


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('name', 'site', 'location_type', 'is_sale_location')
    list_filter = ('site', 'location_type', 'is_sale_location')
    filter_horizontal = ('staff_assigned',)
    search_fields = ('name',)
    autocomplete_fields = ['site']

@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'movement_type', 'from_location', 'to_location', 'created_at')
    list_filter = ('movement_type', 'from_location', 'to_location')
    readonly_fields = ('created_at',)


class PurchaseLineInline(admin.TabularInline):
    model = PurchaseLine
    extra = 1
    autocomplete_fields = ['product', 'purchase_unit', 'to_location']


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'outlet', 'reference', 'purchase_date', 'created_by', 'created_at')
    list_filter = ('outlet', 'purchase_date')
    search_fields = ('reference', 'id')
    inlines = [PurchaseLineInline]
    readonly_fields = ('created_at',)
    autocomplete_fields = ['outlet', 'created_by']


@admin.register(PurchaseLine)
class PurchaseLineAdmin(admin.ModelAdmin):
    list_display = ('purchase', 'product', 'purchase_unit', 'quantity', 'unit_cost', 'to_location')
    list_filter = ('purchase', 'purchase_unit')
    autocomplete_fields = ['purchase', 'product', 'purchase_unit', 'to_location']


@admin.register(WarrantyRecord)
class WarrantyRecordAdmin(admin.ModelAdmin):
    list_display = ('serial_item', 'product', 'warranty_start_date', 'warranty_end_date', 'is_active_display')
    list_filter = ('warranty_end_date',)
    search_fields = ('serial_item__serial_number', 'product__name')
    readonly_fields = ('created_at',)

    def is_active_display(self, obj):
        from django.utils import timezone
        active = obj.warranty_end_date >= timezone.now().date()
        return format_html('<span style="color:{};">{}</span>', 'green' if active else 'red', 'Active' if active else 'Expired')
    is_active_display.short_description = 'အခြေအနေ'

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'message', 'is_read', 'created_at')
    list_editable = ('is_read',)
    list_filter = ('is_read', 'notification_type')


# ----------------------------------------------------
# 7. Product Bundling
# ----------------------------------------------------
class BundleItemInline(admin.TabularInline):
    model = BundleItem
    extra = 1
    autocomplete_fields = ['product']
    ordering = ['sort_order', 'id']


class BundleComponentInline(admin.TabularInline):
    model = BundleComponent
    extra = 0
    autocomplete_fields = ['product']
    ordering = ['sort_order', 'id']
    fields = ('product', 'min_qty', 'max_qty', 'default_qty', 'is_required', 'sort_order')


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'bundle_type', 'pricing_type', 'bundle_price', 'is_active', 'get_items_count')
    list_filter = ('is_active', 'bundle_type', 'pricing_type')
    search_fields = ('name', 'sku')
    inlines = [BundleItemInline, BundleComponentInline]
    fields = (
        'name', 'description', 'sku', 'bundle_type', 'bundle_price',
        'pricing_type', 'discount_type', 'discount_value', 'is_active',
    )

    def get_items_count(self, obj):
        return obj.items.count()
    get_items_count.short_description = 'ပစ္စည်းအရေအတွက်'


@admin.register(BundleItem)
class BundleItemAdmin(admin.ModelAdmin):
    list_display = ('bundle', 'product', 'quantity', 'is_optional', 'sort_order')
    list_filter = ('bundle', 'is_optional')
    autocomplete_fields = ['bundle', 'product']


@admin.register(BundleComponent)
class BundleComponentAdmin(admin.ModelAdmin):
    list_display = ('bundle', 'product', 'min_qty', 'max_qty', 'default_qty', 'is_required', 'sort_order')
    list_filter = ('bundle', 'is_required')
    autocomplete_fields = ['bundle', 'product']


@admin.register(ProductTag)
class ProductTagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('code', 'name_my', 'name_en', 'category', 'base_unit', 'factor_to_base', 'order')
    list_filter = ('category',)
    search_fields = ('code', 'name_my', 'name_en')
    ordering = ('category', 'order', 'name_en')


@admin.register(GlobalSetting)
class GlobalSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'value_decimal', 'market_premium_percentage', 'manual_fixed_rate')
    search_fields = ('key',)
    fieldsets = (
        ('Basic Settings', {
            'fields': ('key', 'value', 'value_decimal')
        }),
        ('Exchange Rate Adjustments', {
            'fields': ('market_premium_percentage', 'manual_fixed_rate'),
            'description': 'For exchange rate keys (e.g., usd_exchange_rate): Set Market Premium % to add markup (e.g., 10 = +10%), or set Manual Fixed Rate to override CBM rate completely.',
        }),
    )


@admin.register(ExchangeRateLog)
class ExchangeRateLogAdmin(admin.ModelAdmin):
    list_display = ('date', 'currency', 'rate', 'source', 'get_rate_display')
    list_filter = ('currency', 'source', 'date')
    search_fields = ('currency',)
    readonly_fields = ('date', 'currency', 'rate', 'source')
    ordering = ('-date', 'currency')
    date_hierarchy = 'date'

    def get_rate_display(self, obj):
        return f"{obj.rate:,.4f} MMK"
    get_rate_display.short_description = 'Rate'


# ----------------------------------------------------
# 8. Payment Method Admin
# ----------------------------------------------------
@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'account_name', 'account_number', 'is_active', 'display_order', 'qr_code_preview')
    list_filter = ('is_active',)
    search_fields = ('name', 'account_name', 'account_number')
    list_editable = ('is_active', 'display_order')
    
    def qr_code_preview(self, obj):
        if obj.qr_code_image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: contain;" />', obj.qr_code_image.url)
        return '-'
    qr_code_preview.short_description = 'QR Code'