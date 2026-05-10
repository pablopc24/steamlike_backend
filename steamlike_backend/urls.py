from django.contrib import admin
from django.urls import path, include
from catalog.views import health
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/library/", include("library.urls")),
    path("api/catalog/", include("catalog.urls")),
    path("api/health/", health),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/", include("auth_app.urls")),
]
