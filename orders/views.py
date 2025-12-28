"""Order workflow views.

Implements order creation and management with role-aware authorization:
- Customers can create and manage only their own orders.
- Staff (manager/admin) can view/manage all orders.
- Status transitions are restricted to an allow-list.
- Sensitive actions (status change, delete) require recent re-auth.
- Key actions and failures are written to the audit log.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
import logging

from accounts.views import require_recent_reauth

from .models import Order
from .forms import OrderForm, StaffOrderForm, OrderItemFormSet
from menu.models import MenuItem
from logs.utils import audit_log

log = logging.getLogger("django")


def _is_manager(user):
    """Return True for manager/admin roles or superusers."""
    return getattr(user, "role", "") in {"manager", "admin"} or user.is_superuser


def _allowed_transitions(status: str):
    """Manager/Admin transitions."""
    return {
        "pending": {"preparing", "cancelled"},
        "preparing": {"completed", "cancelled"},
        "completed": set(),
        "cancelled": set(),
    }.get(status, set())


@login_required
def order_list_view(request):
    if _is_manager(request.user):
        orders = Order.objects.select_related("customer").prefetch_related("order_items__menu_item")
    else:
        orders = (
            Order.objects.filter(customer=request.user)
            .select_related("customer")
            .prefetch_related("order_items__menu_item")
        )
    audit_log(request, request.user, "Viewed order list", "success")
    return render(request, "orders/order_list.html", {"orders": orders})


@login_required
def order_create_view(request):
    order = Order(customer=request.user)  # default status = pending
    FormClass = StaffOrderForm if _is_manager(request.user) else OrderForm

    if request.method == "POST":
        form = FormClass(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)

        if form.is_valid() and formset.is_valid():
            order = form.save(commit=False)
            order.customer = request.user
            if not _is_manager(request.user):
                order.status = "pending"
            order.save()
            formset.save()

            messages.success(request, "Order created successfully.")
            audit_log(request, request.user, f"Created order #{order.pk}", "success")
            return redirect("orders:list")

        messages.error(request, "Please correct the errors below.")
        audit_log(request, request.user, "Order creation validation failed", "fail")
        log.warning("Order create validation errors: %s %s", form.errors, formset.errors)

    else:
        form = FormClass(instance=order)
        formset = OrderItemFormSet(instance=order)

    menu_items = MenuItem.objects.all()
    return render(
        request,
        "orders/order_form.html",
        {"form": form, "formset": formset, "menu_items": menu_items, "title": "Create Order"},
    )


@login_required
def order_update_view(request, pk: int):
    order = get_object_or_404(Order, pk=pk)

    if not (_is_manager(request.user) or order.customer_id == request.user.id):
        audit_log(request, request.user, f"Unauthorized order update attempt #{pk}", "fail")
        log.warning("Access control failure: %s tried to edit order %s", request.user, pk)
        raise Http404("Not found")

    if not _is_manager(request.user) and order.status != "pending":
        messages.error(request, "You can edit or cancel an order only while it is pending.")
        audit_log(request, request.user, f"Attempted edit of non-pending order #{pk}", "fail")
        return redirect("orders:list")

    FormClass = StaffOrderForm if _is_manager(request.user) else OrderForm

    if request.method == "POST":
        form = FormClass(request.POST, instance=order)
        formset = OrderItemFormSet(request.POST, instance=order)

        if form.is_valid() and formset.is_valid():
            obj = form.save(commit=False)
            if not _is_manager(request.user):
                obj.status = "pending"
            obj.save()
            formset.save()

            messages.success(request, "Order updated successfully.")
            audit_log(request, request.user, f"Updated order #{order.pk}", "success")
            return redirect("orders:list")

        messages.error(request, "Please correct the errors below.")
        audit_log(request, request.user, f"Order update validation failed for #{pk}", "fail")
        log.warning("Order update validation errors: %s %s", form.errors, formset.errors)

    else:
        form = FormClass(instance=order)
        formset = OrderItemFormSet(instance=order)

    menu_items = MenuItem.objects.all()
    return render(
        request,
        "orders/order_form.html",
        {"form": form, "formset": formset, "menu_items": menu_items, "title": f"Edit Order #{order.pk}"},
    )


@login_required
@require_recent_reauth
@require_POST
def order_status_transition(request, pk, to: str):
    order = get_object_or_404(Order, pk=pk)

    if not _is_manager(request.user):
        messages.error(request, "Only managers can change order status.")
        audit_log(request, request.user, f"Unauthorized status change attempt on order #{pk}", "fail")
        log.warning("Access control failure: %s tried to change status of order %s", request.user, pk)
        return redirect("orders:list")

    to = to.lower().strip()
    allowed = _allowed_transitions(order.status)
    if to not in allowed:
        audit_log(request, request.user, f"Invalid status transition for order #{pk}", "fail")
        log.warning("Validation failure: invalid status transition %s -> %s", order.status, to)
        return HttpResponseBadRequest("Invalid status transition.")

    order.status = to
    order.save(update_fields=["status"])
    messages.success(request, f"Order #{order.pk} marked as {to}.")
    audit_log(request, request.user, f"Changed order #{order.pk} status to {to}", "success")
    return redirect("orders:list")


@login_required
@require_recent_reauth
def order_delete_view(request, pk):
    order = get_object_or_404(Order, pk=pk)
    is_staff = _is_manager(request.user)
    is_owner = order.customer_id == request.user.id

    if is_owner and not is_staff and order.status != "pending":
        messages.error(request, "You can cancel/delete only while the order is pending.")
        audit_log(request, request.user, f"Unauthorized delete attempt on order #{pk}", "fail")
        log.warning("Access control failure: %s tried to delete order %s", request.user, pk)
        return redirect("orders:list")

    order.delete()
    messages.success(request, f"Order #{pk} deleted.")
    audit_log(request, request.user, f"Deleted order #{pk}", "success")
    return redirect("orders:list")
