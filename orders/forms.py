from django import forms
from .models import Order
from menu.models import MenuItem

class OrderForm(forms.ModelForm):
    items = forms.ModelMultipleChoiceField(
        queryset=MenuItem.objects.filter(is_available=True),   # ✅ Correct field name
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Order
        fields = ['items']
