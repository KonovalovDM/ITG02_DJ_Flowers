# Этот файл добавляет страницу с аналитикой в админку

from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from .analytics import generate_sales_report, export_sales_report_csv

@staff_member_required
def sales_report_view(request):
    """
    Страница отчетов о продажах для администратора.
    """
    report = generate_sales_report()
    return render(request, "reports/sales_report.html", {"report": report})

@staff_member_required
def download_sales_report(request):
    """
    Скачать отчет в формате CSV.
    """
    filename = export_sales_report_csv()
    with open(filename, "r", encoding="utf-8") as file:
        response = HttpResponse(file, content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={filename}"
        return response
