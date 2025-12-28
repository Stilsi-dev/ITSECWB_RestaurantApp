"""Django admin configuration for the custom accounts app.

This module registers the custom `User` model and the `PasswordHistory` model.
It exposes security-relevant fields (role, lockout counters, and timestamps) to
staff/superusers for administration and review.
"""

# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone

from .models import User, PasswordHistory

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Admin UI for the custom `User` model.

    Extends Django's built-in `UserAdmin` to surface RBAC role information and
    lockout state fields (failed logins + locked-until timestamp).
    """
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
        "lock_status",
        "failed_logins",
        "locked_until",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "role")
    search_fields = ("username", "email")
    ordering = ("username",)

    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Security / Lockout", {
            "fields": (
                "role",
                "failed_logins",
                "locked_until",
                "password_changed_at",
                "security_question",
                # security_answer_hash is stored but not editable
            )
        }),
    )

    readonly_fields = ("failed_logins",)

    def lock_status(self, obj):
        """Human-readable lock status derived from `locked_until`."""
        if obj.locked_until and obj.locked_until > timezone.now():
            return "Locked"
        return "OK"
    lock_status.short_description = "Lock Status"

@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    """Read-only view of password hash history for reuse-prevention."""
    list_display = ("user", "changed_at", "password_hash")
    search_fields = ("user__username",)
    ordering = ("-changed_at",)
    readonly_fields = ("user", "changed_at", "password_hash")
