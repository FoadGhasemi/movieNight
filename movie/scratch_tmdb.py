import os
import requests
from dotenv import load_dotenv

load_dotenv()

r = requests.get(
    "https://api.themoviedb.org/3/search/movie",
    params={"query": "batman", "include_adult": "false"},
    headers={
        "Authorization": f"Bearer {os.environ['TMDB_READ_TOKEN']}",
        "accept": "application/json",
    },
    timeout=5,
)
print(r.status_code)
print(r.json()["results"][0])