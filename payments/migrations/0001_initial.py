# Generated manually for the test task.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Discount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("stripe_coupon_id", models.CharField(help_text="Например: coupon id из Stripe Dashboard, начинается с coup_", max_length=120)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Item",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("description", models.TextField(blank=True)),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                ("currency", models.CharField(choices=[("usd", "USD"), ("eur", "EUR")], default="usd", max_length=3)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Tax",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("stripe_tax_rate_id", models.CharField(help_text="Tax Rate ID из Stripe Dashboard, обычно начинается с txr_", max_length=120)),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Order",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("note", models.CharField(blank=True, max_length=255)),
                ("discount", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="orders", to="payments.discount")),
                ("taxes", models.ManyToManyField(blank=True, related_name="orders", to="payments.tax")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="OrderItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("quantity", models.PositiveIntegerField(default=1)),
                ("item", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="order_lines", to="payments.item")),
                ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="lines", to="payments.order")),
            ],
            options={
                "verbose_name": "order item",
                "verbose_name_plural": "order items",
                "unique_together": {("order", "item")},
            },
        ),
        migrations.AddField(
            model_name="order",
            name="items",
            field=models.ManyToManyField(related_name="orders", through="payments.OrderItem", to="payments.item"),
        ),
    ]
