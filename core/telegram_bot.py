"""
telegram_bot.py – отправка уведомлений о заказах через Telegram.
"""
import asyncio
import logging
from aiogram import Bot
from django.conf import settings
from core.models import Order
from asgiref.sync import sync_to_async

TELEGRAM_BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
TELEGRAM_ADMIN_ID = settings.TELEGRAM_ADMIN_ID

bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def notify_admin(message: str):
    """Отправка уведомления админу в Telegram"""
    try:
        await bot.send_message(TELEGRAM_ADMIN_ID, message)
    except Exception as e:
        logging.error(f"Ошибка при отправке сообщения админу: {e}")