import datetime
import re
from django.db import models
from core.models import User
from django.db.models import Sum, F, Value, IntegerField
from django.db.models.functions import Coalesce
from django.conf import settings
from customer.models import Customer
import random


def generate_unique_sku(name, exclude_product_id=None):
    """
    Product name ကနေ barcode/scanner နဲ့ အဆင်ပြေတဲ့ unique SKU ထုတ်ပေးသည်။
    Alphanumeric + hyphen only (CODE128 ဖတ်လို့ရမယ်)။ ပြင်ချင်ရင် product save ပြီးမှ ပြင်လို့ရသည်။
    """
    if not name or not str(name).strip():
        base = 'PROD'
    else:
        base = re.sub(r'[^A-Za-z0-9-]', '', str(name).replace(' ', '-').upper())
        base = (base[:30] or 'PROD')
    sku = base
    n = 1
    qs = Product.objects.all()
    if exclude_product_id:
        qs = qs.exclude(pk=exclude_product_id)
    while qs.filter(sku=sku).exists():
        suffix = f'-{n}'
        sku = (base[: 50 - len(suffix)] + suffix) if len(base) + len(suffix) > 50 else (base + suffix)
        n += 1
    return sku[:50]


class Category(models.Model):
    """Hierarchical Category model with parent-child relationships for Electronic & Machinery industry"""
    name = models.CharField(max_length=100, verbose_name="အမျိုးအစားအမည်")
    description = models.TextField(blank=True, null=True, verbose_name="အကြောင်းအရာ")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Parent Category"
    )
    order = models.IntegerField(default=0, verbose_name="Display Order")
    is_active = models.BooleanField(default=True, verbose_name="Active")

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} > {self.name}"
        return self.name

    @property
    def full_path(self):
        """Returns full category path (e.g., 'Electronics > Solar > Inverters')"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)

    def get_all_children(self):
        """Get all descendant categories recursively"""
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(child.get_all_children())
        return children

    class Meta:
        verbose_name = "ကုန်ပစ္စည်းအမျိုးအစား"
        verbose_name_plural = "ကုန်ပစ္စည်းအမျိုးအစားများ"
        ordering = ['order', 'name']
        unique_together = [['name', 'parent']]  # Same name allowed if different parent


class ProductTag(models.Model):
    """Compatibility / attribute tags (e.g. Socket-AM4, 48V-System) for configurator warnings."""
    name = models.CharField(max_length=80, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Unit(models.Model):
    """Common units for products (Myanmar + English), e.g. ပိဿာ/viss, တစ်လုံး/pcs.
    Conversion: base_unit + factor_to_base so stock can be normalized (e.g. 1 Viss = 100 Tical → 50 tical = 0.5 viss).
    """
    UNIT_CATEGORY_CHOICES = (
        ('mass', 'Mass'),
        ('packaging', 'Packaging'),
        ('count', 'Count'),
        ('length', 'Length'),
        ('volume', 'Volume'),
    )
    name_my = models.CharField(max_length=80, verbose_name="Myanmar name (မြန်မာအမည်)")
    name_en = models.CharField(max_length=80, verbose_name="English name")
    code = models.CharField(max_length=20, unique=True, db_index=True, verbose_name="Short code (e.g. VISS, PCS)")
    category = models.CharField(max_length=20, choices=UNIT_CATEGORY_CHOICES, db_index=True)
    order = models.PositiveIntegerField(default=0, verbose_name="Display order")
    # Conversion to a base unit (e.g. Tical → Viss: 1 tical = 0.01 viss)
    base_unit = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='converted_units',
        verbose_name="Base unit for conversion",
    )
    factor_to_base = models.DecimalField(
        max_digits=20,
        decimal_places=10,
        default=1,
        help_text="How many base units per 1 of this unit. E.g. 1 tical = 0.01 viss.",
        verbose_name="Factor to base unit",
    )

    def __str__(self):
        return f"{self.name_my} / {self.name_en} ({self.code})"

    def to_base_quantity(self, quantity):
        """Convert quantity in this unit to root base unit (e.g. 50 tical → 0.5 viss)."""
        from decimal import Decimal
        q = Decimal(str(quantity)) * self.factor_to_base
        if self.base_unit_id:
            return self.base_unit.to_base_quantity(q)
        return q

    def from_base_quantity(self, base_quantity):
        """Convert quantity from root base unit to this unit (e.g. 0.5 viss → 50 tical)."""
        from decimal import Decimal
        if self.base_unit_id:
            base_quantity = self.base_unit.from_base_quantity(base_quantity)
        return Decimal(str(base_quantity)) / self.factor_to_base if self.factor_to_base else base_quantity

    class Meta:
        ordering = ['category', 'order', 'name_en']
        verbose_name = "ယူနစ် (Unit)"
        verbose_name_plural = "ယူနစ်များ (Units)"


# ----------------- Product Model (Inventory) -----------------
class Product(models.Model):
    """ဂဟေဆော်ပစ္စည်းများ စာရင်း"""
    category = models.ForeignKey(
        Category, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='products',
        verbose_name="အမျိုးအစား"
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(
        max_length=50, unique=True, blank=True,
        verbose_name="SKU/Product ID (blank = auto from name)"
    )
    model_no = models.CharField(
        max_length=100, blank=True, null=True, db_index=True,
        verbose_name="Model No. (ရှာမယ်ဆိုရင် index သုံးမယ်)"
    )
    image = models.ImageField(upload_to='products/', 
                             null=True, blank=True, 
                             verbose_name="ပစ္စည်းပုံ")
    # 💥 stock_qty Field ကို လုံးဝ ဖြုတ်လိုက်ပါပြီ။
    #    Database Field မရှိတော့ပါ။

    retail_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="လက်လီဈေး")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="မူရင်းကုန်ကျစရိတ်")

    # USD-based pricing (for DYNAMIC_USD)
    cost_usd = models.DecimalField(
        max_digits=12, decimal_places=4, null=True, blank=True,
        verbose_name="Cost (USD)"
    )
    markup_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, default=0,
        verbose_name="Markup %"
    )
    PRICE_TYPE_CHOICES = (
        ('FIXED_MMK', 'Fixed MMK'),
        ('DYNAMIC_USD', 'Dynamic (USD + rate)'),
    )
    price_type = models.CharField(
        max_length=20, choices=PRICE_TYPE_CHOICES, default='FIXED_MMK',
        verbose_name="Price type"
    )
    selling_price_mmk = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="Selling price (MMK) – set manually or synced from USD"
    )

    # Serial Number ဖြင့် ခြေရာခံခြင်း ရှိ/မရှိ
    is_serial_tracked = models.BooleanField(default=False, verbose_name="Serial No. ဖြင့် ခြေရာခံမည်")
    serial_number_required = models.BooleanField(
        default=False,
        verbose_name="Serial number required (Inverter/Battery စသည့် တစ်ခုချင်း ခြေရာခံရမည်)"
    )

    # Warranty (လ) - Electronic ပစ္စည်းများအတွက် သက်တမ်း
    warranty_months = models.PositiveIntegerField(default=0, verbose_name="Warranty (လ)")

    # Pharmacy: ဆေးသက်တမ်းကုန်ရက် (သတ်မှတ်ထားရင် ကုန်ပြီးဆေးကို ရောင်းလို့မရ)
    expiry_date = models.DateField(null=True, blank=True, verbose_name="သက်တမ်းကုန်ရက် (ဆေး)")

    # Unit Management for Electronic & Machinery
    UNIT_TYPE_CHOICES = (
        ('PCS', 'Pieces'),
        ('CARD', 'Card'),
        ('SET', 'Sets'),
        ('MTR', 'Meters'),
        ('ROL', 'Rolls'),
        ('KG', 'Kilograms'),
        ('BOX', 'Boxes'),
        ('PKG', 'Packages'),
        ('UNT', 'Units'),
    )
    unit_type = models.CharField(
        max_length=10,
        choices=UNIT_TYPE_CHOICES,
        default='PCS',
        verbose_name="Unit Type"
    )

    # Bulk buy / retail sell: stock is stored in base_unit; can buy in purchase_unit and sell in any unit with conversion
    base_unit = models.ForeignKey(
        'Unit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_as_base',
        verbose_name="Base unit (stock stored in this unit)",
        help_text="e.g. Viss for chili; Feet for wire. All inventory quantities are in this unit.",
    )
    purchase_unit = models.ForeignKey(
        'Unit',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products_bought_in',
        verbose_name="Purchase unit (ဝယ်ယူသည့်ယူနစ်)",
        help_text="e.g. Bag (အိတ်), Roll (ခွေ). Leave blank if same as base.",
    )
    purchase_unit_factor = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        default=1,
        verbose_name="1 Purchase unit = X Base units",
        help_text="e.g. 1 Bag = 30 Viss → 30; 1 Roll = 90 Feet → 90.",
    )

    # Compatibility tags for bundle configurator (e.g. Socket-AM4, 48V-System)
    tags = models.ManyToManyField(ProductTag, related_name='products', blank=True, verbose_name="Compatibility tags")

    def __str__(self):
        # 💥 __str__ method ကို total_stock_qty property ကို သုံးရန် ပြင်ဆင်ပြီးသား
        return f"{self.name} (Total Stock: {self.total_stock_qty})" 
    
    # ----------------------------------------------------------------------
    # Stock Calculation Properties (Movement Model မှ တွက်ချက်သည်)
    # ----------------------------------------------------------------------
    
    # 💥 Property နာမည်ကို calculated_stock_qty သို့ ပြောင်းပြီး total_stock_qty ကို ခေါ်ယူစေပါမည်။
    @property
    def stock_qty(self):
        """
        Serializer များနှင့် View များတွင် stock_qty အစားခေါ်ယူရန် Property
        (Shop Floor Stock ကို ပြန်ပေးသည်)
        """
        return self.shop_floor_stock 

    @property
    def total_stock_qty(self):
        """
        ပစ္စည်း၏ နေရာအားလုံးတွင် ရှိသော စုစုပေါင်း လက်ကျန်အရေအတွက်ကို တွက်ချက်ခြင်း။
        (Inbound - Outbound)
        """
        # (ဒါကို အရင်လိုပဲ ထားပြီး InventoryMovement မှ တွက်ချက်ပါမည်)
        # ဝင်ရောက်မှုနှင့် ထွက်ခွာမှု လော့ဂျစ်
        _zero = Value(0, output_field=IntegerField())
        inbound = self.inventorymovement_set.filter(
             to_location__isnull=False
        ).aggregate(
            sum_qty=Coalesce(Sum('quantity'), _zero, output_field=IntegerField())
        )['sum_qty']

        outbound = self.inventorymovement_set.filter(
            from_location__isnull=False
        ).aggregate(
            sum_qty=Coalesce(Sum('quantity'), _zero, output_field=IntegerField())
        )['sum_qty']
        
        return (inbound or 0) - (outbound or 0)

    # ----------------------------------------------------------------------
    # Location-Specific Stock Calculation (ဒီအပိုင်းကို မပြင်ဆင်တော့ပါ)
    # ----------------------------------------------------------------------
    
    def get_stock_by_location(self, location):
        _zero = Value(0, output_field=IntegerField())
        in_qty = self.inventorymovement_set.filter(
            to_location=location
        ).aggregate(
            sum_qty=Coalesce(Sum('quantity'), _zero, output_field=IntegerField())
        )['sum_qty']

        out_qty = self.inventorymovement_set.filter(
            from_location=location
        ).aggregate(
            sum_qty=Coalesce(Sum('quantity'), _zero, output_field=IntegerField())
        )['sum_qty']
        
        return (in_qty or 0) - (out_qty or 0)

    def get_purchase_to_base_quantity(self, purchase_unit, quantity):
        """
        Convert quantity in purchase_unit to base_unit for stock.
        Returns int (ဒသမမသုံး၊ အရေအတွက်ပဲ).
        """
        from decimal import Decimal
        q = Decimal(str(quantity))
        if not self.base_unit_id:
            return max(1, int(round(q)))
        if purchase_unit and getattr(purchase_unit, 'id', None) == self.purchase_unit_id:
            out = q * (self.purchase_unit_factor or Decimal('1'))
            return max(1, int(round(out)))
        if purchase_unit and self.base_unit_id:
            try:
                out = purchase_unit.to_base_quantity(q) if purchase_unit.id != self.base_unit_id else q
                return max(1, int(round(out)))
            except Exception:
                pass
        return max(1, int(round(q)))

    def cost_per_base_unit(self, unit_cost_in_purchase_unit, purchase_unit):
        """Cost per 1 base unit when buying at unit_cost_in_purchase_unit per purchase_unit. E.g. 15000/Bag, 1 Bag=30 Viss → 500/Viss."""
        from decimal import Decimal
        cost = Decimal(str(unit_cost_in_purchase_unit))
        base_per_one = self.get_purchase_to_base_quantity(purchase_unit, 1)
        if not base_per_one or base_per_one <= 0:
            return cost
        return cost / base_per_one

    def get_stock_at(self, branch_name=None, is_sale_location=None):
        """
        နေရာအလိုက် သို့မဟုတ် ဆိုင်ခွဲအလိုက် လက်ကျန်တွက်ရန်
        """
        movements = self.inventorymovement_set.all()
        
        if branch_name:
            # Branch အလိုက် Filter လုပ်မည်
            movements = movements.filter(
                models.Q(from_location__branch_group=branch_name) | 
                models.Q(to_location__branch_group=branch_name)
            )
        
        # Logic: In - Out
        _zero = Value(0, output_field=IntegerField())
        in_sum = movements.filter(to_location__isnull=False).aggregate(s=Coalesce(Sum('quantity'), _zero, output_field=IntegerField()))['s']
        out_sum = movements.filter(from_location__isnull=False).aggregate(s=Coalesce(Sum('quantity'), _zero, output_field=IntegerField()))['s']
        
        return (in_sum or 0) - (out_sum or 0)
    
    @property
    def shop_floor_stock(self):
        """is_sale_location=True ရှိသော Location များမှ ပထမဆုံးကို သုံးသည် (ဝန်ထမ်း current_location မရှိပါက)"""
        from .models import Location
        sale_location = Location.objects.filter(
            is_sale_location=True,
            location_type__in=('branch', 'shop_floor')
        ).first()
        if not sale_location:
            sale_location = Location.objects.filter(is_sale_location=True).first()
        if not sale_location:
            return 0
        return self.get_stock_by_location(sale_location)

    def get_stock_at_sale_location(self, location):
        """သတ်မှတ်ထားသော Sale Location တစ်ခုမှ Stock ယူခြင်း"""
        if not location:
            return self.shop_floor_stock
        return self.get_stock_by_location(location)

    @property
    def effective_selling_price_mmk(self):
        """Selling price to use in POS: selling_price_mmk if set, else retail_price."""
        if self.selling_price_mmk is not None:
            return self.selling_price_mmk
        return self.retail_price

    def save(self, *args, **kwargs):
        # အသစ်ဖန်တီးချိန်မှာ SKU မထည့်ထားရင် product name ကနေ auto-generate (barcode/scanner နဲ့ အဆင်ပြေ)
        if not self.pk and (not self.sku or not str(self.sku).strip()):
            self.sku = generate_unique_sku(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "ပစ္စည်းစာရင်း (Inventory)"
        verbose_name_plural = "ပစ္စည်းစာရင်းများ (Inventory)"
        ordering = ['name']


class ProductSpecification(models.Model):
    """
    EAV (Entity-Attribute-Value) pattern for dynamic product specifications.
    Allows unlimited technical specs for Electronic & Machinery products.
    Example: Voltage: 220V, Amperage: 160A, Power: 5kW
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='specifications',
        verbose_name="Product"
    )
    label = models.CharField(max_length=100, verbose_name="Specification Label (e.g., Voltage)")
    value = models.CharField(max_length=200, verbose_name="Specification Value (e.g., 220V)")
    order = models.IntegerField(default=0, verbose_name="Display Order")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product Specification"
        verbose_name_plural = "Product Specifications"
        ordering = ['order', 'label']
        unique_together = [['product', 'label']]  # Same label can't be duplicated for same product

    def __str__(self):
        return f"{self.product.name} - {self.label}: {self.value}"


