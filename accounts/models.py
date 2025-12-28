"""Models for authentication, RBAC, and password policy support.

This app uses a custom `User` model to support:
- Role-based access control via `role`.
- Account lockout via `failed_logins` and `locked_until`.
- Password policy metadata (change timestamp + security question/answer hash).
- Optional last authentication event metadata for reporting/auditing.

`PasswordHistory` stores previous password hashes to prevent reuse.
"""

from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model with additional security and RBAC fields."""
    # existing roles/lockout fields you had earlier
    role = models.CharField(max_length=20, default="customer")
    failed_logins = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)

    # password policy & recovery
    password_changed_at = models.DateTimeField(null=True, blank=True)
    security_question = models.CharField(max_length=255, blank=True)
    security_answer_hash = models.CharField(max_length=128, blank=True)

    def mark_password_changed(self):
        """Update the password change timestamp to enforce minimum password age."""
        self.password_changed_at = timezone.now()
        self.save(update_fields=["password_changed_at"])
    
    last_auth_event_at = models.DateTimeField(null=True, blank=True)
    last_auth_event_ok = models.BooleanField(null=True, blank=True)
    last_auth_event_ip = models.GenericIPAddressField(null=True, blank=True)
    last_auth_event_ua = models.TextField(blank=True, null=True)

    def is_locked_now(self):
        """Return True if the account is currently locked out."""
        return bool(self.locked_until and timezone.now() < self.locked_until)


class PasswordHistory(models.Model):
    """
    Stores previous password hashes for each user to block reuse.
    Keep only the most recent N (controlled via settings.PASSWORD_HISTORY_COUNT).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_history")
    password_hash = models.CharField(max_length=255)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self):
        return f"{self.user.username} @ {self.changed_at:%Y-%m-%d %H:%M}"
