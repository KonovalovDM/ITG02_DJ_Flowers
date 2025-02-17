# API для заказов
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from django.views.decorators.csrf import csrf_exempt
from .models import Order, Product
from .serializers import OrderSerializer, ProductSerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny

@api_view(['GET'])
def product_list(request):
    """Список всех товаров"""
    products = Product.objects.all()
    serializer = ProductSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def order_list(request):
    """Список заказов: админ видит все, пользователи — только свои"""
    if request.user.is_staff:
        orders = Order.objects.all()  # Администратор видит все заказы
    else:
        orders = Order.objects.filter(user=request.user)  # Обычный пользователь — только свои

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Требуется аутентификация для обновления статуса
def update_order_status(request, order_id):
    """Обновление статуса заказа"""
    try:
        order = Order.objects.get(id=order_id)

        # Проверка прав пользователя (админ или сам пользователь)
        if not (request.user.is_staff or order.user == request.user):
            return Response({'error': 'Недостаточно прав для изменения статуса заказа'},
                            status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status', order.status)
        if new_status not in ['processing', 'delivering', 'canceled']:
            return Response({'error': 'Неверный статус'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        return Response({'message': 'Статус заказа обновлен', 'status': order.status}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def order_detail(request, order_id):
    """Детали конкретного заказа"""
    try:
        order = Order.objects.get(id=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=404)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_delivery_address(request):
    """Получить сохраненный адрес доставки"""
    user = request.user
    return Response({'delivery_address': user.delivery_address or 'Не указан'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_delivery_address(request):
    """Сохранить новый адрес доставки"""
    user = request.user
    new_address = request.data.get('delivery_address', '').strip()

    if not new_address:
        return Response({'error': 'Адрес не может быть пустым'}, status=status.HTTP_400_BAD_REQUEST)

    user.delivery_address = new_address
    user.save()
    return Response({'message': 'Адрес доставки сохранен'}, status=status.HTTP_200_OK)

@csrf_exempt
@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Доступ только авторизованным
def api_orders(request):
    """Возвращает список заказов (для бота)"""
    if request.user.is_staff:
        orders = Order.objects.all()  # Админ видит все заказы
    else:
        orders = Order.objects.filter(user=request.user)  # Пользователь видит только свои заказы

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
