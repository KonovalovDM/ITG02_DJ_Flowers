# Этот файл анализирует данные из базы и генерирует отчёты

import csv
import datetime
from core.models import Order
from django.http import HttpResponse
from django.utils.timezone import now


def generate_sales_report():
    """
    Генерирует сводный отчет о продажах.
    :return: Список данных о продажах.
    """
    today = now().date()
    orders = Order.objects.filter(order_date=today)

    total_orders = orders.count()
    total_revenue = sum(order.total_price() for order in orders)

    return {
        "date": today,
        "total_orders": total_orders,
        "total_revenue": total_revenue,
    }


def export_sales_report_csv():
    """
    Экспортирует отчет о продажах в CSV-файл.
    :return: CSV-файл с данными о заказах.
    """
    today = now().date()
    filename = f"sales_report_{today}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Дата", "ID заказа", "Клиент", "Сумма", "Статус"])

        for order in Order.objects.filter(order_date=today):
            writer.writerow([
                order.order_date,
                order.id,
                order.user.username,
                order.total_price(),
                order.get_status_display()
            ])

    return filename
