from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register, name="register"),
    path("login/", views.SignInView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(next_page="home"), name="logout"),
    path("account/", views.dashboard, name="dashboard"),
    path("account/requests/new/", views.create_request, name="request_create"),
    path("account/requests/<int:pk>/delete/", views.delete_request, name="request_delete"),
]
