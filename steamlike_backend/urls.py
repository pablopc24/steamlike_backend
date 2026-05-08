from django.contrib import admin
from django.urls import path, include
from catalog.views import health


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/library/", include("library.urls")),
    path("api/auth/", include("auth_app.urls")),
    path("api/catalog/", include("catalog.urls")),
    path("api/health/", health),
]
