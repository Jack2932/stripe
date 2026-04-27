# Generated manually for test task improvements.

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("payments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="order",
            name="customer_email",
            field=models.EmailField(blank=True, default="", max_length=254),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="paid_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="order",
            name="status",
            field=models.CharField(
                choices=[
                    ("cart", "Cart"),
                    ("pending", "Pending payment"),
                    ("paid", "Paid"),
                    ("cancelled", "Cancelled"),
                ],
                default="pending",
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name="order",
            name="stripe_payment_intent_id",
            field=models.CharField(blank=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="stripe_session_id",
            field=models.CharField(blank=True, db_index=True, default="", max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="order",
            name="updated_at",
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
