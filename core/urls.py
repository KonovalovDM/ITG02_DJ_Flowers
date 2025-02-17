from django.urls import path
from .views import catalog, cart, place_order, order_history, register, add_to_cart, cart_view
from .views import profile  # Импортируем функцию профиля
from core.api_views import order_list  # Подключаем обработчик API-заказов



urlpatterns = [
    path("", catalog, name="catalog"),  # Каталог
    path("add_to_cart/<int:product_id>/", add_to_cart, name="add_to_cart"),  # Добавление в корзину
    path("cart/", cart_view, name="cart"),  # Корзина
    path("order/", place_order, name="place_order"),  # Оформление заказа
    path("history/", order_history, name="order_history"),  # История заказов
    path("register/", register, name="register"),  # Регистрация
    path("profile/", profile, name="profile"),
    path("api/orders/", order_list, name="api_orders"),  # API-заказы

]