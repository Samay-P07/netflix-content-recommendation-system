"""
Feature Engineering Module
Constructs weighted metadata representation (feature soup) and TF-IDF matrices.
"""

import re
import logging
from typing import Optional
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)

STOP_ENTITIES = {'not_given', 'unknown', 'nan', 'none', 'null'}


def normalize_entity_names(name_string: str) -> str:
    """
    Transforms multi-word person or country entities into single underscore-bound tokens
    (e.g., 'Christopher Nolan' -> 'christopher_nolan', 'United States' -> 'united_states')
    to prevent unrelated partial word matches in the vectorizer.
    """
    if not name_string or not isinstance(name_string, str):
        return ""

    entities = [e.strip().lower() for e in name_string.split(',') if e.strip()]
    normalized = []
    for ent in entities:
        clean_ent = re.sub(r'[^a-z0-9]+', '_', ent).strip('_')
        if clean_ent and clean_ent not in STOP_ENTITIES:
            normalized.append(clean_ent)
    return ' '.join(normalized)


def normalize_genres(genre_string: str) -> str:
    """
    Standardizes comma-separated genre strings into underscore-bound tokens.
    (e.g., 'Action & Adventure' -> 'action_adventure').
    """
    if not genre_string or not isinstance(genre_string, str):
        return ""
    genres = [g.strip().lower() for g in genre_string.split(',') if g.strip()]
    tokens = []
    for g in genres:
        clean_g = re.sub(r'[^a-z0-9]+', '_', g).strip('_')
        if clean_g:
            tokens.append(clean_g)
    return ' '.join(tokens)


def build_metadata_soup(df: pd.DataFrame, genre_weight: int = 2) -> pd.Series:
    """
    Creates a rich text feature representation by combining content attributes.
    Genres receive higher term frequency to emphasize thematic similarity.

    Args:
        df: Cleaned catalog DataFrame containing:
            ['listed_in', 'type', 'director', 'country', 'rating'].
        genre_weight: Repetition multiplier for genres to boost their TF-IDF weight.

    Returns:
        pd.Series: Text strings representing each title's combined metadata.
    """
    logger.info("Constructing metadata feature soup with genre_weight=%d...", genre_weight)

    genres_tokenized = df['listed_in'].apply(normalize_genres)
    directors_tokenized = df['director'].apply(normalize_entity_names)
    countries_tokenized = df['country'].apply(normalize_entity_names)
    types_tokenized = df['type'].str.lower().str.replace(' ', '_')
    ratings_tokenized = df['rating'].str.lower().str.replace('-', '_')

    # Replicate genres to increase their term frequency in TF-IDF
    weight_factor = max(1, int(genre_weight))
    weighted_genres = (" " + genres_tokenized) * weight_factor

    soup = (
        weighted_genres.str.strip() + " " +
        types_tokenized + " " +
        directors_tokenized + " " +
        countries_tokenized + " " +
        ratings_tokenized
    ).str.strip()

    return soup


class TextVectorizer:
    """
    Encapsulates TF-IDF vectorization with sublinear term-frequency scaling.
    """

    def __init__(self, min_df: int = 2, max_features: Optional[int] = 10000, sublinear_tf: bool = True):
        self.min_df = min_df
        self.max_features = max_features
        self.sublinear_tf = sublinear_tf
        self.vectorizer = TfidfVectorizer(
            stop_words='english',
            token_pattern=r'(?u)\b[\w_]+\b',
            min_df=min_df,
            max_features=max_features,
            sublinear_tf=sublinear_tf
        )
        self.is_fitted = False

    def fit_transform(self, text_series: pd.Series) -> csr_matrix:
        matrix = self.vectorizer.fit_transform(text_series)
        self.is_fitted = True
        logger.info("Fitted TF-IDF matrix with shape %s", matrix.shape)
        return matrix

    def transform(self, text_series: pd.Series) -> csr_matrix:
        if not self.is_fitted:
            raise RuntimeError("Vectorizer must be fitted before transforming new text.")
        return self.vectorizer.transform(text_series)
