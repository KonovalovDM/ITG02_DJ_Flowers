"""
telegram_bot.py – отправка уведомлений о заказах через Telegram.
"""

from aiogram import Bot
from django.conf import settings
from core.models import Order

# Инициализация бота с токеном из settings.py
bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)


async def notify_admin(order_id):
    """
    Отправляет уведомление администратору о новом заказе.

    :param order_id: ID заказа
    """
    try:
        order = Order.objects.get(id=order_id)
        message = (
            f"🛒 Новый заказ!\n"
            f"📌 ID: {order.id}\n"
            f"👤 Пользователь: {order.user.username}\n"
            f"📦 Товары: {order.get_items_display()}\n"
            f"📍 Адрес: {order.delivery_address}\n"
            f"📅 Дата: {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"📌 Статус: {order.get_status_display()}"
        )
        await bot.send_message(chat_id=settings.TELEGRAM_ADMIN_ID, text=message)
    except Order.DoesNotExist:
        print(f"Ошибка: заказ {order_id} не найден.")