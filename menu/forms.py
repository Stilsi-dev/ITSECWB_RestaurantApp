from django import forms
from .models import MenuItem

class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['name', 'description', 'price', 'image', 'category', 'tags', 'is_available']
        widgets = {
            'tags': forms.TextInput(attrs={'placeholder': 'e.g. spicy, vegan'}),
        }
