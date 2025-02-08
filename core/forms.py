from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User
from .models import Order

class UserRegisterForm(UserCreationForm):
    """Форма регистрации пользователя с добавлением Telegram ID"""
    telegram_username = forms.CharField(max_length=32, required=False, help_text="Введите ваш Telegram username (необязательно)")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "telegram_username"]


class OrderForm(forms.ModelForm):
    """Форма оформления заказа"""
    class Meta:
        model = Order
        fields = ['products']
