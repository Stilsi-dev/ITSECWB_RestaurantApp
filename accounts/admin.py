# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone

from .models import User, PasswordHistory

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
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

    readonly_fields = ("failed_logins", "locked_until", "password_changed_at")

    def lock_status(self, obj):
        if obj.locked_until and obj.locked_until > timezone.now():
            return "Locked"
        return "OK"
    lock_status.short_description = "Lock Status"

@admin.register(PasswordHistory)
class PasswordHistoryAdmin(admin.ModelAdmin):
    list_display = ("user", "changed_at", "password_hash")
    search_fields = ("user__username",)
    ordering = ("-changed_at",)
    readonly_fields = ("user", "changed_at", "password_hash")
