"""
Recommendation Evaluation Module
Computes Information Retrieval and RecSys proxy metrics: Precision@K, Recall@K,
F1@K, Catalog Coverage, and Intra-List Diversity (ILD).
"""

import logging
from typing import Dict, Any, List, Set, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import linear_kernel

from .recommendation_engine import NetflixRecommender

logger = logging.getLogger(__name__)


def parse_genres(genre_str: str) -> Set[str]:
    """Extracts lowercase stripped genre set from comma-separated string."""
    if not genre_str or not isinstance(genre_str, str):
        return set()
    return {g.strip().lower() for g in genre_str.split(',') if g.strip()}


def compute_intra_list_diversity(
    recs_df: pd.DataFrame,
    recommender: NetflixRecommender
) -> float:
    """
    Computes Intra-List Diversity (ILD) for a list of recommended items.

    ILD = 1 - (average pairwise cosine similarity within top-K recommendations).
    A higher score indicates a broader variety of recommendations rather than redundant clones.
    """
    if recs_df is None or len(recs_df) < 2:
        return 0.0

    # Retrieve catalog indices for recommended titles
    indices = []
    for t in recs_df['title']:
        try:
            idx, _ = recommender.find_title_index(t)
            indices.append(idx)
        except KeyError:
            continue

    if len(indices) < 2:
        return 0.0

    sub_matrix = recommender.tfidf_matrix[indices]
    sim_matrix = linear_kernel(sub_matrix, sub_matrix)
    n = len(indices)

    # Extract upper triangle without diagonal
    pairwise_sims = sim_matrix[np.triu_indices(n, k=1)]
    pairwise_sims = np.clip(pairwise_sims, 0.0, 1.0)
    mean_sim = float(np.mean(pairwise_sims))

    return float(np.clip(1.0 - mean_sim, 0.0, 1.0))


class RecommendationEvaluator:
    """
    Offline Evaluator for Content-Based Recommenders.

    Methodology & Proxy Evaluation Notice:
    In metadata-only catalogs without user interaction logs (clicks, watch-time, ratings),
    ground truth user preferences do not exist. As is standard in IR literature, we evaluate
    thematic alignment via a Domain-Grounded Proxy (Genre Overlap):
    An item is deemed 'thematically relevant' if it shares at least one core genre with the query.

    Limitations:
    - This measures thematic coherence, NOT real user satisfaction or engagement.
    - Cosine similarity is a geometric feature distance, not recommendation accuracy.
    """

    def __init__(self, recommender: NetflixRecommender):
        if recommender is None or recommender.df is None or recommender.tfidf_matrix is None:
            raise ValueError("Recommender must be initialized and fitted before evaluation.")
        self.recommender = recommender
        # Pre-parse catalog genres once for fast lookups
        self.catalog_genres: List[Set[str]] = [
            parse_genres(g) for g in self.recommender.df['listed_in']
        ]

    def evaluate_query(self, title: str, k: int = 10) -> Tuple[Dict[str, float], List[str]]:
        """
        Evaluates Precision@K, Recall@K, F1@K, and ILD for a single query.

        Returns:
            Tuple[Dict[str, float], List[str]]: (metrics_dict, recommended_titles_list)
        """
        if not isinstance(k, int) or k <= 0:
            raise ValueError(f"k must be a positive integer, got: {k}")

        df = self.recommender.df
        q_idx, matched_title = self.recommender.find_title_index(title)
        query_genres = self.catalog_genres[q_idx]

        recs = self.recommender.recommend(matched_title, top_k=k)
        if recs.empty:
            return {
                'precision_at_k': 0.0,
                'recall_at_k': 0.0,
                'f1_at_k': 0.0,
                'ild': 0.0
            }, []

        # Ground truth proxy: count all catalog items sharing at least one genre with query
        total_relevant = sum(
            1 for idx, g_set in enumerate(self.catalog_genres)
            if idx != q_idx and g_set.intersection(query_genres)
        )

        # Count recommended items sharing at least one genre
        recommended_relevant = sum(
            1 for rec_genres in recs['listed_in'].apply(parse_genres)
            if rec_genres.intersection(query_genres)
        )

        actual_k = len(recs)
        precision = (recommended_relevant / actual_k) if actual_k > 0 else 0.0
        recall = (recommended_relevant / total_relevant) if total_relevant > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        ild = compute_intra_list_diversity(recs, self.recommender)

        metrics = {
            'precision_at_k': round(float(precision), 4),
            'recall_at_k': round(float(recall), 4),
            'f1_at_k': round(float(f1), 4),
            'ild': round(float(ild), 4)
        }
        return metrics, recs['title'].tolist()

    def evaluate_catalog(
        self,
        sample_size: int = 100,
        k: int = 10,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """
        Runs evaluation over a reproducible sample of catalog titles.

        Args:
            sample_size: Number of titles to sample (must be > 0).
            k: Cutoff rank for recommendations (must be > 0).
            random_state: Seed for deterministic sampling.

        Returns:
            Dict[str, Any]: Aggregated benchmark metrics.
        """
        if not isinstance(sample_size, int) or sample_size <= 0:
            raise ValueError(f"sample_size must be a positive integer, got: {sample_size}")
        if not isinstance(k, int) or k <= 0:
            raise ValueError(f"k must be a positive integer, got: {k}")

        df = self.recommender.df
        n_samples = min(sample_size, len(df))
        sample_df = df.sample(n=n_samples, random_state=random_state)

        precisions = []
        recalls = []
        f1s = []
        ilds = []
        unique_recommended_titles = set()

        logger.info("Evaluating recommender on %d sampled queries at K=%d...", n_samples, k)

        for title in sample_df['title']:
            metrics, rec_titles = self.evaluate_query(title, k=k)
            precisions.append(metrics['precision_at_k'])
            recalls.append(metrics['recall_at_k'])
            f1s.append(metrics['f1_at_k'])
            ilds.append(metrics['ild'])
            unique_recommended_titles.update(rec_titles)

        catalog_coverage = (len(unique_recommended_titles) / len(df)) * 100.0

        results = {
            'sample_size': n_samples,
            'k': k,
            'mean_precision_at_k': round(float(np.mean(precisions)), 4),
            'mean_recall_at_k': round(float(np.mean(recalls)), 4),
            'mean_f1_at_k': round(float(np.mean(f1s)), 4),
            'catalog_coverage_pct': round(float(catalog_coverage), 2),
            'mean_intra_list_diversity': round(float(np.mean(ilds)), 4)
        }

        logger.info(
            "Evaluation Complete (N=%d, K=%d) - Precision@%d: %.4f | Recall@%d: %.4f | ILD: %.4f | Coverage: %.2f%%",
            n_samples, k, k, results['mean_precision_at_k'], k, results['mean_recall_at_k'],
            results['mean_intra_list_diversity'], results['catalog_coverage_pct']
        )
        return results
