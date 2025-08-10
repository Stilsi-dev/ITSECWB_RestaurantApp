# restaurant_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    # app urls
    path('logs/', include(('logs.urls', 'logs'), namespace='logs')),
    path("menu/", include(("menu.urls", "menu"), namespace="menu")),
    path('orders/', include(('orders.urls', 'orders'), namespace='orders')),
    path('', include(('accounts.urls', 'accounts'), namespace='accounts')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
