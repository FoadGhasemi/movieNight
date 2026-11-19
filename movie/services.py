import requests
from django.conf import settings

TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w342"
TMDB_MOVIE_URL = "https://api.themoviedb.org/3/movie/{tmdb_id}"


class TMDBError(Exception):
    """TMDB was unreachable or returned an error."""

class TMDBNotFound(TMDBError):
    """TMDB has no movie with this id."""


def _to_movie_dict(result):
    """Convert one TMDB result into our Movie shape."""
    release_date = result.get("release_date") or ""
    poster_path = result.get("poster_path")

    return {
        "tmdb_id": result["id"],
        "title": result.get("title", ""),
        "release_year": int(release_date[:4]) if release_date else None,
        "description": result.get("overview", ""),
        "poster_url": f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else "",
    }


def search_movies(query):
    """Search TMDB; return a list of dicts in our Movie shape."""
    query = query.strip()
    if not query:
        return []

    try:
        response = requests.get(
            TMDB_SEARCH_URL,
            params={"query": query, "include_adult": "false"},
            headers={
                "Authorization": f"Bearer {settings.TMDB_READ_TOKEN}",
                "accept": "application/json",
            },
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        raise TMDBError(f"TMDB request failed: {exc}") from exc

    return [_to_movie_dict(r) for r in response.json().get("results", [])]


def get_movie(tmdb_id):
    """Fetch one movie's details from TMDB; return a dict in our Movie shape."""
    try:
        response = requests.get(
            TMDB_MOVIE_URL.format(tmdb_id=tmdb_id),
            headers={
                "Authorization": f"Bearer {settings.TMDB_READ_TOKEN}",
                "accept": "application/json",
            },
            timeout=5,
        )
        if response.status_code == 404:
            raise TMDBNotFound(f"TMDB has no movie with id {tmdb_id}")
        response.raise_for_status()
    except requests.RequestException as exc:
        raise TMDBError(f"TMDB request failed: {exc}") from exc

    return _to_movie_dict(response.json())