from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

app_name = "user"

urlpatterns = [
    path('logout/', LogoutView.as_view(next_page = "home:home"), name = "logout"),
    path('login/', views.UserLoginView.as_view(), name = "login"),
    path('register/', views.RegisterView.as_view(), name = "register"),
    path('otp_register_login/', views.OtpRegisterLoginView.as_view(), name = "check_otp"),
    path('profile/<int:pk>', views.UserUpdateView.as_view(), name = "profile"),
]