# ----------------- Product Bundling -----------------
class Bundle(models.Model):
    """ပစ္စည်းအစုအပေါင်း (Bundle) - ရွေးချယ်ထားသော ပစ္စည်းများကို တစ်စုတစ်စည်းတည်း ရောင်းချနိုင်သည်"""
    BUNDLE_TYPE_CHOICES = (
        ('PC', 'PC Building'),
        ('Solar', 'Solar Set'),
        ('Machine', 'Machinery Package'),
        ('Fixed', 'Fixed Bundle'),
    )
    PRICING_TYPE_CHOICES = (
        ('FIXED_BUNDLE', 'Fixed Bundle – total price constant'),
        ('CUSTOM_SET', 'Custom Set – sum(item_price × qty)'),
    )
    DISCOUNT_TYPE_CHOICES = (
        ('PERCENTAGE', 'Percentage'),
        ('FIXED_AMOUNT', 'Fixed amount'),
    )
    name = models.CharField(max_length=200, verbose_name="Bundle အမည်")
    description = models.TextField(blank=True, null=True, verbose_name="အကြောင်းအရာ")
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="Bundle SKU/Code")
    bundle_type = models.CharField(
        max_length=20, choices=BUNDLE_TYPE_CHOICES, default='Fixed',
        verbose_name="Bundle type (PC / Solar / Machine / Fixed)"
    )
    # Optional fixed price; if null, frontend uses sum of (product price * quantity)
    bundle_price = models.DecimalField(
        max_digits=12, decimal_places=2, blank=True, null=True,
        verbose_name="Bundle ဈေး (သတ်မှတ်ထားပါက ဤဈေးသုံးမည်)"
    )
    pricing_type = models.CharField(
        max_length=20, choices=PRICING_TYPE_CHOICES, default='CUSTOM_SET',
        verbose_name="Pricing: fixed total vs custom sum"
    )
    discount_type = models.CharField(
        max_length=20, choices=DISCOUNT_TYPE_CHOICES, blank=True, null=True,
        verbose_name="Global bundle discount type"
    )
    discount_value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, null=True, blank=True,
        verbose_name="Discount (percent or fixed MMK)"
    )
    is_active = models.BooleanField(default=True, verbose_name="အသက်သွင်းထား")

    class Meta:
        verbose_name = "ပစ္စည်းအစု (Bundle)"
        verbose_name_plural = "ပစ္စည်းအစုများ (Bundles)"
        ordering = ['name']

    def __str__(self):
        return self.name


