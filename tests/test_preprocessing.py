"""
Unit tests for data preprocessing module.
"""

import os
import pytest
import pandas as pd
from src.data_preprocessing import (
    load_dataset,
    clean_dataset,
    validate_dataset,
    REQUIRED_COLUMNS
)


@pytest.fixture
def sample_raw_df():
    """Provides a controlled synthetic DataFrame for testing."""
    return pd.DataFrame({
        'show_id': ['s1', 's2', 's3', 's4'],
        'type': ['Movie', 'TV Show', 'Movie', 'Movie'],
        'title': ['  Inception  ', 'Breaking Bad', 'Inception', 'Interstellar'],
        'director': ['Christopher Nolan', 'Vince Gilligan', 'Christopher Nolan', 'Not Given'],
        'country': ['United States', 'United States', 'United States', 'Unknown'],
        'release_year': [2010, 2008, 2010, 'invalid_year'],
        'rating': ['PG-13', 'TV-MA', 'PG-13', 'PG-13'],
        'duration': ['148 min', '5 Seasons', '148 min', '169 min'],
        'listed_in': ['Action & Adventure, Sci-Fi', 'Crime TV Shows, Dramas', 'Action & Adventure, Sci-Fi', 'Sci-Fi, Dramas']
    })


def test_load_dataset_nonexistent_file():
    with pytest.raises(FileNotFoundError):
        load_dataset("non_existent_file_path_12345.csv")


def test_load_dataset_empty_file(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("")
    with pytest.raises(ValueError) as exc:
        load_dataset(str(empty_csv))
    assert "empty" in str(exc.value).lower() or "failed" in str(exc.value).lower()


def test_validate_dataset_missing_columns():
    invalid_df = pd.DataFrame({'show_id': ['s1'], 'title': ['Test']})
    with pytest.raises(KeyError) as exc_info:
        validate_dataset(invalid_df)
    assert "missing required schema columns" in str(exc_info.value)


def test_clean_dataset_whitespace_and_duplicates(sample_raw_df):
    cleaned = clean_dataset(sample_raw_df)

    # Inception appeared twice with same type -> deduplicated to 3 records
    assert len(cleaned) == 3
    # Leading/trailing whitespace in '  Inception  ' must be stripped
    assert 'Inception' in cleaned['title'].values
    assert not any(t.startswith(' ') or t.endswith(' ') for t in cleaned['title'])


def test_clean_dataset_removes_empty_and_whitespace_titles():
    df_with_bad_titles = pd.DataFrame({
        'show_id': ['s1', 's2', 's3', 's4', 's5'],
        'type': ['Movie', 'Movie', 'Movie', 'Movie', 'Movie'],
        'title': ['Valid Title 1', '', '   ', 'nan', 'Valid Title 2'],
        'director': ['Dir A', 'Dir B', 'Dir C', 'Dir D', 'Dir E'],
        'country': ['USA', 'USA', 'USA', 'USA', 'USA'],
        'release_year': [2020, 2021, 2022, 2023, 2024],
        'rating': ['PG', 'PG', 'PG', 'PG', 'PG'],
        'duration': ['90 min', '90 min', '90 min', '90 min', '90 min'],
        'listed_in': ['Dramas', 'Dramas', 'Dramas', 'Dramas', 'Dramas']
    })
    cleaned = clean_dataset(df_with_bad_titles)
    # Only Valid Title 1 and Valid Title 2 should remain
    assert len(cleaned) == 2
    assert set(cleaned['title']) == {'Valid Title 1', 'Valid Title 2'}


def test_clean_dataset_placeholder_values(sample_raw_df):
    cleaned = clean_dataset(sample_raw_df)
    interstellar_row = cleaned[cleaned['title'] == 'Interstellar'].iloc[0]
    # 'Not Given' in director and 'Unknown' in country must be standardized to ''
    assert interstellar_row['director'] == ''
    assert interstellar_row['country'] == ''


def test_clean_dataset_invalid_release_year(sample_raw_df):
    cleaned = clean_dataset(sample_raw_df)
    interstellar_row = cleaned[cleaned['title'] == 'Interstellar'].iloc[0]
    # 'invalid_year' should be coerced to the median year (2010)
    assert int(interstellar_row['release_year']) == 2010
