from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Order

class UserRegisterForm(UserCreationForm):
    """Форма регистрации пользователя с добавлением Telegram ID"""
    telegram_id = forms.IntegerField(required=False, help_text="Введите ваш Telegram ID (необязательно)")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "telegram_id", "delivery_address"]

class OrderForm(forms.ModelForm):
    """Форма оформления заказа"""
    delivery_address = forms.CharField(
        max_length=255, required=True, help_text="Введите адрес доставки"
    )

    class Meta:
        model = Order
        fields = ['products', 'delivery_address']


class UserUpdateForm(forms.ModelForm):
    """Форма обновления данных профиля"""
    delivery_address = forms.CharField(max_length=255, required=False, label="Адрес доставки")

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "phone_number", "telegram_id", "delivery_address"]