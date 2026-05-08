from django.urls import path
from .views import register
from .views import login_view, me 
urlpatterns = [
    path("register/", register),
    path("login/", login_view),
    path("me/", me),
]