class BundleItem(models.Model):
    """Bundle တစ်ခုအတွင်း ပစ္စည်းတစ်မျိုးစီ (အရေအတွက် + ရွေးချယ်မှု)"""
    bundle = models.ForeignKey(
        Bundle, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='bundle_items'
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="အရေအတွက်")
    is_optional = models.BooleanField(
        default=False,
        verbose_name="ရွေးချယ်မှု (True ဖြစ်လျှင် ဝယ်ယူသူက ဖယ်နိုင်သည်)"
    )
    sort_order = models.PositiveSmallIntegerField(default=0, verbose_name="အစဉ်လိုက်")

    class Meta:
        verbose_name = "Bundle ပစ္စည်းတစ်ခု"
        verbose_name_plural = "Bundle ပစ္စည်းများ"
        ordering = ['bundle', 'sort_order', 'id']
        unique_together = [['bundle', 'product']]

    def __str__(self):
        return f"{self.bundle.name} – {self.product.name} x {self.quantity} (optional={self.is_optional})"


class BundleComponent(models.Model):
    """Configurator slot: min/max/default qty and required flag (e.g. CPU required for PC bundle)."""
    bundle = models.ForeignKey(
        Bundle, on_delete=models.CASCADE, related_name='components'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='bundle_components'
    )
    min_qty = models.PositiveIntegerField(default=0, verbose_name="Min quantity")
    max_qty = models.PositiveIntegerField(default=1, verbose_name="Max quantity")
    default_qty = models.PositiveIntegerField(default=1, verbose_name="Default quantity")
    is_required = models.BooleanField(default=False, verbose_name="Required (e.g. CPU)")
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['bundle', 'sort_order', 'id']
        unique_together = [['bundle', 'product']]

    def __str__(self):
        return f"{self.bundle.name} – {self.product.name} (min={self.min_qty}, max={self.max_qty}, required={self.is_required})"


