# orders/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from logs.models import Log

@login_required
def order_list_view(request):
    Log.objects.create(user=request.user, action="Viewed order list",
                       ip_address=request.META.get('REMOTE_ADDR'),
                       user_agent=request.META.get('HTTP_USER_AGENT', ''),
                       status='success')
    return render(request, "orders/order_list.html")  # create this template

@login_required
def order_create_view(request):
    Log.objects.create(user=request.user, action="Opened order create page",
                       ip_address=request.META.get('REMOTE_ADDR'),
                       user_agent=request.META.get('HTTP_USER_AGENT', ''),
                       status='success')
    return render(request, "orders/order_create.html")  # create this template
