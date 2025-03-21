# Этот файл анализирует данные из базы и генерирует отчёты

import csv
from datetime import datetime, timedelta
from core.models import Order, Report
from django.utils.timezone import now


def export_sales_report_csv():
    """
    Экспортирует отчёт о продажах в CSV-файл.
    """
    today = now().date()
    start_date = today - timedelta(days=30)  # Заказы за последние 30 дней
    filename = f"sales_report_{today}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Дата", "ID заказа", "Клиент", "Сумма", "Статус"])

        # Фильтруем заказы за последние 30 дней
        orders = Order.objects.filter(order_date__date__gte=start_date, order_date__date__lte=today)

        for order in orders:
            writer.writerow([
                order.order_date.strftime("%Y-%m-%d"),
                order.id,
                order.user.username if order.user else "Неизвестный клиент",
                order.price,
                order.get_status_display()
            ])

    return filename


def generate_sales_report(start_date: datetime, end_date: datetime, report_date=None):
    """
    Генерирует и сохраняет отчёт о продажах с разбивкой по статусам за указанный период времени.

    :param start_date: Начало периода (datetime)
    :param end_date: Конец периода (datetime)
    :param report_date: Дата отчёта (если не указана, используется end_date)
    """

    # Фильтруем заказы за указанный период
    orders = Order.objects.filter(order_date__date__gte=start_date, order_date__date__lte=end_date)
    print(f"Заказы за период с {start_date} по {end_date}: {orders.count()} шт.")

    if not orders.exists():
        print("⚠️ Нет заказов для формирования отчета.")
        return None  # Если заказов нет, возвращаем None

    # Группируем заказы по статусам
    status_counts = {status[0]: {"count": 0, "revenue": 0} for status in Order.STATUS_CHOICES}

    for order in orders:
        status_counts[order.status]["count"] += 1
        status_counts[order.status]["revenue"] += order.price  # Используем `order.price`

    # Создаём отчет и сохраняем в базу данных
    report = Report.objects.create(
        date=report_date if report_date else end_date,  # Используем report_date, если он передан
        total_orders=orders.count(),
        total_revenue=sum(order.price for order in orders),

        pending_orders=status_counts["pending"]["count"],
        pending_revenue=status_counts["pending"]["revenue"],

        processing_orders=status_counts["processing"]["count"],
        processing_revenue=status_counts["processing"]["revenue"],

        delivering_orders=status_counts["delivering"]["count"],
        delivering_revenue=status_counts["delivering"]["revenue"],

        completed_orders=status_counts["completed"]["count"],
        completed_revenue=status_counts["completed"]["revenue"],

        canceled_orders=status_counts["canceled"]["count"],
        canceled_revenue=status_counts["canceled"]["revenue"],
    )

    return report


# Пример использования функции
if __name__ == "__main__":
    # Отчёт за последний день
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    generate_sales_report(yesterday, today)

    # Отчёт за последнюю неделю
    last_week = today - timedelta(weeks=1)
    generate_sales_report(last_week, today)

    # Отчёт за последний месяц
    last_month = today - timedelta(days=30)
    generate_sales_report(last_month, today)