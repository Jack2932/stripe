import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from payments.models import Item, Order, OrderItem


class Command(BaseCommand):
    help = "Create cafe demo items and an optional admin user."

    def handle(self, *args, **options):
        # Old demo names from early drafts. Removing them keeps the public catalog clean
        # if the command is run more than once during local testing.
        Item.objects.filter(name__in=["Coffee beans", "Notebook", "Sticker pack"]).delete()

        menu = [
            {
                "name": "Бабл ти Манго-Маракуйя",
                "description": "Холодный чай с пюре манго, маракуйей и шариками тапиоки. Лёгкий фруктовый вкус без лишней приторности.",
                "price": Decimal("5.90"),
                "currency": "eur",
            },
            {
                "name": "Раф Ванильный",
                "description": "Мягкий раф на сливках с ванилью и плотной кофейной базой. Хороший вариант для проверки оплаты одного товара.",
                "price": Decimal("4.80"),
                "currency": "eur",
            },
            {
                "name": "Латте Солёная карамель",
                "description": "Классический латте с карамельным сиропом, щепоткой соли и нежной молочной пеной.",
                "price": Decimal("4.50"),
                "currency": "eur",
            },
            {
                "name": "Айс Матча Латте",
                "description": "Матча, молоко и лёд. Освежающий напиток для тех, кто хочет не кофе, но с бодрым характером.",
                "price": Decimal("5.20"),
                "currency": "eur",
            },
            {
                "name": "Капучино Ореховый",
                "description": "Капучино с лёгкой ореховой нотой и густой пеной. Небольшая позиция для корзины и общего заказа.",
                "price": Decimal("3.90"),
                "currency": "eur",
            },
            {
                "name": "Брауни с фундуком",
                "description": "Шоколадный брауни с фундуком. Отлично добавляется вторым товаром в корзину перед оплатой.",
                "price": Decimal("3.40"),
                "currency": "eur",
            },
        ]

        created_items = []
        for data in menu:
            item, _ = Item.objects.update_or_create(
                name=data["name"],
                defaults={
                    "description": data["description"],
                    "price": data["price"],
                    "currency": data["currency"],
                },
            )
            created_items.append(item)

        if not Order.objects.exists() and len(created_items) >= 2:
            order = Order.objects.create(note="Демо-заказ кофейни: напиток и десерт")
            OrderItem.objects.create(order=order, item=created_items[1], quantity=1)
            OrderItem.objects.create(order=order, item=created_items[-1], quantity=2)
            self.stdout.write(self.style.SUCCESS(f"Created demo order #{order.id}"))

        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

        if username and password:
            User = get_user_model()
            if not User.objects.filter(username=username).exists():
                User.objects.create_superuser(username=username, email=email, password=password)
                self.stdout.write(self.style.SUCCESS(f"Created admin user '{username}'"))

        self.stdout.write(self.style.SUCCESS("Cafe demo data is ready"))
