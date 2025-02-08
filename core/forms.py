from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Order

class UserRegisterForm(UserCreationForm):
    """Форма регистрации пользователя с добавлением Telegram ID"""
    telegram_id = forms.IntegerField(required=False, help_text="Введите ваш Telegram ID (необязательно)")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "telegram_id"]


class OrderForm(forms.ModelForm):
    """Форма оформления заказа"""
    class Meta:
        model = Order
        fields = ['products']
