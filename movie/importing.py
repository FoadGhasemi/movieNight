from . import services
from .models import Movie


def get_or_import_movie(tmdb_id):
    """Return our Movie for this TMDB id, asking TMDB only if we don't have it yet.

    Raises services.TMDBError if TMDB is needed and unavailable.
    """
    movie = Movie.objects.filter(tmdb_id=tmdb_id).first()
    if movie is not None:
        return movie
    data = services.get_movie(tmdb_id)
    movie, _ = Movie.objects.get_or_create(tmdb_id=tmdb_id, defaults=data)
    return movie