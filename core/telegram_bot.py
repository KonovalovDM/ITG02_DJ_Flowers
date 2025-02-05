"""
telegram_bot.py – отправка уведомлений о заказах через Telegram.
"""

from aiogram import Bot
from django.conf import settings
from core.models import Order
from asgiref.sync import sync_to_async

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)

async def notify_admin(order_id):
    """
    Отправляет уведомление администратору о новом заказе.
    """
    try:
        # Корректный асинхронный запрос к базе данных
        order = await sync_to_async(Order.objects.get, thread_sensitive=True)(id=order_id)
        message = (
            f"🛒 Новый заказ!\n"
            f"📌 ID: {order.id}\n"
            f"👤 Пользователь: {order.user.username}\n"
            f"📦 Товары: {order.products.all()}\n"
            f"📅 Дата: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📌 Статус: {order.get_status_display()}"
        )
        await bot.send_message(chat_id=settings.TELEGRAM_ADMIN_ID, text=message)
    except Order.DoesNotExist:
        print(f"Ошибка: заказ {order_id} не найден.")
