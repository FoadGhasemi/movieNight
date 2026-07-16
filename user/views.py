from django.contrib.auth.views import LoginView
from django.shortcuts import render

class UserLogin(LoginView):
    template_name = "user:login.html"