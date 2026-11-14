"""
Poster Service for CineMatch
Provides official IMDb/OMDb posters for catalog titles with multi-tier caching
and guaranteed SVG poster generation fallback so no title ever has a broken image.
"""

import os
import re
import json
import logging
import urllib.parse
from typing import Dict, Optional
import httpx

logger = logging.getLogger(__name__)

CACHE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "posters_cache.json"
)

_MEMORY_CACHE: Dict[str, str] = {}

if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            _MEMORY_CACHE = json.load(f)
    except Exception as e:
        logger.warning("Failed to load posters_cache.json: %s", e)


def _save_cache() -> None:
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(_MEMORY_CACHE, f)
    except Exception as e:
        logger.warning("Failed to save posters_cache.json: %s", e)


CURATED_POSTERS: Dict[str, str] = {
    "inception": "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "stranger things": "https://m.media-amazon.com/images/M/MV5BMjEzMDAxOTUyMV5BMl5BanBnXkFtZTgwNzAxMzYzOTE@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "interstellar": "https://m.media-amazon.com/images/M/MV5BYzdjMDAxZGItMjI2My00ODA1LTlkNzItOWFjMDU5ZDJlYWY3XkEyXkFqcGc@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "the dark knight": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "the witcher": "https://m.media-amazon.com/images/M/MV5BOTQzMzNmMzUtODgwNS00YTdhLTg5N2MtOWU1YTc4YWY3NjRlXkEyXkFqcGc@._V1_QL75_UY562_CR35,0,380,562_.jpg",
    "narcos": "https://m.media-amazon.com/images/M/MV5BNmFjODU3YzgtMGUwNC00ZGI3LWFkZjQtMjkxZDc3NmQ1MzFiXkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "breaking bad": "https://m.media-amazon.com/images/M/MV5BMzU5ZGYzNmQtMTdhYy00OGRiLTg0NmQtYjVjNzliZTg1ZGE4XkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "peaky blinders": "https://m.media-amazon.com/images/M/MV5BOGM0NGY3ZmItOGE2ZC00OWIxLTk0N2EtZWY4Yzg3ZDlhNGI3XkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "squid game": "https://m.media-amazon.com/images/M/MV5BMDcxY2VkMDQtYTM5NC00Yzk4LTkyOTAtZjg1NmZhMTA0Nzg2XkEyXkFqcGc@._V1_QL75_UY562_CR7,0,380,562_.jpg",
    "lucifer": "https://m.media-amazon.com/images/M/MV5BNDJjMzc4NGYtZmFmNS00YWY3LThjMzUtYzM0ZDI3OTk3N2FiXkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "sex education": "https://m.media-amazon.com/images/M/MV5BODg1OTgyOTUtYmQzYi00YjlkLTkyOTgtYTM0Nzg4NDcyOGY1XkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "midnight mass": "https://m.media-amazon.com/images/M/MV5BYWFjMDM5MzgtZWI3OC00ZWRmLThlNTktN2ZkMTc3ZTA5NGEzXkEyXkFqcGc@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "ganglands": "https://m.media-amazon.com/images/M/MV5BYWJkOWM3NDQtYmQ0Mi00MzliLTg4YzctNDk2ZjY4NDQwYTRmXkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "the box": "https://m.media-amazon.com/images/M/MV5BMTI4MDA5NjIwM15BMl5BanBnXkFtZTcwNTA2MjY0Mg@@._V1_QL75_UX380_CR0,1,380,562_.jpg",
    "the signal": "https://m.media-amazon.com/images/M/MV5BMDEwYjVkZGItMjc3Zi00YjI5LWE0YTUtODQ4NzRiM2FmYmNmXkEyXkFqcGc@._V1_QL75_UX380_CR0,4,380,562_.jpg",
    "clash of the titans": "https://m.media-amazon.com/images/M/MV5BMTYxNjg4MzU5OV5BMl5BanBnXkFtZTcwOTA3NTUwMw@@._V1_QL75_UX380_CR0,0,380,562_.jpg",
    "dragonheart: battle for the heartfire": "https://m.media-amazon.com/images/M/MV5BZTEyMmE0OTgtMzkzOS00ZTVkLWI3MjMtYmIyOTM0YTg3OWQ2XkEyXkFqcGc@._V1_QL75_UY562_CR7,0,380,562_.jpg",
    "seventh son": "https://m.media-amazon.com/images/M/MV5BMjA4NjA3ODc0Nl5BMl5BanBnXkFtZTgwNTQ2Njg0NDE@._V1_SX300.jpg",
    "cory carson christmas": "https://m.media-amazon.com/images/M/MV5BZDQyODljMTItMDk2YS00ZDMzLTg2NmUtY2FkOTQxNzQzMmNjXkEyXkFqcGc@._V1_UY562_CR11,0,380,562_.jpg",
    "cory carson": "https://m.media-amazon.com/images/M/MV5BZDQyODljMTItMDk2YS00ZDMzLTg2NmUtY2FkOTQxNzQzMmNjXkEyXkFqcGc@._V1_UY562_CR11,0,380,562_.jpg"
}

GENRE_COLORS = {
    "action": ("#e50914", "#3b0003"),
    "sci-fi": ("#00d2ff", "#031b33"),
    "horror": ("#990000", "#1a0000"),
    "comedy": ("#ff9900", "#331f00"),
    "drama": ("#8b5cf6", "#1e113a"),
    "children": ("#10b981", "#022c1e"),
    "documentaries": ("#06b6d4", "#042f36"),
    "thrillers": ("#f43f5e", "#2e0811"),
}


