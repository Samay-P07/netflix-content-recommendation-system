"""
Reusable UI Components for CineMatch
Provides XSS-safe HTML card rendering for movies, TV shows, and recommendations.
"""

import html
from typing import Dict, Any, Optional


def render_movie_card(
    item: Dict[str, Any],
    is_recommendation: bool = False,
    is_saved: bool = False
) -> str:
    """Renders a cinematic card component as safe HTML."""
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

    score_html = ""
    if is_recommendation and "similarity_percentage" in item:
        pct = item["similarity_percentage"]
        score_val = item.get("similarity_score", 0.0)
        score_html = f'<span class="badge-score" title="Cosine similarity: {score_val:.4f}">★ {pct}% Match</span>'

    explanation_html = ""
    if is_recommendation and item.get("explanation"):
        explanation_text = html.escape(str(item.get("explanation")))
        explanation_html = f'''
        <div class="card-explanation">
            <strong>Why recommended:</strong> {explanation_text}
        </div>
        '''

    director_html = f'<span>• Dir: {director}</span>' if director and director.lower() not in {'', 'unknown', 'nan'} else ''
    country_html = f'<span>• {country}</span>' if country and country.lower() not in {'', 'unknown', 'nan'} else ''

    return f"""
    <div class="movie-card">
        <div class="card-header-row">
            <div>
                <span class="badge {type_badge_cls}">{content_type}</span>
                {rating_badge}
                {duration_badge}
                <div class="card-title" style="margin-top: 6px;">{title} ({release_year})</div>
            </div>
            <div>
                {score_html}
            </div>
        </div>
        <div class="card-meta">
            <span style="color: #e50914; font-weight: 600;">{listed_in}</span>
            {director_html}
            {country_html}
        </div>
        {explanation_html}
    </div>
    """
