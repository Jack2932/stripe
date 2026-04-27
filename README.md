# Bean & Bubble Store (Django + Stripe)

Небольшое тестовое приложение — мини-кофейня с оплатой через Stripe.

## Что есть в проекте

* список товаров (кофе, бабл ти и т.д.)
* страница товара с кнопкой покупки
* корзина
* оформление заказа
* оплата через Stripe Checkout
* после оплаты заказ помечается как оплаченный
* админка Django

## Как запустить локально

```bash
git clone https://github.com/your_username/bean-bubble-store.git
cd bean-bubble-store
```

Создать `.env`:

```bash
cp .env.example .env
```

Вставить свои Stripe ключи:

```env
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

Запуск через Docker:

```bash
docker compose up --build
```

Открыть:

```text
http://localhost:8000/
```

---

## Без Docker

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py create_demo_data
python manage.py runserver
```

---

## Админка

```text
/admin/
```

логин: admin
пароль: admin12345

---

## Онлайн версия

```text
https://your-project.onrender.com
```

---

## Тестовая карта Stripe

```text
4242 4242 4242 4242
```

любая дата и CVC

---

## Немного про реализацию

* корзина хранится в session
* при оплате создаётся Stripe Checkout Session
* после успешной оплаты заказ помечается как paid (через webhook + success страницу)
