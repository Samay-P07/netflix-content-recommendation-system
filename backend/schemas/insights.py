from typing import List, Dict, Any
from pydantic import BaseModel


class ItemCount(BaseModel):
    name: str
    count: int


class InsightsResponse(BaseModel):
    total_titles: int
    movies_count: int
    tv_shows_count: int
    type_distribution: Dict[str, int]
    top_genres: List[ItemCount]
    top_countries: List[ItemCount]
    release_year_distribution: List[ItemCount]
    catalog_summary: str
