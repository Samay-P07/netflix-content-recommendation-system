"""
Reusable UI Components for CineMatch
Provides rich streaming-card HTML rendering with poster artwork,
floating badges, and verifiable recommendation explanations.
"""

import html
from typing import Dict, Any, Optional
from frontend.components.poster_helper import get_poster_visual


def render_movie_card(
    item: Dict[str, Any],
    is_recommendation: bool = False,
    is_saved: bool = False
) -> str:
    """Renders a modern streaming-style movie card with poster imagery and badges."""
    title = html.escape(str(item.get("title", "")))
    content_type = html.escape(str(item.get("type", "Movie")))
    release_year = html.escape(str(item.get("release_year", "")))
    rating = html.escape(str(item.get("rating", "")))
    duration = html.escape(str(item.get("duration", "")))
    listed_in = html.escape(str(item.get("listed_in", "")))
    country = html.escape(str(item.get("country", "")))
    director = html.escape(str(item.get("director", "")))
    show_id = html.escape(str(item.get("show_id", "")))

    type_badge_cls = "badge-tv" if "tv" in content_type.lower() else "badge-movie"
    rating_badge = f'<span class="badge badge-rating">{rating}</span>' if rating else ''
    duration_badge = f'<span class="badge badge-rating">{duration}</span>' if duration else ''

    # Poster visual
    visual = get_poster_visual(title, listed_in)
    if visual["type"] == "image":
        poster_style = f"background: url('{visual['url']}') center/cover no-repeat;"
        poster_content = ""
    else:
        poster_style = f"background: {visual['gradient']};"
        initials = "".join([w[0] for w in title.split()[:2] if w]).upper()
        poster_content = f'''
        <div class="poster-fallback-inner">
            <div class="poster-icon">🎬</div>
            <div class="poster-initials">{initials}</div>
        </div>
        '''

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
        explanation_html = f'''
        <div class="card-explanation">
            <span class="explanation-icon">💡</span>
            <span><strong>Why recommended:</strong> {explanation_text}</span>
        </div>
        '''

    director_html = f'<span class="meta-director">• Dir: {director}</span>' if director and director.lower() not in {'', 'unknown', 'nan'} else ''
    country_html = f'<span class="meta-country">• {country}</span>' if country and country.lower() not in {'', 'unknown', 'nan'} else ''

    return f"""
    <div class="streaming-card">
        <div class="poster-container" style="{poster_style}">
            <div class="poster-overlay">
                <div class="poster-top-bar">
                    <span class="badge {type_badge_cls}">{content_type}</span>
                    {rating_badge}
                </div>
                {score_html}
            </div>
            {poster_content}
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
    </div>
    """


def render_hero_spotlight(item: Dict[str, Any]) -> str:
    """Renders the top featured hero banner shown in modern streaming apps."""
    title = html.escape(str(item.get("title", "")))
    content_type = html.escape(str(item.get("type", "Movie")))
    release_year = html.escape(str(item.get("release_year", "")))
    rating = html.escape(str(item.get("rating", "")))
    duration = html.escape(str(item.get("duration", "")))
    listed_in = html.escape(str(item.get("listed_in", "")))
    country = html.escape(str(item.get("country", "")))
    director = html.escape(str(item.get("director", "")))

    visual = get_poster_visual(title, listed_in)
    bg_style = f"background: linear-gradient(90deg, rgba(12, 16, 26, 0.96) 35%, rgba(12, 16, 26, 0.75) 70%, rgba(12, 16, 26, 0.4) 100%), url('{visual['url']}') center/cover;" if visual["type"] == "image" else f"background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(20, 26, 40, 0.95)), {visual['gradient']};"

    return f"""
    <div class="hero-spotlight" style="{bg_style}">
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
    </div>
    """
