"""
Titles and Search API Endpoints
"""

from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException, status

from backend.services.catalog_service import CatalogService
from backend.schemas.titles import PaginatedTitlesResponse, TitleDetail, TitleSearchResponse

router = APIRouter(prefix="/titles", tags=["Titles & Search"])


@router.get("", response_model=PaginatedTitlesResponse)
def list_titles(
    q: Optional[str] = Query(None, description="Free text search query"),
    type: Optional[str] = Query(None, description="Format filter: 'Movie' or 'TV Show'"),
    genre: Optional[str] = Query(None, description="Genre filter"),
    year: Optional[int] = Query(None, description="Exact release year filter"),
    year_min: Optional[int] = Query(None, description="Minimum release year"),
    year_max: Optional[int] = Query(None, description="Maximum release year"),
    sort_by: str = Query("title_asc", pattern="^(title_asc|title_desc|year_desc|year_asc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """Retrieves paginated and filtered catalog titles."""
    catalog = CatalogService.get_instance()
    return catalog.search_titles(
        query=q,
        content_type=type,
        genre=genre,
        year=year,
        year_min=year_min,
        year_max=year_max,
        sort_by=sort_by,
        page=page,
        page_size=page_size
    )


@router.get("/search", response_model=TitleSearchResponse)
def search_titles_fast(
    q: str = Query(..., min_length=1, description="Search query string"),
    limit: int = Query(10, ge=1, le=50)
):
    """Fast search endpoint for autocomplete and instant query lookups."""
    catalog = CatalogService.get_instance()
    res = catalog.search_titles(query=q, page=1, page_size=limit)
    return TitleSearchResponse(total=res.total, items=res.items)


@router.get("/genres", response_model=List[str])
def list_genres():
    """Returns all available distinct genres in the catalog."""
    catalog = CatalogService.get_instance()
    return catalog.get_available_genres()


@router.get("/{title_id}", response_model=TitleDetail)
def get_title_details(title_id: str):
    """Retrieves detailed metadata for a specific title by show_id or title text."""
    catalog = CatalogService.get_instance()
    details = catalog.get_title(title_id)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Title '{title_id}' was not found in the catalog."
        )
    return details
