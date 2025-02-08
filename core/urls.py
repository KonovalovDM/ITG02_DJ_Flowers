from django.urls import path
from .views import catalog, cart, place_order, order_history, register, add_to_cart, cart_view

urlpatterns = [
    path("", catalog, name="catalog"),  # Каталог
    path("add_to_cart/<int:product_id>/", add_to_cart, name="add_to_cart"),  # Добавление в корзину
    path("cart/", cart_view, name="cart"),  # Корзина
    path("order/", place_order, name="place_order"),  # Оформление заказа
    path("history/", order_history, name="order_history"),  # История заказов
    path("register/", register, name="register"),  # Регистрация
]
