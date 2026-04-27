import json

import stripe
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import Item, Order, OrderItem
from .services import create_item_checkout_session, create_order_checkout_session, get_public_key, retrieve_checkout_session

CART_SESSION_KEY = "cart"


def _cart(request) -> dict[str, int]:
    cart = request.session.get(CART_SESSION_KEY, {})
    return {str(item_id): int(quantity) for item_id, quantity in cart.items() if int(quantity) > 0}


def _save_cart(request, cart: dict[str, int]) -> None:
    request.session[CART_SESSION_KEY] = cart
    request.session.modified = True


def _cart_items(request):
    cart = _cart(request)
    ids = [int(item_id) for item_id in cart.keys()]
    items = Item.objects.filter(id__in=ids)
    rows = []
    for item in items:
        qty = cart.get(str(item.id), 0)
        rows.append({"item": item, "quantity": qty, "line_total": item.price * qty})
    return rows


def _cart_count(request) -> int:
    return sum(_cart(request).values())


def _cart_total(rows):
    total = 0
    currency = ""
    for row in rows:
        total += row["line_total"]
        currency = row["item"].currency
    return total, currency


def _build_order_from_cart(request) -> Order:
    rows = _cart_items(request)
    if not rows:
        raise ValueError("Cart is empty")

    currencies = {row["item"].currency for row in rows}
    if len(currencies) != 1:
        raise ValueError("В одной корзине должны быть товары только в одной валюте")

    order = Order.objects.create(status=Order.STATUS_PENDING, note="Created from cart")
    for row in rows:
        OrderItem.objects.create(order=order, item=row["item"], quantity=row["quantity"])
    return order


@require_GET
def item_list(request):
    items = Item.objects.all()
    paid_orders = Order.objects.prefetch_related("lines__item").filter(status=Order.STATUS_PAID)[:5]
    return render(
        request,
        "payments/item_list.html",
        {"items": items, "paid_orders": paid_orders, "cart_count": _cart_count(request)},
    )


@require_GET
def item_detail(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    try:
        public_key = get_public_key(item.currency)
    except ImproperlyConfigured as error:
        return HttpResponseBadRequest(str(error))

    return render(
        request,
        "payments/item_detail.html",
        {"item": item, "stripe_public_key": public_key, "cart_count": _cart_count(request)},
    )


@require_GET
def buy_item(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    try:
        session = create_item_checkout_session(item, request)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse({"id": session.id, "url": getattr(session, "url", None)})


@require_POST
def add_to_cart(request, pk: int):
    item = get_object_or_404(Item, pk=pk)
    cart = _cart(request)
    cart[str(item.id)] = cart.get(str(item.id), 0) + 1
    _save_cart(request, cart)
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True, "cart_count": _cart_count(request)})
    return redirect("payments:cart")


@require_POST
def update_cart(request, pk: int):
    get_object_or_404(Item, pk=pk)
    try:
        quantity = int(request.POST.get("quantity", "1"))
    except ValueError:
        quantity = 1
    cart = _cart(request)
    if quantity <= 0:
        cart.pop(str(pk), None)
    else:
        cart[str(pk)] = min(quantity, 99)
    _save_cart(request, cart)
    return redirect("payments:cart")


@require_POST
def clear_cart(request):
    _save_cart(request, {})
    return redirect("payments:cart")


@require_GET
def cart_detail(request):
    rows = _cart_items(request)
    total, currency = _cart_total(rows)
    mixed_currency = len({row["item"].currency for row in rows}) > 1
    public_key = ""
    if rows and not mixed_currency:
        try:
            public_key = get_public_key(currency)
        except ImproperlyConfigured:
            public_key = ""
    return render(
        request,
        "payments/cart.html",
        {
            "rows": rows,
            "total": total,
            "currency": currency,
            "mixed_currency": mixed_currency,
            "stripe_public_key": public_key,
            "cart_count": _cart_count(request),
        },
    )


@require_GET
def cart_buy(request):
    try:
        order = _build_order_from_cart(request)
        session = create_order_checkout_session(order, request)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse({"id": session.id, "url": getattr(session, "url", None), "order_id": order.id})


@require_GET
def order_detail(request, pk: int):
    order = get_object_or_404(Order.objects.prefetch_related("lines__item", "taxes"), pk=pk)
    if order.currency == "mixed":
        return HttpResponseBadRequest("Order contains items with different currencies")

    try:
        public_key = get_public_key(order.currency)
    except ImproperlyConfigured as error:
        return HttpResponseBadRequest(str(error))

    return render(
        request,
        "payments/order_detail.html",
        {"order": order, "stripe_public_key": public_key, "cart_count": _cart_count(request)},
    )


@require_GET
def buy_order(request, pk: int):
    order = get_object_or_404(Order.objects.prefetch_related("lines__item", "taxes"), pk=pk)
    try:
        session = create_order_checkout_session(order, request)
    except Exception as error:
        return JsonResponse({"error": str(error)}, status=400)

    return JsonResponse({"id": session.id, "url": getattr(session, "url", None)})


@require_GET
def success(request):
    session_id = request.GET.get("session_id")
    order = None
    if session_id:
        order = Order.objects.filter(stripe_session_id=session_id).prefetch_related("lines__item").first()
        if order and order.status != Order.STATUS_PAID:
            try:
                session = retrieve_checkout_session(order.currency, session_id)
                if getattr(session, "payment_status", "") == "paid":
                    customer = getattr(session, "customer_details", None)
                    email = getattr(customer, "email", "") if customer else ""
                    order.mark_paid(
                        session_id=session.id,
                        payment_intent_id=getattr(session, "payment_intent", "") or "",
                        customer_email=email or "",
                    )
                    _save_cart(request, {})
            except Exception:
                # Webhook still remains the main reliable way to confirm payment.
                pass
    return render(request, "payments/success.html", {"session_id": session_id, "order": order, "cart_count": _cart_count(request)})


@require_GET
def paid_orders(request):
    orders = Order.objects.prefetch_related("lines__item").filter(status=Order.STATUS_PAID)
    return render(request, "payments/paid_orders.html", {"orders": orders, "cart_count": _cart_count(request)})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

    try:
        if webhook_secret:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        else:
            event = json.loads(payload.decode("utf-8"))
    except Exception as error:
        return HttpResponseBadRequest(str(error))

    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        order_id = session.get("metadata", {}).get("order_id")
        if order_id:
            order = Order.objects.filter(pk=order_id).first()
            if order:
                customer = session.get("customer_details") or {}
                order.mark_paid(
                    session_id=session.get("id", ""),
                    payment_intent_id=session.get("payment_intent", "") or "",
                    customer_email=customer.get("email", "") or "",
                )

    return HttpResponse(status=200)


@require_GET
def cancel(request, kind: str, pk: int):
    if kind == "item":
        return redirect("payments:item_detail", pk=pk)
    if kind == "order":
        order = Order.objects.filter(pk=pk).first()
        if order and order.status == Order.STATUS_PENDING:
            order.status = Order.STATUS_CANCELLED
            order.save(update_fields=["status", "updated_at"])
        return redirect("payments:cart")
    return redirect("payments:item_list")
