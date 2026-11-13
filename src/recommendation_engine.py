"""
Recommendation Engine Module
Implements on-demand cosine similarity recommendations with fuzzy title matching,
stable ID lookup, explanation generation, format filtering, and robust error handling.
"""

import logging
import difflib
from typing import Optional, List, Dict, Any, Tuple, Set
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import linear_kernel

from .feature_engineering import build_metadata_soup, TextVectorizer

logger = logging.getLogger(__name__)

REC_COLUMNS = [
    'show_id', 'title', 'type', 'release_year', 'rating', 'country',
    'duration', 'listed_in', 'director', 'similarity_score', 'explanation', 'query_title'
]


def generate_recommendation_explanation(query_row: pd.Series, candidate_row: pd.Series) -> str:
    """
    Constructs a verifiable explanation string describing why a candidate item was recommended.
    Based on shared genres, matching director, country, and format attributes from the actual catalog.
    """
    reasons = []

    # 1. Check shared genres
    q_genres = [g.strip() for g in str(query_row.get('listed_in', '')).split(',') if g.strip()]
    c_genres = [g.strip() for g in str(candidate_row.get('listed_in', '')).split(',') if g.strip()]
    c_genres_lower = {g.lower() for g in c_genres}
    shared_genres = [g for g in q_genres if g.lower() in c_genres_lower]

    if shared_genres:
        reasons.append(f"Shares genres: {', '.join(shared_genres[:3])}")

    # 2. Check matching director
    q_dir = str(query_row.get('director', '')).strip()
    c_dir = str(candidate_row.get('director', '')).strip()
    if q_dir and c_dir and q_dir.lower() not in {'', 'unknown', 'not given', 'nan'}:
        q_directors = {d.strip().lower() for d in q_dir.split(',') if d.strip()}
        c_directors = {d.strip().lower() for d in c_dir.split(',') if d.strip()}
        shared_directors = q_directors.intersection(c_directors)
        if shared_directors:
            # Format nicely using original casing if possible
            reasons.append(f"Directed by {q_dir}")

    # 3. Check matching country
    q_country = str(query_row.get('country', '')).strip()
    c_country = str(candidate_row.get('country', '')).strip()
    if q_country and c_country and q_country.lower() not in {'', 'unknown', 'not given', 'nan'}:
        q_countries = {c.strip().lower() for c in q_country.split(',') if c.strip()}
        c_countries = {c.strip().lower() for c in c_country.split(',') if c.strip()}
        shared_countries = q_countries.intersection(c_countries)
        if shared_countries and len(reasons) < 2:
            reasons.append(f"Origin: {q_country.split(',')[0].strip()}")

    # 4. Fallback if no specific entity overlap
    if not reasons:
        if str(query_row.get('type', '')) == str(candidate_row.get('type', '')):
            reasons.append(f"Related {candidate_row.get('type', 'title')} with thematic metadata alignment")
        else:
            reasons.append("Thematic metadata alignment in content attributes")

    return " • ".join(reasons)


