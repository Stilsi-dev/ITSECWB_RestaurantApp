from django.urls import path
from . import views

urlpatterns = [
    path('', views.menu_list_view, name='menu_list'),
    path('create/', views.menu_create_view, name='menu_create'),
    path('<int:pk>/edit/', views.menu_edit_view, name='menu_edit'),
    path('<int:pk>/delete/', views.menu_delete_view, name='menu_delete'),
]
