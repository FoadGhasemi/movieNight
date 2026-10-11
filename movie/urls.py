from django.urls import path
from . import views

app_name = "movie"

urlpatterns = [
    path("my-movies/", views.MyMoviesAPIView.as_view(), name="my_movies"),
    path('search/', views.MovieSearchView.as_view(), name="search"),
    path('detail/<slug:movie_slug>', views.MoviesDetailView.as_view(), name="detail"),
    path('update/<slug:entry_slug>', views.EntryUpdateView.as_view(), name="update"),
    path('delete/<slug:entry_slug>', views.EntryDeleteView.as_view(), name="delete"),
]