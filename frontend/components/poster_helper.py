"""
Poster and Visual Artwork Helper for CineMatch
Provides curated high-resolution backdrop art for popular titles
and stylized genre-gradient visual posters for all catalog items.
"""

import hashlib
from typing import Dict, Any

# Curated high-resolution cinematic artwork for popular catalogue titles
CURATED_POSTERS = {
    "inception": "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=600&auto=format&fit=crop&q=80",
    "stranger things": "https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=600&auto=format&fit=crop&q=80",
    "interstellar": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=600&auto=format&fit=crop&q=80",
    "the dark knight": "https://images.unsplash.com/photo-1509248961158-e54f6934749c?w=600&auto=format&fit=crop&q=80",
    "the witcher": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80",
    "narcos": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=600&auto=format&fit=crop&q=80",
    "breaking bad": "https://images.unsplash.com/photo-1533227268428-f9ed0900fb3b?w=600&auto=format&fit=crop&q=80",
    "black mirror": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop&q=80",
    "the matrix": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=600&auto=format&fit=crop&q=80",
    "titanic": "https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=600&auto=format&fit=crop&q=80",
    "joker": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?w=600&auto=format&fit=crop&q=80",
    "peaky blinders": "https://images.unsplash.com/photo-1485846234645-a62644f84728?w=600&auto=format&fit=crop&q=80",
    "the queen's gambit": "https://images.unsplash.com/photo-1529699211952-734e80c4d42b?w=600&auto=format&fit=crop&q=80",
    "dark": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=600&auto=format&fit=crop&q=80",
    "money heist": "https://images.unsplash.com/photo-1557804506-669a67965ba0?w=600&auto=format&fit=crop&q=80",
    "lucifer": "https://images.unsplash.com/photo-1508739773434-c26b3d09e071?w=600&auto=format&fit=crop&q=80",
    "crown": "https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop&q=80",
    "squid game": "https://images.unsplash.com/photo-1511512578047-dfb367046420?w=600&auto=format&fit=crop&q=80",
    "avengers": "https://images.unsplash.com/photo-1568605117036-5fe5e7bab0b7?w=600&auto=format&fit=crop&q=80"
}

# Thematic color palettes for dynamic poster artwork
GENRE_PALETTES = [
    ("linear-gradient(135deg, #0f2027, #203a43, #2c5364)", "#00d2ff"), # Sci-Fi/Fantasy
    ("linear-gradient(135deg, #1f1c2c, #928dab)", "#e50914"),           # Drama/Noir
    ("linear-gradient(135deg, #232526, #414345)", "#ff9900"),           # Action/Thriller
    ("linear-gradient(135deg, #141e30, #243b55)", "#00b4d8"),           # Adventure
    ("linear-gradient(135deg, #3a1c71, #d76d77, #ffaf7b)", "#ff4b4b"), # Romance/Comedy
    ("linear-gradient(135deg, #000000, #434343)", "#ff2a2a"),           # Horror/Crime
    ("linear-gradient(135deg, #114357, #f29492)", "#ffa07a"),           # Indie/Doc
]


def get_poster_visual(title: str, genre: str = "") -> Dict[str, str]:
    """
    Returns an image URL if curated, or a CSS gradient background with accent color.
    """
    norm_title = title.strip().lower()

    # 1. Exact or partial curated match
    for key, img_url in CURATED_POSTERS.items():
        if key in norm_title:
            return {"type": "image", "url": img_url, "gradient": "", "accent": "#e50914"}

    # 2. Deterministic genre/title hash gradient
    hash_val = int(hashlib.md5((title + genre).encode('utf-8')).hexdigest(), 16)
    palette_idx = hash_val % len(GENRE_PALETTES)
    grad, accent = GENRE_PALETTES[palette_idx]

    return {
        "type": "gradient",
        "url": "",
        "gradient": grad,
        "accent": accent
    }
