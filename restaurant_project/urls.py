from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('logs/', include('logs.urls')),
    path('menu/', include('menu.urls')),
    path('orders/', include('orders.urls')),   # <- include the app's urls
    path('', include('accounts.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
