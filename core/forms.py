from django import forms
from .models import Order

class OrderForm(forms.ModelForm):
    """Форма оформления заказа"""
    class Meta:
        model = Order
        fields = ['products']
