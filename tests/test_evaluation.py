"""
Unit tests for the Recommendation Evaluation module.
"""

import pytest
import pandas as pd
from src.recommendation_engine import NetflixRecommender
from src.evaluation import RecommendationEvaluator, parse_genres, compute_intra_list_diversity


@pytest.fixture
def synthetic_recommender():
    df = pd.DataFrame({
        'show_id': ['s1', 's2', 's3', 's4', 's5'],
        'type': ['Movie', 'Movie', 'Movie', 'TV Show', 'TV Show'],
        'title': ['SciFi Alpha', 'SciFi Beta', 'Comedy Gamma', 'Comedy Delta', 'Drama Epsilon'],
        'director': ['Dir A', 'Dir A', 'Dir B', 'Dir C', 'Dir D'],
        'country': ['USA', 'USA', 'UK', 'UK', 'Canada'],
        'release_year': [2020, 2021, 2019, 2018, 2022],
        'rating': ['PG-13', 'PG-13', 'TV-MA', 'TV-MA', 'TV-14'],
        'duration': ['100 min', '110 min', '90 min', '1 Season', '2 Seasons'],
        'listed_in': ['Sci-Fi', 'Sci-Fi', 'Comedies', 'Comedies', 'Dramas']
    })
    rec = NetflixRecommender(min_df=1)
    rec.fit(df)
    return rec


def test_parse_genres():
    genres = parse_genres("Action & Adventure, Comedies , Dramas")
    assert genres == {'action & adventure', 'comedies', 'dramas'}
    assert parse_genres("") == set()
    assert parse_genres(None) == set()


def test_compute_intra_list_diversity_insufficient_items(synthetic_recommender):
    # Single item or empty DataFrame must return 0.0
    single_df = pd.DataFrame({'title': ['SciFi Alpha']})
    assert compute_intra_list_diversity(single_df, synthetic_recommender) == 0.0
    assert compute_intra_list_diversity(pd.DataFrame(), synthetic_recommender) == 0.0
    assert compute_intra_list_diversity(None, synthetic_recommender) == 0.0


def test_compute_intra_list_diversity_range(synthetic_recommender):
    recs = synthetic_recommender.recommend('SciFi Alpha', top_k=3)
    ild = compute_intra_list_diversity(recs, synthetic_recommender)
    assert 0.0 <= ild <= 1.0


def test_evaluator_unfitted_recommender():
    empty_rec = NetflixRecommender()
    with pytest.raises(ValueError):
        RecommendationEvaluator(empty_rec)


def test_evaluate_query_metrics(synthetic_recommender):
    evaluator = RecommendationEvaluator(synthetic_recommender)
    metrics, rec_titles = evaluator.evaluate_query('SciFi Alpha', k=2)

    assert 'precision_at_k' in metrics
    assert 'recall_at_k' in metrics
    assert 'f1_at_k' in metrics
    assert 'ild' in metrics
    assert len(rec_titles) == 2
    assert 0.0 <= metrics['precision_at_k'] <= 1.0
    assert 0.0 <= metrics['recall_at_k'] <= 1.0
    assert 0.0 <= metrics['f1_at_k'] <= 1.0
    assert 0.0 <= metrics['ild'] <= 1.0


def test_evaluate_query_invalid_k(synthetic_recommender):
    evaluator = RecommendationEvaluator(synthetic_recommender)
    with pytest.raises(ValueError):
        evaluator.evaluate_query('SciFi Alpha', k=0)
    with pytest.raises(ValueError):
        evaluator.evaluate_query('SciFi Alpha', k=-3)


def test_evaluate_catalog_sample_and_coverage(synthetic_recommender):
    evaluator = RecommendationEvaluator(synthetic_recommender)
    results = evaluator.evaluate_catalog(sample_size=3, k=2, random_state=42)

    assert results['sample_size'] == 3
    assert results['k'] == 2
    assert 0.0 <= results['mean_precision_at_k'] <= 1.0
    assert 0.0 <= results['catalog_coverage_pct'] <= 100.0
    assert 0.0 <= results['mean_intra_list_diversity'] <= 1.0


def test_evaluate_catalog_invalid_params(synthetic_recommender):
    evaluator = RecommendationEvaluator(synthetic_recommender)
    with pytest.raises(ValueError):
        evaluator.evaluate_catalog(sample_size=0, k=5)
    with pytest.raises(ValueError):
        evaluator.evaluate_catalog(sample_size=10, k=0)
