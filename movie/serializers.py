from rest_framework import serializers
from rest_framework.exceptions import APIException
from . import services
from .importing import get_or_import_movie
from .models import Movie, UserMovieEntry
import logging


logger = logging.getLogger(__name__)

class MovieServiceUnavailable(APIException):
    status_code = 502
    default_detail = "Movie service is unavailable. Please try again."
    default_code = "movie_service_unavailable"


class MovieImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("tmdb_id", "title", "release_year", "description", "poster_url", "slug")
        read_only_fields = ("slug",)
        # Without this, DRF adds a UniqueValidator and rejects any movie already in the DB
        extra_kwargs = {"tmdb_id": {"validators": []}}


class MovieEntrySerializer(serializers.ModelSerializer):
    movie = MovieImportSerializer(read_only=True)

    class Meta:
        model = UserMovieEntry
        fields = ("movie", "status")


class AddEntrySerializer(serializers.Serializer):
    tmdb_id = serializers.IntegerField(min_value=1)
    status = serializers.ChoiceField(
        choices=UserMovieEntry.WatchStatus.choices,
        default=UserMovieEntry.WatchStatus.WATCHLIST,
    )

    def create(self, validated_data):
        tmdb_id = validated_data["tmdb_id"]
        try:
            movie = get_or_import_movie(tmdb_id)
        except services.TMDBError as exc:
            logger.warning("TMDB lookup failed for %s", tmdb_id, exc_info=True)
            raise MovieServiceUnavailable() from exc

        entry, _ = UserMovieEntry.objects.get_or_create(
            user=self.context["request"].user,
            movie=movie,
            defaults={"status": validated_data["status"]},
        )
        return entry

    def to_representation(self, instance):                  # reply in the familiar shape
        return MovieEntrySerializer(instance, context=self.context).data