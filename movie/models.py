from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify


class Genre(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Movie(models.Model):
    """The 'Master Data' - could eventually be populated via an API like TMDB"""
    tmdb_id = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=255, blank=False)
    release_year = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True)
    poster_url = models.URLField(blank=True)  # Link to an image
    genres = models.ManyToManyField(Genre, blank=True, related_name='movies')
    slug = models.SlugField(null=False, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.tmdb_id}-{self.title}")[:50]
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("movie:detail", args=[self.slug])


class UserMovieEntry(models.Model):
    """The 'User Interaction' - This is what the user actually tracks"""

    class WatchStatus(models.TextChoices):
        # These can be translated like _('watched')
        WATCHED = 'Watched', 'watched'
        WATCHLIST = 'Watchlist', 'watchlist'
        DROPPED = 'Dropped', 'dropped'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=False, on_delete=models.CASCADE, related_name='entries')
    movie = models.ForeignKey(Movie, null=False, on_delete=models.CASCADE, related_name='user_entries')

    status = models.CharField(max_length=10, choices=WatchStatus, default=WatchStatus.WATCHLIST)
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True
    , validators = [MinValueValidator(0), MaxValueValidator(10)],
    )
    review = models.TextField(blank=True)
    date_added = models.DateTimeField(auto_now_add=True)
    date_watched = models.DateField(null=True, blank=True)
    slug = models.SlugField(null=False, unique=True, blank=True)

    class Meta:
        # Prevents a user from adding the same movie twice
        constraints = [
            models.UniqueConstraint(fields=["user", "movie"], name="unique_user_movie"),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = f"{self.user_id}-{self.movie_id}"
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("movie:update", args=[self.slug])
