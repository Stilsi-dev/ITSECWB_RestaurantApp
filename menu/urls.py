# menu/urls.py
from django.urls import path
from . import views

app_name = "menu"

urlpatterns = [
    path("", views.menu_list_view, name="list"),
    path("new/", views.menu_create_view, name="create"),
    path("<int:pk>/edit/", views.menu_edit_view, name="edit"),
    path("<int:pk>/delete/", views.menu_delete_view, name="delete"),

    # Optional legacy aliases so old templates like {% url 'menu_edit' pk %} still work
    path("", views.menu_list_view, name="menu_list"),
    path("new/", views.menu_create_view, name="menu_create"),
    path("<int:pk>/edit/", views.menu_edit_view, name="menu_edit"),
    path("<int:pk>/delete/", views.menu_delete_view, name="menu_delete"),
]
