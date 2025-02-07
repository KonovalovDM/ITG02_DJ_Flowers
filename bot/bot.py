"""
bot.py – запуск Telegram-бота с обработчиками
"""

import os
import sys
import asyncio
import aiohttp
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

def get_admin_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{order_id}")],
        [InlineKeyboardButton(text="🚚 В доставке", callback_data=f"in_delivery_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{order_id}")]
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
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/orders/") as response:
            if response.status == 200:
                orders = await response.json()
                text = "📋 **Список заказов:**\n\n"
                for order in orders:
                    text += f"🆔 {order['id']} | {order['status']}\n"
                if message.from_user.id == ADMIN_ID:
                    for order in orders:
                        keyboard = get_admin_keyboard(order["id"])
                        await message.answer(f"🆔 Заказ {order['id']} | Статус: {order['status']}",
                                             reply_markup=keyboard)
                else:
                    await message.answer(text, parse_mode="Markdown")
            else:
                await message.answer("❌ Ошибка получения заказов.")


# 🔹 Обработчик команды /order <id>
@dp.message(Command("order"))
async def get_order_detail(message: types.Message):
    """Получить детали конкретного заказа"""
    try:
        order_id = int(message.text.split()[1])
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/orders/{order_id}/") as response:
                if response.status == 200:
                    order = await response.json()
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
        await message.answer("⚠️ Введите корректный ID заказа. Пример: `/order 123`")

# 🔹 Обработчик inline-кнопок (админка)
@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    """Обработчик нажатий на кнопки админки"""
    if call.from_user.id != ADMIN_ID:
        await call.answer("У вас нет прав для выполнения этого действия.", show_alert=True)
        return

    # Извлекаем order_id из callback_data
    data_parts = call.data.split("_")
    if len(data_parts) != 2:
        await call.answer("❌ Ошибка данных!", show_alert=True)
        return

    action, order_id = data_parts
    if not order_id.isdigit():
        await call.answer("❌ Неверный формат ID заказа.", show_alert=True)
        return

    order_id = int(order_id)

    # Исправленный mapping (соответствует БД)
    status_mapping = {
        "confirm": "processing",      # "В работе"
        "in_delivery": "delivering",  # "В доставке"
        "cancel": "canceled"          # "Отменен"
    }

    if action not in status_mapping:
        await call.answer("❌ Некорректное действие!", show_alert=True)
        return

    new_status = status_mapping[action]

    # Отправляем запрос в API
    async with aiohttp.ClientSession() as session:
        print(f"Отправляем запрос: {API_URL}/orders/{order_id}/update/ со статусом: {new_status}")
        async with session.post(f"{API_URL}/orders/{order_id}/update/", json={"status": new_status}) as response:
            if response.status == 200:
                await call.message.answer(f"✅ Заказ {order_id} теперь {new_status}", reply_markup=get_admin_keyboard(order_id))
            else:
                await call.message.answer("❌ Ошибка обновления заказа.")

# 🔹 Запуск бота
async def main():
    """Запуск бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



