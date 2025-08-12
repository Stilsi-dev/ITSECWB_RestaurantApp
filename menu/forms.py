from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from .models import MenuItem


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ["name", "description", "category", "tags", "price", "is_available", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"maxlength": 100}),
            "tags": forms.TextInput(attrs={"maxlength": 200}),
        }

    def clean_name(self):
        name = (self.cleaned_data.get("name") or "").strip()
        if len(name) < 2:
            raise ValidationError("Name must be at least 2 characters.")
        return name

    def clean_description(self):
        desc = (self.cleaned_data.get("description") or "").strip()
        if len(desc) < 10:
            raise ValidationError("Description must be at least 10 characters.")
        return desc

    def clean_price(self):
        price = self.cleaned_data.get("price")
        if price is None:
            raise ValidationError("Price is required.")
        if price < Decimal("0.00"):
            raise ValidationError("Price cannot be negative.")
        # max fits Decimal(8,2), but we enforce explicit business cap too
        if price > Decimal("999999.99"):
            raise ValidationError("Price is too large.")
        return price

    def clean_tags(self):
        tags = (self.cleaned_data.get("tags") or "").strip()
        if len(tags) > 200:
            raise ValidationError("Tags must be 200 characters or fewer.")
        return tags
