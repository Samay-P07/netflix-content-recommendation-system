"""
FastAPI Application Entry Point
Configures CORS, registers API routers, and initializes services.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.core.config import settings
from backend.api.routes import health, titles, recommendations, insights, history
from backend.services.catalog_service import CatalogService
from backend.db.session import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    logger.info("Starting CineMatch Backend API...")
    try:
        init_db()
        CatalogService.get_instance()
        logger.info("CineMatch Catalog and Database initialized successfully.")
    except Exception as e:
        logger.error("Startup initialization warning: %s", e)
    yield
    # Shutdown sequence
    logger.info("Shutting down CineMatch Backend API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "CineMatch — AI-Powered Movie & TV Recommendation Platform API. "
        "Provides content-based recommendations via TF-IDF vectorization and cosine similarity, "
        "comprehensive catalog filtering, and real-dataset analytics."
    ),
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(health.router)
app.include_router(titles.router)
app.include_router(recommendations.router)
app.include_router(insights.router)
app.include_router(history.router)


@app.get("/", include_in_schema=False)
def root_redirect():
    return JSONResponse({
        "message": "Welcome to CineMatch API",
        "docs": "/docs",
        "health": "/health",
        "version": settings.VERSION
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
