from django.urls import path
from .views import catalog, cart, place_order, order_history, register

urlpatterns = [
    path("", catalog, name="catalog"),  # Каталог теперь доступен по /catalog/
    path("cart/", cart, name="cart"),
    path("order/", place_order, name="place_order"),
    path("history/", order_history, name="order_history"),
    path("register/", register, name="register"),  # Страница регистрации
]
