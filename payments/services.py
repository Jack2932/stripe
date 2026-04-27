from decimal import Decimal, ROUND_HALF_UP

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

from .models import Item, Order

ZERO_DECIMAL_CURRENCIES = {
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga", "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf"
}


def money_to_minor_units(amount: Decimal, currency: str) -> int:
    currency = currency.lower()
    if currency in ZERO_DECIMAL_CURRENCIES:
        return int(amount.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def get_stripe_keys(currency: str) -> dict[str, str]:
    currency = currency.lower()
    keys = getattr(settings, "STRIPE_KEYS", {}).get(currency)
    if not keys or not keys.get("public") or not keys.get("secret"):
        raise ImproperlyConfigured(f"Stripe keys for currency '{currency}' are not configured")
    return keys


def get_public_key(currency: str) -> str:
    return get_stripe_keys(currency)["public"]


def _success_url(request, kind: str, object_id: int) -> str:
    url = request.build_absolute_uri(reverse("payments:success"))
    return f"{url}?kind={kind}&id={object_id}&session_id={{CHECKOUT_SESSION_ID}}"


def _cancel_url(request, kind: str, object_id: int) -> str:
    return request.build_absolute_uri(reverse("payments:cancel", kwargs={"kind": kind, "pk": object_id}))


def _line_item_from_item(item: Item, quantity: int = 1, tax_rate_ids: list[str] | None = None) -> dict:
    product_data = {"name": item.name}
    if item.description:
        product_data["description"] = item.description[:900]

    line_item = {
        "price_data": {
            "currency": item.currency,
            "product_data": product_data,
            "unit_amount": money_to_minor_units(item.price, item.currency),
        },
        "quantity": quantity,
    }
    if tax_rate_ids:
        line_item["tax_rates"] = tax_rate_ids
    return line_item


def create_item_checkout_session(item: Item, request):
    keys = get_stripe_keys(item.currency)
    stripe.api_key = keys["secret"]

    return stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode="payment",
        line_items=[_line_item_from_item(item)],
        success_url=_success_url(request, "item", item.pk),
        cancel_url=_cancel_url(request, "item", item.pk),
        client_reference_id=f"item:{item.pk}",
        metadata={"item_id": str(item.pk)},
    )


def create_order_checkout_session(order: Order, request):
    lines = list(order.lines.select_related("item"))
    if not lines:
        raise ValueError("Order is empty")

    currencies = {line.item.currency for line in lines}
    if len(currencies) != 1:
        raise ValueError("All items in one order must have the same currency")

    currency = currencies.pop()
    keys = get_stripe_keys(currency)
    stripe.api_key = keys["secret"]

    tax_rate_ids = [tax.stripe_tax_rate_id for tax in order.taxes.filter(is_active=True) if tax.stripe_tax_rate_id]
    line_items = [
        _line_item_from_item(line.item, quantity=line.quantity, tax_rate_ids=tax_rate_ids)
        for line in lines
    ]

    session_params = {
        "payment_method_types": ["card"],
        "mode": "payment",
        "line_items": line_items,
        "success_url": _success_url(request, "order", order.pk),
        "cancel_url": _cancel_url(request, "order", order.pk),
        "client_reference_id": f"order:{order.pk}",
        "metadata": {"order_id": str(order.pk)},
    }

    if order.discount and order.discount.is_active and order.discount.stripe_coupon_id:
        session_params["discounts"] = [{"coupon": order.discount.stripe_coupon_id}]

    session = stripe.checkout.Session.create(**session_params)
    order.status = Order.STATUS_PENDING
    order.stripe_session_id = session.id
    order.save(update_fields=["status", "stripe_session_id", "updated_at"])
    return session


def retrieve_checkout_session(currency: str, session_id: str):
    keys = get_stripe_keys(currency)
    stripe.api_key = keys["secret"]
    return stripe.checkout.Session.retrieve(session_id)