class NetflixRecommender:
    """
    Content-Based Recommendation Engine for Netflix Catalog.

    Computes cosine similarity on-the-fly against the sparse TF-IDF feature space,
    avoiding the massive memory footprint of precomputing an N x N dense matrix.
    Supports resolution by stable show_id or title string.
    """

    def __init__(self, genre_weight: int = 2, min_df: Optional[int] = None):
        self.genre_weight = genre_weight
        self.min_df = min_df
        self.vectorizer: Optional[TextVectorizer] = None
        self.df: Optional[pd.DataFrame] = None
        self.tfidf_matrix: Optional[csr_matrix] = None
        self._title_lookup: Dict[str, int] = {}
        self._id_lookup: Dict[str, int] = {}
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
        self._id_lookup = {}
        for idx, row in self.df.iterrows():
            title = str(row['title'])
            norm_title = title.strip().lower()
            if norm_title not in self._title_lookup:
                self._title_lookup[norm_title] = idx

            show_id = str(row.get('show_id', '')).strip().lower()
            if show_id and show_id not in self._id_lookup:
                self._id_lookup[show_id] = idx

        self.titles_list = self.df['title'].tolist()
        logger.info("NetflixRecommender successfully fitted on %d titles.", len(self.df))
        return self

    def find_title_index(self, query: str) -> Tuple[int, str]:
        """
        Resolves query string (or show_id) to catalog index using exact ID,
        exact title, scored substring, or fuzzy matching.

        Returns:
            Tuple[int, str]: (catalog_index, matched_official_title)

        Raises:
            ValueError: If query is empty or not a string.
            KeyError: If title cannot be resolved.
        """
        if not query or not isinstance(query, str):
            raise ValueError("Query title must be a non-empty string.")

        clean_query = query.strip().lower()

        # 1. Exact match by stable show_id if present
        if clean_query in self._id_lookup:
            idx = self._id_lookup[clean_query]
            return idx, self.df.loc[idx, 'title']

        # 2. Exact match by title (case-insensitive & stripped)
        if clean_query in self._title_lookup:
            idx = self._title_lookup[clean_query]
            return idx, self.df.loc[idx, 'title']

        # 3. Substring match with similarity scoring
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
            logger.info("Substring matched '%s' to '%s'", query, best_title)
            return best_idx, best_title

        # 4. Fuzzy matching using Levenshtein ratio cutoff
        matches = difflib.get_close_matches(clean_query, self._title_lookup.keys(), n=1, cutoff=0.6)
        if matches:
            best_match = matches[0]
            idx = self._title_lookup[best_match]
            logger.info("Fuzzy matched '%s' to '%s'", query, self.df.loc[idx, 'title'])
            return idx, self.df.loc[idx, 'title']

        raise KeyError(
            f"Title '{query}' was not found in the catalog. "
            "Please check the spelling or select a title from the catalog."
        )

    def find_index_by_id(self, show_id: str) -> Tuple[int, str]:
        """
        Resolves a stable show_id (e.g. 's1') directly to catalog row index.

        Raises:
            KeyError: If show_id does not exist.
        """
        clean_id = str(show_id).strip().lower()
        if clean_id not in self._id_lookup:
            raise KeyError(f"Title ID '{show_id}' not found in the catalog.")
        idx = self._id_lookup[clean_id]
        return idx, self.df.loc[idx, 'title']

    def recommend(
        self,
        title: str,
        top_k: int = 10,
        filter_type: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Generates top-K similar recommendations for a given title or show_id.

        Args:
            title: Query movie or TV show name or show_id.
            top_k: Number of recommendations to return (default: 10).
            filter_type: Optional format filter ('Movie' or 'TV Show').

        Returns:
            pd.DataFrame: Recommended titles with similarity scores, explanation, and metadata.
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
        query_row = self.df.iloc[query_idx]
        query_vector = self.tfidf_matrix[query_idx]

        # Calculate cosine similarity of query vector against all catalog vectors
        # For L2-normalized TF-IDF, linear_kernel equals cosine similarity
        sim_scores = linear_kernel(query_vector, self.tfidf_matrix).flatten()

        # Identify candidate indices sorted descending by similarity score,
        # with secondary deterministic sort by catalog index
        candidate_indices = np.argsort(-sim_scores, kind='mergesort')

        recs = []
        for idx in candidate_indices:
            # Self-exclusion: Never recommend query item to itself
            if idx == query_idx:
                continue

            row = self.df.iloc[idx]
            # Secondary check: exclude any identical titles
            if str(row['title']).strip().lower() == matched_title.strip().lower():
                continue

            # Format filtering
            if filter_type:
                if str(row['type']).strip().lower() != filter_type.strip().lower():
                    continue

            score = float(sim_scores[idx])
            explanation = generate_recommendation_explanation(query_row, row)

            recs.append({
                'show_id': row.get('show_id', f"s{idx+1}"),
                'title': row['title'],
                'type': row['type'],
                'release_year': int(row['release_year']),
                'rating': row['rating'],
                'country': row['country'],
                'duration': row['duration'],
                'listed_in': row['listed_in'],
                'director': row['director'],
                'similarity_score': round(score, 4),
                'explanation': explanation,
                'query_title': matched_title
            })

            if len(recs) == top_k:
                break

        if not recs:
            return pd.DataFrame(columns=REC_COLUMNS)

        return pd.DataFrame(recs)

    def get_title_details(self, title_or_id: str) -> Dict[str, Any]:
        """Returns metadata dictionary for a specific title or show_id."""
        idx, matched_title = self.find_title_index(title_or_id)
        row = self.df.iloc[idx]
        return {
            'show_id': row.get('show_id', f"s{idx+1}"),
            'title': row['title'],
            'type': row['type'],
            'release_year': int(row['release_year']),
            'rating': row['rating'],
            'country': row['country'],
            'duration': row['duration'],
            'director': row['director'],
            'listed_in': row['listed_in']
        }
