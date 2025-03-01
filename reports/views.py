# Этот файл добавляет страницу с аналитикой в админку

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from .analytics import generate_sales_report, export_sales_report_csv
from core.models import Report


@staff_member_required
def sales_report_view(request):
    """Страница отчётов о продажах для администратора."""
    report = Report.objects.order_by("-date").first()

    # Если отчёта нет — создаем новый
    if not report or report.date != now().date():
        report = generate_sales_report()

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
