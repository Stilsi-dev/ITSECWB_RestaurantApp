from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def dashboard_view(request):
    if request.user.role == 'admin':
        return render(request, 'dashboard_admin.html')
    elif request.user.role == 'manager':
        return render(request, 'dashboard_manager.html')
    else:
        return render(request, 'dashboard_customer.html')
