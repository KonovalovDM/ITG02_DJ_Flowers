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
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.filters.callback_data import CallbackData


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

# Временное хранилище данных пользователя для регистрации
user_data = {}


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

def create_admin_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Мои заказы", callback_data=f"orders_{order_id}")],
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{order_id}")],
        [InlineKeyboardButton(text="🚚 В доставке", callback_data=f"in_delivery_{order_id}")],
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{order_id}")],
        [InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics")]
    ])

def get_keyboard_for_user(user):
    """Выбирает правильную клавиатуру в зависимости от прав пользователя"""
    if user.is_superuser:
        return admin_keyboard
    elif user.is_staff:
        return staff_keyboard
    return customer_keyboard


request_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📲 Отправить контакт", request_contact=True)]],
    resize_keyboard=True
)

# from core.models import User, Order  # Импортируем модель пользователя и заказа

# 🔹 Привязка Telegram ID
@dp.message(Command("start"))
async def start(message: types.Message):
    """Приветствие и автоматическая регистрация пользователя"""
    from core.models import User  # Импортируем модель пользователя

    telegram_id = message.from_user.id
    username = message.from_user.username

    # Проверяем, есть ли уже пользователь
    user = await sync_to_async(User.objects.filter(telegram_id=telegram_id).first, thread_sensitive=True)()

    if user:
        # В зависимости от роли пользователя выбираем клавиатуру
        if user.is_admin:
            keyboard = admin_keyboard  # Клавиатура для администратора
        elif user.is_staff:
            keyboard = staff_keyboard  # Клавиатура для сотрудника
        else:
            keyboard = customer_keyboard  # Клавиатура для клиента

#        keyboard = get_keyboard_for_user(user)  # Выбираем правильную клавиатуру
        await message.answer("🌸 Добро пожаловать! Вы авторизованы.", reply_markup=keyboard)

    else:
        # Новый пользователь, запрашиваем имя
        await message.answer("🔹 Добро пожаловать! Введите ваше имя для регистрации.")
        dp.message.register(get_user_name, F.text)

# Блок для отладки - начало

@dp.callback_query(lambda c: c.data == 'orders')
async def process_orders(callback_query: types.CallbackQuery):
    await callback_query.answer("📦 Тут будет список ваших заказов.")

@dp.callback_query(lambda c: c.data == 'confirm')
async def process_confirm(callback_query: types.CallbackQuery):
    await callback_query.answer("✅ Заказ подтвержден.")

@dp.callback_query(lambda c: c.data == 'in_delivery')
async def process_delivery(callback_query: types.CallbackQuery):
    await callback_query.answer("🚚 Заказ в доставке.")

@dp.callback_query(lambda c: c.data.startswith("orders_"))
async def process_order(callback_query: types.CallbackQuery):
    order_id = callback_query.data.split("_")[1]
    keyboard = create_admin_keyboard(order_id)  # создаем клавиатуру для этого заказа
    await callback_query.message.edit_text(f"Информация по заказу {order_id}", reply_markup=keyboard)

# Блок для отладки - конец

async def get_user_name(message: types.Message):
    """Обрабатывает имя пользователя"""
    from core.models import User  # Импортируем модель пользователя

    telegram_id = message.from_user.id
    username = message.from_user.username
    full_name = message.text.strip()

    # Сохраняем имя и запрашиваем телефон
    user_data[telegram_id] = {"full_name": full_name, "username": username}

    request_contact_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📲 Отправить контакт", request_contact=True)]],
        resize_keyboard=True
    )

    await message.answer("📞 Отправьте ваш номер телефона для завершения регистрации.",
                         reply_markup=request_contact_keyboard)


@dp.message(F.contact)
async def register_user(message: types.Message):
    """Регистрирует пользователя по переданному контакту"""
    from core.models import User  # Импортируем модель пользователя

    telegram_id = message.from_user.id
    phone_number = message.contact.phone_number

    # Получаем ранее введенное имя
    user_info = user_data.pop(telegram_id, {})
    full_name = user_info.get("full_name", "Пользователь")
    username = user_info.get("username", None)

    # Создаем пользователя в БД
    user = await sync_to_async(User.objects.create)(
        telegram_id=telegram_id,
        username=username or f"user_{telegram_id}",
        first_name=full_name,
        phone_number=phone_number
    )

    await message.answer("✅ Регистрация завершена! Вы можете пользоваться ботом.", reply_markup=customer_keyboard)


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
        await bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode="HTML")
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

    await call.message.answer(message, parse_mode="HTML")

@dp.message(Command("link"))
async def link_telegram(message: types.Message):
    """Привязка Telegram ID к аккаунту"""
    args = message.text.split()
    if len(args) != 2 or not args[1].isdigit():
        await message.reply("❌ Используйте формат: /link <ID_пользователя>")
        return

    user_id = int(args[1])
    from core.models import User  # Импортируем здесь, чтобы избежать проблем с зависимостями

    user = await sync_to_async(User.objects.filter(id=user_id).first)()
    if user:
        user.telegram_id = message.from_user.id  # Привязка Telegram ID
        await sync_to_async(user.save)()
        await message.reply("✅ Telegram успешно привязан к вашему аккаунту!")
    else:
        await message.reply("❌ Пользователь не найден.")




