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

@login_required
def place_order(request):
    """Оформление заказа (синхронная версия)"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            form.save_m2m()

            # Асинхронный вызов из синхронного кода
            threading.Thread(target=lambda: asyncio.run(notify_admin(order.id))).start()

            messages.success(request, '✅ Заказ успешно создан!')
            return redirect('order_history')
    else:
        form = OrderForm()
    return render(request, 'order.html', {'form': form})


@login_required
def order_history(request):
    """История заказов"""
    orders = Order.objects.filter(user=request.user)
    return render(request, 'order_history.html', {'orders': orders})


def catalog_view(request):
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})


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


def cart_view(request):
    cart = request.session.get("cart", {})  # Загружаем корзину
    return render(request, "cart.html", {"cart": cart})


