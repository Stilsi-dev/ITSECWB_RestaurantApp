# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list_view, name="list"),          # /orders/
    path("create/", views.order_create_view, name="create") # /orders/create/
]
