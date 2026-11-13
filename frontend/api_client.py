"""
CineMatch API Client
Communicates with the FastAPI backend with timeout protection, error resilience,
and transparent in-process fallback when the REST server is offline.
"""

import os
import logging
from typing import Optional, List, Dict, Any
import httpx

logger = logging.getLogger(__name__)

DEFAULT_API_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")


class CineMatchClient:
    """Client for CineMatch REST API with in-process local fallback."""

    def __init__(self, base_url: str = DEFAULT_API_URL, timeout: float = 4.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._in_process_service = None

    def _get_local_services(self):
        if self._in_process_service is None:
            from backend.services.catalog_service import CatalogService
            from backend.services.history_service import HistoryService
            from backend.db.session import SessionLocal
            
            db = SessionLocal() if SessionLocal else None
            self._in_process_service = (
                CatalogService.get_instance(),
                HistoryService(db)
            )
        return self._in_process_service

    def get_health(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/health")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        # In-process fallback
        catalog, _ = self._get_local_services()
        from backend.db.session import is_db_available
        return {
            "status": "healthy" if catalog.df is not None else "degraded",
            "version": "1.0.0 (Local In-Process)",
            "catalog_loaded": catalog.df is not None,
            "total_titles": len(catalog.df) if catalog.df is not None else 0,
            "database_connected": is_db_available()
        }

    def list_titles(
        self,
        q: Optional[str] = None,
        type: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        sort_by: str = "title_asc",
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        params = {
            "sort_by": sort_by,
            "page": page,
            "page_size": page_size
        }
        if q: params["q"] = q
        if type and type != "All": params["type"] = type
        if genre and genre != "All": params["genre"] = genre
        if year: params["year"] = year
        if year_min: params["year_min"] = year_min
        if year_max: params["year_max"] = year_max

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/titles", params=params)
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        # In-process fallback
        catalog, _ = self._get_local_services()
        res = catalog.search_titles(
            query=q,
            content_type=type if type != "All" else None,
            genre=genre if genre != "All" else None,
            year=year,
            year_min=year_min,
            year_max=year_max,
            sort_by=sort_by,
            page=page,
            page_size=page_size
        )
        return res.model_dump()

    def search_titles_fast(self, q: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/titles/search", params={"q": q, "limit": limit})
                if resp.status_code == 200:
                    return resp.json().get("items", [])
        except Exception:
            pass

        catalog, _ = self._get_local_services()
        res = catalog.search_titles(query=q, page=1, page_size=limit)
        return [item.model_dump() for item in res.items]

    def get_title_details(self, title_id: str) -> Optional[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/titles/{title_id}")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        catalog, _ = self._get_local_services()
        details = catalog.get_title(title_id)
        return details.model_dump() if details else None

    def get_recommendations(
        self,
        title_id: str,
        limit: int = 10,
        type: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        params = {"limit": limit}
        if type and type != "All":
            params["type"] = type

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/recommendations/{title_id}", params=params)
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        catalog, _ = self._get_local_services()
        recs = catalog.get_recommendations(
            show_id_or_title=title_id,
            top_k=limit,
            filter_type=type if type != "All" else None
        )
        return recs.model_dump() if recs else None

    def get_insights(self) -> Dict[str, Any]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/insights/overview")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        catalog, _ = self._get_local_services()
        return catalog.get_insights().model_dump()

    def get_genres(self) -> List[str]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/titles/genres")
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            pass

        catalog, _ = self._get_local_services()
        return catalog.get_available_genres()

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/history", params={"limit": limit})
                if resp.status_code == 200:
                    return resp.json().get("items", [])
        except Exception:
            pass

        _, history = self._get_local_services()
        res = history.get_search_history(limit)
        return [i.model_dump() for i in res.items]

    def record_search(self, query: str, selected_title_id: Optional[str] = None) -> None:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                client.post(
                    f"{self.base_url}/history",
                    json={"query": query, "selected_title_id": selected_title_id}
                )
                return
        except Exception:
            pass

        _, history = self._get_local_services()
        history.record_search(query, selected_title_id)

    def clear_history(self) -> None:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                client.delete(f"{self.base_url}/history")
                return
        except Exception:
            pass

        _, history = self._get_local_services()
        history.clear_search_history()

    def get_saved_titles(self, limit: int = 50) -> List[str]:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.get(f"{self.base_url}/saved", params={"limit": limit})
                if resp.status_code == 200:
                    return [item["show_id"] for item in resp.json().get("items", [])]
        except Exception:
            pass

        _, history = self._get_local_services()
        res = history.get_saved_titles(limit)
        return [i.show_id for i in res.items]

    def save_title(self, show_id: str) -> None:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                client.post(f"{self.base_url}/saved", json={"show_id": show_id})
                return
        except Exception:
            pass

        _, history = self._get_local_services()
        history.save_title(show_id)

    def remove_saved_title(self, show_id: str) -> None:
        try:
            with httpx.Client(timeout=self.timeout) as client:
                client.delete(f"{self.base_url}/saved/{show_id}")
                return
        except Exception:
            pass

        _, history = self._get_local_services()
        history.remove_saved_title(show_id)
