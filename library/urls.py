from django.urls import path
from . import views

urlpatterns = [
    path("entries/", views.entries_list),
    path("entries/<int:entry_id>/", views.entry_detail),
]
