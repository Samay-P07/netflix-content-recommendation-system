# CineMatch — REST API Specification

**Base URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs` (Swagger UI) / `http://localhost:8000/redoc`

---

## 1. System Endpoints

### `GET /health`
Returns system status, index size, and database health.
- **Status:** 200 OK
- **Response:**
  ```json
  {
    "status": "healthy",
    "version": "1.0.0",
    "catalog_loaded": true,
    "total_titles": 8786,
    "database_connected": true
  }
  ```

---

## 2. Titles & Catalogue Endpoints

### `GET /titles`
Paginated search and multi-attribute filtering.
- **Query Parameters:**
  - `q` (string, optional): Search keyword.
  - `type` (string, optional): `"Movie"` or `"TV Show"`.
  - `genre` (string, optional): Genre substring.
  - `year` (int, optional): Exact release year.
  - `year_min` (int, optional): Minimum release year.
  - `year_max` (int, optional): Maximum release year.
  - `sort_by` (string, default: `"title_asc"`): `"title_asc"`, `"title_desc"`, `"year_desc"`, `"year_asc"`.
  - `page` (int, default: 1, min: 1).
  - `page_size` (int, default: 20, max: 100).
- **Status:** 200 OK
- **Response:**
  ```json
  {
    "total": 8786,
    "page": 1,
    "page_size": 20,
    "total_pages": 440,
    "items": [
      {
        "show_id": "s1",
        "title": "Dick Johnson Is Dead",
        "type": "Movie",
        "release_year": 2020,
        "rating": "PG-13",
        "duration": "90 min",
        "listed_in": "Documentaries",
        "country": "United States"
      }
    ]
  }
  ```

### `GET /titles/search?q={query}&limit=10`
Fast lookup for autocomplete queries.

### `GET /titles/genres`
Returns list of all 42 distinct genres in the catalogue.

### `GET /titles/{title_id}`
Returns metadata details for a specific `show_id` (e.g. `s1`) or title string.
- **Status:** 200 OK or 404 Not Found.

---

## 3. Recommendation Endpoints

### `GET /recommendations/{title_id}`
Computes top-$K$ recommendations with geometric cosine similarity and verifiable explanation.
- **Query Parameters:**
  - `limit` (int, default: 10, min: 1, max: 50).
  - `type` (string, optional): Filter by `"Movie"` or `"TV Show"`.
- **Status:** 200 OK or 404 Not Found.
- **Response:**
  ```json
  {
    "query_id": "s1",
    "query_title": "Inception",
    "total_recommendations": 5,
    "disclaimer": "Similarity scores reflect geometric cosine proximity across catalog metadata...",
    "recommendations": [
      {
        "show_id": "s824",
        "title": "The Box",
        "type": "Movie",
        "release_year": 2009,
        "rating": "PG-13",
        "country": "United States",
        "duration": "115 min",
        "listed_in": "Sci-Fi & Fantasy, Thrillers",
        "director": "Richard Kelly",
        "similarity_score": 0.8902,
        "similarity_percentage": 89,
        "explanation": "Shares genres: Sci-Fi & Fantasy, Thrillers • Origin: United States",
        "query_title": "Inception"
      }
    ]
  }
  ```

---

## 4. Catalogue Insights Endpoints

### `GET /insights/overview`
Aggregated dataset descriptive statistics.
- **Status:** 200 OK
- **Response:**
  ```json
  {
    "total_titles": 8786,
    "movies_count": 6126,
    "tv_shows_count": 2660,
    "type_distribution": { "Movie": 6126, "TV Show": 2660 },
    "top_genres": [{ "name": "Dramas", "count": 2426 }, ...],
    "top_countries": [{ "name": "United States", "count": 3686 }, ...],
    "release_year_distribution": [{ "name": "2020", "count": 953 }, ...],
    "catalog_summary": "Catalog comprises 8,786 titles..."
  }
  ```

---

## 5. History & Saved Titles Endpoints

- `GET /history`: Get recent searches.
- `POST /history`: Record search `{"query": "Inception", "selected_title_id": "s1"}`.
- `DELETE /history`: Clear search history.
- `GET /saved`: List saved titles.
- `POST /saved`: Bookmark title `{"show_id": "s1"}`.
- `DELETE /saved/{show_id}`: Remove bookmark.
