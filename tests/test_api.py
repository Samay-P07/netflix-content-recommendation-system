"""
API End-to-End and Integration Tests for CineMatch FastAPI Backend
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert data["catalog_loaded"] is True
    assert data["total_titles"] > 8000


def test_api_list_titles():
    response = client.get("/titles?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == 10
    assert "show_id" in data["items"][0]
    assert "title" in data["items"][0]


def test_api_filter_titles():
    response = client.get("/titles?type=Movie&genre=Action&page_size=5")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["type"] == "Movie"
        assert "Action" in item["listed_in"]


def test_api_search_fast():
    response = client.get("/titles/search?q=Stranger%20Things&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    titles = [item["title"] for item in data["items"]]
    assert any("Stranger Things" in t for t in titles)


def test_api_title_details_and_not_found():
    # Valid show_id
    response = client.get("/titles/s1")
    assert response.status_code == 200
    data = response.json()
    assert data["show_id"] == "s1"
    assert "title" in data

    # Nonexistent
    bad_resp = client.get("/titles/nonexistent_title_xyz_12345")
    assert bad_resp.status_code == 404


def test_api_recommendations():
    response = client.get("/recommendations/s1?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert data["query_id"] == "s1"
    assert len(data["recommendations"]) == 5
    # Must not contain query item
    rec_ids = [r["show_id"] for r in data["recommendations"]]
    assert "s1" not in rec_ids
    # Must contain explanation
    assert len(data["recommendations"][0]["explanation"]) > 0


def test_api_recommendations_with_filter():
    response = client.get("/recommendations/s1?limit=3&type=Movie")
    assert response.status_code == 200
    data = response.json()
    for r in data["recommendations"]:
        assert r["type"] == "Movie"


def test_api_insights():
    response = client.get("/insights/overview")
    assert response.status_code == 200
    data = response.json()
    assert data["total_titles"] > 8000
    assert data["movies_count"] > 0
    assert data["tv_shows_count"] > 0
    assert len(data["top_genres"]) > 0
    assert len(data["top_countries"]) > 0


def test_api_history_lifecycle():
    # 1. Post search
    post_resp = client.post("/history", json={"query": "Interstellar", "selected_title_id": "s1"})
    assert post_resp.status_code == 201

    # 2. Get history
    get_resp = client.get("/history?limit=10")
    assert get_resp.status_code == 200
    items = get_resp.json()["items"]
    queries = [i["query"] for i in items]
    assert "Interstellar" in queries

    # 3. Clear history
    del_resp = client.delete("/history")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] >= 1


def test_api_saved_titles_lifecycle():
    # 1. Save title
    post_resp = client.post("/saved", json={"show_id": "s100"})
    assert post_resp.status_code == 201

    # 2. Get saved
    get_resp = client.get("/saved")
    assert get_resp.status_code == 200
    saved_ids = [s["show_id"] for s in get_resp.json()["items"]]
    assert "s100" in saved_ids

    # 3. Delete saved
    del_resp = client.delete("/saved/s100")
    assert del_resp.status_code == 200
