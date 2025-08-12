from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("menu", "0002_menuitem_category_menuitem_image_menuitem_tags"),
        ("orders", "0003_migrate_m2m_to_orderitem"),
    ]

    operations = [
        # Drop the old auto M2M join table
        migrations.RemoveField(
            model_name="order",
            name="items",
        ),
        # Re-add the field pointing to the explicit through model.
        migrations.AddField(
            model_name="order",
            name="items",
            field=models.ManyToManyField(
                to="menu.menuitem",
                through="orders.OrderItem",
                related_name="orders",
                blank=True,
            ),
        ),
    ]
