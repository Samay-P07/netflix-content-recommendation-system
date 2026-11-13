"""
Unit tests for feature engineering module.
"""

import pytest
import pandas as pd
from src.feature_engineering import (
    normalize_entity_names,
    normalize_genres,
    build_metadata_soup,
    TextVectorizer
)


def test_normalize_entity_names():
    result = normalize_entity_names("Christopher Nolan, Vince Gilligan")
    assert result == "christopher_nolan vince_gilligan"
    assert normalize_entity_names("") == ""
    assert normalize_entity_names(None) == ""


def test_normalize_entity_names_filters_placeholders():
    # 'Not Given', 'Unknown' should not produce tokens
    assert normalize_entity_names("Not Given") == ""
    assert normalize_entity_names("Unknown") == ""


def test_normalize_genres():
    result = normalize_genres("Action & Adventure, Sci-Fi & Fantasy")
    assert "action_adventure" in result
    assert "sci_fi_fantasy" in result
    assert normalize_genres("") == ""
    assert normalize_genres(None) == ""


def test_build_metadata_soup_weighting():
    df = pd.DataFrame({
        'listed_in': ['Comedies'],
        'type': ['Movie'],
        'director': ['Taika Waititi'],
        'country': ['New Zealand'],
        'rating': ['PG-13']
    })
    soup = build_metadata_soup(df, genre_weight=3)
    soup_text = soup.iloc[0]

    # 'comedies' should appear 3 times due to weight factor
    assert soup_text.count("comedies") == 3
    assert "taika_waititi" in soup_text
    assert "new_zealand" in soup_text
    assert "pg_13" in soup_text


def test_text_vectorizer_fit_and_transform():
    corpus = pd.Series(["action movie", "action comedy", "drama romantic"])
    vectorizer = TextVectorizer(min_df=1)
    matrix = vectorizer.fit_transform(corpus)

    assert matrix.shape[0] == 3
    assert matrix.shape[1] > 0
    assert vectorizer.is_fitted

    # Transform new text
    new_matrix = vectorizer.transform(pd.Series(["action drama"]))
    assert new_matrix.shape[0] == 1


def test_text_vectorizer_unfitted_transform():
    vectorizer = TextVectorizer()
    with pytest.raises(RuntimeError):
        vectorizer.transform(pd.Series(["sample text"]))
