# Этот файл добавляет пути для отображения аналитики

from django.urls import path
from .views import sales_report_view, download_sales_report

urlpatterns = [
    path("sales/", sales_report_view, name="sales_report"),
    path("sales/download/", download_sales_report, name="download_sales_report"),
]
