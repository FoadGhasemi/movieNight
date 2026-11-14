"""
Tests for the entries API:
    /movie/api/entries/          (EntryListCreateAPIView)
    /movie/api/entries/<pk>/     (EntryDetail)
plus ownership checks on the template-based update/delete pages.

Put this file at movie/tests/test_entries_api.py (with an empty movie/tests/__init__.py,
and delete movie/tests.py if it exists), then run:

    python manage.py test movie
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from movie.models import Movie, UserMovieEntry
from unittest.mock import patch
from movie import services
from django.test import SimpleTestCase


User = get_user_model()


def movie_payload(tmdb_id=1, title="Batman"):
    return {
        "tmdb_id": tmdb_id,
        "title": title,
        "release_year": 1989,
        "poster_url": "",
    }


class EntryAPITestCase(APITestCase):
    """Shared users, movie and helpers. Has no test_ methods, so it runs nothing itself."""

    @classmethod
    def setUpTestData(cls):
        # Built once per class and rolled back between tests, so it is cheap.
        cls.alice = User.objects.create_user(username="alice", password="pass12345")
        cls.bob = User.objects.create_user(username="bob", password="pass12345")
        cls.batman = Movie.objects.create(
            tmdb_id=1, title="Batman", release_year=1989, description="Dark knight."
        )

    def setUp(self):
        self.list_url = reverse("movie:api_entries")
        # Every test acts as alice unless it switches user.
        self.client.force_authenticate(user=self.alice)

    def add_entry(self, user, movie=None, **extra):
        """Create an entry straight in the DB (no API involved)."""
        return UserMovieEntry.objects.create(user=user, movie=movie or self.batman, **extra)

    def post_entry(self, tmdb_id=1, entry_status="Watchlist"):
        return self.client.post(
            self.list_url, {"tmdb_id": tmdb_id, "status": entry_status}, format="json"
        )


class EntryListCreateTests(EntryAPITestCase):
    def test_create_entry_for_new_movie(self):
        res = self.post_entry(tmdb_id=99)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        entry = UserMovieEntry.objects.get(user=self.alice, movie__tmdb_id=99)
        self.assertEqual(entry.status, "Watchlist")
        self.assertEqual(Movie.objects.filter(tmdb_id=99).count(), 1)

    def test_create_entry_reuses_existing_movie(self):
        # Batman (tmdb_id=1) is already in the table. If an auto-added UniqueValidator
        # sits on tmdb_id, this returns 400 before get_or_create ever runs.
        res = self.post_entry()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(Movie.objects.filter(tmdb_id=1).count(), 1)
        self.assertTrue(
            UserMovieEntry.objects.filter(user=self.alice, movie=self.batman).exists()
        )

    def test_posting_same_movie_twice_keeps_one_entry(self):
        # create() uses get_or_create, so a repeated POST is idempotent.
        self.post_entry()
        self.post_entry()

        self.assertEqual(UserMovieEntry.objects.filter(user=self.alice).count(), 1)

    def test_two_users_can_track_the_same_movie(self):
        self.post_entry()
        self.client.force_authenticate(user=self.bob)
        res = self.post_entry()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.assertEqual(UserMovieEntry.objects.filter(movie=self.batman).count(), 2)
        self.assertEqual(Movie.objects.count(), 1)

    def test_list_returns_only_my_entries(self):
        heat = Movie.objects.create(tmdb_id=2, title="Heat", release_year=1995, description="x")
        self.add_entry(self.alice)
        self.add_entry(self.bob, movie=heat)

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["results"][0]["movie"]["title"], "Batman")

    def test_anonymous_requests_are_rejected(self):
        self.client.force_authenticate(user=None)

        get_res = self.client.get(self.list_url)
        post_res = self.post_entry()

        # Session auth answers 403, token/JWT auth would answer 401.
        for res in (get_res, post_res):
            self.assertIn(
                res.status_code,
                (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
            )
        self.assertEqual(UserMovieEntry.objects.count(), 0)

    from unittest.mock import patch  # add to the imports at the top if it's not there

    @patch("movie.importing.services.get_movie")
    def test_bad_payload_returns_400_and_creates_nothing(self, mock_get_movie):
        cases = {
            "missing tmdb_id": ({"status": "Watchlist"}, "tmdb_id"),
            "tmdb_id not a number": ({"tmdb_id": "abc", "status": "Watchlist"}, "tmdb_id"),
            "tmdb_id zero": ({"tmdb_id": 0, "status": "Watchlist"}, "tmdb_id"),
            "unknown status": ({"tmdb_id": 1, "status": "Binged"}, "status"),
        }
        for name, (body, error_key) in cases.items():
            with self.subTest(name):
                res = self.client.post(self.list_url, body, format="json")
                self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn(error_key, res.data)

        mock_get_movie.assert_not_called()  # invalid input must never reach TMDB
        self.assertEqual(UserMovieEntry.objects.count(), 0)


class PageViewOwnershipTests(TestCase):
    """The template-based update/delete pages must not touch other users' entries."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="pass12345")
        cls.bob = User.objects.create_user(username="bob", password="pass12345")
        movie = Movie.objects.create(
            tmdb_id=1, title="Batman", release_year=1989, description="Dark knight."
        )
        cls.entry = UserMovieEntry.objects.create(user=cls.alice, movie=movie)

    def test_update_page_of_someone_elses_entry_is_404(self):
        self.client.force_login(self.bob)

        res = self.client.get(reverse("movie:update", args=[self.entry.slug]))

        self.assertEqual(res.status_code, 404)

    def test_delete_of_someone_elses_entry_is_404_and_keeps_it(self):
        self.client.force_login(self.bob)

        res = self.client.post(reverse("movie:delete", args=[self.entry.slug]))

        self.assertEqual(res.status_code, 404)
        self.assertTrue(UserMovieEntry.objects.filter(pk=self.entry.pk).exists())


