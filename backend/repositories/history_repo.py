"""
Database Repository for Search History and Saved Titles
"""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.db.models import SearchHistory, SavedTitle

logger = logging.getLogger(__name__)


class HistoryRepository:
    """Manages search history records in PostgreSQL."""

    def __init__(self, db: Optional[Session]):
        self.db = db

    def add_search(self, query: str, selected_title_id: Optional[str] = None) -> Optional[SearchHistory]:
        if not self.db:
            return None
        try:
            record = SearchHistory(query=query.strip(), selected_title_id=selected_title_id)
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            logger.error("Failed to add search history: %s", e)
            self.db.rollback()
            return None

    def get_recent_searches(self, limit: int = 20) -> List[SearchHistory]:
        if not self.db:
            return []
        try:
            return (
                self.db.query(SearchHistory)
                .order_by(desc(SearchHistory.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to fetch search history: %s", e)
            return []

    def clear_history(self) -> int:
        if not self.db:
            return 0
        try:
            count = self.db.query(SearchHistory).delete()
            self.db.commit()
            return count
        except Exception as e:
            logger.error("Failed to clear search history: %s", e)
            self.db.rollback()
            return 0


class SavedTitleRepository:
    """Manages saved/favourite titles in PostgreSQL."""

    def __init__(self, db: Optional[Session]):
        self.db = db

    def save_title(self, show_id: str) -> Optional[SavedTitle]:
        if not self.db:
            return None
        try:
            clean_id = show_id.strip()
            existing = self.db.query(SavedTitle).filter(SavedTitle.show_id == clean_id).first()
            if existing:
                return existing
            record = SavedTitle(show_id=clean_id)
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            logger.error("Failed to save title: %s", e)
            self.db.rollback()
            return None

    def get_saved_titles(self, limit: int = 50) -> List[SavedTitle]:
        if not self.db:
            return []
        try:
            return (
                self.db.query(SavedTitle)
                .order_by(desc(SavedTitle.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            logger.error("Failed to get saved titles: %s", e)
            return []

    def remove_saved_title(self, show_id: str) -> bool:
        if not self.db:
            return False
        try:
            clean_id = show_id.strip()
            record = self.db.query(SavedTitle).filter(SavedTitle.show_id == clean_id).first()
            if record:
                self.db.delete(record)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error("Failed to remove saved title: %s", e)
            self.db.rollback()
            return False

    def is_saved(self, show_id: str) -> bool:
        if not self.db:
            return False
        try:
            clean_id = show_id.strip()
            return self.db.query(SavedTitle).filter(SavedTitle.show_id == clean_id).first() is not None
        except Exception as e:
            logger.error("Failed to check if title is saved: %s", e)
            return False
