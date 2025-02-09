# Маршруты API

from django.urls import path
from .api_views import order_list, order_detail, update_order_status, product_list, save_delivery_address, get_delivery_address

urlpatterns = [
    path('products/', product_list, name='product_list'),
    path('orders/', order_list, name='order_list'),
    path('orders/<int:order_id>/', order_detail, name='order_detail'),
    path('orders/<int:order_id>/update/', update_order_status, name='update_order_status'),
    path('user/address/', get_delivery_address, name='get_delivery_address'),
    path('user/address/save/', save_delivery_address, name='save_delivery_address'),

]
