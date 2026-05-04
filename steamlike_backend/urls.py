from django.contrib import admin
from django.urls import path, include
from library.views import catalog_search

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/catalog/search/", catalog_search),
    path("api/library/", include("library.urls")),
    path("api/auth/", include("auth_app.urls")),
    path("api/catalog/", include("catalog.urls")),
]
