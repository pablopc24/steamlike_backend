from django.urls import path
from . import views

urlpatterns = [
    path("entries/", views.entries_list_create),
    path("entries/<int:entry_id>/", views.entry_detail),
]