# ----------------- Discount Rule (Promotions) -----------------
class DiscountRule(models.Model):
    """လျှော့ဈေး / ပရိုမိုးရှင်း စည်းမျဉ်း (POS မှာ ရွေးသုံးနိုင်)"""
    DISCOUNT_TYPE_CHOICES = (
        ('PERCENTAGE', 'ရာခိုင်နှုန်း (%)'),
        ('FIXED_AMOUNT', 'သတ်မှတ်ပမာဏ (MMK)'),
    )
    name = models.CharField(max_length=120, verbose_name="အမည်")
    discount_type = models.CharField(
        max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='PERCENTAGE'
    )
    value = models.DecimalField(
        max_digits=12, decimal_places=2, default=0,
        help_text="Percentage (0-100) or fixed MMK amount"
    )
    min_purchase = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True,
        verbose_name="အနည်းဆုံး ဝယ်ယူငွေ (MMK)"
    )
    start_date = models.DateField(null=True, blank=True, verbose_name="စတင်ရက်")
    end_date = models.DateField(null=True, blank=True, verbose_name="ပြီးဆုံးရက်")
    is_active = models.BooleanField(default=True, verbose_name="အသက်သွင်းထား")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "လျှော့ဈေး စည်းမျဉ်း"
        verbose_name_plural = "လျှော့ဈေး စည်းမျဉ်းများ"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_discount_type_display()} {self.value})"


# ----------------- Modifier (e.g. size, add-ons) -----------------
class ModifierGroup(models.Model):
    """ပစ္စည်း ရွေးချယ်မှု အုပ်စု (ဥပမာ အရွယ်အစား, အပို)"""
    name = models.CharField(max_length=80, verbose_name="အမည်")
    description = models.CharField(max_length=200, blank=True, verbose_name="ဖော်ပြချက်")
    is_required = models.BooleanField(default=False, verbose_name="ရွေးရမည်")
    max_selections = models.PositiveSmallIntegerField(default=1, verbose_name="အများဆုံး ရွေးချယ်မှု")
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Modifier အုပ်စု"
        verbose_name_plural = "Modifier အုပ်စုများ"
        ordering = ['display_order', 'name']

    def __str__(self):
        return self.name


