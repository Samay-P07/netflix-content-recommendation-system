"""
Recommendation Engine Module
Implements on-demand cosine similarity recommendations with fuzzy title matching,
format filtering, and robust error handling.
"""

import logging
import difflib
from typing import Optional, List, Dict, Any, Tuple
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import linear_kernel

from .feature_engineering import build_metadata_soup, TextVectorizer

logger = logging.getLogger(__name__)

REC_COLUMNS = [
    'title', 'type', 'release_year', 'rating', 'country',
    'duration', 'listed_in', 'director', 'similarity_score', 'query_title'
]


class NetflixRecommender:
    """
    Content-Based Recommendation Engine for Netflix Catalog.

    Computes cosine similarity on-the-fly against the sparse TF-IDF feature space,
    avoiding the massive memory footprint of precomputing an N x N dense matrix.
    """

    def __init__(self, genre_weight: int = 2, min_df: Optional[int] = None):
        self.genre_weight = genre_weight
        self.min_df = min_df
        self.vectorizer: Optional[TextVectorizer] = None
        self.df: Optional[pd.DataFrame] = None
        self.tfidf_matrix: Optional[csr_matrix] = None
        self._title_lookup: Dict[str, int] = {}
        self.titles_list: List[str] = []

    def fit(self, df: pd.DataFrame) -> "NetflixRecommender":
        """
        Fits the recommender by building the metadata soup and TF-IDF matrix.

        Args:
            df: Preprocessed Netflix catalog DataFrame.

        Returns:
            self: Fitted recommender instance.
        """
        if df is None or df.empty:
            raise ValueError("Cannot fit recommender on an empty or None DataFrame.")

        self.df = df.copy().reset_index(drop=True)
        soup = build_metadata_soup(self.df, genre_weight=self.genre_weight)

        # Handle min_df adaptively for small unit-test DataFrames
        actual_min_df = self.min_df if self.min_df is not None else (1 if len(self.df) < 10 else 2)
        self.vectorizer = TextVectorizer(min_df=actual_min_df)
        self.tfidf_matrix = self.vectorizer.fit_transform(soup)

        # Build normalized lookup index for O(1) title matching
        self._title_lookup = {}
        for idx, title in enumerate(self.df['title']):
            norm_title = title.strip().lower()
            if norm_title not in self._title_lookup:
                self._title_lookup[norm_title] = idx

        self.titles_list = self.df['title'].tolist()
        logger.info("NetflixRecommender successfully fitted on %d titles.", len(self.df))
        return self

    def find_title_index(self, query_title: str) -> Tuple[int, str]:
        """
        Resolves query string to catalog index using exact, scored substring, or fuzzy matching.

        Returns:
            Tuple[int, str]: (catalog_index, matched_official_title)

        Raises:
            ValueError: If query_title is empty or not a string.
            KeyError: If title cannot be resolved.
        """
        if not query_title or not isinstance(query_title, str):
            raise ValueError("Query title must be a non-empty string.")

        clean_query = query_title.strip().lower()

        # 1. Exact match (case-insensitive & stripped)
        if clean_query in self._title_lookup:
            idx = self._title_lookup[clean_query]
            return idx, self.df.loc[idx, 'title']

        # 2. Substring match with similarity scoring
        substring_candidates = []
        for norm_title, idx in self._title_lookup.items():
            if clean_query in norm_title:
                ratio = difflib.SequenceMatcher(None, clean_query, norm_title).ratio()
                substring_candidates.append((ratio, idx, self.df.loc[idx, 'title']))

        if substring_candidates:
            # Sort descending by similarity ratio
            substring_candidates.sort(key=lambda x: x[0], reverse=True)
            best_idx = substring_candidates[0][1]
            best_title = substring_candidates[0][2]
            logger.info("Substring matched '%s' to '%s'", query_title, best_title)
            return best_idx, best_title

        # 3. Fuzzy matching using Levenshtein ratio cutoff
        matches = difflib.get_close_matches(clean_query, self._title_lookup.keys(), n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            idx = self._title_lookup[best_match]
            logger.info("Fuzzy matched '%s' to '%s'", query_title, self.df.loc[idx, 'title'])
            return idx, self.df.loc[idx, 'title']

        raise KeyError(
            f"Title '{query_title}' was not found in the catalog. "
            "Please check the spelling or select a title from the catalog."
        )

    def recommend(
        self,
        title: str,
        top_k: int = 10,
        filter_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generates top-K similar recommendations for a given title.

        Args:
            title: Query movie or TV show name.
            top_k: Number of recommendations to return (default: 10).
            filter_type: Optional format filter ('Movie' or 'TV Show').

        Returns:
            pd.DataFrame: Recommended titles with similarity scores and metadata.
        """
        if self.df is None or self.tfidf_matrix is None:
            raise RuntimeError("Recommender has not been fitted. Call fit() first.")

        if not isinstance(top_k, int) or top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got: {top_k}")

        if filter_type is not None:
            clean_filter = filter_type.strip().lower()
            if clean_filter not in ['movie', 'tv show']:
                raise ValueError(
                    f"Invalid filter_type '{filter_type}'. Allowed values are 'Movie', 'TV Show', or None."
                )

        query_idx, matched_title = self.find_title_index(title)
        query_vector = self.tfidf_matrix[query_idx]

        # Calculate cosine similarity of query vector against all catalog vectors
        # For L2-normalized TF-IDF, linear_kernel equals cosine similarity
        sim_scores = linear_kernel(query_vector, self.tfidf_matrix).flatten()

        # Identify candidate indices sorted descending by similarity score
        candidate_indices = np.argsort(sim_scores)[::-1]

        recs = []
        for idx in candidate_indices:
            # Self-exclusion: Never recommend query item to itself
            if idx == query_idx:
                continue

            row = self.df.iloc[idx]
            # Secondary check: exclude any identical titles
            if row['title'].strip().lower() == matched_title.strip().lower():
                continue

            # Format filtering
            if filter_type:
                if row['type'].strip().lower() != filter_type.strip().lower():
                    continue

            score = float(sim_scores[idx])
            recs.append({
                'title': row['title'],
                'type': row['type'],
                'release_year': int(row['release_year']),
                'rating': row['rating'],
                'country': row['country'],
                'duration': row['duration'],
                'listed_in': row['listed_in'],
                'director': row['director'],
                'similarity_score': round(score, 4),
                'query_title': matched_title
            })

            if len(recs) == top_k:
                break

        if not recs:
            return pd.DataFrame(columns=REC_COLUMNS)

        return pd.DataFrame(recs)

    def get_title_details(self, title: str) -> Dict[str, Any]:
        """Returns metadata dictionary for a specific title."""
        idx, matched_title = self.find_title_index(title)
        row = self.df.iloc[idx]
        return {
            'title': row['title'],
            'type': row['type'],
            'release_year': int(row['release_year']),
            'rating': row['rating'],
            'country': row['country'],
            'duration': row['duration'],
            'director': row['director'],
            'listed_in': row['listed_in']
        }
