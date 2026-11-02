## Authentication & Authorization

### not logged-in users allowed to do:
- search
- see movies details
- see an empty list as the list of their movies

### logged-in (registered) users allowed to do:
- search
- see their review on the movie
- see the list of their movies
- add the movie to their list of movies
- update each movie's review in the list
- delete the movie from the list
- (full CRUD)

## Add to Watchlist Structure in regard to APIView

            USER INTERFACE
                 │
        "Add to Watchlist"
                 │
                 ↓
            JavaScript
          UI interaction
                 │
                 ↓
             HTTP/JSON
                 │
                 ↓
             DRF API
        "add this movie"
                 │
                 ↓
            Serializer
       validate/transform data
                 │
                 ↓
          Domain operation
                 │
                 ↓
           Django Model
                 │
                 ↓
             Database

- then the serializer gets the data back to HTML page via APIView's JSONRenderer and Js in the HTML page handles it 