class ModifierOption(models.Model):
    """အုပ်စုအတွင်းက ရွေးချယ်စရာ တစ်ခု (ဥပမာ Large, +500 MMK)"""
    group = models.ForeignKey(
        ModifierGroup, on_delete=models.CASCADE, related_name='options'
    )
    name = models.CharField(max_length=80, verbose_name="အမည်")
    price_adjustment = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        verbose_name="ဈေး ထပ်ထည့်ငွေ (MMK)"
    )
    display_order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Modifier ရွေးချယ်စရာ"
        verbose_name_plural = "Modifier ရွေးချယ်စရာများ"
        ordering = ['group', 'display_order', 'name']

    def __str__(self):
        return f"{self.group.name} – {self.name} ({self.price_adjustment} MMK)"


# ----------------- Payment Method Model -----------------
class PaymentMethod(models.Model):
    """ငွေပေးချေမှု နည်းလမ်းများ (KPay, Wave Pay, AYA Pay, Cash, etc.)"""
    name = models.CharField(max_length=50, unique=True, verbose_name="အမည်")
    qr_code_image = models.ImageField(
        upload_to='payment_qr/',
        null=True,
        blank=True,
        verbose_name="QR Code ပုံ"
    )
    account_name = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="အကောင့်အမည်"
    )
    account_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="အကောင့်နံပါတ်/ဖုန်းနံပါတ်"
    )
    is_active = models.BooleanField(default=True, verbose_name="အသုံးပြုနိုင်သည်")
    display_order = models.IntegerField(default=0, verbose_name="ပြသရန် အစဉ်")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "ငွေပေးချေမှု နည်းလမ်း"
        verbose_name_plural = "ငွေပေးချေမှု နည်းလမ်းများ"
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


# ----------------- Sale Transaction Model (Approval Flow) -----------------
STATUS_CHOICES = (
    ('pending', 'Pending (အတည်ပြုရန်စောင့်ဆိုင်းဆဲ)'),
    ('approved', 'Approved (အတည်ပြုပြီး)'),
    ('rejected', 'Rejected (ငြင်းပယ်ပြီး)'),
)

PAYMENT_STATUS_CHOICES = (
    ('pending', 'Pending Payment (ငွေပေးချေရန် စောင့်ဆိုင်းဆဲ)'),
    ('paid', 'Paid (ငွေပေးချေပြီး)'),
    ('failed', 'Payment Failed (ငွေပေးချေမှု မအောင်မြင်)'),
    ('cash', 'Cash Payment (လက်ငင်း)'),
)

class SaleTransaction(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey('customer.Customer', on_delete=models.SET_NULL, null=True, blank=True)
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    sale_location = models.ForeignKey('Location', on_delete=models.PROTECT, null=True)  # မဖြစ်မနေလိုသည်
    outlet = models.ForeignKey(
        'core.Outlet', on_delete=models.PROTECT, null=True, blank=True,
        related_name='sale_transactions', help_text="Outlet where sale occurred (audit + isolation)."
    )
    
    # ဤ field များသည် SaleItem မှ စုစုပေါင်းကို တွက်ယူမည်ဖြစ်၍ blank=True ထားပါ
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    reject_reason = models.TextField(null=True, blank=True)
    
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approvals')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Payment fields
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="ငွေပေးချေမှု နည်းလမ်း"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending',
        verbose_name="ငွေပေးချေမှု အခြေအနေ"
    )
    payment_proof_screenshot = models.ImageField(
        upload_to='payment_proofs/',
        null=True,
        blank=True,
        verbose_name="ငွေပေးချေမှု အတည်ပြုပုံ"
    )
    payment_proof_uploaded_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        # Outlet: derive from sale_location for audit and isolation
        if self.sale_location and not self.outlet_id:
            self.outlet_id = getattr(self.sale_location, 'outlet_id', None)
        # ၁။ Invoice Number မရှိသေးလျှင် (အသစ်ဆောက်ချိန်တွင်) Generate လုပ်မည်
        if not self.invoice_number:
            date_part = datetime.datetime.now().strftime('%y%m%d') # ဥပမာ- 251227
            
            # ၂။ ထပ်မနေသော နံပါတ်ရသည်အထိ ပတ်မည်
            while True:
                # INV-251227-XXXX (random ၄ လုံး)
                random_part = "".join([str(random.randint(0, 9)) for _ in range(4)])
                new_invoice_no = f"INV-{date_part}-{random_part}"
                
                # ၃။ Database ထဲမှာ ရှိပြီးသားလား စစ်မည်
                if not SaleTransaction.objects.filter(invoice_number=new_invoice_no).exists():
                    self.invoice_number = new_invoice_no
                    break
        
        # ၄။ မူလ save() ကို ခေါ်ပြီး သိမ်းမည်
        super().save(*args, **kwargs)





SERIAL_STATUS_CHOICES = (
    ('in_stock', 'In Stock'), # လက်ရှိ Inventory ထဲတွင် ရှိနေဆဲ
    ('sold', 'Sold'),         # ရောင်းချပြီး (Approved Transaction)
    ('defective', 'Defective'), # ချို့ယွင်းချက်ရှိ၍ ရောင်းချ၍မရ
    ('pending_sale', 'Pending Sale Approval'),
)

