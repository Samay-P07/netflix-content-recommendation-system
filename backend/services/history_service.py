"""
History and Saved Titles Service Layer
"""

from typing import List, Optional
from sqlalchemy.orm import Session

from backend.repositories.history_repo import HistoryRepository, SavedTitleRepository
from backend.schemas.history import (
    SearchHistoryItem, SearchHistoryResponse,
    SavedTitleItem, SavedTitlesResponse
)


class HistoryService:
    def __init__(self, db: Optional[Session]):
        self.history_repo = HistoryRepository(db)
        self.saved_repo = SavedTitleRepository(db)

    def record_search(self, query: str, selected_title_id: Optional[str] = None) -> Optional[SearchHistoryItem]:
        rec = self.history_repo.add_search(query, selected_title_id)
        if rec:
            return SearchHistoryItem.model_validate(rec)
        return None

    def get_search_history(self, limit: int = 20) -> SearchHistoryResponse:
        records = self.history_repo.get_recent_searches(limit)
        items = [SearchHistoryItem.model_validate(r) for r in records]
        return SearchHistoryResponse(total=len(items), items=items)

    def clear_search_history(self) -> int:
        return self.history_repo.clear_history()

    def save_title(self, show_id: str) -> Optional[SavedTitleItem]:
        rec = self.saved_repo.save_title(show_id)
        if rec:
            return SavedTitleItem.model_validate(rec)
        return None

    def get_saved_titles(self, limit: int = 50) -> SavedTitlesResponse:
        records = self.saved_repo.get_saved_titles(limit)
        items = [SavedTitleItem.model_validate(r) for r in records]
        return SavedTitlesResponse(total=len(items), items=items)

    def remove_saved_title(self, show_id: str) -> bool:
        return self.saved_repo.remove_saved_title(show_id)

    def is_title_saved(self, show_id: str) -> bool:
        return self.saved_repo.is_saved(show_id)
