"""
Poster and Visual Artwork Helper for CineMatch
Fetches real official movie posters from OMDb/IMDb API for every catalog title,
with multi-tier caching (memory + local JSON file) and fallback art.
"""

import os
import json
import logging
import hashlib
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "posters_cache.json"
)

# In-memory fast cache
_POSTER_MEMORY_CACHE: Dict[str, str] = {}

# Load persistent disk cache if exists
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            _POSTER_MEMORY_CACHE = json.load(f)
    except Exception as e:
        logger.warning("Could not load posters_cache.json: %s", e)


def _save_disk_cache():
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_POSTER_MEMORY_CACHE, f)
    except Exception as e:
        logger.warning("Could not persist posters_cache.json: %s", e)


# Curated high-resolution cinematic artwork fallback
CURATED_POSTERS = {
    "inception": "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "stranger things": "https://m.media-amazon.com/images/M/MV5BMjEzMDAxOTUyMV5BMl5BanBnXkFtZTgwNzAxMzYzOTE@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "interstellar": "https://m.media-amazon.com/images/M/MV5BYzdjMDAxZGItMjI2My00ODA1LTlkNzItOWFjMDU5ZDJlYWY3XkEyXkFqcGc@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "the dark knight": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "the witcher": "https://m.media-amazon.com/images/M/MV5BN2FiOWU4YzYtMzZiOS00MzcyLTlkOGEtKQ@@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "narcos": "https://m.media-amazon.com/images/M/MV5BNmFjODU3YzgtMGUwNC00ZGI3LWFkZjQtMjkxZDc3NmQ1MzFiXkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "breaking bad": "https://m.media-amazon.com/images/M/MV5BMzU5ZGYzNmQtMTdhYy00OGRiLTg0NmQtYjVjNzliZTg1ZGE4XkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "peaky blinders": "https://m.media-amazon.com/images/M/MV5BM2NlYTFlNmYtOTlhNi00N2Y4LWJmOGEtZGU1MTMzNzczNDY5XkEyXkFqcGc@._V1_QL75_UX380_CR0,0,380,562_.jpg"
}

GENRE_PALETTES = [
    ("linear-gradient(135deg, #0f2027, #203a43, #2c5364)", "#00d2ff"),
    ("linear-gradient(135deg, #1f1c2c, #928dab)", "#e50914"),
    ("linear-gradient(135deg, #232526, #414345)", "#ff9900"),
    ("linear-gradient(135deg, #141e30, #243b55)", "#00b4d8"),
    ("linear-gradient(135deg, #3a1c71, #d76d77, #ffaf7b)", "#ff4b4b"),
    ("linear-gradient(135deg, #000000, #434343)", "#ff2a2a")
]


def fetch_real_movie_poster(title: str, year: Optional[int] = None) -> Optional[str]:
    """
    Fetches real official movie poster using OMDb API with caching.
    """
    clean_title = title.strip()
    cache_key = f"{clean_title.lower()}_{year or ''}"

    # Check cache first
    if cache_key in _POSTER_MEMORY_CACHE:
        cached_url = _POSTER_MEMORY_CACHE[cache_key]
        if cached_url and cached_url != "N/A":
            return cached_url

    # Check curated dictionary
    title_lower = clean_title.lower()
    for k, u in CURATED_POSTERS.items():
        if k in title_lower:
            _POSTER_MEMORY_CACHE[cache_key] = u
            return u

    # Fetch from OMDb API
    params = {"t": clean_title, "apikey": "trilogy"}
    if year:
        params["y"] = int(year)

    try:
        with httpx.Client(timeout=2.5) as http_client:
            r = http_client.get("https://www.omdbapi.com/", params=params)
            if r.status_code == 200:
                data = r.json()
                poster = data.get("Poster")
                if poster and poster != "N/A":
                    _POSTER_MEMORY_CACHE[cache_key] = poster
                    # Save every 5 new cached items
                    if len(_POSTER_MEMORY_CACHE) % 5 == 0:
                        _save_disk_cache()
                    return poster
    except Exception:
        pass

    return None


def get_poster_visual(title: str, genre: str = "", year: Optional[int] = None) -> Dict[str, str]:
    """
    Returns the real official poster if available, or artistic genre-gradient.
    """
    # 1. Try real poster
    real_poster = fetch_real_movie_poster(title, year)
    if real_poster:
        return {"type": "image", "url": real_poster, "gradient": "", "accent": "#e50914"}

    # 2. Dynamic gradient fallback
    hash_val = int(hashlib.md5((title + genre).encode('utf-8')).hexdigest(), 16)
    palette_idx = hash_val % len(GENRE_PALETTES)
    grad, accent = GENRE_PALETTES[palette_idx]

    return {
        "type": "gradient",
        "url": "",
        "gradient": grad,
        "accent": accent
    }
