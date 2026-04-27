from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("", views.item_list, name="item_list"),

    path("item/<int:pk>", views.item_detail, name="item_detail"),
    path("item/<int:pk>/", views.item_detail),
    path("buy/<int:pk>", views.buy_item, name="buy_item"),
    path("buy/<int:pk>/", views.buy_item),

    path("cart/", views.cart_detail, name="cart"),
    path("cart/buy/", views.cart_buy, name="cart_buy"),
    path("cart/clear/", views.clear_cart, name="clear_cart"),
    path("cart/add/<int:pk>/", views.add_to_cart, name="add_to_cart"),
    path("cart/update/<int:pk>/", views.update_cart, name="update_cart"),

    path("order/<int:pk>", views.order_detail, name="order_detail"),
    path("order/<int:pk>/", views.order_detail),
    path("order/<int:pk>/buy", views.buy_order, name="buy_order"),
    path("order/<int:pk>/buy/", views.buy_order),

    path("orders/paid/", views.paid_orders, name="paid_orders"),
    path("success/", views.success, name="success"),
    path("cancel/<str:kind>/<int:pk>/", views.cancel, name="cancel"),
    path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]
