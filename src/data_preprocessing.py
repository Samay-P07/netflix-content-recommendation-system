"""
Data Preprocessing Module
Handles catalog loading, schema validation, placeholder imputation, and deduplication.
"""

import os
import logging
from typing import List
import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: List[str] = [
    'show_id', 'type', 'title', 'director', 'country',
    'release_year', 'rating', 'duration', 'listed_in'
]

METADATA_PLACEHOLDER_VALUES = {'not given', 'unknown', 'nan', 'none', 'null', ''}
INVALID_TITLE_VALUES = {'nan', 'none', 'null', ''}


def load_dataset(filepath: str) -> pd.DataFrame:
    """
    Loads Netflix catalog CSV from disk with validation.

    Args:
        filepath: Absolute or relative path to CSV file.

    Returns:
        pd.DataFrame: Loaded raw dataset.

    Raises:
        FileNotFoundError: If filepath does not exist.
        ValueError: If file is empty or corrupted.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset file not found at: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except Exception as exc:
        raise ValueError(f"Failed to parse CSV file: {exc}") from exc

    if df.empty:
        raise ValueError("Loaded dataset is empty.")

    logger.info("Loaded raw catalog with %d rows and %d columns.", df.shape[0], df.shape[1])
    return df


def validate_dataset(df: pd.DataFrame) -> None:
    """
    Validates that necessary schema columns exist in the DataFrame.

    Raises:
        KeyError: If required columns are missing.
    """
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise KeyError(f"Dataset missing required schema columns: {missing}")


def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw Netflix metadata, removes exact title duplicates,
    purges empty or whitespace-only titles, and standardizes missing metadata entries.

    Args:
        df: Raw pandas DataFrame.

    Returns:
        pd.DataFrame: Cleaned and normalized DataFrame.
    """
    validate_dataset(df)
    df_clean = df.copy()

    # 1. Clean Title & Type
    df_clean['title'] = (
        df_clean['title']
        .fillna('')
        .astype(str)
        .str.replace('\xa0', ' ', regex=False)
        .str.strip()
    )
    df_clean['type'] = (
        df_clean['type']
        .fillna('')
        .astype(str)
        .str.replace('\xa0', ' ', regex=False)
        .str.strip()
    )

    # 2. Filter out empty, whitespace-only, or invalid titles
    initial_count = len(df_clean)
    valid_title_mask = df_clean['title'].apply(
        lambda t: len(t.strip()) > 0 and t.strip().lower() not in INVALID_TITLE_VALUES
    )
    df_clean = df_clean[valid_title_mask]
    empty_titles_dropped = initial_count - len(df_clean)
    if empty_titles_dropped > 0:
        logger.info("Removed %d records with empty or whitespace-only titles.", empty_titles_dropped)

    # 3. Clean optional metadata columns (standardize placeholders like 'Not Given', 'Unknown')
    metadata_cols = ['director', 'country', 'rating', 'duration', 'listed_in']
    for col in metadata_cols:
        df_clean[col] = (
            df_clean[col]
            .fillna('')
            .astype(str)
            .str.replace('\xa0', ' ', regex=False)
            .str.strip()
        )
        df_clean[col] = df_clean[col].apply(
            lambda x: '' if x.strip().lower() in METADATA_PLACEHOLDER_VALUES else x.strip()
        )

    # 4. Ensure release_year is numeric integer; impute invalid with median
    df_clean['release_year'] = pd.to_numeric(df_clean['release_year'], errors='coerce')
    median_year = df_clean['release_year'].median()
    if pd.isna(median_year):
        median_year = 2018
    df_clean['release_year'] = df_clean['release_year'].fillna(median_year).astype(int)

    # 5. Deduplicate titles across (title, type)
    pre_dedup_count = len(df_clean)
    df_clean = df_clean.drop_duplicates(subset=['title', 'type'], keep='first')
    duplicates_dropped = pre_dedup_count - len(df_clean)
    if duplicates_dropped > 0:
        logger.info("Removed %d duplicate title records.", duplicates_dropped)

    # Reset index cleanly
    df_clean = df_clean.reset_index(drop=True)
    logger.info("Cleaned dataset ready: %d records.", len(df_clean))
    return df_clean


def load_and_preprocess_data(filepath: str) -> pd.DataFrame:
    """Convenience pipeline to load and clean catalog in one step."""
    raw_df = load_dataset(filepath)
    return clean_dataset(raw_df)
