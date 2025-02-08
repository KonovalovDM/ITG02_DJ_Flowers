# Модели базы данных
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model

class User(AbstractUser):
    """Расширенная модель пользователя"""
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True, verbose_name="Telegram ID")
    # Поле is_staff уже есть в AbstractUser, его переопределять не нужно
    # is_admin обычно определяется через is_superuser, который тоже уже есть в AbstractUser
#    is_staff = models.BooleanField(default=False, verbose_name="Сотрудник")
#    is_admin = models.BooleanField(default=False, verbose_name="Администратор")

    def __str__(self):
        return self.telegram_id or self.username

    @property
    def is_admin(self):
        return self.is_superuser

    @property
    def is_staff_user(self):
        return self.is_staff

    @property
    def is_regular_user(self):
        return not self.is_staff and not self.is_superuser

class Product(models.Model):
    """Модель для хранения информации о цветах"""
    name = models.CharField(max_length=255, verbose_name="Название")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    image = models.ImageField(upload_to="products/", verbose_name="Изображение")

    def __str__(self):
        return self.name


class Order(models.Model):
    """Модель заказа"""
    STATUS_CHOICES = [
        ('pending', 'В обработке'),
        ('processing', 'В работе'),
        ('delivering', 'В доставке'),
        ('completed', 'Выполнен'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    products = models.ManyToManyField(Product, verbose_name="Товары")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")

    def __str__(self):
        return f"Заказ {self.id} - {self.user.username}"


class Report(models.Model):
    """Модель отчета по заказам"""
    date = models.DateField(auto_now_add=True, verbose_name="Дата отчета")
    total_orders = models.PositiveIntegerField(verbose_name="Количество заказов")
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Выручка")

    def __str__(self):
        return f"Отчет {self.date}"
