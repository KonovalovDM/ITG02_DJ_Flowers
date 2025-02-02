# Маршруты API

from django.urls import path
from .api_views import order_list, update_order_status, product_list

urlpatterns = [
    path('products/', product_list, name='product_list'),
    path('orders/', order_list, name='order_list'),
    path('orders/<int:order_id>/update/', update_order_status, name='update_order_status'),
]
