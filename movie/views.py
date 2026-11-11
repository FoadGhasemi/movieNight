from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, DeleteView
from rest_framework.permissions import IsAuthenticated
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from . import services
from .forms import EntryForm
from .models import UserMovieEntry, Movie
from rest_framework import generics
from .serializers import MovieEntrySerializer, EntryDetailSerializer
import logging
from django.views.generic import TemplateView


logger = logging.getLogger(__name__)


class MovieSearchView(TemplateView):
    template_name = "movie/search_from_tmdb.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        q = self.request.GET.get("q", "").strip()
        context.update({"q": q, "movies": [], "error": None})

        if q:
            try:
                context["movies"] = services.search_movies(q)
            except services.TMDBError:
                logger.warning("TMDB search failed for %r", q, exc_info=True)
                context["error"] = "Movie search is unavailable right now. Please try again."
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

    def get_queryset(self):
        return (
            UserMovieEntry.objects
            .filter(user=self.request.user)
            .select_related("movie")
        )


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
