from django.urls import path
from .views import catalog_search, catalog_resolve, health
from .views import debug_email_test


urlpatterns = [
    path("search/", catalog_search),
    path("resolve/", catalog_resolve),
    path("health/", health),
    path("debug/email/test/", debug_email_test),
]