class SerialItem(models.Model):
    """
    Serial Number ဖြင့် ခြေရာခံရမည့် ပစ္စည်းတစ်ခုစီ၏ အချက်အလက်
    ဖုန်းဆိုင်အတွက်: serial_number = IMEI ၁, imei_2 = IMEI ၂ (အနည်းဆုံးနှစ်ခု ရှိနိုင်သည်)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE, 
                                limit_choices_to={'is_serial_tracked': True})
    serial_number = models.CharField(max_length=100, unique=True, 
                                     verbose_name="Serial No. / IMEI 1")
    imei_2 = models.CharField(
        max_length=100, blank=True, null=True, db_index=True,
        verbose_name="IMEI 2 (ဖုန်းဆိုင်အတွက် ဒုတိယ IMEI)"
    )
    status = models.CharField(max_length=20, choices=SERIAL_STATUS_CHOICES, default='in_stock')
    
    # ရောင်းချခဲ့သော Transaction ကို ညွှန်ပြသည် (Sold ဖြစ်မှသာ ရှိမည်)
    sale_transaction = models.OneToOneField('SaleTransaction', on_delete=models.SET_NULL, 
                                             null=True, blank=True, related_name='serial_item')
    
    current_location = models.ForeignKey(
        'Location', 
        on_delete=models.PROTECT, 
        related_name='serial_items_in_stock',
        null=True, blank=True,
        verbose_name="လက်ရှိတည်နေရာ"
    )

    def save(self, *args, **kwargs):
        if not self.serial_number:
            # ၁။ Prefix သတ်မှတ်ခြင်း
            prefix = "SN"
            
            # ၂။ ရက်စွဲယူခြင်း
            date_part = datetime.date.today().strftime('%Y%m')
            
            # ၃။ ဒီ Product အတွက် နောက်ဆုံးထုတ်ထားတဲ့ Serial ကို ရှာခြင်း
            search_prefix = f"{prefix}-{self.product.sku}-{date_part}"
            
            last_item = SerialItem.objects.filter(
                serial_number__startswith=search_prefix
            ).order_by('serial_number').last()

            if last_item:
                try:
                    last_no = int(last_item.serial_number.split('-')[-1])
                    new_no = last_no + 1
                except (ValueError, IndexError):
                    new_no = 1
            else:
                new_no = 1

            self.serial_number = f"{search_prefix}-{new_no:04d}"

        # 💥 အရေးကြီး - ဒီအောက်က unit_price တွက်တဲ့စာကြောင်းရှိနေရင် ဖျက်လိုက်ပါ
        # self.subtotal = self.unit_price * self.quantity  <-- ဒီစာကြောင်းကို ဖျက်ပါ
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.serial_number} - {self.product.name} ({self.get_status_display()})"
    
    def _add_months(self, start_date, months):
        """ရက်စွဲထဲကို လ အရေအတွက် ပေါင်းထည့်ခြင်း"""
        if not start_date or months <= 0:
            return None
        d = start_date.date() if hasattr(start_date, 'date') else start_date
        year, month, day = d.year, d.month, d.day
        month += months
        while month > 12:
            month -= 12
            year += 1
        # ရက်များလွန်သော လများအတွက် ပြင်ဆင်ခြင်း
        import calendar
        max_day = calendar.monthrange(year, month)[1]
        day = min(day, max_day)
        return datetime.date(year, month, day)

    @property
    def warranty_end_date(self):
        """ရောင်းချပြီး Warranty သက်တမ်းကုန်မည့်ရက်"""
        if self.status != 'sold' or not self.sale_transaction:
            return None
        approved_at = self.sale_transaction.approved_at
        if not approved_at or not self.product.warranty_months:
            return None
        return self._add_months(approved_at, self.product.warranty_months)

    @property
    def is_warranty_active(self):
        """Warranty သက်တမ်းရှိသေးလား"""
        end = self.warranty_end_date
        if not end:
            return False
        from django.utils import timezone
        return timezone.now().date() <= end

    class Meta:
        verbose_name = "Serial Number Item"
        verbose_name_plural = "Serial Number Items"
        ordering = ['serial_number']


class SerialNumberHistory(models.Model):
    """
    Complete audit trail for Serial Numbers - tracks all movements and status changes
    from Purchase to Sale to Repair/Return
    """
    serial_item = models.ForeignKey(
        SerialItem,
        on_delete=models.CASCADE,
        related_name='history_records',
        verbose_name="Serial Item"
    )
    ACTION_CHOICES = (
        ('purchased', 'Purchased'),
        ('received', 'Received at Location'),
        ('transferred', 'Transferred'),
        ('sold', 'Sold'),
        ('returned', 'Returned'),
        ('repair_started', 'Repair Started'),
        ('repair_completed', 'Repair Completed'),
        ('defective', 'Marked as Defective'),
        ('status_changed', 'Status Changed'),
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="Action")
    from_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='serial_history_from',
        verbose_name="From Location"
    )
    to_location = models.ForeignKey(
        'Location',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='serial_history_to',
        verbose_name="To Location"
    )
    from_status = models.CharField(max_length=20, choices=SERIAL_STATUS_CHOICES, null=True, blank=True)
    to_status = models.CharField(max_length=20, choices=SERIAL_STATUS_CHOICES, null=True, blank=True)
    transaction = models.ForeignKey(
        'SaleTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Related Transaction"
    )
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Created By"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Serial Number History"
        verbose_name_plural = "Serial Number Histories"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.serial_item.serial_number} - {self.get_action_display()} ({self.created_at})"


class WarrantyRecord(models.Model):
    """Warranty သက်တမ်း မှတ်တမ်း (Serial ပစ္စည်းရောင်းချပြီးနောက် ဖန်တီးသည်)"""
    serial_item = models.OneToOneField(SerialItem, on_delete=models.CASCADE, related_name='warranty_record')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    sale_transaction = models.ForeignKey(SaleTransaction, on_delete=models.CASCADE)
    warranty_start_date = models.DateField(verbose_name="Warranty စသည့်ရက်")
    warranty_end_date = models.DateField(verbose_name="Warranty ကုန်မည့်ရက်")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Warranty မှတ်တမ်း"
        verbose_name_plural = "Warranty မှတ်တမ်းများ"


class GlobalSetting(models.Model):
    """Key-value store for app-wide settings (e.g. usd_exchange_rate)."""
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=500, blank=True)
    value_decimal = models.DecimalField(max_digits=18, decimal_places=6, null=True, blank=True)
    # Manual rate adjustment fields
    market_premium_percentage = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True,
        verbose_name="Market Premium % (e.g., +10 for 10% markup)",
        help_text="Percentage to add to CBM rate (e.g., 10 = +10%)"
    )
    manual_fixed_rate = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True,
        verbose_name="Manual Fixed Rate (overrides CBM rate)",
        help_text="If set, this rate will be used instead of CBM rate"
    )
    # Hybrid Exchange Rate System fields
    is_auto_sync = models.BooleanField(
        default=True,
        verbose_name="Auto-Sync Enabled",
        help_text="If True, use scraped CBM rate. If False, use manual_usd_rate."
    )
    manual_usd_rate = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True,
        verbose_name="Manual USD Rate",
        help_text="Manual override rate when is_auto_sync=False"
    )

    class Meta:
        ordering = ['key']

    def __str__(self):
        return f"{self.key}={self.value or self.value_decimal}"
    
    @property
    def get_active_usd_rate(self):
        """
        Get the active USD exchange rate based on hybrid system logic.
        
        Returns:
            Decimal: Active USD rate (MMK per 1 USD) or None
            
        Logic:
            - If is_auto_sync=True: Use latest scraped rate from ExchangeRateLog
            - If is_auto_sync=False: Use manual_usd_rate
        """
        from django.utils import timezone
        
        if not self.is_auto_sync:
            # Manual mode: use manual_usd_rate
            if self.manual_usd_rate is not None:
                return self.manual_usd_rate
            else:
                # Fallback: if manual_usd_rate not set, use value_decimal
                return self.value_decimal
        
        # Auto-sync mode: get latest scraped rate from ExchangeRateLog
        from .models import ExchangeRateLog
        latest_log = ExchangeRateLog.objects.filter(
            currency='USD',
            source__in=['CBM', 'Scraped']
        ).order_by('-date', '-id').first()
        
        if latest_log:
            return latest_log.rate
        
        # Fallback: use value_decimal if no scraped rate found
        return self.value_decimal


class ExchangeRateLog(models.Model):
    """Daily exchange rate log for multiple currencies (USD, THB, SGD). One row per date per currency."""
    CURRENCY_CHOICES = (
        ('USD', 'US Dollar'),
        ('THB', 'Thai Baht'),
        ('SGD', 'Singapore Dollar'),
    )
    date = models.DateField()
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='USD')
    rate = models.DecimalField(max_digits=18, decimal_places=4, verbose_name="Rate (MMK per unit)")
    source = models.CharField(max_length=50, default='CBM', verbose_name="Source (CBM/Manual)")

    class Meta:
        ordering = ['-date', 'currency']
        unique_together = [['date', 'currency']]
        verbose_name = 'Exchange Rate Log'
        verbose_name_plural = 'Exchange Rate Logs'

    def __str__(self):
        return f"{self.date}: {self.currency} = {self.rate} MMK"


class Site(models.Model):
    """
    ဆိုင်တစ်ခု သို့မဟုတ် ဆိုင်ခွဲတစ်ခု။ အတွင်းမှာ အရောင်းဆိုင် + ဂိုထောင် (Location) တွဲထားနိုင်သည်။
    """
    name = models.CharField(max_length=100, verbose_name="ဆိုင်/ဆိုင်ခွဲအမည်")
    address = models.TextField(blank=True, null=True, verbose_name="လိပ်စာ")
    code = models.CharField(max_length=50, blank=True, null=True, unique=True, verbose_name="ကုဒ်")

    class Meta:
        verbose_name = "ဆိုင်/ဆိုင်ခွဲ (Site)"
        verbose_name_plural = "ဆိုင်များ/ဆိုင်ခွဲများ (Sites)"
        ordering = ['name']

    def __str__(self):
        return self.name


class Location(models.Model):
    TYPE_CHOICES = (
        ('warehouse', 'ဂိုဒေါင် (Warehouse)'),
        ('branch', 'ဆိုင်ခွဲ (Branch)'),
        ('shop_floor', 'ရောင်းချရန်နေရာ (Shop Floor)'),
    )
    """
    ပစ္စည်းများ ထားရှိရာ နေရာများ။ Multi-Outlet: each Outlet has Warehouse + Shopfloor.
    """
    outlet = models.ForeignKey(
        'core.Outlet', on_delete=models.CASCADE, null=True, blank=True,
        related_name='locations', verbose_name="Outlet"
    )
    site = models.ForeignKey(
        Site, on_delete=models.CASCADE, null=True, blank=True,
        related_name='locations', verbose_name="ဆ/ဆိုင်ခွဲ (Site)"
    )
    name = models.CharField(max_length=100)  # unique per outlet via constraint
    branch_group = models.CharField(max_length=100, blank=True, null=True, help_text="ဆိုင်ခွဲအမည် (ဟောင်း)")
    location_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='branch')
    address = models.TextField(blank=True, null=True)
    is_sale_location = models.BooleanField(default=False, 
                                           help_text="ဝန်ထမ်းများ ရောင်းချရန်အတွက် အသုံးပြုသည့် နေရာဟုတ်/မဟုတ်။")

    # ✅ ဝန်ထမ်းချိတ်ဆက်မှု ထပ်ထည့်ခြင်း
    staff_assigned = models.ManyToManyField(
        User, 
        related_name='assigned_locations', 
        blank=True, 
        help_text="ဤ Location (ဆိုင်/ဂိုဒေါင်) တွင် တာဝန်ပေးထားသော ဝန်ထမ်းများ။"
    )

    def __str__(self):
        return f"{self.name} ({self.get_location_type_display()})"
    
    class Meta:
        verbose_name_plural = "Locations"
        constraints = [
            models.UniqueConstraint(
                fields=['outlet', 'name'],
                name='inventory_location_outlet_name_uniq',
                condition=models.Q(outlet__isnull=False),
            ),
        ]



# ----------------------------------------------------
# Inventory Movement Model (Double-Entry System အတွက်)
# ----------------------------------------------------

MOVEMENT_TYPE_CHOICES = (
    ('inbound', 'Inbound (Stock Received/Return)'),
    ('outbound', 'Outbound (Sale/Withdrawal)'),
    ('transfer', 'Transfer (Location Change)'),
    ('adjustment', 'Adjustment (Count/Fix)'),
    ('rejected', 'Rejected Sale Log'),
)

class InventoryMovement(models.Model):
    """
    ပစ္စည်း အရေအတွက် ပြောင်းလဲမှုတိုင်းကို မှတ်တမ်းတင်သည့် Model
    (Double-Entry စာရင်းကိုင် စနစ်ကဲ့သို့ လုပ်ဆောင်သည်)
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    # နေရာရွှေ့ပြောင်းမှု
    from_location = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                      null=True, blank=True, related_name='moved_from')
    to_location = models.ForeignKey(Location, on_delete=models.SET_NULL,
                                    null=True, blank=True, related_name='moved_to')

    quantity = models.PositiveIntegerField(
        default=1,
        help_text="အရေအတွက် (ပြည်ပြည်သူသုံး integer ပဲ)"
    )
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPE_CHOICES, default='adjustment')

    # Audit: which outlet this movement belongs to (for isolation and reports)
    outlet = models.ForeignKey(
        'core.Outlet', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='inventory_movements', help_text="Outlet context (from to_location or from_location)."
    )

    # မှတ်တမ်းနှင့် ဆက်စပ်မှု
    created_at = models.DateTimeField(auto_now_add=True)
    moved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    # ရောင်းချမှု (သို့မဟုတ်) ဝယ်ယူမှု Transaction ကို ညွှန်ပြသည်
    sale_transaction = models.ForeignKey(SaleTransaction, on_delete=models.SET_NULL, 
                                         null=True, blank=True, related_name='inventory_movements')
    
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.product.name} - {self.get_movement_type_display()} ({self.quantity})"


