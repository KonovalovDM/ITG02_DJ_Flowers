from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.urls import path
from django.shortcuts import redirect
from .models import Report, Product, Order, User

admin.site.register(Product)
admin.site.register(User, UserAdmin)

class ReportAdmin(admin.ModelAdmin):
    change_list_template = "admin/reports.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path("reports/", self.admin_site.admin_view(self.reports_view), name="admin-reports"),
        ]
        return custom_urls + urls

    def reports_view(self, request):
        return redirect("/reports/sales/")

admin.site.register(Report, ReportAdmin)

class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'order_date', 'total_price', 'delivery_address')
    list_filter = ('status', "order_date")
    search_fields = ('user__username', 'id')
    ordering = ("-order_date",)
    list_editable = ("status", "delivery_address")  # ✅ Теперь можно редактировать в списке заказов
    fields = ("user", "products", "status", "order_date", "total_price", "delivery_address")  # ✅ Позволяем изменять внутри заказа

    def total_price(self, obj):
        return obj.total_price  # Теперь используется свойство модели

    total_price.short_description = "Общая стоимость"  # Название в админке

admin.site.register(Order, OrderAdmin)  # Оставляем только одну регистрацию с кастомной админкой


from django.contrib import admin
from .models import Order