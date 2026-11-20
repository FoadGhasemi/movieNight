from unittest.mock import patch

import requests
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from movie import services
from movie.models import Movie, UserMovieEntry

User = get_user_model()


class EntryAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(
            username="alice", password="pass12345"
        )
        cls.bob = User.objects.create_user(
            username="bob", password="pass12345"
        )
        cls.batman = Movie.objects.create(
            tmdb_id=1,
            title="Batman",
            release_year=1989,
            description="Dark knight."
        )

    def setUp(self):
        self.list_url = reverse("movie:api_entries")
        self.client.force_authenticate(user=self.alice)

        # Prevent every API test from making a real TMDB request.
        self.tmdb_patcher = patch("movie.importing.services.get_movie")
        self.mock_get_movie = self.tmdb_patcher.start()
        self.addCleanup(self.tmdb_patcher.stop)

    def add_entry(self, user, movie=None, **extra):
        return UserMovieEntry.objects.create(
            user=user,
            movie=movie or self.batman,
            **extra
        )

    def post_entry(self, tmdb_id=1, entry_status="Watchlist"):
        return self.client.post(
            self.list_url,
            {"tmdb_id": tmdb_id, "status": entry_status},
            format="json"
        )

HEAT = {
    "tmdb_id": 99,
    "title": "Heat",
    "release_year": 1995,
    "description": "x",
    "poster_url": ""
}

class EntryListCreateTests(EntryAPITestCase):

    def test_create_entry_for_new_movie(self):
        self.mock_get_movie.return_value = HEAT

        res = self.post_entry(tmdb_id=99)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)

        self.mock_get_movie.assert_called_once_with(99)

        entry = UserMovieEntry.objects.get(
            user=self.alice,
            movie__tmdb_id=99
        )

        self.assertTrue(UserMovieEntry.objects.filter(user=self.alice, movie__tmdb_id=99).exists())
        self.assertEqual(entry.status, "Watchlist")
        self.assertEqual(Movie.objects.filter(tmdb_id=99).count(), 1)

    def test_create_entry_reuses_existing_movie(self):
        res = self.post_entry()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED, res.data)
        self.mock_get_movie.assert_not_called()

        self.assertEqual(Movie.objects.filter(tmdb_id=1).count(), 1)

        self.assertTrue(
            UserMovieEntry.objects.filter(
                user=self.alice,
                movie=self.batman
            ).exists()
        )

    def test_posting_same_movie_twice_keeps_one_entry(self):
        self.post_entry()
        self.post_entry()

        self.assertEqual(
            UserMovieEntry.objects.filter(user=self.alice).count(),
            1
        )

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

    def test_bad_payload_returns_400_and_creates_nothing(self):
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

        self.mock_get_movie.assert_not_called()
        self.assertEqual(UserMovieEntry.objects.count(), 0)

    def test_existing_movie_does_not_call_tmdb(self):
        res = self.post_entry(tmdb_id=1)  # Batman is already in the database

        self.assertEqual(res.status_code, 201, res.data)
        self.mock_get_movie.assert_not_called()

    def test_tmdb_down_returns_502(self):
        self.mock_get_movie.side_effect = services.TMDBError("down")
        res = self.post_entry(tmdb_id=99)

        self.assertEqual(res.status_code, 502)
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
        cls.alice_entry = UserMovieEntry.objects.create(user=cls.alice, movie=movie)
        cls.bob_entry = UserMovieEntry.objects.create(user=cls.bob, movie=movie)

    def test_bob_cannot_open_alices_update_page(self):
        self.client.force_login(self.bob)
        res = self.client.get(reverse("movie:update", args=[self.alice_entry.slug]))
        self.assertEqual(res.status_code, 404)

    def test_delete_of_someone_elses_entry_is_404_and_keeps_it(self):
        self.client.force_login(self.bob)

        res = self.client.post(reverse("movie:delete", args=[self.alice_entry.slug]))

        self.assertEqual(res.status_code, 404)
        self.assertTrue(UserMovieEntry.objects.filter(pk=self.alice_entry.pk).exists())


class SlugUniquenessTests(TestCase):
    """Regression tests for the slug collisions."""

    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", password="pass12345")
        cls.bob = User.objects.create_user(username="bob", password="pass12345")
        cls.movie = Movie.objects.create(
            tmdb_id=1, title="Batman", release_year=1989, description="x"
        )

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


def fake_response(status_code):
    """A real requests.Response, so raise_for_status() behaves like in real life."""
    response = requests.Response()
    response.status_code = status_code
    return response


class GetMovieErrorTests(SimpleTestCase):

    @patch("movie.services.requests.get", return_value=fake_response(404))
    def test_404_raises_tmdb_not_found(self, mock_get):
        with self.assertRaises(services.TMDBNotFound):
            services.get_movie(1)

    @patch("movie.services.requests.get")
    def test_other_http_errors_raise_tmdb_error(self, mock_get):
        for code in (400, 401, 429, 500, 502):
            with self.subTest(code=code):
                mock_get.return_value = fake_response(code)

                with self.assertRaises(services.TMDBError) as ctx:
                    services.get_movie(1)

                self.assertNotIsInstance(ctx.exception, services.TMDBNotFound)

    @patch("movie.services.requests.get", side_effect=requests.Timeout())
    def test_timeout_raises_tmdb_error(self, mock_get):
        with self.assertRaises(services.TMDBError) as ctx:
            services.get_movie(1)

        self.assertNotIsInstance(ctx.exception, services.TMDBNotFound)