# ----------------- Purchase Module (Bulk buy → stock in base unit) -----------------
class Purchase(models.Model):
    """ဝယ်ယူမှု ခေါင်းစဉ်။ Purchase entry with lines; each line can use purchase unit and converts to base for stock."""
    outlet = models.ForeignKey(
        'core.Outlet',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchases',
        verbose_name="ဆိုင်ခွဲ",
    )
    reference = models.CharField(max_length=80, blank=True, verbose_name="အမှတ်အသား/ဖောင်နံပါတ်")
    purchase_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='purchases_created',
    )

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = "ဝယ်ယူမှု"
        verbose_name_plural = "ဝယ်ယူမှုများ"

    def __str__(self):
        return f"Purchase #{self.id} ({self.reference or self.created_at})"


class PurchaseLine(models.Model):
    """Single line: product bought in purchase_unit; quantity and cost in that unit; converted to base for stock."""
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='lines',
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    purchase_unit = models.ForeignKey(
        'Unit',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchase_lines',
        verbose_name="ဝယ်ယူသည့်ယူနစ်",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="အရေအတွက် (ယူနစ်အလိုက်)",
    )
    unit_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="ယူနစ်ဈေး (MMK)",
    )
    to_location = models.ForeignKey(
        Location,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='purchase_lines',
        help_text="Stock received to this location",
    )

    class Meta:
        verbose_name = "ဝယ်ယူမှု လိုင်း"
        verbose_name_plural = "ဝယ်ယူမှု လိုင်းများ"

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost

    def quantity_in_base_unit(self):
        """Quantity converted to product's base unit for stock."""
        return self.product.get_purchase_to_base_quantity(self.purchase_unit, self.quantity)

    def cost_per_base_unit(self):
        """Unit cost per product base unit (for costing)."""
        return self.product.cost_per_base_unit(self.unit_cost, self.purchase_unit)

    def __str__(self):
        return f"{self.purchase} – {self.product.name} x {self.quantity} @ {self.unit_cost}"


