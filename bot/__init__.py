"""
__init__.py – инициализация Telegram-бота
"""

from bot.bot import bot, dp
from bot.handlers import router

# Подключаем обработчики команд
dp.include_router(router)
