from django.urls import path
from .views import register
from .views import login_view, me, change_password
urlpatterns = [
    path("register/", register),
    path("login/", login_view),
    path("me/", me),
    path("me/password/", change_password)
]
