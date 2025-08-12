# orders/urls.py
from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list_view, name="list"),
    path("create/", views.order_create_view, name="create"),
    path("<int:pk>/edit/", views.order_update_view, name="update"),
    path("<int:pk>/delete/", views.order_delete_view, name="delete"),
    path("<int:pk>/status/<str:to>/", views.order_status_transition, name="status"),  # NEW
]
