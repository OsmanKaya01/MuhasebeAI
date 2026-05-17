from django.urls import path
from . import views

urlpatterns = [
    path("sign/", views.register_view, name="sign"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout")
]
