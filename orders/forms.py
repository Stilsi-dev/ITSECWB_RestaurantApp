from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from .models import Order, OrderItem
from menu.models import MenuItem


class OrderForm(forms.ModelForm):
    """Customer form (no status)"""
    class Meta:
        model = Order
        fields = ("table_number",)
        widgets = {
            "table_number": forms.TextInput(attrs={
                "class": "form-control table-input",
                "placeholder": "e.g., A1 or B2",
                "maxlength": 32,
                "inputmode": "text",
                "autocomplete": "off",
                "spellcheck": "false",
            }),
        }

    def clean_table_number(self):
        value = (self.cleaned_data.get("table_number") or "").strip()
        if value and len(value) < 1:
            # not really reachable (since len<1 means empty),
            # but keeps intent explicit for the requirement
            raise ValidationError("Table code must be at least 1 character.")
        if len(value) > 32:
            raise ValidationError("Table code must be at most 32 characters.")
        return value


class StaffOrderForm(forms.ModelForm):
    """Manager/Admin form (can change status)"""
    class Meta:
        model = Order
        fields = ("table_number", "status")
        widgets = {
            "table_number": forms.TextInput(attrs={
                "class": "form-control table-input",
                "placeholder": "e.g., A1 or B2",
                "maxlength": 32,
                "inputmode": "text",
                "autocomplete": "off",
                "spellcheck": "false",
            }),
            "status": forms.Select(attrs={"class": "form-control"}),
        }

    def clean_table_number(self):
        value = (self.cleaned_data.get("table_number") or "").strip()
        if value and len(value) < 1:
            raise ValidationError("Table code must be at least 1 character.")
        if len(value) > 32:
            raise ValidationError("Table code must be at most 32 characters.")
        return value


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ("menu_item", "quantity", "notes")
        widgets = {
            "menu_item": forms.Select(attrs={"class": "form-control"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "min": 1, "max": 100}),
            "notes": forms.TextInput(attrs={"class": "form-control", "placeholder": "Optional notes", "maxlength": 255}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["menu_item"].queryset = MenuItem.objects.all().order_by("name")

    def clean_quantity(self):
        q = self.cleaned_data.get("quantity")
        if q is None:
            raise ValidationError("Quantity is required.")
        if q < 1 or q > 100:
            raise ValidationError("Quantity must be between 1 and 100.")
        return q

    def clean_notes(self):
        notes = (self.cleaned_data.get("notes") or "").strip()
        if len(notes) > 255:
            raise ValidationError("Notes must be 255 characters or fewer.")
        return notes


OrderItemFormSet = inlineformset_factory(
    Order,
    OrderItem,
    form=OrderItemForm,
    extra=10,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
