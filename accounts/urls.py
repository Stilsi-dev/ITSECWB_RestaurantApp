# accounts/urls.py
from django.urls import path
from . import views

app_name = "accounts"

urlpatterns = [
    path("", views.login_view, name="root_login"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("manage-users/", views.manage_users_view, name="manage_users"),

    # security question setup (after register / later from banner)
    path("setup-security-question/", views.setup_security_question_view, name="setup_security_question"),

    # re-auth & change password
    path("reauth/", views.reauth_view, name="reauth"),
    path("change-password/", views.change_password_view, name="change_password"),

    # password reset flow
    path("reset/", views.reset_start_view, name="reset_start"),
    path("reset/question/", views.reset_question_view, name="reset_question"),
    path("reset/new/", views.reset_set_password_view, name="reset_set_password"),
]
