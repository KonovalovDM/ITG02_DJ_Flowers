from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Order
from .forms import OrderForm
from core.telegram_bot import notify_admin
from asgiref.sync import sync_to_async
import asyncio
import threading

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

# @login_required
# async def place_order(request):
#     """Оформление заказа"""
#     if request.method == 'POST':
#         form = OrderForm(request.POST)
#         if form.is_valid():
#             order = form.save(commit=False)
#             order.user = request.user
#             order.save()
#             form.save_m2m()
#             # Используем sync_to_async для вызова синхронной функции notify_admin
#             await sync_to_async(notify_admin)(order.id)  # Уведомление в Telegram
#             messages.success(request, '✅ Заказ успешно создан!')
#             return redirect('order_history')
#     else:
#         form = OrderForm()
#     return render(request, 'order.html', {'form': form})

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