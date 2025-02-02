from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Order
from .forms import OrderForm
from core.telegram_bot import notify_admin

def catalog(request):
    """Отображение каталога цветов"""
    products = Product.objects.all()
    return render(request, 'catalog.html', {'products': products})

@login_required
def cart(request):
    """Отображение корзины"""
    return render(request, 'cart.html')

@login_required
async def place_order(request):
    """Оформление заказа"""
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.save()
            form.save_m2m()
            await notify_admin(order.id)  # Уведомление в Telegram
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