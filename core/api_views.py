# API для заказов

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Order, Product
from .serializers import OrderSerializer, ProductSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from django.views.decorators.csrf import csrf_exempt

@api_view(['GET'])
def product_list(request):
    """Список всех товаров"""
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)



@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Проверяем, авторизован ли пользователь
def order_list(request):
    """Список заказов: админ видит все, пользователи — только свои"""
    if request.user.is_staff:
        orders = Order.objects.all()  # Администратор видит все заказы
    else:
        orders = Order.objects.filter(user=request.user)  # Обычный пользователь — только свои

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)

@csrf_exempt  # Отключает CSRF для этого API-метода
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_order_status(request, order_id):
    """Обновление статуса заказа"""
    try:
        order = Order.objects.get(id=order_id)
        new_status = request.data.get('status', order.status)
        print(f"Обновление заказа {order_id} -> {new_status}")  # Добавляем отладку
        order.status = new_status
        order.save()
        order.refresh_from_db()  # Добавляем обновление ORM
        return Response({'message': 'Статус заказа обновлен', 'status': order.status}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_order_detail(request, order_id):
    """Детали конкретного заказа"""
    try:
        order = Order.objects.get(id=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=404)


