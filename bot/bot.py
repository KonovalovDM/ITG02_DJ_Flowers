"""
bot.py – запуск Telegram-бота с обработчиками
"""
import os
import sys
import logging
import asyncio
import aiohttp
import django
from asgiref.sync import sync_to_async
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from django.conf import settings    # Импортируем настройки Django

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,  # Устанавливаем уровень логирования на DEBUG
    format='%(asctime)s - %(levelname)s - %(message)s',  # Формат вывода
)
# Проверка путей
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Используем logging.debug вместо print
logging.debug("🔍 PYTHONPATH: %s", sys.path)

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


# Инициализация бота и диспетчера
TOKEN = settings.TELEGRAM_BOT_TOKEN
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ID администратора (кому отправлять уведомления)
ADMIN_ID = settings.TELEGRAM_ADMIN_ID

# URL API Django-сервера
API_URL = settings.API_URL


# 🔹 Клавиатуры
customer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
])

staff_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
    [InlineKeyboardButton(text="🚚 В доставке", callback_data="in_delivery")],
])

admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
    [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm")],
    [InlineKeyboardButton(text="🚚 В доставке", callback_data="in_delivery")],
    [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")],
    [InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics")]
])

request_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📲 Отправить контакт", request_contact=True)]],
    resize_keyboard=True
)

# from core.models import User, Order  # Импортируем модель пользователя и заказа
# 🔹 Привязка Telegram ID
@dp.message(Command("start"))
async def start(message: types.Message):
    """Приветственное сообщение и проверка регистрации"""

    user = await get_user_by_telegram_id(message.from_user.id)

    if user:
        keyboard = get_user_keyboard(user)
        await message.answer("🌸 Добро пожаловать! Вы авторизованы.", reply_markup=keyboard)
    else:
        await message.answer(
            "🔑 Вы не зарегистрированы!\nОтправьте ваш контакт, чтобы привязать Telegram ID.",
            reply_markup=request_contact_keyboard
        )

async def get_user_by_telegram_id(telegram_id):
    """Получает пользователя по Telegram ID"""
    from core.models import User
    return await asyncio.to_thread(User.objects.filter, telegram_id=telegram_id).first()

def get_user_keyboard(user):
    """Выбирает клавиатуру в зависимости от роли"""
    if user.is_admin:
        return admin_keyboard
    elif user.is_staff:
        return staff_keyboard
    return customer_keyboard

@dp.message(F.contact)
async def register_telegram_id(message: types.Message):
    """Обрабатывает отправленный контакт и привязывает Telegram ID"""
    user_phone = message.contact.phone_number
    from core.models import User

    user = await asyncio.to_thread(User.objects.filter, phone_number=user_phone).first()

    if user:
        user.telegram_id = message.from_user.id
        await asyncio.to_thread(user.save)
        keyboard = get_user_keyboard(user)
        await message.answer("✅ Telegram ID успешно привязан!", reply_markup=keyboard)
    else:
        await message.answer("❌ Ваш номер не найден в базе. Пожалуйста, зарегистрируйтесь на сайте.")

# 🔹 Уведомление админа о новом заказе
async def notify_admin(order_id):
    """Отправляет администратору уведомление о новом заказе"""

    try:
        from core.models import Order
        order = await asyncio.to_thread(Order.objects.get, id=order_id)
        message = (
            f"🛒 *Новый заказ!*\n"
            f"📌 *ID*: {order.id}\n"
            f"👤 *Пользователь*: {order.user.username}\n"
            f"📦 *Товары*: {order.products.all().count()} шт.\n"
            f"📍 *Дата заказа*: {order.order_date.strftime('%d.%m.%Y %H:%M')}\n"
            f"📌 *Статус*: {order.get_status_display()}"
        )
        await bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode="Markdown")
    except Order.DoesNotExist:
        print(f"Ошибка: заказ {order_id} не найден.")

# 🔹 Кнопка "📊 Аналитика"
@dp.callback_query(F.data == "analytics")
async def send_analytics(call: types.CallbackQuery):
    """Отправляет администраторам статистику заказов"""
    from core.models import Order
    total_orders = await asyncio.to_thread(Order.objects.count)
    total_revenue = await asyncio.to_thread(lambda: sum(order.total_price for order in Order.objects.all()))

    message = (
        f"📊 *Аналитика продаж*\n"
        f"📦 *Всего заказов*: {total_orders}\n"
        f"💰 *Общая выручка*: {total_revenue} руб."
    )

    await call.message.answer(message, parse_mode="Markdown")

@dp.message(Command("link"))
async def link_telegram(message: types.Message):
    """Привязка Telegram ID к аккаунту"""
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.reply("❌ Используйте формат: /link <ID_пользователя>")
        return

    user_id = int(args[1])
    from core.models import User  # Импортируем здесь, чтобы избежать проблем с зависимостями

    user = await sync_to_async(User.objects.filter)(id=user_id)
    if user.exists():
        user = await sync_to_async(user.update)(telegram_id=message.from_user.id)
        await message.reply("✅ Telegram успешно привязан к вашему аккаунту!")
    else:
        await message.reply("❌ Пользователь не найден.")



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
                        keyboard = admin_keyboard(order["id"])
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
                await call.message.answer(f"✅ Заказ {order_id} теперь {new_status}", reply_markup=admin_keyboard(order_id))
            else:
                await call.message.answer("❌ Ошибка обновления заказа.")

# 🔹 Запуск бота
async def main():
    """Запуск бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())



