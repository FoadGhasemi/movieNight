from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from .forms import UserCreationForm, UserLoginForm
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model

User = get_user_model()


def user_login(request):
    if request.user.is_authenticated:
        return redirect("home:home")

    if request.method == "POST":
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                return redirect("home:home")
            form.add_error(None, "Invalid username or password.")
    else:
        form = UserLoginForm()

    return render(request, "user/login.html", {"form": form})


def user_register(request):
    if request.user.is_authenticated:
        return redirect('home:home')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home:home')
    else:
        form = UserCreationForm()
    return render(request, 'user/register.html', {'form': form})


def user_logout(request):
    logout(request)
    return redirect('home:home')


class UserUpdateView(LoginRequiredMixin, UpdateView):
    model = User
    template_name = "user_profile.html"