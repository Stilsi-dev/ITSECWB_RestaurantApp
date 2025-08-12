# restaurant_project/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),

    # apps
    path("", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("menu/", include(("menu.urls", "menu"), namespace="menu")),
    path("orders/", include(("orders.urls", "orders"), namespace="orders")),
    path("logs/", include(("logs.urls", "logs"), namespace="logs")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Safe error handlers (used when DEBUG=False)
handler400 = "restaurant_project.error_views.error_400"
handler403 = "restaurant_project.error_views.error_403"
handler404 = "restaurant_project.error_views.error_404"
handler500 = "restaurant_project.error_views.error_500"
