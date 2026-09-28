from decimal import Decimal
from uuid import uuid4

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    icon = models.CharField(
        max_length=12,
        default='🛍️'
    )

    def save(self, *a, **kw):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*a, **kw)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        max_length=160
    )

    slug = models.SlugField(
        unique=True,
        blank=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products'
    )

    description = models.TextField()

    price = models.DecimalField(
        max_digits=9,
        decimal_places=2
    )

    discount_price = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True
    )

    stock = models.PositiveIntegerField(
        default=0
    )

    image = models.ImageField(
        upload_to='products/',
        blank=True
    )

    brand = models.CharField(
        max_length=100
    )

    unit = models.CharField(
        max_length=40
    )

    rating = models.DecimalField(
        max_digits=2,
        decimal_places=1,
        default=4.0,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(5)
        ]
    )

    is_available = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def save(self, *a, **kw):
        if not self.slug:
            self.slug = slugify(self.name)

        super().save(*a, **kw)

    @property
    def selling_price(self):
        return (
            self.discount_price
            if self.discount_price is not None
            else self.price
        )

    @property
    def discount_percent(self):
        return (
            int(
                (self.price - self.selling_price)
                * 100
                / self.price
            )
            if self.price
            else 0
        )

    def __str__(self):
        return self.name


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    city = models.CharField(
        max_length=80,
        blank=True
    )

    pin_code = models.CharField(
        max_length=10,
        blank=True
    )

    budget = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.user.username


class Address(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='addresses'
    )

    full_name = models.CharField(
        max_length=100
    )

    phone = models.CharField(
        max_length=15
    )

    house = models.CharField(
        max_length=160
    )

    street = models.CharField(
        max_length=160
    )

    area = models.CharField(
        max_length=160
    )

    city = models.CharField(
        max_length=80
    )

    state = models.CharField(
        max_length=80
    )

    pin_code = models.CharField(
        max_length=10
    )

    is_default = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['-is_default', '-id']

    def save(self, *a, **kw):
        if self.is_default:
            Address.objects.filter(
                user=self.user
            ).exclude(
                pk=self.pk
            ).update(
                is_default=False
            )

        super().save(*a, **kw)

    def __str__(self):
        return f'{self.full_name}, {self.city}'


class Coupon(models.Model):
    code = models.CharField(
        max_length=30,
        unique=True
    )

    percent = models.PositiveIntegerField(
        validators=[MaxValueValidator(100)]
    )

    minimum_amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        default=0
    )

    maximum_discount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        null=True,
        blank=True
    )

    expires_at = models.DateTimeField()

    is_active = models.BooleanField(
        default=True
    )

    def valid_for(self, amount):
        return (
            self.is_active
            and self.expires_at > timezone.now()
            and amount >= self.minimum_amount
        )

    def discount(self, amount):
        value = amount * Decimal(self.percent) / 100

        return (
            min(value, self.maximum_discount)
            if self.maximum_discount
            else value
        )

    def __str__(self):
        return self.code


class Order(models.Model):

    STATUS = [
        ('placed', 'Order Placed'),
        ('confirmed', 'Confirmed'),
        ('packing', 'Packing'),
        ('delivery', 'Out for Delivery'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('paid', 'Paid'),
        ('failed', 'Payment Failed'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders'
    )

    order_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False
    )

    address = models.ForeignKey(
        Address,
        on_delete=models.PROTECT
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    payment_method = models.CharField(
        max_length=12,
        choices=[
            ('cod', 'Cash on Delivery'),
            ('upi', 'UPI'),
            ('card', 'Credit / Debit Card'),
        ]
    )

    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS,
        default='pending'
    )

    # -----------------------------------------
    # Razorpay Standard Checkout Order ID
    # -----------------------------------------
    razorpay_order_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # -----------------------------------------
    # Razorpay Payment ID
    # -----------------------------------------
    razorpay_payment_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # -----------------------------------------
    # Razorpay UPI QR Code ID
    # -----------------------------------------
    razorpay_qr_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=12,
        choices=STATUS,
        default='placed'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def save(self, *a, **kw):
        if not self.order_number:
            self.order_number = 'BB' + uuid4().hex[:10].upper()

        super().save(*a, **kw)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField()

    price = models.DecimalField(
        max_digits=9,
        decimal_places=2
    )

    @property
    def total(self):
        return self.price * self.quantity


class Review(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    rating = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(5)
        ]
    )

    comment = models.TextField(
        max_length=500
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'user'],
                name='one_review_per_product'
            )
        ]


class GroceryPlan(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='grocery_plan'
    )

    name = models.CharField(
        max_length=100,
        default='My weekly basket'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


class GroceryPlanItem(models.Model):
    plan = models.ForeignKey(
        GroceryPlan,
        on_delete=models.CASCADE,
        related_name='items'
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE
    )

    day = models.CharField(
        max_length=12,
        choices=[
            (d, d)
            for d in [
                'Monday',
                'Tuesday',
                'Wednesday',
                'Thursday',
                'Friday',
                'Saturday',
                'Sunday'
            ]
        ],
        default='Monday'
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['plan', 'product', 'day'],
                name='one_plan_product_day'
            )
        ]


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='gallery'
    )

    image = models.ImageField(
        upload_to='products/gallery/'
    )

    alt_text = models.CharField(
        max_length=200,
        blank=True
    )

    is_main = models.BooleanField(
        default=False
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} - Image"