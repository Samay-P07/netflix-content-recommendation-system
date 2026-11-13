"""
Insights API Endpoints
"""

from fastapi import APIRouter
from backend.services.catalog_service import CatalogService
from backend.schemas.insights import InsightsResponse

router = APIRouter(prefix="/insights", tags=["Catalog Insights"])


@router.get("/overview", response_model=InsightsResponse)
def get_insights():
    """Returns aggregated descriptive statistics computed from the actual dataset."""
    catalog = CatalogService.get_instance()
    return catalog.get_insights()
