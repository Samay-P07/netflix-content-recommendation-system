"""
Unit tests for the Recommendation Engine module.
"""

import pytest
import pandas as pd
from src.recommendation_engine import NetflixRecommender


@pytest.fixture
def synthetic_catalog():
    """Provides a synthetic catalog for deterministic testing."""
    return pd.DataFrame({
        'show_id': ['s1', 's2', 's3', 's4', 's5'],
        'type': ['TV Show', 'TV Show', 'Movie', 'Movie', 'TV Show'],
        'title': [
            'Stranger Things',
            'Chilling Adventures of Sabrina',
            'The Dark Knight',
            'Batman Begins',
            'Friends'
        ],
        'director': ['Duffer Brothers', '', 'Christopher Nolan', 'Christopher Nolan', ''],
        'country': ['United States', 'United States', 'United States', 'United States', 'United States'],
        'release_year': [2016, 2018, 2008, 2005, 1994],
        'rating': ['TV-14', 'TV-14', 'PG-13', 'PG-13', 'TV-14'],
        'duration': ['4 Seasons', '4 Seasons', '152 min', '140 min', '10 Seasons'],
        'listed_in': [
            'TV Horror, TV Sci-Fi & Fantasy',
            'TV Horror, TV Sci-Fi & Fantasy',
            'Action & Adventure, Dramas',
            'Action & Adventure, Dramas',
            'Classic TV Shows, TV Comedies'
        ]
    })


@pytest.fixture
def recommender(synthetic_catalog):
    rec = NetflixRecommender(genre_weight=2, min_df=1)
    rec.fit(synthetic_catalog)
    return rec


def test_fit_on_empty_df():
    rec = NetflixRecommender()
    with pytest.raises(ValueError):
        rec.fit(pd.DataFrame())
    with pytest.raises(ValueError):
        rec.fit(None)


def test_find_title_index_exact_and_case_insensitive(recommender):
    idx, title = recommender.find_title_index('stranger things')
    assert title == 'Stranger Things'
    assert idx == 0


def test_find_title_index_substring(recommender):
    idx, title = recommender.find_title_index('dark knight')
    assert title == 'The Dark Knight'


def test_find_title_index_fuzzy(recommender):
    idx, title = recommender.find_title_index('Batman Begin')
    assert title == 'Batman Begins'


def test_find_title_index_invalid_inputs(recommender):
    with pytest.raises(ValueError):
        recommender.find_title_index("")
    with pytest.raises(ValueError):
        recommender.find_title_index(None)
    with pytest.raises(KeyError):
        recommender.find_title_index("Completely Nonexistent Title 99999")


def test_recommend_exact_match(recommender):
    recs = recommender.recommend('Stranger Things', top_k=2)
    assert not recs.empty
    assert len(recs) == 2
    # Sabrina shares exact genres & format with Stranger Things
    assert recs.iloc[0]['title'] == 'Chilling Adventures of Sabrina'
    assert recs.iloc[0]['similarity_score'] > 0.4


def test_recommend_excludes_self(recommender):
    recs = recommender.recommend('The Dark Knight', top_k=4)
    # Target title itself must NOT be in recommendations
    assert 'The Dark Knight' not in recs['title'].values


def test_recommend_top_k_bounds(recommender):
    recs = recommender.recommend('Stranger Things', top_k=1)
    assert len(recs) == 1
    # Asking for more than catalog length should safely return available
    recs_all = recommender.recommend('Stranger Things', top_k=50)
    assert len(recs_all) == 4  # Total catalog has 5, excluding self leaves 4


def test_recommend_invalid_top_k(recommender):
    with pytest.raises(ValueError):
        recommender.recommend('Stranger Things', top_k=0)
    with pytest.raises(ValueError):
        recommender.recommend('Stranger Things', top_k=-5)


def test_recommend_filter_by_type(recommender):
    recs_tv = recommender.recommend('The Dark Knight', top_k=3, filter_type='TV Show')
    assert all(recs_tv['type'] == 'TV Show')

    recs_movies = recommender.recommend('Stranger Things', top_k=3, filter_type='Movie')
    assert all(recs_movies['type'] == 'Movie')


def test_recommend_invalid_filter_type(recommender):
    with pytest.raises(ValueError) as exc:
        recommender.recommend('Stranger Things', filter_type='Podcast')
    assert "Invalid filter_type" in str(exc.value)


def test_recommend_unfitted_error():
    rec = NetflixRecommender()
    with pytest.raises(RuntimeError):
        rec.recommend('Stranger Things')


def test_get_title_details(recommender):
    details = recommender.get_title_details('The Dark Knight')
    assert details['title'] == 'The Dark Knight'
    assert details['director'] == 'Christopher Nolan'
    assert details['type'] == 'Movie'
