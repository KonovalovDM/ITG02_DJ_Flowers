# API для заказов
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, serializers
from django.views.decorators.csrf import csrf_exempt
from .models import Order, Product, User
from .serializers import OrderSerializer, ProductSerializer
from django.shortcuts import get_object_or_404
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
        print(f"🔍 Получен запрос на обновление заказа {order.id}")  # ✅ Лог запроса

        # Проверка прав пользователя (админ или сам пользователь)
        if not (request.user.is_staff or order.user == request.user):
            print("🚫 Недостаточно прав для изменения статуса заказа")  # ✅ Лог ошибки прав
            return Response({'error': 'Недостаточно прав для изменения статуса заказа'},
                            status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status', order.status)
        print(f"🔄 Новый статус: {new_status}")  # ✅ Логируем переданный статус
        if new_status not in ['processing', 'delivering', 'completed', 'canceled']:  # ✅ Добавили 'completed'
            print("❌ Неверный статус!")  # ✅ Лог ошибки статуса
            return Response({'error': 'Неверный статус'}, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()
        print(f"✅ Статус заказа {order.id} успешно обновлен: {order.status}")  # ✅ Лог успешного обновления

        return Response({'message': 'Статус заказа обновлен', 'status': order.status}, status=status.HTTP_200_OK)
    except Order.DoesNotExist:
        print("❌ Заказ не найден!")  # ✅ Лог ошибки отсутствия заказа
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # <-- Только для авторизованных
def order_detail(request, order_id):
    """Детали заказа: админ видит все, пользователь — только свои"""
    try:
        order = Order.objects.get(id=order_id)

        if not request.user.is_staff and order.user != request.user:
            return Response({'error': 'Доступ запрещен'}, status=status.HTTP_403_FORBIDDEN)

        serializer = OrderSerializer(order)
        return Response(serializer.data)

    except Order.DoesNotExist:
        return Response({'error': 'Заказ не найден'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])  # <-- Только для авторизованных
def get_delivery_address(request):
    """Получить сохраненный адрес доставки"""
    user = request.user
    return Response({'delivery_address': user.delivery_address or 'Не указан'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])  # <-- Только для авторизованных
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
    """Админ видит все заказы, пользователь — только свои"""
    if request.user.is_staff:
        orders = Order.objects.all()  # Админ видит все заказы
    else:
        orders = Order.objects.filter(user=request.user)  # Пользователь видит только свои заказы

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

import logging
logger = logging.getLogger(__name__)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_orders(request):
    user = request.user
    telegram_id = request.query_params.get('telegram_id')

    if telegram_id:
        user = User.objects.filter(telegram_id=telegram_id).first()
        if not user:
            return Response({'error': 'Пользователь не найден'}, status=status.HTTP_404_NOT_FOUND)

    # Админ видит все заказы, пользователь только свои
    orders = Order.objects.all() if user.is_staff else Order.objects.filter(user=user)

    logger.debug(f"📦 {user.username} запросил заказы: {[order.id for order in orders]}")

    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_order_details(request, order_id):
    """Возвращает детали заказа, но только если он принадлежит пользователю"""
    user = request.user  # Получаем авторизованного пользователя

    if user.is_staff:
        order = get_object_or_404(Order, id=order_id)  # Админ видит все заказы
    else:
        order = get_object_or_404(Order, id=order_id, user=user)  # Пользователь только свои

    logger.debug(f"📦 Запрошен заказ {order.id} пользователем {user.username}")

    serializer = OrderSerializer(order)
    return Response(serializer.data)




