from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from movie.models import Movie


class Home(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["movies"] = Movie.objects.all()
        return context