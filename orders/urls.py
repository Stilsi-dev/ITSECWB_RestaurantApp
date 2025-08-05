from django.urls import path
from . import views

app_name = 'orders'  # Important for namespace

urlpatterns = [
    path('', views.order_list_view, name='list'),      # Orders list
    path('create/', views.order_create_view, name='create'),  # Create order
]
