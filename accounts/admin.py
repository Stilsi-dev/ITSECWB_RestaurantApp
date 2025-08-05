from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        (None, {'fields': ('role', 'is_locked')}),
    )
    list_display = ('username', 'email', 'role', 'is_locked', 'is_staff')

admin.site.register(User, UserAdmin)
