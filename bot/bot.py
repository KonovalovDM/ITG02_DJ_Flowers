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
TELEGRAM_ADMIN_ID = settings.TELEGRAM_ADMIN_ID

# URL API Django-сервера
API_URL = settings.API_URL

# Для API-запросов в bot.py используем TELEGRAM_API_TOKEN
headers = {"Authorization": f"Token {settings.TELEGRAM_API_TOKEN}"}

# 🔹 Клавиатуры
customer_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
])

staff_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="orders")],
])

admin_static_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="📦 Мои заказы", callback_data="admin_orders")],
    [InlineKeyboardButton(text="📊 Аналитика", callback_data="analytics")]
])


def create_admin_keyboard(order_id):
    """Создает клавиатуру управления конкретным заказом"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{order_id}")],
        [InlineKeyboardButton(text="🚚 В доставке", callback_data=f"in_delivery_{order_id}")],
        [InlineKeyboardButton(text="✅ Завершить", callback_data=f"complet_{order_id}")],  # Добавляем "Завершить"
        [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{order_id}")]
    ])

import re

# 🔹 Функция экранирования специальных символов MarkdownV2
def escape_md(text):
    """Экранирует специальные символы MarkdownV2"""
    return re.sub(r"([_*\[\]()~`>#\+\-=|{}.!])", r"\\\1", str(text))


def get_keyboard_for_user(user):
    """Выбирает клавиатуру в зависимости от роли пользователя"""
    if user.is_superuser:
        return admin_static_keyboard  # Только общие кнопки
    elif user.is_staff:
        return staff_keyboard
    return customer_keyboard


request_contact_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="📲 Отправить контакт", request_contact=True)]],
    resize_keyboard=True
)


# 🔹 Обработчик /start
@dp.message(Command("start"))
async def start(message: types.Message):
    """Приветствие и автоматическая регистрация пользователя"""
    from core.models import User

    telegram_id = message.from_user.id
    username = message.from_user.username

    user = await sync_to_async(User.objects.filter(telegram_id=telegram_id).first, thread_sensitive=True)()

    if user:
        keyboard = get_keyboard_for_user(user)
        await message.answer("🌸 Добро пожаловать! Вы авторизованы.", reply_markup=keyboard)
    else:
        await message.answer("🔹 Добро пожаловать! Введите ваше имя для регистрации.")
        dp.message.register(get_user_name, F.text)


# 🔹 Обработчик выбора заказа для админа
@dp.callback_query(lambda c: c.data == "admin_orders")
async def show_admin_orders(callback_query: types.CallbackQuery):
    """Выводит список заказов с кнопками управления"""
    headers = {"Authorization": f"Token {settings.TELEGRAM_API_TOKEN}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/orders/", headers=headers) as response:
            if response.status == 200:
                orders = await response.json()
                if not orders:
                    await callback_query.message.answer("📭 Нет активных заказов.")
                    return

                text = "📋 **Список заказов:**\n\n"
                for order in orders:
                    text += f"🆔 {order['id']} | Статус: {order['status']}\n"
                    keyboard = create_admin_keyboard(order["id"])
                    await callback_query.message.answer(text, reply_markup=keyboard)

            else:
                await callback_query.answer("❌ Ошибка получения заказов!", show_alert=True)


# 🔹 Обработчик inline-кнопок (админка)
@dp.callback_query()
async def handle_callback(call: types.CallbackQuery):
    """Обработчик админских действий с заказами (только для админов и персонала)"""
    from core.models import User

    print(f"🔹 Получен callback_data: {call.data}")  # ✅ Лог входящих данных

    # ✅ Проверяем, является ли пользователь админом или сотрудником
    user = await asyncio.to_thread(lambda: User.objects.filter(telegram_id=call.from_user.id).first())

    if not user:
        await call.answer("🚫 Ошибка: пользователь не найден.", show_alert=True)
        return

    if not user.is_staff and not user.is_superuser:
        # ✅ Передаем обработку в show_user_orders (если это обычный пользователь)
        await show_user_orders(call)
        return

    # ✅ Код ниже выполняется только для админов и персонала
    data_parts = call.data.rsplit("_", 1)  # ✅ Разделяем только по последнему "_"

    if len(data_parts) == 1:
        if data_parts[0] == "analytics":
            await send_analytics(call)  # Теперь аналитика вызывается корректно
        elif data_parts[0] == "admin_orders":
            await show_admin_orders(call)
        else:
            await call.answer("❌ Ошибка данных!", show_alert=True)
        return

    if len(data_parts) != 2:
        print("❌ Ошибка данных! data_parts:", data_parts)  # ✅ Лог ошибки формата
        await call.answer("❌ Ошибка данных!", show_alert=True)
        return

    action, order_id = data_parts
    if not order_id.isdigit():
        print(f"❌ Неверный формат ID заказа: {order_id}")  # ✅ Лог ошибки ID
        await call.answer("❌ Неверный формат ID заказа.", show_alert=True)
        return

    order_id = int(order_id)
    status_mapping = {
        "confirm": "processing",        # В работе
        "in_delivery": "delivering",    # В доставке
        "cancel": "canceled",           # Отменён
        "complet": "completed"          # Выполнен
    }

    if action not in status_mapping:
        print(f"❌ Некорректное действие: {action}")  # ✅ Лог ошибки действия
        await call.answer("❌ Некорректное действие!", show_alert=True)
        return

    new_status = status_mapping[action]
    print(f"✅ Обновление заказа {order_id}, новый статус: {new_status}")  # ✅ Лог успешного перехода к обновлению

    headers = {"Authorization": f"Token {settings.TELEGRAM_API_TOKEN}"}
    payload = {"status": new_status}

    async with aiohttp.ClientSession() as session:
        print(f"📡 Отправка запроса: {API_URL}/orders/{order_id}/update/ с данными {payload}")  # ✅ Лог запроса

        async with session.post(f"{API_URL}/orders/{order_id}/update/", json=payload, headers=headers) as response:
            response_text = await response.text()
            print(f"📡 API ответил: {response.status} - {response_text}")  # ✅ Лог ответа API

            if response.status == 200:
                new_text = f"✅ Заказ {order_id} теперь в статусе: {new_status}"
                await call.message.edit_text(new_text, reply_markup=create_admin_keyboard(order_id))  # ✅ Обновляем текст
            else:
                await call.answer("❌ Ошибка обновления заказа.", show_alert=True)

import re

def escape_md(text):
    """Экранирует специальные символы MarkdownV2"""
    return re.sub(r"([_*\[\]()~`>#\+\-=|{}.!])", r"\\\1", str(text))

# 🔹 Показываем заказы пользователя
# @dp.callback_query(F.data == "orders")
async def show_user_orders(call: types.CallbackQuery):
    """Отображает заказы обычного пользователя"""
    from core.models import User
    import aiohttp

    telegram_id = call.from_user.id

    # 🔹 Ищем пользователя в БД
    user = await asyncio.to_thread(lambda: User.objects.filter(telegram_id=telegram_id).first())

    if not user:
        await call.answer("🚫 Ошибка: пользователь не найден.", show_alert=True)
        return

    headers = {"Authorization": f"Token {settings.TELEGRAM_API_TOKEN}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_URL}/orders/", headers=headers) as response:
            if response.status != 200:
                await call.answer("❌ Ошибка получения заказов.", show_alert=True)
                return

            orders_data = await response.json()

            if not orders_data:
                await call.answer("📭 У вас пока нет заказов.", show_alert=True)
                return

    # 🔹 Формируем список заказов
    orders_text = "📦 *Ваши заказы:*\n\n"
    for order in orders_data:
        order_text = (
            f"🆔 Заказ {escape_md(str(order['id']))}\n"
            f"📍 Адрес: {escape_md(str(order['delivery_address']))}\n"
            f"💰 Сумма: {escape_md(str(order['total_price']))} руб\n"
            f"📅 Дата: {escape_md(str(order['order_date']))}\n"
            f"📌 Статус: {escape_md(str(order['status']))}\n"
            f"{escape_md('--------------------------------')}\n"
        )

        # Если сообщение превысит лимит, отправляем часть и создаём новое
        if len(orders_text) + len(order_text) > 4000:
            await call.message.answer(orders_text, parse_mode="MarkdownV2")
            orders_text = "📦 *Ваши заказы (продолжение...)*\n\n"

        orders_text += order_text

    # Отправляем оставшуюся часть
    if orders_text:
        await call.message.answer(orders_text, parse_mode="MarkdownV2")




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
        await bot.send_message(chat_id=TELEGRAM_ADMIN_ID, text=message, parse_mode="HTML")
    except Order.DoesNotExist:
        print(f"Ошибка: заказ {order_id} не найден.")


# 🔹 Кнопка "📊 Аналитика"
@dp.callback_query(F.data == "analytics")
async def send_analytics(call: types.CallbackQuery):
    """Отправляет администраторам детальную аналитику"""
    from reports.analytics import generate_sales_report  # ⬅️ Переносим импорт внутрь функции
    from core.models import Report
    from datetime import datetime, timedelta
    import asyncio

    today = datetime.now().date()
    yesterday = today - timedelta(days=30)

    # Проверяем, есть ли отчёт за вчера
    report = await asyncio.to_thread(lambda: Report.objects.order_by("-date").first())

    if not report or report.date < yesterday:
        print("🔄 Генерация нового отчёта...")
        report = await asyncio.to_thread(lambda: generate_sales_report(yesterday, today))

    if not report:
        await call.answer("📊 Данных пока нет. Попробуйте позже.", show_alert=True)
        return

    # ✅ Приводим данные к числам, чтобы избежать форматных ошибок
    pending_orders = int(report.pending_orders)
    pending_revenue = float(report.pending_revenue)

    processing_orders = int(report.processing_orders)
    processing_revenue = float(report.processing_revenue)

    delivering_orders = int(report.delivering_orders)
    delivering_revenue = float(report.delivering_revenue)

    completed_orders = int(report.completed_orders)
    completed_revenue = float(report.completed_revenue)

    canceled_orders = int(report.canceled_orders)
    canceled_revenue = float(report.canceled_revenue)

    total_orders = pending_orders + processing_orders + delivering_orders + completed_orders
    total_revenue = pending_revenue + processing_revenue + delivering_revenue + completed_revenue

    # ✅ Формируем текст сообщения
    message = (
        f"📊 *Аналитика за 30 дней на {escape_md(report.date)}*\n"
        f"```\n"
        f"{escape_md('Статус'):<15} {escape_md('Выручка'):>10} {escape_md('Заказы'):>8}\n"
        f"{'-' * 34}\n"
        f"{escape_md('В обработке'):<15} {pending_revenue:>10.2f} {pending_orders:>8}\n"
        f"{escape_md('В работе'):<15} {processing_revenue:>10.2f} {processing_orders:>8}\n"
        f"{escape_md('В доставке'):<15} {delivering_revenue:>10.2f} {delivering_orders:>8}\n"
        f"{escape_md('Выполнено'):<15} {completed_revenue:>10.2f} {completed_orders:>8}\n"
        f"{'-' * 34}\n"
        f"{escape_md('ИТОГО'):<15} {total_revenue:>10.2f} {total_orders:>8}\n"
        f"{escape_md('Отменено'):<15} {canceled_revenue:>10.2f} {canceled_orders:>8}\n"
        f"```"
    )

    await call.message.answer(message, parse_mode="MarkdownV2")


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
    headers = {"Authorization": f"Token {settings.TELEGRAM_API_TOKEN}"}  # <-- Используем Token

    async with aiohttp.ClientSession() as session:
        print(f"🔍 Токен, переданный в API: {settings.TELEGRAM_API_TOKEN}")

        async with session.get(f"{API_URL}/orders/", headers=headers) as response:
            response_text = await response.text()
            print(f"📡 API ответил: {response_text}")  # <-- Отладка: смотрим, что вернул сервер

            if response.status == 200:
                orders = await response.json()
                if not orders:
                    await message.answer("📭 У вас пока нет заказов.")
                    return

                text = "📋 **Список заказов:**\n\n"
                for order in orders:
                    text += f"🆔 {order['id']} | Статус: {order['status']}\n"

                # Разбиваем текст на части по 4096 символов
                for chunk in [text[i:i + 4000] for i in range(0, len(text), 4000)]:
                    await message.answer(chunk, parse_mode="HTML")

            else:
                await message.answer(f"❌ Ошибка получения заказов. Код: {response.status}")
                print(response_text)  # Логируем ответ API, но не отправляем в Telegram



# 🔹 Обработчик команды /order <id>
@dp.message(Command("order"))
async def order_detail(message: types.Message):
    """Получить детали конкретного заказа"""
    try:
        order_id = int(message.text.split()[1])
        headers = {"Authorization": f"Token {settings.TELEGRAM_API_TOKEN}"}
        print(f"🔍 Отправляемый заголовок: {headers}")  # ✅ Отладочный вывод
        async with aiohttp.ClientSession() as session:
            print(f"🔍 Токен, переданный в API: {settings.TELEGRAM_API_TOKEN}")

            async with session.get(f"{API_URL}/orders/{order_id}/", headers=headers) as response:
                if response.status == 200:
                    order = await response.json()
                    print(f"🔍 Данные заказа: {order}")  # ✅ Проверка, какие данные приходят

                    # ✅ Получаем адрес доставки, если его нет, ставим "Не указан"
                    delivery_address = order.get("delivery_address", "Не указан")

                    # ✅ Получаем дату заказа, если поле называется иначе (например, order_date)
                    created_at = order.get("order_date", order.get("created_at", "Дата не указана"))

                    # ✅ Формируем список товаров
                    products_list = ", ".join([product["name"] for product in order.get("products", [])])

                    text = (
                        f"🛒 **Заказ {order.get('id', 'Неизвестный')}**\n"
                        f"📦 Товары: {products_list}\n"
                        f"📍 Доставка: {delivery_address}\n"
                        f"📅 Дата: {created_at}\n"
                        f"📌 Статус: {order.get('status', 'Неизвестен')}\n"
                        f"💰 Сумма: {order.get('total_price', '0')} руб."
                    )
                    await message.answer(text, parse_mode="HTML")

                elif response.status == 404:
                    await message.answer("❌ Заказ не найден. Проверьте ID.")

                else:
                    response_text = await response.text()
                    await message.answer(
                        f"❌ Ошибка при получении данных заказа. Код: {response.status}\n{response_text}"
                    )

    except (IndexError, ValueError):
        await message.answer("⚠️ Введите корректный ID заказа. Пример: `/order 7`")



# 🔹 Обработчик оформления заказа
@dp.message(Command("new_order"))
async def new_order(message: types.Message, state: FSMContext):
    """Оформление нового заказа с выбором адреса"""
    user_id = message.from_user.id
    async with aiohttp.ClientSession() as session:
        print(f"🔍 Токен, переданный в API: {settings.TELEGRAM_API_TOKEN}")

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
        print(f"🔍 Токен, переданный в API: {settings.TELEGRAM_API_TOKEN}")

        async with session.get(f"{API_URL}/user/{user_id}/address") as response:
            if response.status == 200:
                user_data = await response.json()
                address = user_data.get("delivery_address", "Не указан")

                await callback.message.answer(f"✅ Используем сохраненный адрес: {address}\nЗаказ оформлен!")
                # Здесь можно отправить данные заказа на API

    await callback.answer()


# 🔹 Запуск бота
async def main():
    """Запуск бота"""
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())