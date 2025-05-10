from django.urls import path, include
from .views import homepage, authView
# homepage, register, CustomLoginView, CustomLogoutView
urlpatterns = [
    path("", homepage, name="home"),
    path("register/", authView, name="authView"),
    path("accounts/", include("django.contrib.auth.urls")),
    # path('register/', register, name='register'),
    # path('login/', CustomLoginView.as_view(), name='login'),
    # path('logout/', CustomLogoutView.as_view(), name='logout'),
]
