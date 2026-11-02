from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from .forms import EntryForm
from .models import UserMovieEntry, Movie
from django.db.models import Q
from rest_framework import generics
from .serializers import MovieEntrySerializer, EntryDetailSerializer


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



class EntryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MovieEntrySerializer
    permission_classes = [IsAuthenticated]
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    # Should be removed
    template_name = "movie/my_movies.html"

    def get_queryset(self):
        return (
            UserMovieEntry.objects
            .filter(user=self.request.user)
            .select_related("movie")
        )


class EntryDetail(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = EntryDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserMovieEntry.objects.filter(user=self.request.user).select_related("movie")



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


class OwnEntriesMixin(LoginRequiredMixin):
    """Login required, and only the current user's entries are reachable."""
    def get_queryset(self):
        return UserMovieEntry.objects.filter(user=self.request.user).select_related("movie")

class EntryUpdateView(OwnEntriesMixin, UpdateView):
    model = UserMovieEntry
    form_class = EntryForm
    template_name = "movie/entry_update_form.html"
    slug_url_kwarg = 'entry_slug'

    def get_success_url(self):
        return reverse('movie:detail', kwargs={'movie_slug': self.object.movie.slug})


class EntryDeleteView(OwnEntriesMixin, DeleteView):
    model = UserMovieEntry
    template_name = "movie/entry_confirm_delete.html"
    success_url = reverse_lazy("movie:my_movies")
    slug_url_kwarg = 'entry_slug'
