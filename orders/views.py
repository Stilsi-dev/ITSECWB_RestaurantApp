from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order
from .forms import OrderForm
from logs.models import Log
from menu.models import MenuItem

@login_required
def order_list_view(request):
    if request.user.role in ['manager', 'admin']:
        orders = Order.objects.all().order_by('-created_at')
    else:
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')

    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_create_view(request):
    if request.user.role != 'customer':
        messages.error(request, "Only customers can place orders.")
        return redirect('order_list')

    menu_items = MenuItem.objects.all()

    if request.method == 'POST':
        selected_items = request.POST.getlist('items')
        if not selected_items:
            messages.error(request, "Please select at least one item.")
            return redirect('order_create')

        order = Order.objects.create(customer=request.user)
        order.items.set(selected_items)
        messages.success(request, "Your order has been placed!")
        return redirect('order_list')

    return render(request, 'orders/order_form.html', {'menu_items': menu_items})

@login_required
def order_cancel_view(request, pk):  # pk matches <int:pk>
    order = get_object_or_404(Order, pk=pk)

    if request.user.role == 'customer' and order.customer != request.user:
        messages.error(request, "You are not authorized to cancel this order.")
        return redirect('order_list')

    if order.status != 'pending':
        messages.error(request, "Only pending orders can be cancelled.")
        return redirect('order_list')

    order.status = 'cancelled'
    order.save()

    Log.objects.create(
        user=request.user,
        action=f"Cancelled order (ID: {order.id})",
        ip_address=request.META.get('REMOTE_ADDR'),
        status='success'
    )

    messages.success(request, f"Order #{order.id} has been cancelled.")
    return redirect('order_list')

@login_required
def order_update_status_view(request, pk, status):
    order = get_object_or_404(Order, pk=pk)

    if request.user.role not in ['manager', 'admin']:
        messages.error(request, "You are not authorized to update order statuses.")
        return redirect('order_list')

    valid_statuses = ['pending', 'preparing', 'completed', 'cancelled']
    if status not in valid_statuses:
        messages.error(request, "Invalid status.")
        return redirect('order_list')

    order.status = status
    order.save()

    messages.success(request, f"Order #{order.id} marked as {status}.")
    return redirect('order_list')

@login_required
def order_prepare_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, "You are not authorized to update orders.")
        return redirect('order_list')

    if order.status == 'pending':
        order.status = 'preparing'
        order.save()
        Log.objects.create(
            user=request.user,
            action=f"Marked order #{order.id} as PREPARING",
            ip_address=request.META.get('REMOTE_ADDR'),
            status='success'
        )
        messages.success(request, f"Order #{order.id} is now PREPARING.")
    return redirect('order_list')


@login_required
def order_complete_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    if request.user.role not in ['manager', 'admin']:
        messages.error(request, "You are not authorized to complete orders.")
        return redirect('order_list')

    if order.status == 'preparing':
        order.status = 'completed'
        order.save()
        Log.objects.create(
            user=request.user,
            action=f"Marked order #{order.id} as COMPLETED",
            ip_address=request.META.get('REMOTE_ADDR'),
            status='success'
        )
        messages.success(request, f"Order #{order.id} is now COMPLETED.")
    return redirect('order_list')
