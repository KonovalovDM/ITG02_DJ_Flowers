"""
__init__.py – делает папку bot модулем
"""

from .bot import bot, dp    # Подключаем бота и диспетчер
# from bot.handlers import router

# Подключаем обработчики команд
# dp.include_router(router)