# MovieNight

MovieNight is a Django-based entertainment platform that helps users discover movies, organize their personal movie collections, and keep track of their movie-watching activity.

The project integrates with [The Movie Database (TMDB)](https://www.themoviedb.org/) to search for movies and retrieve movie information.

## Features

### Movie discovery
- Search for movies using the TMDB API.
- Retrieve movie information, including titles, release years, descriptions, and poster images.
- Import movie information into the local database when needed.

### Personal movie collection
- Add movies to your personal collection.
- Organize entries using three watch statuses:
  - **Watchlist** – movies you plan to watch.
  - **Watched** – movies you have watched.
  - **Dropped** – movies you started but decided not to continue.
- Rate movies on a 0–10 scale.
- Write reviews and record the date you watched a movie.
- View and manage your own movie entries.

### User accounts
- User registration and login.
- User profile management.
- Personal movie collections associated with individual accounts.

### REST API
- Django REST Framework-based API for listing and creating movie entries.
- Authenticated access to the movie-entry API.
- JSON and browsable API responses.
- Paginated API responses.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend programming language |
| Django | Web framework |
| Django REST Framework | REST API |
| PostgreSQL | Database |
| TMDB API | Movie search and metadata |
| Requests | External API communication |
| Pillow | Image-related functionality |
| Ruff | Python linting |
| GitHub Actions | Continuous integration |

## Project Structure

```text
movieNight/
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
├── home/
├── movie/
│   ├── importing.py
│   ├── services.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── movieNight/
│   ├── settings.py
│   └── urls.py
├── static/
├── templates/
├── user/
├── .env.example
├── manage.py
├── pyproject.toml
├── requirements.txt
└── ruff.toml
```

### Application design

The movie application separates shared movie information from each user's personal interaction with a movie.

- **Movie:** Stores shared movie metadata, identified by its unique TMDB ID.
- **UserMovieEntry:** Represents a user's relationship with a movie, including watch status, rating, review, and dates.
- **Genre:** Stores movie genres and their relationships with movies.

A database constraint prevents the same user from adding the same movie more than once.

The movie import process also checks the local database before requesting information from TMDB. This avoids unnecessary external API requests for movies that have already been imported.

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.14
- PostgreSQL
- Git
- A TMDB API read access token

### 1. Clone the repository

```bash
git clone https://github.com/FoadGhasemi/movieNight.git
cd movieNight
```

### 2. Create a virtual environment

**Windows (PowerShell):**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root, using `.env.example` as a starting point:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
TMDB_READ_TOKEN=your-tmdb-read-access-token
```

You can obtain a TMDB read access token from your TMDB account's API settings.

**Database configuration:** MovieNight uses PostgreSQL. Before running the application, configure the database connection in `movieNight/settings.py` to match your local PostgreSQL database. Use environment variables for the database name, username, password, host, and port rather than hard-coding credentials.

### 5. Apply database migrations

```bash
python manage.py migrate
```

### 6. Create a superuser

```bash
python manage.py createsuperuser
```

### 7. Run the development server

```bash
python manage.py runserver
```

Open the application at:

```text
http://127.0.0.1:8000/
```

## API

The movie application exposes an authenticated endpoint for managing personal movie entries.

### List movie entries

```http
GET /movie/api/entries/
```

Returns the authenticated user's movie entries.

### Add a movie entry

```http
POST /movie/api/entries/
Content-Type: application/json
```

Example request:

```json
{
  "tmdb_id": 550,
  "status": "Watchlist"
}
```

The API uses the supplied TMDB ID to find or import the movie, then creates a personal entry for the authenticated user.

If the movie already exists in the local database, the application reuses it instead of requesting it from TMDB again.

Available statuses:

- `Watchlist`
- `Watched`
- `Dropped`

The API requires authentication. Responses support JSON and Django REST Framework's browsable API interface.

## Testing

Run the Django test suite with:

```bash
python manage.py test
```

The project also uses Ruff for code quality checks:

```bash
ruff check .
```

## Continuous Integration

GitHub Actions runs the project's CI workflow on pushes to the `master` branch and on pull requests.

The workflow:

1. Checks out the repository.
2. Sets up Python 3.14.
3. Installs project dependencies.
4. Installs Ruff.

The workflow currently runs the Django test suite automatically.

## License

No license has been specified for this repository yet.
