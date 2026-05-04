from django.urls import path
from .views import catalog_search, catalog_resolve

urlpatterns = [
    path("search/", catalog_search),
    path("resolve/", catalog_resolve),
]
