"""
SQLAlchemy Models for CineMatch
Defines persistent entities: SearchHistory and SavedTitle.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Index
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SearchHistory(Base):
    __tablename__ = "search_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    query = Column(String(255), nullable=False)
    selected_title_id = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    __table_args__ = (
        Index("idx_search_history_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<SearchHistory(id={self.id}, query='{self.query}', selected_title_id='{self.selected_title_id}')>"


class SavedTitle(Base):
    __tablename__ = "saved_titles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    show_id = Column(String(50), nullable=False, unique=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    def __repr__(self) -> str:
        return f"<SavedTitle(id={self.id}, show_id='{self.show_id}')>"
