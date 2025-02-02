"""
bot.py – запуск Telegram-бота
"""
import sys
import os
import django
import asyncio
import requests
from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command

# Устанавливаем переменную окружения для Django
# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flowers.settings")
django.setup()

from django.conf import settings  # Импортируем настройки Django

TOKEN = settings.TELEGRAM_BOT_TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ID администратора (кому отправлять уведомления)
ADMIN_ID = settings.TELEGRAM_ADMIN_ID

# URL API Django-сервера
API_URL = settings.API_URL

# Создаем Router для команд
router = Router()
dp.include_router(router)  # Подключаем Router к диспетчеру


@router.message(Command("start"))
async def start(message: types.Message):
    """Обработчик команды /start"""
    await message.answer("Привет! Я бот по доставке цветов.")


@router.message(Command("orders"))
async def get_orders(message: types.Message):
    """Обработчик команды /orders - получение списка заказов с API"""
    response = requests.get("http://127.0.0.1:8000/api/orders/")
    if response.status_code == 200:
        orders = response.json()
        text = "\n".join([f"Заказ {o['id']}: {o['status']}" for o in orders])
        await message.answer(text)
    else:
        await message.answer("Ошибка получения заказов.")


async def main():
    """Запуск бота"""
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
