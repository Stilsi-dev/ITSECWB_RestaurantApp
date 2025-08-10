from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["name", "description", "category", "tags", "price", "is_available", "image"]
