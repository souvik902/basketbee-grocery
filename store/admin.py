from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Product,
    ProductImage,
    Category,
    CustomerProfile,
    Address,
    Coupon,
    Order,
    OrderItem,
    Review,
    GroceryPlan,
    GroceryPlanItem,
)


admin.site.site_header = "BasketBee Control Room"
admin.site.site_title = "BasketBee Admin"
admin.site.index_title = "Store Management"


# =========================================
# PRODUCT IMAGE INLINE
# =========================================

class ProductImageInline(admin.TabularInline):

    model = ProductImage

    extra = 3

    fields = (
        "preview",
        "image",
        "alt_text",
        "is_main",
    )

    readonly_fields = ("preview",)


    @admin.display(description="Preview")
    def preview(self, obj):

        if obj.image:

            return format_html(
                '<img src="{}" width="90" height="90" '
                'style="object-fit:contain;border-radius:10px;'
                'border:1px solid #ddd;">',
                obj.image.url
            )

        return "No image"


# =========================================
# PRODUCT ADMIN
# =========================================

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "preview",
        "name",
        "brand",
        "category",
        "selling_price",
        "stock",
        "is_available",
    )

    list_filter = (
        "category",
        "is_available",
    )

    search_fields = (
        "name",
        "brand",
    )

    prepopulated_fields = {
        "slug": ("name",)
    }

    inlines = [
        ProductImageInline
    ]


    @admin.display(description="Photo")
    def preview(self, product):

        if product.image:

            return format_html(
                '<img src="{}" width="55" height="55" '
                'style="object-fit:contain;border-radius:8px;">',
                product.image.url
            )

        return "—"


# =========================================
# ORDER ITEMS
# =========================================

class OrderItemInline(admin.TabularInline):

    model = OrderItem

    extra = 0

    readonly_fields = (
        "product",
        "quantity",
        "price",
    )

    can_delete = False


# =========================================
# ORDER ADMIN
# =========================================

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        "order_number",
        "user",
        "total_amount",
        "payment_method",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "payment_method",
    )

    search_fields = (
        "order_number",
        "user__username",
        "user__email",
    )

    readonly_fields = (
        "order_number",
        "created_at",
    )

    inlines = [
        OrderItemInline
    ]


# =========================================
# OTHER MODELS
# =========================================

admin.site.register([
    Category,
    CustomerProfile,
    Address,
    Coupon,
    OrderItem,
    Review,
    GroceryPlan,
    GroceryPlanItem,
])
