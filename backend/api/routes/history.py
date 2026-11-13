"""
Search History and Saved Titles API Endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.services.history_service import HistoryService
from backend.schemas.history import (
    SearchHistoryCreate, SearchHistoryItem, SearchHistoryResponse,
    SavedTitleCreate, SavedTitleItem, SavedTitlesResponse
)

router = APIRouter(tags=["Search History & Saved Titles"])


@router.get("/history", response_model=SearchHistoryResponse)
def get_search_history(
    limit: int = Query(20, ge=1, le=100),
    db: Optional[Session] = Depends(get_db)
):
    """Retrieves recent search queries."""
    service = HistoryService(db)
    return service.get_search_history(limit=limit)


@router.post("/history", response_model=Optional[SearchHistoryItem], status_code=status.HTTP_201_CREATED)
def record_search(
    item: SearchHistoryCreate,
    db: Optional[Session] = Depends(get_db)
):
    """Logs a search query to search history."""
    service = HistoryService(db)
    rec = service.record_search(item.query, item.selected_title_id)
    return rec


@router.delete("/history", status_code=status.HTTP_200_OK)
def clear_search_history(db: Optional[Session] = Depends(get_db)):
    """Clears all logged search history."""
    service = HistoryService(db)
    cleared = service.clear_search_history()
    return {"message": "Search history cleared successfully", "deleted_count": cleared}


@router.get("/saved", response_model=SavedTitlesResponse)
def get_saved_titles(
    limit: int = Query(50, ge=1, le=100),
    db: Optional[Session] = Depends(get_db)
):
    """Retrieves saved/favourite title IDs."""
    service = HistoryService(db)
    return service.get_saved_titles(limit=limit)


@router.post("/saved", response_model=Optional[SavedTitleItem], status_code=status.HTTP_201_CREATED)
def save_title(
    item: SavedTitleCreate,
    db: Optional[Session] = Depends(get_db)
):
    """Saves a title to favourites."""
    service = HistoryService(db)
    rec = service.save_title(item.show_id)
    return rec


@router.delete("/saved/{show_id}", status_code=status.HTTP_200_OK)
def remove_saved_title(
    show_id: str,
    db: Optional[Session] = Depends(get_db)
):
    """Removes a title from saved favourites."""
    service = HistoryService(db)
    removed = service.remove_saved_title(show_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Title '{show_id}' was not in saved list.")
    return {"message": f"Title '{show_id}' removed from saved list."}
