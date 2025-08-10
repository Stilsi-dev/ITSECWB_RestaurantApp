# accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("manage-users/", views.manage_users_view, name="manage_users"),
    path("logout/", views.logout_view, name="logout"),  # if using your custom logout
    path("", views.login_view, name="root_login"),      # root -> login (optional)
]