def generate_svg_poster(title: str, genre: str = "", year: str = "") -> str:
    """Generates an embedded, vector SVG poster with crisp typography and theme colors."""
    g_lower = genre.lower() if genre else ""
    accent_color, bg_dark = ("#e50914", "#121826")
    for key, (acc, bg) in GENRE_COLORS.items():
        if key in g_lower:
            accent_color, bg_dark = acc, bg
            break

    # Truncate title cleanly
    safe_title = title.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', '&quot;')
    clean_genre = genre.split(",")[0].strip().replace("&", "&amp;") if genre else "Featured"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{bg_dark}"/>
      <stop offset="60%" stop-color="#0b0f19"/>
      <stop offset="100%" stop-color="#05070c"/>
    </linearGradient>
    <linearGradient id="glow" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{accent_color}" stop-opacity="0.4"/>
      <stop offset="100%" stop-color="{accent_color}" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#bg)"/>
  <rect width="100%" height="60%" fill="url(#glow)"/>
  <circle cx="150" cy="170" r="50" fill="#131b2c" stroke="{accent_color}" stroke-width="2" opacity="0.9"/>
  <text x="150" y="180" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="34" fill="{accent_color}" text-anchor="middle">🎬</text>
  <rect x="25" y="250" width="250" height="2" fill="{accent_color}" opacity="0.6"/>
  <text x="150" y="295" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="20" font-weight="bold" fill="#ffffff" text-anchor="middle">{safe_title[:22]}</text>
  <text x="150" y="325" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="13" font-weight="600" fill="{accent_color}" text-anchor="middle">{clean_genre.upper()}</text>
  <text x="150" y="355" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif" font-size="12" fill="#94a3b8" text-anchor="middle">{year} • CINEMATCH</text>
</svg>"""
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg)


def get_poster_url(title: str, year: Optional[int] = None, genre: str = "") -> str:
    """
    Returns official IMDb/OMDb poster image URL, or guaranteed SVG vector poster.
    """
    if not title:
        return generate_svg_poster("Featured Title", genre, str(year or 2021))

    clean_t = title.strip()
    cache_key = f"{clean_t.lower()}_{year or ''}"

    # 1. Check memory cache
    if cache_key in _MEMORY_CACHE and _MEMORY_CACHE[cache_key]:
        return _MEMORY_CACHE[cache_key]

    # 2. Check curated dictionary
    t_lower = clean_t.lower()
    for cur_key, cur_url in CURATED_POSTERS.items():
        if cur_key in t_lower:
            _MEMORY_CACHE[cache_key] = cur_url
            return cur_url

def search_omdb_variations(title: str, year: Optional[int] = None) -> Optional[str]:
    """
    Performs intelligent multi-variation search against OMDb to locate official IMDb posters.
    Handles prefixes ('A Go! Go!', '#', '@'), subtitles, punctuation, and release years.
    """
    clean = re.sub(r'\(.*?\)', '', str(title)).strip()
    clean = re.sub(r'^[#@!]+', '', clean).strip()
    clean = re.sub(r'^[A-Za-z]\s+Go!\s+Go!\s+', '', clean, flags=re.IGNORECASE).strip()

    variations = [clean]
    if ':' in clean:
        variations.append(clean.split(':')[0].strip())
    if ' - ' in clean:
        variations.append(clean.split(' - ')[0].strip())
    no_punct = re.sub(r'[^a-zA-Z0-9\s]', ' ', clean).strip()
    if no_punct and no_punct not in variations:
        variations.append(no_punct)

    for q in variations:
        for y in [year, None]:
            params = {'t': q, 'apikey': 'trilogy'}
            if y:
                try:
                    params['y'] = int(y)
                except Exception:
                    pass
            try:
                with httpx.Client(timeout=2.0) as client:
                    resp = client.get("https://www.omdbapi.com/", params=params)
                    if resp.status_code == 200:
                        data = resp.json()
                        p = data.get("Poster")
                        if p and p != "N/A" and p.startswith("http"):
                            return p
            except Exception:
                pass
    return None


def get_poster_url(title: str, year: Optional[int] = None, genre: str = "") -> str:
    """
    Returns official IMDb/OMDb poster image URL, or guaranteed SVG vector poster.
    """
    if not title:
        return generate_svg_poster("Featured Title", genre, str(year or 2021))

    clean_t = title.strip()
    y_str = str(year) if year else ""
    cache_key = f"{clean_t.lower()}_{y_str}"

    # 1. Check memory cache (only if valid http URL)
    if cache_key in _MEMORY_CACHE and _MEMORY_CACHE[cache_key].startswith("http"):
        return _MEMORY_CACHE[cache_key]

    # Reload from disk cache if not in memory
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                disk_cache = json.load(f)
                _MEMORY_CACHE.update(disk_cache)
                if cache_key in _MEMORY_CACHE and _MEMORY_CACHE[cache_key].startswith("http"):
                    return _MEMORY_CACHE[cache_key]
        except Exception:
            pass

    # 2. Check curated dictionary
    t_lower = clean_t.lower()
    for cur_key, cur_url in CURATED_POSTERS.items():
        if cur_key in t_lower:
            _MEMORY_CACHE[cache_key] = cur_url
            return cur_url

    # 3. Intelligent multi-variation query to OMDb
    found_poster = search_omdb_variations(clean_t, year)
    if found_poster:
        _MEMORY_CACHE[cache_key] = found_poster
        _save_cache()
        return found_poster

    # 4. Fallback to guaranteed SVG poster data URI (do NOT persist SVG in cache permanently)
    return generate_svg_poster(clean_t, genre, y_str)
