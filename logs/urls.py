from django.urls import path
from . import views

app_name = "logs" 

urlpatterns = [
    path('', views.admin_logs_view, name='admin_logs'),
]
