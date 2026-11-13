"""
Recommendations API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException, status

from backend.services.catalog_service import CatalogService
from backend.schemas.recommendations import RecommendationsResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.get("/{title_id}", response_model=RecommendationsResponse)
def get_recommendations(
    title_id: str,
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations (top-K)"),
    type: Optional[str] = Query(None, description="Format filter: 'Movie' or 'TV Show'")
):
    """
    Computes top-K recommendations for a given title or show_id.
    Excludes the query title itself and returns verifiable explanations.
    """
    catalog = CatalogService.get_instance()
    recs = catalog.get_recommendations(show_id_or_title=title_id, top_k=limit, filter_type=type)

    if not recs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to find title or generate recommendations for '{title_id}'."
        )

    return recs
