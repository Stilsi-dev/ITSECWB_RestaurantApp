from decimal import Decimal
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator
from django.utils import timezone
from django.db.models import Q
from menu.models import MenuItem


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'customer'},
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # Keep short and human-entered; validate min/max length
    table_number = models.CharField(
        max_length=32,
        blank=True,
        default="",
        validators=[MinLengthValidator(0)]  # harmless (keeps blank allowed); real cap enforced by max_length
    )

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            # If provided, table_number length must be 1..32 (max handled by field; enforce min at DB when not empty)
            models.CheckConstraint(
                name="orders_order_table_number_len",
                check=Q(table_number="") | Q(table_number__regex=r"^.{1,32}$"),
            ),
        ]

    def __str__(self):
        return f"Order #{self.id} by {self.customer.username}"


class OrderItem(models.Model):
    # Business rule: quantity must be 1..100 (adjust upper bound if you prefer)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(100)]
    )
    # Keep notes short; model already caps at 255 (length validation)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="orders_orderitem_quantity_range",
                check=Q(quantity__gte=1) & Q(quantity__lte=100),
            ),
            models.CheckConstraint(
                name="orders_orderitem_notes_len",
                check=Q(notes="") | Q(notes__regex=r"^.{0,255}$"),
            ),
        ]

    def __str__(self):
        return f"{self.quantity} × {self.menu_item.name} (Order #{self.order_id})"
