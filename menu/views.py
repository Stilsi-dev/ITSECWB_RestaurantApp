# menu/views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .models import MenuItem
from .forms import MenuItemForm

def _require_admin(request):
    # Adjust this if you use permissions instead of a role field
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if getattr(request.user, "role", None) != "admin":
        messages.error(request, "Not authorized.")
        return redirect("accounts:dashboard")
    return None

@login_required
def menu_list_view(request):
    guard = _require_admin(request)
    if guard: return guard
    items = MenuItem.objects.all().order_by("name")
    return render(request, "menu/menu_list.html", {"menu_items": items})

@login_required
def menu_create_view(request):
    guard = _require_admin(request)
    if guard: return guard
    if request.method == "POST":
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu item created.")
            return redirect("menu:menu_list")
    else:
        form = MenuItemForm()
    return render(request, "menu/menu_form.html", {"form": form, "title": "Create Menu Item"})

@login_required
def menu_update_view(request, pk: int):
    guard = _require_admin(request)
    if guard: return guard
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == "POST":
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Menu item updated.")
            return redirect("menu:menu_list")
    else:
        form = MenuItemForm(instance=item)
    return render(request, "menu/menu_form.html", {"form": form, "title": f"Edit: {item.name}"})

@login_required
@require_POST
def menu_delete_view(request, pk: int):
    guard = _require_admin(request)
    if guard: return guard
    item = get_object_or_404(MenuItem, pk=pk)
    item.delete()
    messages.success(request, "Menu item deleted.")
    return redirect("menu:menu_list")

def menu_edit_view(request, pk):
    # Reuse your existing update logic
    return menu_update_view(request, pk)
