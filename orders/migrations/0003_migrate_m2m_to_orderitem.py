from django.db import migrations

def copy_m2m_to_orderitem(apps, schema_editor):
    """
    Copy each (order_id, menuitem_id) pair from the old auto M2M table
    into the new OrderItem rows with quantity=1 and price snapshot.
    """
    Order = apps.get_model("orders", "Order")
    OrderItem = apps.get_model("orders", "OrderItem")
    MenuItem = apps.get_model("menu", "MenuItem")

    # Name of the auto-created M2M table from 0001:
    # <app>_<model>_<field>  ->  orders_order_items
    m2m_table = "orders_order_items"

    conn = schema_editor.connection
    with conn.cursor() as cursor:
        try:
            cursor.execute(f"SELECT order_id, menuitem_id FROM {m2m_table}")
            rows = cursor.fetchall()
        except Exception:
            # If the table doesn't exist (fresh DB with no data), just exit.
            rows = []

    # Build a quick menu price cache to avoid N queries
    menu_prices = {}
    for m in MenuItem.objects.all().only("id", "price"):
        menu_prices[m.id] = m.price

    # Insert OrderItem rows
    for order_id, menuitem_id in rows:
        OrderItem.objects.get_or_create(
            order_id=order_id,
            menu_item_id=menuitem_id,
            defaults={
                "quantity": 1,
                "price_at_order": menu_prices.get(menuitem_id),
                "notes": "",
            },
        )

def noop_reverse(apps, schema_editor):
    # No safe reverse
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("orders", "0002_alter_order_options_alter_order_customer_orderitem_and_more"),
    ]
    operations = [
        migrations.RunPython(copy_m2m_to_orderitem, noop_reverse),
    ]
