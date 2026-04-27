from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Item(models.Model):
    USD = "usd"
    EUR = "eur"

    CURRENCY_CHOICES = [
        (USD, "USD"),
        (EUR, "EUR"),
    ]

    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default=USD)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return f"{self.name} — {self.price} {self.currency.upper()}"


class Discount(models.Model):
    name = models.CharField(max_length=120)
    stripe_coupon_id = models.CharField(
        max_length=120,
        help_text="Например: coupon id из Stripe Dashboard, начинается с coup_",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Tax(models.Model):
    name = models.CharField(max_length=120)
    stripe_tax_rate_id = models.CharField(
        max_length=120,
        help_text="Tax Rate ID из Stripe Dashboard, обычно начинается с txr_",
    )
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    STATUS_CART = "cart"
    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_CART, "Cart"),
        (STATUS_PENDING, "Pending payment"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    items = models.ManyToManyField(Item, through="OrderItem", related_name="orders")
    discount = models.ForeignKey(
        Discount,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="orders",
    )
    taxes = models.ManyToManyField(Tax, blank=True, related_name="orders")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING)
    stripe_session_id = models.CharField(max_length=255, blank=True, db_index=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    customer_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order #{self.pk or 'new'}"

    @property
    def total_price(self) -> Decimal:
        total = Decimal("0.00")
        for line in self.lines.select_related("item"):
            total += line.item.price * line.quantity
        return total

    @property
    def currency(self) -> str:
        currencies = {line.item.currency for line in self.lines.select_related("item")}
        if not currencies:
            return ""
        if len(currencies) > 1:
            return "mixed"
        return currencies.pop()

    def clean(self):
        super().clean()
        if self.discount and not self.discount.is_active:
            raise ValidationError({"discount": "Нельзя прикрепить неактивную скидку."})

    def mark_paid(self, session_id: str = "", payment_intent_id: str = "", customer_email: str = ""):
        from django.utils import timezone

        self.status = self.STATUS_PAID
        self.paid_at = self.paid_at or timezone.now()
        if session_id:
            self.stripe_session_id = session_id
        if payment_intent_id:
            self.stripe_payment_intent_id = payment_intent_id
        if customer_email:
            self.customer_email = customer_email
        self.save(update_fields=[
            "status",
            "paid_at",
            "stripe_session_id",
            "stripe_payment_intent_id",
            "customer_email",
            "updated_at",
        ])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name="order_lines")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ["order", "item"]
        verbose_name = "order item"
        verbose_name_plural = "order items"

    def __str__(self) -> str:
        return f"{self.item.name} × {self.quantity}"

    @property
    def line_total(self) -> Decimal:
        return self.item.price * self.quantity
