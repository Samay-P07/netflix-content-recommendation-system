from typing import List, Optional
from pydantic import BaseModel, Field


class RecommendationItem(BaseModel):
    show_id: str
    title: str
    type: str
    release_year: int
    rating: Optional[str] = ""
    country: Optional[str] = ""
    duration: Optional[str] = ""
    listed_in: Optional[str] = ""
    director: Optional[str] = ""
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    similarity_percentage: int = Field(..., description="Similarity expressed as 0-100%")
    explanation: str = Field(..., description="Verifiable reason based on shared metadata attributes")
    query_title: str
    poster_url: Optional[str] = ""


class RecommendationsResponse(BaseModel):
    query_id: str
    query_title: str
    total_recommendations: int
    disclaimer: str = (
        "Similarity scores reflect geometric cosine proximity across catalog metadata "
        "(genres, director, country, rating) and do not represent prediction of user satisfaction."
    )
    recommendations: List[RecommendationItem]