class Notification(models.Model):
    # ဤ Notification ကို လက်ခံမည့်သူ (Admin များ၊ သို့မဟုတ် တောင်းဆိုသူ Staff)
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    
    # Notification ၏ အကြောင်းအရာ
    message = models.CharField(max_length=255)
    
    # Notification ရဲ့ အမျိုးအစား (ဥပမာ: Sale Approved, Sale Rejected, Low Stock)
    notification_type = models.CharField(max_length=50, default='system') 
    
    # ဖတ်ပြီး/မဖတ်ရသေး
    is_read = models.BooleanField(default=False)
    
    # ဤ Notification ကို ဖြစ်ပေါ်စေသော Transaction (ချိတ်ဆက်ထားခြင်း)
    sale_transaction = models.ForeignKey(
        'SaleTransaction', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"To {self.recipient.username}: {self.message[:30]}..."




class SaleItem(models.Model):
    """ဘောက်ချာတစ်ခုချင်းစီတွင် ပါဝင်သော ပစ္စည်းအသေးစိတ်"""
    sale_transaction = models.ForeignKey(
        SaleTransaction, 
        on_delete=models.CASCADE, 
        related_name='sale_items' # ✅ serializer တွင် ပြန်ခေါ်ရန် အမည်
    )
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="အရေအတွက်",
    )
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def save(self, *args, **kwargs):
        # subtotal ကို auto တွက်ချက်ခြင်း
        self.subtotal = self.unit_price * int(self.quantity)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"



class Sale(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    invoice_number = models.CharField(max_length=20, unique=True, editable=False, null=True, blank=True)
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    outlet = models.ForeignKey(
        'core.Outlet', on_delete=models.PROTECT, null=True, blank=True,
        related_name='sales', help_text="Outlet where sale occurred."
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            date_str = datetime.date.today().strftime('%Y%m%d')
            last_sale = Sale.objects.filter(invoice_number__startswith=date_str).order_by('invoice_number').last()
            new_no = (int(last_sale.invoice_number.split('-')[-1]) + 1) if last_sale else 1
            self.invoice_number = f"{date_str}-{new_no:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Voucher {self.id} - {self.staff.username}"
    
