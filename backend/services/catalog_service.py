"""
Catalog and Recommendation Service Layer
Decouples API endpoints from raw data processing and ML algorithms.
"""

import os
import logging
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd
from collections import Counter

from backend.core.config import settings
from backend.services.poster_service import get_poster_url
from src.data_preprocessing import load_and_preprocess_data
from src.recommendation_engine import NetflixRecommender
from backend.schemas.titles import TitleSummary, TitleDetail, PaginatedTitlesResponse, TitleSearchResponse
from backend.schemas.recommendations import RecommendationItem, RecommendationsResponse
from backend.schemas.insights import InsightsResponse, ItemCount

logger = logging.getLogger(__name__)


class CatalogService:
    """Singleton service managing dataset ingestion, search filtering, and recommendations."""

    _instance: Optional["CatalogService"] = None

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path or settings.DATA_PATH
        self.df: Optional[pd.DataFrame] = None
        self.recommender: Optional[NetflixRecommender] = None
        self._initialize()

    @classmethod
    def get_instance(cls, data_path: Optional[str] = None) -> "CatalogService":
        if cls._instance is None:
            cls._instance = cls(data_path)
        return cls._instance

    def _initialize(self) -> None:
        """Loads dataset and fits the recommendation engine."""
        target_path = self.data_path
        if not os.path.exists(target_path):
            # Check relative fallbacks
            fallbacks = ["data/Dataset.csv", "../data/Dataset.csv", "Dataset.csv"]
            for fb in fallbacks:
                if os.path.exists(fb):
                    target_path = fb
                    break

        if not os.path.exists(target_path):
            raise FileNotFoundError(f"Catalog dataset could not be found at: {self.data_path}")

        logger.info("Initializing CatalogService from: %s", target_path)
        self.df = load_and_preprocess_data(target_path)
        self.recommender = NetflixRecommender(genre_weight=2)
        self.recommender.fit(self.df)
        logger.info("CatalogService initialized with %d titles.", len(self.df))

    def get_title(self, show_id_or_title: str) -> Optional[TitleDetail]:
        """Fetches full metadata details for a title by show_id or title text."""
        if self.recommender is None:
            return None
        try:
            details = self.recommender.get_title_details(show_id_or_title)
            poster = get_poster_url(details['title'], details['release_year'], details['listed_in'])
            return TitleDetail(
                show_id=details['show_id'],
                title=details['title'],
                type=details['type'],
                release_year=details['release_year'],
                rating=details['rating'],
                duration=details['duration'],
                listed_in=details['listed_in'],
                country=details['country'],
                director=details['director'],
                poster_url=poster
            )
        except (KeyError, ValueError):
            return None

    def search_titles(
        self,
        query: Optional[str] = None,
        content_type: Optional[str] = None,
        genre: Optional[str] = None,
        year: Optional[int] = None,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        sort_by: str = "title_asc",
        page: int = 1,
        page_size: int = 20
    ) -> PaginatedTitlesResponse:
        """
        Searches and filters the catalog with pagination and sorting.
        """
        if self.df is None:
            return PaginatedTitlesResponse(total=0, page=1, page_size=page_size, total_pages=0, items=[])

        filtered = self.df

        # Text query filter
        if query and query.strip():
            q_clean = query.strip().lower()
            filtered = filtered[
                filtered['title'].str.lower().str.contains(q_clean, na=False) |
                filtered['director'].str.lower().str.contains(q_clean, na=False) |
                filtered['listed_in'].str.lower().str.contains(q_clean, na=False)
            ]

        # Content type filter
        if content_type and content_type.lower() in ['movie', 'tv show']:
            filtered = filtered[filtered['type'].str.lower() == content_type.lower()]

        # Genre filter
        if genre and genre.strip():
            g_clean = genre.strip().lower()
            filtered = filtered[filtered['listed_in'].str.lower().str.contains(g_clean, na=False)]

        # Specific year filter
        if year is not None:
            filtered = filtered[filtered['release_year'] == year]

        # Year range filter
        if year_min is not None:
            filtered = filtered[filtered['release_year'] >= year_min]
        if year_max is not None:
            filtered = filtered[filtered['release_year'] <= year_max]

        # Sorting
        if sort_by == "title_asc":
            filtered = filtered.sort_values(by="title", ascending=True)
        elif sort_by == "title_desc":
            filtered = filtered.sort_values(by="title", ascending=False)
        elif sort_by == "year_desc":
            filtered = filtered.sort_values(by="release_year", ascending=False)
        elif sort_by == "year_asc":
            filtered = filtered.sort_values(by="release_year", ascending=True)

        total = len(filtered)
        total_pages = max(1, (total + page_size - 1) // page_size)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size

        page_records = filtered.iloc[start_idx:end_idx]

        items = [
            TitleSummary(
                show_id=row['show_id'],
                title=row['title'],
                type=row['type'],
                release_year=int(row['release_year']),
                rating=row.get('rating', ''),
                duration=row.get('duration', ''),
                listed_in=row.get('listed_in', ''),
                country=row.get('country', ''),
                poster_url=get_poster_url(row['title'], int(row['release_year']), row.get('listed_in', ''))
            )
            for _, row in page_records.iterrows()
        ]

        return PaginatedTitlesResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            items=items
        )

    def get_recommendations(
        self,
        show_id_or_title: str,
        top_k: int = 10,
        filter_type: Optional[str] = None
    ) -> Optional[RecommendationsResponse]:
        """Generates recommendations with explanation metadata."""
        if self.recommender is None:
            return None

        try:
            idx, matched_title = self.recommender.find_title_index(show_id_or_title)
            query_row = self.recommender.df.iloc[idx]
            query_id = query_row.get('show_id', f"s{idx+1}")

            recs_df = self.recommender.recommend(matched_title, top_k=top_k, filter_type=filter_type)

            rec_items = []
            for _, row in recs_df.iterrows():
                score = float(row['similarity_score'])
                poster = get_poster_url(row['title'], int(row['release_year']), row.get('listed_in', ''))
                rec_items.append(
                    RecommendationItem(
                        show_id=row['show_id'],
                        title=row['title'],
                        type=row['type'],
                        release_year=int(row['release_year']),
                        rating=row.get('rating', ''),
                        country=row.get('country', ''),
                        duration=row.get('duration', ''),
                        listed_in=row.get('listed_in', ''),
                        director=row.get('director', ''),
                        similarity_score=score,
                        similarity_percentage=int(round(score * 100)),
                        explanation=row['explanation'],
                        query_title=matched_title,
                        poster_url=poster
                    )
                )

            return RecommendationsResponse(
                query_id=query_id,
                query_title=matched_title,
                total_recommendations=len(rec_items),
                recommendations=rec_items
            )
        except (KeyError, ValueError) as err:
            logger.warning("Could not generate recommendations for '%s': %s", show_id_or_title, err)
            return None

    def get_insights(self) -> InsightsResponse:
        """Computes verifiable catalog insights from real dataset records."""
        if self.df is None:
            raise RuntimeError("Catalog not loaded.")

        total_titles = len(self.df)
        type_counts = self.df['type'].value_counts().to_dict()
        movies_count = int(type_counts.get('Movie', 0))
        tv_shows_count = int(type_counts.get('TV Show', 0))

        # Top Genres
        genre_counter = Counter()
        for genres_str in self.df['listed_in'].dropna():
            for g in genres_str.split(','):
                clean_g = g.strip()
                if clean_g:
                    genre_counter[clean_g] += 1
        top_genres = [ItemCount(name=k, count=v) for k, v in genre_counter.most_common(10)]

        # Top Countries
        country_counter = Counter()
        for c_str in self.df['country'].dropna():
            for c in c_str.split(','):
                clean_c = c.strip()
                if clean_c and clean_c.lower() not in {'', 'unknown', 'not given', 'nan'}:
                    country_counter[clean_c] += 1
        top_countries = [ItemCount(name=k, count=v) for k, v in country_counter.most_common(10)]

        # Release year distribution (last 20 available years)
        year_counts = self.df['release_year'].value_counts().sort_index(ascending=False).head(20).to_dict()
        year_dist = [ItemCount(name=str(k), count=int(v)) for k, v in sorted(year_counts.items())]

        summary = (
            f"Catalog comprises {total_titles:,} titles ({movies_count:,} Movies and {tv_shows_count:,} TV Shows) "
            f"spanning {len(genre_counter)} unique genres across {len(country_counter)} countries."
        )

        return InsightsResponse(
            total_titles=total_titles,
            movies_count=movies_count,
            tv_shows_count=tv_shows_count,
            type_distribution={"Movie": movies_count, "TV Show": tv_shows_count},
            top_genres=top_genres,
            top_countries=top_countries,
            release_year_distribution=year_dist,
            catalog_summary=summary
        )

    def get_available_genres(self) -> List[str]:
        """Returns sorted list of all unique genres in catalog."""
        if self.df is None:
            return []
        genres = set()
        for genres_str in self.df['listed_in'].dropna():
            for g in genres_str.split(','):
                clean_g = g.strip()
                if clean_g:
                    genres.add(clean_g)
        return sorted(list(genres))

    def get_available_years(self) -> Tuple[int, int]:
        """Returns (min_year, max_year) in catalog."""
        if self.df is None:
            return (1920, 2021)
        return int(self.df['release_year'].min()), int(self.df['release_year'].max())
