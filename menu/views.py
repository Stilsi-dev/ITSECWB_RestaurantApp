"""Menu management views.

Implements CRUD for menu items with RBAC enforcement:
- Only manager/admin (or superuser) can access menu management pages.
- All access control failures are fail-secure (generic 403) and audited.
- Deletions are protected by a recent re-authentication requirement.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
import logging

from accounts.views import require_recent_reauth

from .forms import MenuItemForm
from .models import MenuItem
from logs.utils import audit_log

log = logging.getLogger("django")


def _is_manager(user):
    """Return True for manager/admin roles or superusers."""
    return getattr(user, "role", None) in {"manager", "admin"} or user.is_superuser


def _deny(request, action: str):
    """
    Fail securely:
    - Return generic 403 without leaking details
    - Log access control failure to both Django logs and audit trail
    """
    user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
    audit_log(request, user, action, "fail")
    log.warning("Access control failure: user=%s path=%s action=%s", user, request.path, action)
    return HttpResponseForbidden("You are not allowed to perform this action.")


@login_required
def menu_list_view(request):
    if not _is_manager(request.user):
        return _deny(request, "View menu list (manager-only)")

    items = MenuItem.objects.all().order_by("name")
    audit_log(request, request.user, "Viewed menu list", "success")
    return render(request, "menu/menu_list.html", {"items": items})


@login_required
def menu_create_view(request):
    if not _is_manager(request.user):
        return _deny(request, "Create menu item (manager-only)")

    if request.method == "POST":
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            messages.success(request, "Menu item created.")
            audit_log(request, request.user, f"Created menu item #{item.pk} ({item.name})", "success")
            return redirect("menu:list")

        # Validation failure logging (2.4.5)
        messages.error(request, "Please correct the errors below.")
        audit_log(request, request.user, "Create menu item validation failed", "fail")
        log.warning("Menu create validation errors: %s", dict(form.errors))
    else:
        form = MenuItemForm()

    return render(request, "menu/menu_form.html", {"form": form, "title": "Add Menu Item"})


@login_required
def menu_edit_view(request, pk):
    if not _is_manager(request.user):
        return _deny(request, "Edit menu item (manager-only)")

    item = get_object_or_404(MenuItem, pk=pk)

    if request.method == "POST":
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, "Menu item updated.")
            audit_log(request, request.user, f"Updated menu item #{item.pk} ({item.name})", "success")
            return redirect("menu:list")

        # Validation failure logging (2.4.5)
        messages.error(request, "Please correct the errors below.")
        audit_log(request, request.user, f"Edit menu item #{pk} validation failed", "fail")
        log.warning("Menu edit validation errors for #%s: %s", pk, dict(form.errors))
    else:
        form = MenuItemForm(instance=item)

    return render(request, "menu/menu_form.html", {"form": form, "title": f"Edit: {item.name}"})


@login_required
@require_recent_reauth
def menu_delete_view(request, pk):
    if not _is_manager(request.user):
        return _deny(request, "Delete menu item (manager-only)")

    item = get_object_or_404(MenuItem, pk=pk)

    if request.method == "POST":
        name = item.name
        item.delete()
        messages.success(request, "Menu item deleted.")
        audit_log(request, request.user, f"Deleted menu item #{pk} ({name})", "success")
        return redirect("menu:list")

    # GET: show confirm page – do not leak internals
    audit_log(request, request.user, f"Viewed delete confirm for menu item #{pk}", "success")
    return render(request, "menu/menu_confirm_delete.html", {"item": item})
