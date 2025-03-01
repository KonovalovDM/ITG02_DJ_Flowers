# Модели базы данных
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth import get_user_model


class User(AbstractUser):
    """Расширенная модель пользователя"""
    telegram_id = models.BigIntegerField(null=True, blank=True, unique=True, verbose_name="Telegram ID")
    telegram_username = models.CharField(max_length=32, null=True, blank=True, verbose_name="Telegram Username")
    phone_number = models.CharField(max_length=15, null=True, blank=True, unique=True, verbose_name="Телефон")
    delivery_address = models.TextField(null=True, blank=True)  # Поле для сохранения адреса


    def __str__(self):
        # Преобразуем telegram_id в строку, если оно не None, иначе возвращаем username
        return str(self.telegram_id) if self.telegram_id is not None else self.username

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
    price = models.DecimalField(max_digits=10, decimal_places=2, default=1000.0, verbose_name="Цена")
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
        ("canceled", "Отменён"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    products = models.ManyToManyField(Product, verbose_name="Товары")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Статус")
    order_date = models.DateTimeField(auto_now_add=True, verbose_name="Дата заказа")
    delivery_address = models.CharField(max_length=255, blank=True, null=True,
                                        verbose_name="Адрес доставки")

    @property
    def total_price(self):
        return sum(product.price for product in self.products.all())    # ✅ Вычисляем сумму заказа

    def __str__(self):
        return f"Заказ {self.id} - {self.user.username}"


class Report(models.Model):
    """Модель отчета по заказам с разбивкой по статусам"""
    date = models.DateField(auto_now_add=True, verbose_name="Дата отчета")

    # Общие суммы и количество
    total_orders = models.PositiveIntegerField(default=0, verbose_name="Всего заказов")
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Общая выручка")

    # Разбивка по статусам
    pending_orders = models.PositiveIntegerField(default=0, verbose_name="В обработке (заказы)")
    pending_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="В обработке (выручка)")

    processing_orders = models.PositiveIntegerField(default=0, verbose_name="В работе (заказы)")
    processing_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="В работе (выручка)")

    delivering_orders = models.PositiveIntegerField(default=0, verbose_name="В доставке (заказы)")
    delivering_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="В доставке (выручка)")

    completed_orders = models.PositiveIntegerField(default=0, verbose_name="Выполнен (заказы)")
    completed_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Выполнен (выручка)")

    canceled_orders = models.PositiveIntegerField(default=0, verbose_name="Отменён (заказы)")
    canceled_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Отменён (выручка)")

    # @classmethod
    # def generate_report(cls):
    #     """Создает или обновляет отчет за текущий день"""
    #     from datetime import date
    #     from core.models import Order
    #
    #     today = date.today()
    #     total_orders = Order.objects.count()
    #     total_revenue = sum(order.total_price for order in Order.objects.all())
    #
    #     report, created = cls.objects.update_or_create(
    #         date=today,
    #         defaults={"total_orders": total_orders, "total_revenue": total_revenue}
    #     )
    #     return report

    def __str__(self):
        return f"Аналитика {self.date}"

    class Meta:
        verbose_name = "Отчет"
        verbose_name_plural = "Отчеты"