# 🔹 Обработчик команды /orders
@dp.message(Command("orders"))
async def get_orders(message: types.Message):
    """Получить список заказов"""
    headers = {"Authorization": f"Bearer {settings.TELEGRAM_BOT_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/orders/", headers=headers) as response:
            if response.status == 200:
                orders = await response.json()
                if not orders:
                    await message.answer("📭 У вас пока нет заказов.")
                    return

                text = "📋 **Список заказов:**\n\n"
                for order in orders:
                    products_list = ", ".join([product['name'] for product in order['products']])
                    text += f"🆔 {order['id']} | Товары: {products_list} | Статус: {order['status']}\n"

                await message.answer(text, parse_mode="HTML")
            else:
                await message.answer(f"❌ Ошибка получения заказов. Статус ответа API: {response.status}")
                # Логируем детали ответа
                response_text = await response.text()
                print(f"API response: {response_text}")





# 🔹 Обработчик команды /order <id>
@dp.message(Command("order"))
async def order_detail(message: types.Message):
    """Получить детали конкретного заказа"""
    try:
        order_id = int(message.text.split()[1])
        headers = {"Authorization": f"Bearer {settings.TELEGRAM_BOT_TOKEN}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{API_URL}/orders/{order_id}/", headers=headers) as response:
                if response.status == 200:
                    order = await response.json()
                    delivery_address = order.get('delivery_address', 'Не указан')

                    # Получаем дату заказа из поля 'created_at', которое переименовано в 'order_date' на сервере
                    created_at = order.get('created_at',
                                           'Дата не доступна')  # Уже получаем как 'created_at' через сериализатор

                    products_list = ", ".join([product['name'] for product in order['products']])
                    text = (
                        f"🛒 **Заказ {order['id']}**\n"
                        f"📦 Товары: {products_list}\n"
                        f"📍 Доставка: {delivery_address}\n"
                        f"📅 Дата: {created_at}\n"
                        f"📌 Статус: {order['status']}\n"
                        f"💰 Сумма: {order['total_price']} руб."
                    )
                    await message.answer(text, parse_mode="HTML")
                elif response.status == 404:
                    await message.answer("❌ Заказ не найден. Проверьте ID.")
                else:
                    await message.answer("❌ Ошибка при получении данных заказа.")
    except (IndexError, ValueError):
        await message.answer("⚠️ Введите корректный ID заказа. Пример: `/order 7`")


# 🔹 Обработчик оформления заказа
@dp.message(Command("new_order"))
async def new_order(message: types.Message, state: FSMContext):
    """Оформление нового заказа с выбором адреса"""
    user_id = message.from_user.id
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/user/{user_id}/address") as response:
            if response.status == 200:
                user_data = await response.json()
                saved_address = user_data.get("delivery_address")

                if saved_address:
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text=f"📍 {saved_address}", callback_data="use_saved_address")],
                        [InlineKeyboardButton(text="🆕 Ввести новый", callback_data="new_address")]
                    ])
                    await message.answer("Выберите адрес доставки:", reply_markup=keyboard)
                else:
                    await message.answer("Введите ваш адрес доставки:")
                    await state.set_state("waiting_for_address")


@dp.message(F.state == "waiting_for_address")
async def get_delivery_address(message: types.Message, state: FSMContext):
    """Сохранение нового адреса"""
    user_id = message.from_user.id
    address = message.text

    async with aiohttp.ClientSession() as session:
        await session.post(f"{API_URL}/user/{user_id}/address", json={"delivery_address": address})

    await message.answer(f"✅ Адрес сохранен: {address}\nТеперь можно оформить заказ!")
    await state.clear()


@dp.callback_query(F.data == "use_saved_address")
async def use_saved_address(callback: CallbackQuery):
    """Использование сохраненного адреса"""
    user_id = callback.from_user.id
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/user/{user_id}/address") as response:
            if response.status == 200:
                user_data = await response.json()
                address = user_data.get("delivery_address", "Не указан")

                await callback.message.answer(f"✅ Используем сохраненный адрес: {address}\nЗаказ оформлен!")
                # Здесь можно отправить данные заказа на API

    await callback.answer()




# 🔹 Обработчик inline-кнопок (админка)
@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    """Обработчик нажатий на кнопки админки"""
    if call.from_user.id != ADMIN_ID:
        await call.answer("🚫 У вас нет прав для выполнения этого действия.", show_alert=True)
        return

    data_parts = call.data.split("_")
    if len(data_parts) != 2:
        await call.answer("❌ Ошибка данных!", show_alert=True)
        return

    action, order_id = data_parts
    if not order_id.isdigit():
        await call.answer("❌ Неверный формат ID заказа.", show_alert=True)
        return

    order_id = int(order_id)

    status_mapping = {
        "confirm": "processing",
        "in_delivery": "delivering",
        "cancel": "canceled"
    }

    if action not in status_mapping:
        await call.answer("❌ Некорректное действие!", show_alert=True)
        return

    new_status = status_mapping[action]

    headers = {"Authorization": f"Bearer {settings.TELEGRAM_BOT_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_URL}/orders/{order_id}/update/", json={"status": new_status}, headers=headers) as response:
            if response.status == 200:
                await call.message.edit_text(f"✅ Заказ {order_id} теперь {new_status}")
            else:
                await call.message.answer("❌ Ошибка обновления заказа.")


# 🔹 Запуск бота
async def main():
    """Запуск бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())