# core/management/commands/generate_report.py

from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from reports.analytics import generate_sales_report  # функция находится в reports/analytics.py


class Command(BaseCommand):
    help = 'Generate sales report for a specific date range'

    def handle(self, *args, **kwargs):
        # Получаем сегодняшнюю дату и дату вчера
        today = datetime.now().date()
        yesterday = today - timedelta(days=51)

        # Генерируем отчёт за вчера
        report = generate_sales_report(yesterday, today)
        self.stdout.write(self.style.SUCCESS(f'Successfully generated report: {report}'))