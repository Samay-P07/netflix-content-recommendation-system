"""
Health Check Endpoint
"""

from fastapi import APIRouter, status
from pydantic import BaseModel

from backend.core.config import settings
from backend.services.catalog_service import CatalogService
from backend.db.session import is_db_available

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    status: str
    version: str
    catalog_loaded: bool
    total_titles: int
    database_connected: bool


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def get_health():
    """Health check endpoint verifying catalog ingestion and database connectivity."""
    catalog = CatalogService.get_instance()
    loaded = catalog.df is not None and not catalog.df.empty
    total = len(catalog.df) if loaded else 0
    db_ok = is_db_available()

    return HealthResponse(
        status="healthy" if loaded else "degraded",
        version=settings.VERSION,
        catalog_loaded=loaded,
        total_titles=total,
        database_connected=db_ok
    )
