# accounts/signals.py
from __future__ import annotations

from datetime import timedelta
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.core.cache import cache
from django.dispatch import receiver
from django.utils import timezone
from logs.utils import audit_log

User = get_user_model()


def _client_meta(request):
    if not request:
        return None, ""
    ip = request.META.get("REMOTE_ADDR") or None
    ua = (request.META.get("HTTP_USER_AGENT") or "")[:1024]
    return ip, ua


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request, **kwargs):
    """
    Record failed login attempts, enforce lockout window, and cache the 'last failed'
    so we can show 'last use (success or failure)' at next successful login without
    adding new DB fields.
    """
    username = (credentials or {}).get("username", "") or ""
    user = None
    try:
        user = User.objects.filter(username=username).first()
    except Exception:
        user = None

    ip, ua = _client_meta(request)

    # Persist counters/lockout only if the account exists
    if user:
        max_fail = int(getattr(settings, "LOCKOUT_MAX_FAILURES", 5))
        cooldown = int(getattr(settings, "LOCKOUT_COOLDOWN_MINUTES", 15))

        user.failed_logins = (user.failed_logins or 0) + 1
        if user.failed_logins >= max_fail:
            user.locked_until = timezone.now() + timedelta(minutes=cooldown)
            user.failed_logins = 0  # reset counter after lock is applied

        user.save(update_fields=["failed_logins", "locked_until"])

        # cache the most recent failure (timestamp + ip) for banner
        cache.set(
            f"last_failed_auth:{user.username}",
            {"ts": timezone.now().isoformat(), "ip": ip},
            timeout=60 * 60 * 24 * 7,  # 7 days
        )

    # audit
    try:
        audit_log(request, user, "Login attempt", "fail", extra=f"username={username}")
    except Exception:
        pass


@receiver(user_logged_in)
def on_logged_in(sender, request, user, **kwargs):
    """
    On success: reset counters/lock, and record a cache flag we can use for
    single-request banners in the login view (the view will pop and message).
    """
    ip, ua = _client_meta(request)

    # Reset failure counters on success
    changed = []
    if getattr(user, "failed_logins", None) not in (None, 0):
        user.failed_logins = 0
        changed.append("failed_logins")
    if getattr(user, "locked_until", None):
        user.locked_until = None
        changed.append("locked_until")
    if changed:
        user.save(update_fields=changed)

    # Stash marker so the view can display the banner immediately
    if hasattr(request, "session"):
        request.session["just_logged_in"] = True
        request.session["just_logged_in_ip"] = ip

    try:
        audit_log(request, user, "Login successful", "success")
    except Exception:
        pass


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    try:
        audit_log(request, user, "Logout", "success")
    except Exception:
        pass