class SlugUniquenessTests(TestCase):
    """Regression tests for the slug collisions."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="pass12345")
        cls.bob = User.objects.create_user(username="bob", password="pass12345")
        cls.movie = Movie.objects.create(
            tmdb_id=1, title="Batman", release_year=1989, description="x"
        )

    # I suspect we already have this tested in test_two_users_can_track_the_same_movie
    def test_two_users_can_have_entries_for_the_same_movie(self):
        alice_entry = UserMovieEntry.objects.create(user=self.alice, movie=self.movie)
        bob_entry = UserMovieEntry.objects.create(user=self.bob, movie=self.movie)

        self.assertNotEqual(alice_entry.slug, bob_entry.slug)

    def test_two_movies_with_the_same_title_get_different_slugs(self):
        remake = Movie.objects.create(
            tmdb_id=2, title="Batman", release_year=2022, description="y"
        )

        self.assertNotEqual(self.movie.slug, remake.slug)


class SameMovieOwnershipTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="pass12345")
        cls.bob = User.objects.create_user(username="bob", password="pass12345")
        movie = Movie.objects.create(
            tmdb_id=1, title="Batman", release_year=1989, description="x"
        )
        cls.alice_entry = UserMovieEntry.objects.create(user=cls.alice, movie=movie)
        cls.bob_entry = UserMovieEntry.objects.create(user=cls.bob, movie=movie)

    # I'm afraid we tested that in test_update_page_of_someone_elses_entry_is_404
    def test_bob_cannot_open_alices_update_page(self):
        self.client.force_login(self.bob)
        res = self.client.get(reverse("movie:update", args=[self.alice_entry.slug]))
        self.assertEqual(res.status_code, 404)

    def test_bob_can_open_his_own_update_page(self):
        self.client.force_login(self.bob)
        res = self.client.get(reverse("movie:update", args=[self.bob_entry.slug]))
        self.assertEqual(res.status_code, 200)


class SearchMoviesTests(SimpleTestCase):
    @patch("movie.services.requests.get")
    def test_maps_tmdb_result_to_our_shape(self, mock_get):
        mock_get.return_value.json.return_value = {"results": [{
            "id": 1, "title": "The Batman", "overview": "Dark.",
            "release_date": "2022-03-01", "poster_path": "/a.jpg",
        }]}

        result = services.search_movies("batman")

        self.assertEqual(result, [{
            "tmdb_id": 1, "title": "The Batman", "release_year": 2022,
            "description": "Dark.", "poster_url": "https://image.tmdb.org/t/p/w342/a.jpg",
        }])


class GetMovieTests(SimpleTestCase):

    @patch("movie.services.requests.get")
    def test_get_movie_returns_our_shape(self, mock_get):
        # ARRANGE: what TMDB would answer
        mock_get.return_value.json.return_value = {
            "id": 1,
            "title": "The Batman",
            "overview": "Dark.",
            "release_date": "2022-03-01",
            "poster_path": "/a.jpg",
        }

        # ACT
        result = services.get_movie(1)

        # ASSERT
        self.assertEqual(result, {
            "tmdb_id": 1,
            "title": "The Batman",
            "release_year": 2022,
            "description": "Dark.",
            "poster_url": "https://image.tmdb.org/t/p/w342/a.jpg",
        })
        mock_get.assert_called_once()
        self.assertTrue(mock_get.call_args.args[0].endswith("/movie/1"))   # the right URL


HEAT = {"tmdb_id": 99, "title": "Heat", "release_year": 1995,
        "description": "x", "poster_url": ""}

@patch("movie.importing.services.get_movie", return_value=HEAT)
def test_create_entry_for_new_movie(self, mock_get_movie):
    res = self.post_entry(tmdb_id=99)

    self.assertEqual(res.status_code, 201, res.data)
    mock_get_movie.assert_called_once_with(99)
    self.assertTrue(UserMovieEntry.objects.filter(user=self.alice, movie__tmdb_id=99).exists())

@patch("movie.importing.services.get_movie")
def test_existing_movie_does_not_call_tmdb(self, mock_get_movie):
    res = self.post_entry(tmdb_id=1)         # Batman is already in the database

    self.assertEqual(res.status_code, 201, res.data)
    mock_get_movie.assert_not_called()

@patch("movie.importing.services.get_movie", side_effect=services.TMDBError("down"))
def test_tmdb_down_returns_502(self, mock_get_movie):
    res = self.post_entry(tmdb_id=99)

    self.assertEqual(res.status_code, 502)
    self.assertEqual(UserMovieEntry.objects.count(), 0)



