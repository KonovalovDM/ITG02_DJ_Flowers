"""
URL configuration for flowers project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from core import views  # Импортируем views из приложения core
# from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),  # Главная страница
    path('accounts/', include('django.contrib.auth.urls')),  # подключение стандартных маршрутов аутентификации
    path("catalog/", views.catalog, name="catalog"),
    path("cart/", views.cart, name="cart"),
    path("order/", views.place_order, name="place_order"),
    path("history/", views.order_history, name="order_history"),
    path("api/", include("core.api_urls")),  # Подключение API
]