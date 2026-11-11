from rest_framework import serializers
from .models import Movie, UserMovieEntry


class MovieImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ("tmdb_id", "title", "release_year", "description", "poster_url", "slug")
        read_only_fields = ("slug",)
        # Without this, DRF adds a UniqueValidator and rejects any movie already in the DB
        extra_kwargs = {"tmdb_id": {"validators": []}}


class MovieEntrySerializer(serializers.ModelSerializer):
    movie = MovieImportSerializer()

    class Meta:
        model = UserMovieEntry
        fields = ("movie", "status")

    def create(self, validated_data):
        movie_data = validated_data.pop("movie")

        movie, _ = Movie.objects.get_or_create(
            tmdb_id=movie_data["tmdb_id"],
            defaults=movie_data,
        )

        entry, created = UserMovieEntry.objects.get_or_create(
            user=self.context["request"].user,
            movie=movie,
            defaults=validated_data,
        )

        return entry
