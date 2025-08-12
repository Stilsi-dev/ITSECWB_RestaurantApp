# accounts/signals.py
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from logs.utils import audit_log

User = get_user_model()

@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    audit_log(request, user, "Login successful", "success")

@receiver(user_login_failed)
def on_login_failed(sender, credentials, request, **kwargs):
    username = (credentials or {}).get("username", "")
    user = None
    if username:
        try:
            user = User.objects.filter(username=username).first()
        except Exception:
            user = None
    audit_log(request, user, f"Login failed", "fail", extra=f"username={username}")

@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    audit_log(request, user, "Logout", "success")
