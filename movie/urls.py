from django.urls import path
from . import views

app_name = "movie"

urlpatterns = [
    path('my_movies/', views.MyMoviesListView.as_view(), name="my_movies"),
    path('search/', views.MovieSearchView.as_view(), name="search"),
    path('detail/<int:pk>', views.MoviesDetailView.as_view(), name="detail"),
    path('add_entry/', views.add_from_api_view, name="add_from_api"),
    path('update/<int:pk>', views.EntryUpdateView.as_view(), name="update"),
]