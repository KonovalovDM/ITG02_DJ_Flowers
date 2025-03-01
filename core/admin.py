from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import redirect
from .models import Report, Product, Order, User
from django.contrib.admin.sites import site

admin.site.register(Product)
admin.site.register(User, UserAdmin)

class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "telegram_id", "email", "is_staff", "is_superuser")
    search_fields = ("username", "telegram_id", "email")

    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительная информация", {"fields": ("telegram_id",)}),
    )

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_username', 'get_telegram_id', 'status', 'order_date', 'total_price_display', 'delivery_address')
    list_filter = ('status', "order_date")
    search_fields = ('user__username', 'user__telegram_id', 'id')
    ordering = ("-order_date",)
    list_editable = ("status", "delivery_address")  # ✅ Разрешаем менять статус и адрес прямо в списке
    # ✅ Исключаем `order_date` из полей редактирования
    readonly_fields = ("order_date", "total_price_display")   # ✅ Эти поля редактировать нельзя
    fields = ("user", "products", "status", "delivery_address", "total_price_display")  # ✅ Доступные поля при редактировании

    # ✅ Отображение суммы заказа
    @admin.display(description="Общая стоимость")  # Название в админке
    def total_price_display(self, obj):
        return f"{obj.total_price} руб."  # ✅ Теперь это корректно отображается

    def get_username(self, obj):
        return obj.user.username

    get_username.short_description = "Имя пользователя"

    def get_telegram_id(self, obj):
        return obj.user.telegram_id if obj.user.telegram_id else "Не указан"

    get_telegram_id.short_description = "Telegram ID"

if site.is_registered(Order):
    admin.site.unregister(Order)
admin.site.register(Order, OrderAdmin)

class ReportAdmin(admin.ModelAdmin):
    list_display = ("date", "total_orders", "total_revenue")
    ordering = ("-date",)
    readonly_fields = ("date", "total_orders", "total_revenue")  # ✅ Делаем отчеты только для чтения

if site.is_registered(Report):
    admin.site.unregister(Report)
admin.site.register(Report, ReportAdmin)

