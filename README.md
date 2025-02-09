# ITG02_DJ_Flowers
 Проекта_на_Django "Telegram_bot_FlowerDelivery"

    Проект сайта FlowerDelivery с привязанным к нему Телеграмм ботом
    Реализована регистрация на сайте и через бота
    Права staff и admin раздаются на сайте администраиором после регистрации
    При регистрации всем присваиваются права user
    Прект задумывался к реализации с уровнем Advanced с добавлением элементов Master
    Т.е. реализована аналитика, не реализованы отзывы
    Идентификация по Telegram_ID и номеру телефона
    

#### Запуск программы 

    python manage.py runserver


#### Запуск Телеграмм бота

    python -m bot.bot

Примерная струкутура проекта

        ITG02_DJ_Flowers/                     # Корневая папка проекта
        │── manage.py                      # Управление проектом Django
        │── requirements.txt                # Список зависимостей
        │── db.sqlite3                      # База данных (SQLite)
        │
        ├── flowers/                   # Основная конфигурация Django
        │   │── __init__.py
        │   │── settings.py                  # Настройки Django (здесь будет токен бота)
        │   │── urls.py                       # Главный роутинг
        │   │── wsgi.py                       # WSGI сервер для продакшена
        │   │── asgi.py                       # ASGI сервер (если будет WebSocket)
        │
        ├── core/                            # Основное приложение
        │   │── __init__.py
        │   │── models.py                     # Модели базы данных
        │   │── views.py                      # Вьюхи для сайта
        │   │── urls.py                       # URL-маршруты
        │   │── forms.py                      # Формы для ввода данных
        │   │── admin.py                      # Регистрация моделей в админке
        │   │── serializers.py                 # API сериализаторы
        │   │── telegram_bot.py                # Код для Telegram-бота
        │   │── api_views.py                   # API для заказов
        │
        │── static/                          # Статические файлы (Bootstrap, CSS, JS, изображения)
        │   │── css/
        │   │── js/
        │   │── images/
        │
        │── templates/                       # HTML-шаблоны (Jinja)
        │   │── base.html                     # Общий шаблон
        │   │── index.html                     # Главная страница
        │   │── catalog.html                   # Каталог товаров
        │   │── cart.html                      # Корзина
        │   │── order_history.html             # История заказов
        │   │── order_detail.html              # Детали заказа
        │   │── admin_orders.html              # Управление заказами
        │
        │── bot/                              # Телеграм-бот
        │   │── __init__.py
        │   │── bot.py                         # Основной код бота
 
        │
        └── reports/                           # Отчёты и аналитика
            │── views.py                        # Вьюхи
            │── analytics.py                    # Анализ данных
            │── urls.py                         # Пути