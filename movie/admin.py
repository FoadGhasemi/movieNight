from django.contrib import admin

from .models import Genre, Movie, UserMovieEntry


class MovieAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "get_genres")

    @admin.display(description="Genres")
    def get_genres(self, obj):
        return ", ".join(g.name for g in obj.genres.all())


admin.site.register(Movie, MovieAdmin)
admin.site.register(Genre)
admin.site.register(UserMovieEntry)