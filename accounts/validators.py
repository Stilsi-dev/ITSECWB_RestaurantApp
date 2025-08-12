import re
from datetime import timedelta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from django.conf import settings


class StrongPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r'[A-Z]', password):
            raise ValidationError("Password must include at least one uppercase letter.")
        if not re.search(r'[a-z]', password):
            raise ValidationError("Password must include at least one lowercase letter.")
        if not re.search(r'[0-9]', password):
            raise ValidationError("Password must include at least one number.")
        if not re.search(r'[\W_]', password):
            raise ValidationError("Password must include at least one special character (!@#$...).")

    def get_help_text(self):
        return ("Your password must contain at least one uppercase letter, "
                "one lowercase letter, one number, and one special character.")


class PasswordHistoryValidator:
    """
    2.1.10 Prevent password re-use: compare new password to last N hashes.
    Works for registration and password change forms (Django passes `user`).
    """
    def validate(self, password, user=None):
        if not user or not user.pk:
            return  # no history for brand-new users
        keep = getattr(settings, "PASSWORD_HISTORY_COUNT", 5)
        for ph in user.password_history.all()[:keep]:
            if check_password(password, ph.password_hash):
                raise ValidationError("You cannot reuse a recent password.")

    def get_help_text(self):
        return "You cannot reuse your recent passwords."


class MinimumPasswordAgeValidator:
    """
    2.1.11: Password must be at least MIN_PASSWORD_AGE_DAYS old before change.
    """
    def validate(self, password, user=None):
        min_days = getattr(settings, "MIN_PASSWORD_AGE_DAYS", 1)
        if not user or not user.pk or not user.password_changed_at:
            return
        if timezone.now() < user.password_changed_at + timedelta(days=min_days):
            raise ValidationError(f"Password can only be changed after {min_days} day(s).")

    def get_help_text(self):
        min_days = getattr(settings, "MIN_PASSWORD_AGE_DAYS", 1)
        return f"You can change your password only after {min_days} day(s)."
