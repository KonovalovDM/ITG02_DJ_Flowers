"""
keyboards.py – клавиатуры Telegram-бота
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Клавиатура для просмотра заказов
orders_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
    [InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")]
])

# Клавиатура для управления заказами админом
admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
    [InlineKeyboardButton(text="🚚 В доставке", callback_data="in_delivery")],
    [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")]
])