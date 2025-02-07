from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Order
from .forms import OrderForm
from core.telegram_bot import notify_admin
from asgiref.sync import sync_to_async
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login

import asyncio
import threading

def register(request):
    """Регистрация нового пользователя"""
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("index")  # Перенаправляем на главную страницу
    else:
        form = UserCreationForm()
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