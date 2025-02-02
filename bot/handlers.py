"""
handlers.py – обработчики сообщений и команд бота
"""

import requests
from aiogram import types, Router
from aiogram.filters import Command
from .bot import API_URL
from bot.keyboards import orders_keyboard, admin_keyboard

router = Router()

@router.message(Command("start"))
async def start(message: types.Message):
    """Приветственное сообщение"""
    await message.answer(
        "🌸 Добро пожаловать в FlowerDeliveryBot! \n"
        "Вы можете посмотреть свои заказы, используя команду /orders.",
        reply_markup=orders_keyboard
    )

@router.message(Command("orders"))
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

@router.message(Command("order"))
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

@router.callback_query()
async def handle_callback(call: types.CallbackQuery):
    """Обработчик нажатий на кнопки"""
    if call.data == "refresh":
        await get_orders(call.message)
    elif call.data in ["confirm", "in_delivery", "cancel"]:
        order_id = call.message.text.split()[1]  # ID заказа
        new_status = {"confirm": "Подтвержден", "in_delivery": "В доставке", "cancel": "Отменен"}[call.data]
        response = requests.post(f"{API_URL}/orders/{order_id}/", json={"status": new_status})
        if response.status_code == 200:
            await call.message.answer(f"✅ Заказ {order_id} теперь {new_status}")
        else:
            await call.message.answer("❌ Ошибка обновления заказа.")