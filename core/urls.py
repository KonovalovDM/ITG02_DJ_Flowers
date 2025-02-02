from django.urls import path
from .views import catalog, cart, place_order, order_history

urlpatterns = [
    path('catalog/', catalog, name='catalog'),
    path('cart/', cart, name='cart'),
    path('order/', place_order, name='place_order'),
    path('history/', order_history, name='order_history'),
]
