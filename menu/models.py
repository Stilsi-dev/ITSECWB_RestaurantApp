# menu/models.py
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator, MinLengthValidator


class MenuItem(models.Model):
    CATEGORY_CHOICES = [
        ('appetizer', 'Appetizer'),
        ('main', 'Main Course'),
        ('dessert', 'Dessert'),
        ('drinks', 'Drinks'),
    ]

    name = models.CharField(max_length=100, validators=[MinLengthValidator(2)])
    description = models.TextField()
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("0.00")),
            MaxValueValidator(Decimal("999999.99")),
        ],
    )
    image = models.ImageField(upload_to='menu_images/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    tags = models.CharField(max_length=200, blank=True)
    is_available = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                name="menu_menuitem_price_range",
                check=models.Q(price__gte=0) & models.Q(price__lte=999999.99),
            ),
            models.CheckConstraint(
                name="menu_menuitem_name_len",
                check=models.Q(name__regex=r"^.{2,100}$"),
            ),
            models.CheckConstraint(
                name="menu_menuitem_tags_len",
                check=models.Q(tags="") | models.Q(tags__regex=r"^.{0,200}$"),
            ),
        ]

    def __str__(self):
        return self.name
