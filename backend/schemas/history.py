from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SearchHistoryCreate(BaseModel):
    query: str = Field(..., min_length=1, max_length=255)
    selected_title_id: Optional[str] = None


class SearchHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    selected_title_id: Optional[str] = None
    created_at: datetime


class SearchHistoryResponse(BaseModel):
    total: int
    items: List[SearchHistoryItem]


class SavedTitleCreate(BaseModel):
    show_id: str


class SavedTitleItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    show_id: str
    created_at: datetime


class SavedTitlesResponse(BaseModel):
    total: int
    items: List[SavedTitleItem]
