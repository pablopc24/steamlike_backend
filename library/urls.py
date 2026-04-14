from django.urls import path
from .views import health, create_library_entry, list_library_entries, library_entry_detail, LibraryEntryDetailView


urlpatterns = [
    path("health/", health),
    path("entries/", create_library_entry),
     path("entries/", list_library_entries),  # GET listado
    path("entries/<int:entry_id>/", library_entry_detail),  # GET detalle
     path("entries/<int:pk>/", LibraryEntryDetailView.as_view()),
]

