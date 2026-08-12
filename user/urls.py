from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView, LoginView

app_name = "user"

urlpatterns = [
    #path('logout/', LogoutView.as_view(next_page = "home:home") , name = "logout"),
    path('logout/', views.user_logout , name = "logout"),
    path('login/', LoginView.as_view(template_name = "user/login.html", redirect_authenticated_user=True,
                                     next_page = "home:home")
         , name = "login"),
    path('register/', views.user_register, name = "register"),
    #path('otp_register_login/', views.OtpRegisterLoginView.as_view(), name = "check_otp"),
    path('profile/<int:pk>', views.UserUpdateView.as_view(), name = "profile"),
]