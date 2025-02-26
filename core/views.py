from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Order, User
from .forms import OrderForm, UserRegisterForm
from core.telegram_bot import notify_admin
from asgiref.sync import sync_to_async
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from .forms import UserUpdateForm  # Импорт формы обновления профиля


import asyncio
import threading

def register(request):
    """Регистрация пользователя с отправкой ссылки в Telegram"""
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            telegram_message = f"Привет, {user.username}! Привяжите ваш Telegram, отправив команду /link {user.id} в нашем боте."
            send_mail(
                "Привяжите ваш Telegram",
                telegram_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
            return redirect("login")  # Перенаправляем на страницу входа
    else:
        form = UserRegisterForm()
    return render(request, "registration/register.html", {"form": form})

@login_required
def some_view(request):
    context = {
        'username': request.user.username,  # Добавляем имя пользователя
    }
    return render(request, 'your_template.html', context)

def index(request):
    """Главная страница"""
    return render(request, "index.html")

def catalog(request):
    """Отображение каталога цветов"""
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})

@login_required
def cart(request):
    """Отображение корзины"""
    return render(request, 'cart.html')


import logging

@login_required
def place_order(request):
    """Оформление заказа с выбором или вводом нового адреса"""
    logging.debug("🔹 Вызвана place_order")

    saved_addresses = list(Order.objects.filter(user=request.user)
                           .values_list("delivery_address", flat=True)
                           .distinct())
    if request.user.delivery_address:
        saved_addresses.insert(0, request.user.delivery_address)  # Основной адрес в начало списка

    if request.method == "POST":
        logging.debug("📨 POST-запрос получен")

        selected_address = request.POST.get("delivery_address")
        new_address = request.POST.get("new_address", "").strip()

        # ✅ Проверяем новый адрес
        if selected_address == "new" and new_address:
            delivery_address = new_address
            request.user.delivery_address = new_address  # Сохраняем в профиль
            request.user.save()
            logging.debug(f"📍 Новый адрес сохранен: {delivery_address}")
        else:
            delivery_address = selected_address
            logging.debug(f"📍 Выбран адрес: {delivery_address}")

        # ✅ Проверяем корзину
        cart = request.session.get("cart", {})
        if not cart:
            messages.error(request, "❌ Корзина пуста! Добавьте товары перед оформлением заказа.")
            return redirect("cart")

        logging.debug(f"🛒 Товары в корзине: {cart}")

        # ✅ Создаем заказ (без использования формы)
        order = Order.objects.create(
            user=request.user,
            delivery_address=delivery_address,
            price=sum(float(item["price"]) * item["quantity"] for item in cart.values()),
            status="pending"
        )
        logging.debug(f"✅ Заказ создан: ID {order.id}")

        # ✅ Добавляем товары в заказ
        product_ids = map(int, cart.keys())
        products = Product.objects.filter(id__in=product_ids)
        order.products.set(products)
        logging.debug(f"✅ Добавлены товары: {list(products.values_list('name', flat=True))}")

        # ✅ Очищаем корзину после заказа
        request.session["cart"] = {}
        request.session["delivery_address"] = order.delivery_address
        request.session.modified = True

        # ✅ Формируем сообщение для администратора
        admin_message = (
                f"📦 Новый заказ #{order.id}\n"
                f"👤 Клиент: {request.user.username} (ID: {request.user.id})\n"
                f"📍 Адрес: {order.delivery_address}\n"
                f"💰 Сумма: {order.price} руб.\n"
                f"🛒 Товары: " + ", ".join(order.products.values_list("name", flat=True))
        )

        # ✅ Асинхронное уведомление админу в телеграм
        threading.Thread(target=lambda: asyncio.run(notify_admin(admin_message))).start()

        messages.success(request, "✅ Заказ успешно создан!")
        return redirect("order_history")  # ✅ Переадресация на "Мои заказы"

    return render(request, "order.html", {"saved_addresses": saved_addresses})



@login_required
def repeat_order(request, order_id):
    """Повторяет заказ, добавляя товары в корзину и перенаправляет в корзину"""
    old_order = get_object_or_404(Order, id=order_id, user=request.user)

    # Загружаем корзину
    cart = request.session.get("cart", {})
    cart.clear()  # Очищаем корзину перед повтором заказа

    # Добавляем товары из старого заказа
    for product in old_order.products.all():
        cart[str(product.id)] = {
            "name": product.name,
            "price": float(product.price),
            "image": product.image.url,
            "quantity": 1,  # Количество оставляем 1 (можно изменить на прошлое)
        }

    request.session["cart"] = cart
    request.session["delivery_address"] = old_order.delivery_address  # Сохраняем адрес

    request.session.modified = True
    return redirect("cart")  # Перенаправляем пользователя в корзину


@login_required
def order_history(request):
    """История заказов с отображением товаров и адреса доставки"""
    orders = Order.objects.filter(user=request.user) \
        .select_related("user") \
        .prefetch_related("products")  # Загружаем связанные товары
    return render(request, 'order_history.html', {'orders': orders})



def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    cart = request.session.get("cart", {})  # Получаем корзину из сессии
    if str(product_id) in cart:
        cart[str(product_id)]["quantity"] += 1
    else:
        cart[str(product_id)] = {
            "name": product.name,
            "price": float(product.price),
            "image": product.image.url,
            "quantity": 1,
        }

    request.session["cart"] = cart  # Сохраняем корзину
    request.session.modified = True  # Обновляем сессию

    return redirect("cart")  # Перенаправляем в корзину


@login_required
def cart_view(request):
    """Отображение корзины с загруженными товарами и адресом доставки"""
    cart = request.session.get("cart", {})
    delivery_address = request.session.get("delivery_address", request.user.delivery_address)  # Загружаем адрес

    return render(request, "cart.html", {"cart": cart, "delivery_address": delivery_address})


@login_required
def profile(request):
    """Страница профиля пользователя"""
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            # Обновляем адрес вручную
            request.user.delivery_address = form.cleaned_data["delivery_address"]
            request.user.save()  # Сохраняем пользователя
            messages.success(request, "✅ Данные успешно обновлены!")
            return redirect("profile")
    else:
        form = UserUpdateForm(instance=request.user)

    delivery_address = request.user.delivery_address or "Адрес не указан"

    return render(request, "profile.html", {
        "form": form,
        "delivery_address": delivery_address
    })
