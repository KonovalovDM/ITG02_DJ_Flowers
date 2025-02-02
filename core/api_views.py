# API для заказов

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Order, Product
from .serializers import OrderSerializer, ProductSerializer

@api_view(['GET'])
def product_list(request):
    """Список всех товаров"""
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def order_list(request):
    """Список всех заказов"""
    orders = Order.objects.all()
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def update_order_status(request, order_id):
    """Обновление статуса заказа"""
    try:
        order = Order.objects.get(id=order_id)
        order.status = request.data.get('status', order.status)
        order.save()
        return Response({'message': 'Статус заказа обновлен'}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)