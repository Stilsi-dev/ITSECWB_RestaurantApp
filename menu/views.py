from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import MenuItem
from .forms import MenuItemForm

@login_required
def menu_list_view(request):
    menu_items = MenuItem.objects.all()
    return render(request, 'menu/menu_list.html', {'menu_items': menu_items})

@login_required
def menu_create_view(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ New menu item added successfully!")
            return redirect('menu_list')
    else:
        form = MenuItemForm()
    return render(request, 'menu/menu_form.html', {'form': form})

@login_required
def menu_edit_view(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Menu item updated successfully!")
            return redirect('menu_list')
    else:
        form = MenuItemForm(instance=item)
    return render(request, 'menu/menu_form.html', {'form': form})

@login_required
def menu_delete_view(request, pk):
    item = get_object_or_404(MenuItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "🗑️ Menu item deleted successfully!")
        return redirect('menu_list')
    return render(request, 'menu/menu_confirm_delete.html', {'item': item})
