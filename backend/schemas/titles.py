from typing import Optional, List
from pydantic import BaseModel, Field


class TitleSummary(BaseModel):
    show_id: str
    title: str
    type: str
    release_year: int
    rating: Optional[str] = ""
    duration: Optional[str] = ""
    listed_in: Optional[str] = ""
    country: Optional[str] = ""
    poster_url: Optional[str] = ""


class TitleDetail(TitleSummary):
    director: Optional[str] = ""
    date_added: Optional[str] = ""


class PaginatedTitlesResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[TitleSummary]


class TitleSearchResponse(BaseModel):
    total: int
    items: List[TitleSummary]
