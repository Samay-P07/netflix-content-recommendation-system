"""
Reusable UI Components for CineMatch
Provides clean streaming-card HTML rendering with real movie posters,
floating badges, and verifiable recommendation explanations.
"""

import html
import textwrap
from typing import Dict, Any, Optional
from frontend.components.poster_helper import get_poster_visual


def render_movie_card(
    item: Dict[str, Any],
    is_recommendation: bool = False,
    is_saved: bool = False
) -> str:
    """Renders a modern streaming-style movie card with real poster image and badges."""
    title = html.escape(str(item.get("title", "")))
    content_type = html.escape(str(item.get("type", "Movie")))
    raw_year = item.get("release_year", "")
    release_year = html.escape(str(raw_year))
    rating = html.escape(str(item.get("rating", "")))
    duration = html.escape(str(item.get("duration", "")))
    listed_in = html.escape(str(item.get("listed_in", "")))
    country = html.escape(str(item.get("country", "")))
    director = html.escape(str(item.get("director", "")))
    show_id = html.escape(str(item.get("show_id", "")))

    type_badge_cls = "badge-tv" if "tv" in content_type.lower() else "badge-movie"
    rating_badge = f'<span class="badge badge-rating">{rating}</span>' if rating else ''

    # Fetch real official poster
    numeric_year = int(raw_year) if str(raw_year).isdigit() else None
    visual = get_poster_visual(item.get("title", ""), listed_in, numeric_year)

    if visual["type"] == "image":
        poster_markup = f'<img src="{visual["url"]}" class="poster-img" alt="{title}" loading="lazy" onerror="this.style.display=\'none\'" />'
        container_bg = 'background-color: #121826;'
    else:
        initials = "".join([w[0] for w in title.split()[:2] if w]).upper()
        poster_markup = f'<div class="poster-fallback-inner"><div class="poster-icon">🎬</div><div class="poster-initials">{initials}</div></div>'
        container_bg = f'background: {visual["gradient"]};'

    # Score badge
    score_html = ""
    if is_recommendation and "similarity_percentage" in item:
        pct = item["similarity_percentage"]
        score_val = item.get("similarity_score", 0.0)
        score_html = f'<div class="badge-score-floating" title="Cosine similarity: {score_val:.4f}">★ {pct}% Match</div>'

    # Explanation section
    explanation_html = ""
    if is_recommendation and item.get("explanation"):
        explanation_text = html.escape(str(item.get("explanation")))
        explanation_html = f'<div class="card-explanation"><span class="explanation-icon">💡</span><span><strong>Why recommended:</strong> {explanation_text}</span></div>'

    director_html = f'<span class="meta-director">• Dir: {director}</span>' if director and director.lower() not in {'', 'unknown', 'nan'} else ''
    country_html = f'<span class="meta-country">• {country}</span>' if country and country.lower() not in {'', 'unknown', 'nan'} else ''

    card_raw = f'''<div class="streaming-card">
<div class="poster-container" style="{container_bg}">
{poster_markup}
<div class="poster-overlay">
<div class="poster-top-bar">
<span class="badge {type_badge_cls}">{content_type}</span>
{rating_badge}
</div>
{score_html}
</div>
</div>
<div class="card-body">
<div class="card-title-row">
<h4 class="card-title" title="{title}">{title}</h4>
<span class="card-year">{release_year}</span>
</div>
<div class="card-genre">{listed_in}</div>
<div class="card-submeta">
{director_html}
{country_html}
</div>
{explanation_html}
</div>
</div>'''

    # Ensure no leading whitespace so Markdown never turns it into a code block
    return "\n".join([line.strip() for line in card_raw.splitlines() if line.strip()])


def render_hero_spotlight(item: Dict[str, Any]) -> str:
    """Renders the top featured hero banner with real poster artwork."""
    title = html.escape(str(item.get("title", "")))
    content_type = html.escape(str(item.get("type", "Movie")))
    raw_year = item.get("release_year", "")
    release_year = html.escape(str(raw_year))
    rating = html.escape(str(item.get("rating", "")))
    duration = html.escape(str(item.get("duration", "")))
    listed_in = html.escape(str(item.get("listed_in", "")))
    country = html.escape(str(item.get("country", "")))
    director = html.escape(str(item.get("director", "")))

    numeric_year = int(raw_year) if str(raw_year).isdigit() else None
    visual = get_poster_visual(item.get("title", ""), listed_in, numeric_year)

    if visual["type"] == "image":
        bg_style = f"background: linear-gradient(90deg, rgba(11, 15, 25, 0.95) 30%, rgba(11, 15, 25, 0.75) 65%, rgba(11, 15, 25, 0.4) 100%), url('{visual['url']}') center/cover;"
        hero_poster_img = f'<div class="hero-poster-col"><img src="{visual["url"]}" class="hero-poster-thumb" alt="{title}" /></div>'
    else:
        bg_style = f"background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(20, 26, 40, 0.95)), {visual['gradient']};"
        hero_poster_img = ''

    hero_raw = f'''<div class="hero-spotlight" style="{bg_style}">
<div class="hero-wrapper">
<div class="hero-content">
<div class="hero-badges">
<span class="badge badge-hero">{content_type}</span>
<span class="badge badge-rating">{rating}</span>
<span class="badge badge-rating">{release_year}</span>
<span class="badge badge-rating">{duration}</span>
</div>
<h1 class="hero-heading">{title}</h1>
<p class="hero-genres">{listed_in}</p>
<div class="hero-meta">
<span>Director: <strong>{director if director else 'Not specified'}</strong></span>
<span>•</span>
<span>Country: <strong>{country if country else 'Global'}</strong></span>
</div>
</div>
{hero_poster_img}
</div>
</div>'''

    return "\n".join([line.strip() for line in hero_raw.splitlines() if line.strip()])
