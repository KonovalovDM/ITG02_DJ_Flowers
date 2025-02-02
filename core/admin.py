from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from django.utils.html import format_html
from .models import Report

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