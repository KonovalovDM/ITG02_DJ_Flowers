from rest_framework import serializers
from .models import Order, Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    # Сериализация связанных товаров
    products = ProductSerializer(many=True)

    # Переименуем поле 'order_date' в 'created_at', чтобы соответствовать ожиданиям в боте
    created_at = serializers.DateTimeField(source='order_date')

    class Meta:
        model = Order
        fields = ['id', 'user', 'products', 'status', 'order_date', 'created_at', 'total_price']
