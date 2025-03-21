# Этот файл добавляет страницу с аналитикой в админку

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from .analytics import generate_sales_report, export_sales_report_csv
from core.models import Report
from datetime import datetime, timedelta
from django.utils import timezone

@staff_member_required
def sales_report_view(request):
    """Страница отчётов о продажах для администратора."""
    today = datetime.now().date() - timedelta(days=1)  # Используем timezone для корректной работы с временем
    yesterday = today - timedelta(days=30)

    report = Report.objects.order_by("-date").first()

    # Если отчёта нет за вчера, создаём новый
    if not report or report.date < yesterday:
        report = generate_sales_report(yesterday, today)

    # Добавляем информацию о периоде отчёта и времени формирования
    report.period = f"с {yesterday.strftime('%d.%m.%Y')} по {today.strftime('%d.%m.%Y')}"
    report.generated_at = timezone.now().strftime("%d.%m.%Y %H:%M:%S")

    return render(request, "reports/sales_report.html", {"report": report})


@staff_member_required
def download_sales_report(request):
    """
    Скачать отчёт в формате CSV.
    """
    filename = export_sales_report_csv()
    with open(filename, "r", encoding="utf-8") as file:
        response = HttpResponse(file, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
