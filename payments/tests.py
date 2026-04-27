from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.test import TestCase, override_settings

from .models import Item
from .services import money_to_minor_units


class MoneyHelperTests(TestCase):
    def test_usd_amount_goes_to_cents(self):
        self.assertEqual(money_to_minor_units(Decimal("12.50"), "usd"), 1250)


@override_settings(
    STRIPE_KEYS={
        "usd": {"public": "pk_test_usd", "secret": "sk_test_usd"},
        "eur": {"public": "pk_test_eur", "secret": "sk_test_eur"},
    }
)
class BuyItemViewTests(TestCase):
    def test_buy_endpoint_returns_checkout_session_id(self):
        item = Item.objects.create(
            name="Test item",
            description="Small test item",
            price="10.00",
            currency="usd",
        )
        fake_session = SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.test/session")

        with patch("payments.services.stripe.checkout.Session.create", return_value=fake_session) as create_session:
            response = self.client.get(f"/buy/{item.id}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["id"], "cs_test_123")
        self.assertEqual(create_session.call_args.kwargs["mode"], "payment")
