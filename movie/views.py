from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView
from .models import UserMovieEntry, Movie
from django.contrib.auth.decorators import login_required
from django.db.models import Q


@login_required
def add_from_api_view(request):
    if request.method == 'POST':
        tmdb_id = request.POST.get('tmdb_id')

        # 1. Get or create the local Movie instance
        movie, created = Movie.objects.get_or_create(
            tmdb_id=tmdb_id,
            defaults={
                'title': request.POST.get('title'),
                'release_year': request.POST.get('release_year'),
                'poster_url': request.POST.get('poster_url'),
            }
        )

        # 2. Create the UserMovieEntry
        UserMovieEntry.objects.get_or_create(
            user=request.user,
            movie=movie,
            defaults={'status': 'WATCHLIST'}
        )

        return redirect('movie:my_movies')


class MovieSearchView(ListView):
    model = Movie
    template_name = "movie/search_from_tmdb.html"
    context_object_name = "movies"

    def get_queryset(self):
        q = self.request.GET.get("q", "")

        # This aught to be connected to the API
        if not q:
            return Movie.objects.none()

        return Movie.objects.filter(
            Q(title__icontains=q) |
            Q(description__icontains=q)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["q"] = self.request.GET.get("q", "")
        return context


class MyMoviesListView(ListView):
    model = UserMovieEntry
    template_name = 'movie/my_movies.html'

    """def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = timezone.now()
        return context"""


class MoviesDetailView(ListView):
    pass