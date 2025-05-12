from django.urls import path, include
from .views import homepage, registerPage, loginPage, logoutUser
# homepage, register, CustomLoginView, CustomLogoutView
urlpatterns = [
    path("", homepage, name="home"),
    path("login/", loginPage, name="login"),
    path("register/", registerPage, name="register"),
    path("logout/", logoutUser, name="logout"),
]
