"""
bot.py – запуск Telegram-бота с обработчиками
"""

import os
import sys
import asyncio
import requests
import django
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from django.conf import settings

# Проверка путей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print("🔍 PYTHONPATH:", sys.path)

# Указываем Django, где искать настройки
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "flowers.settings")

# Защита от повторного запуска setup()
if not django.conf.settings.configured:
    try:
        django.setup()
        print("✅ Django настроен!")
    except RuntimeError as e:
        print(f"❌ Ошибка Django setup: {e}")
        sys.exit(1)

from django.conf import settings  # Импортируем настройки Django

# Инициализация бота и диспетчера
TOKEN = settings.TELEGRAM_BOT_TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ID администратора (кому отправлять уведомления)
ADMIN_ID = settings.TELEGRAM_ADMIN_ID

# URL API Django-сервера
API_URL = settings.API_URL

# 🔹 Клавиатуры
orders_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
    [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")]
])

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
    [InlineKeyboardButton(text="🚚 В доставке", callback_data="in_delivery")],
    [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
])

# 🔹 Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    """Приветственное сообщение"""
    await message.answer(
        "🌸 Добро пожаловать в FlowerDeliveryBot!\n"
        "Вы можете посмотреть свои заказы, используя команду /orders.",
        reply_markup=orders_keyboard
    )

# 🔹 Обработчик команды /orders
@dp.message(Command("orders"))
async def get_orders(message: types.Message):
    """Получить список заказов"""
    response = requests.get(f"{API_URL}/orders/")
    if response.status_code == 200:
        orders = response.json()
        text = "📋 **Список заказов:**\n\n"
        for order in orders:
            text += f"🆔 {order['id']} | {order['status']}\n"
        await message.answer(text, parse_mode="Markdown")
    else:
        await message.answer("❌ Ошибка получения заказов.")

# 🔹 Обработчик команды /order <id>
@dp.message(Command("order"))
async def get_order_detail(message: types.Message):
    """Получить детали конкретного заказа"""
    try:
        order_id = int(message.text.split()[1])
        response = requests.get(f"{API_URL}/orders/{order_id}/")
        if response.status_code == 200:
            order = response.json()
            text = (
                f"🛒 **Заказ {order['id']}**\n"
                f"📦 Товары: {order['items']}\n"
                f"📍 Доставка: {order['delivery_address']}\n"
                f"📅 Дата: {order['created_at']}\n"
                f"📌 Статус: {order['status']}"
            )
            await message.answer(text, parse_mode="Markdown")
        else:
            await message.answer("❌ Заказ не найден.")
    except (IndexError, ValueError):
        await message.answer("⚠ Введите корректный ID заказа. Пример: `/order 123`")

# 🔹 Обработчик inline-кнопок (админка)
@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    """Обработчик нажатий на кнопки"""
    if call.data == "refresh":
        await get_orders(call.message)
    elif call.data in ["confirm", "in_delivery", "cancel"]:
        order_id = call.message.text.split()[1]  # ID заказа
        new_status = {"confirm": "Подтвержден", "in_delivery": "В доставке", "cancel": "Отменен"}[call.data]
        response = requests.post(f"{API_URL}/orders/{order_id}/", json={"status": new_status})
        if response.status_code == 200:
            await call.message.answer(f"✅ Заказ {order_id} теперь {new_status}", reply_markup=admin_keyboard)
        else:
            await call.message.answer("❌ Ошибка обновления заказа.")

# 🔹 Запуск бота
async def main():
    """Запуск бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
