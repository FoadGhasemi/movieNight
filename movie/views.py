from winreg import DeleteValue

from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, TemplateView, DetailView, UpdateView, DeleteView
from .forms import EntryForm
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

    # When you come from the button this view receives post, unlike when you get redirected from login
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

    def get_queryset(self, **kwargs):
        # If the user is not logged in, return an empty list to avoid errors
        if not self.request.user.is_authenticated:
            return UserMovieEntry.objects.none()

        return UserMovieEntry.objects.filter(user=self.request.user).select_related('movie')


class MoviesDetailView(DetailView):
    model = Movie
    template_name = 'movie/movie_detail.html'
    context_object_name = 'movie'
    slug_url_kwarg = 'movie_slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Check if the current user has an entry for this movie
        if self.request.user.is_authenticated:
            context['user_entry'] = UserMovieEntry.objects.filter(
                user=self.request.user,
                movie=self.object
            ).first()
        return context


class EntryUpdateView(UpdateView):
    model = UserMovieEntry
    form_class = EntryForm
    template_name = "movie/entry_update_form.html"
    slug_url_kwarg = 'entry_slug'

    def get_success_url(self):
        return reverse('movie:detail', kwargs={'movie_slug': self.object.movie.slug})


class EntryDeleteView(DeleteView):
    model = UserMovieEntry
    template_name = "movie/entry_confirm_delete.html"
    success_url = reverse_lazy("movie:my_movies")
    slug_url_kwarg = 'entry_slug'

    def get_queryset(self):
        return super().get_queryset().select_related('movie')

