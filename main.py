"""
Command-Line Interface for Netflix Content Recommendation System
Allows querying recommendations and running quantitative RecSys offline evaluations.
"""

import os
import sys
import argparse
import logging
import pandas as pd

from src.data_preprocessing import load_and_preprocess_data
from src.recommendation_engine import NetflixRecommender
from src.evaluation import RecommendationEvaluator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('main')


def setup_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Netflix Content-Based Recommendation System CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        '--title', '-t',
        type=str,
        default=None,
        help="Netflix title to query for similar recommendations."
    )
    parser.add_argument(
        '--top_k', '-k',
        type=int,
        default=5,
        help="Number of recommendations to return (must be > 0)."
    )
    parser.add_argument(
        '--type',
        type=str,
        choices=['Movie', 'TV Show'],
        default=None,
        help="Filter recommendations by format ('Movie' or 'TV Show')."
    )
    parser.add_argument(
        '--data_path', '-d',
        type=str,
        default=os.path.join('data', 'Dataset.csv'),
        help="Path to Netflix dataset CSV."
    )
    parser.add_argument(
        '--evaluate', '-e',
        action='store_true',
        help="Run quantitative offline proxy evaluation across catalog samples."
    )
    parser.add_argument(
        '--sample_size', '-s',
        type=int,
        default=100,
        help="Sample size of queries for evaluation (must be > 0)."
    )
    return parser


def main():
    parser = setup_cli_parser()
    args = parser.parse_args()

    if args.top_k <= 0:
        logger.error("--top_k must be a positive integer, got: %d", args.top_k)
        sys.exit(1)

    if args.sample_size <= 0:
        logger.error("--sample_size must be a positive integer, got: %d", args.sample_size)
        sys.exit(1)

    # Locate dataset
    data_path = args.data_path
    if not os.path.exists(data_path):
        alt_paths = ['Dataset.csv', os.path.join('..', 'Dataset.csv')]
        for alt in alt_paths:
            if os.path.exists(alt):
                data_path = alt
                break

    try:
        df = load_and_preprocess_data(data_path)
    except Exception as exc:
        logger.error("Failed to load dataset from '%s': %s", data_path, exc)
        sys.exit(1)

    recommender = NetflixRecommender(genre_weight=2)
    recommender.fit(df)

    if args.evaluate:
        print("\n" + "=" * 70)
        print(" OFFLINE RECSYS PROXY EVALUATION REPORT (GENRE RELEVANCE)")
        print("=" * 70)
        evaluator = RecommendationEvaluator(recommender)
        results = evaluator.evaluate_catalog(sample_size=args.sample_size, k=args.top_k)
        print(f"Sampled Query Size        : {results['sample_size']} titles")
        print(f"Cutoff Rank (K)           : {results['k']}")
        print(f"Mean Precision@{results['k']}       : {results['mean_precision_at_k']:.4f}  (fraction of recs sharing query genre)")
        print(f"Mean Recall@{results['k']}          : {results['mean_recall_at_k']:.4f}  (fraction of catalog-wide genre matches retrieved)")
        print(f"Mean F1@{results['k']}              : {results['mean_f1_at_k']:.4f}")
        print(f"Catalog Coverage          : {results['catalog_coverage_pct']:.2f}% (unique titles surfaced)")
        print(f"Intra-List Diversity (ILD): {results['mean_intra_list_diversity']:.4f} (1 - mean pairwise cosine similarity)")
        print("=" * 70)
        print("Note: In the absence of user watch logs, genre overlap serves as an offline proxy.")
        print("Cosine similarity measures feature vector closeness, not user satisfaction.\n")
        return

    # If title is provided, run recommendations
    query_title = args.title or "Stranger Things"
    print("\n" + "=" * 70)
    print(f" NETFLIX RECOMMENDATIONS FOR: '{query_title}'")
    print("=" * 70)

    try:
        details = recommender.get_title_details(query_title)
        print(f"Query Item : {details['title']} ({details['release_year']}) | {details['type']} | {details['rating']}")
        print(f"Genres     : {details['listed_in']}")
        print(f"Director   : {details['director'] or 'Not Listed'} | Country: {details['country'] or 'Global'}")
        print("-" * 70)

        recs = recommender.recommend(query_title, top_k=args.top_k, filter_type=args.type)
        if recs.empty:
            print("[-] No matching titles found with the specified filter.")
            return

        for idx, row in recs.iterrows():
            sim_pct = int(round(row['similarity_score'] * 100))
            print(f"{idx+1:2d}. {row['title']} ({row['release_year']})")
            print(f"    Format : {row['type']:<7} | Rating: {row['rating']:<7} | Match Score: {sim_pct}% ({row['similarity_score']})")
            print(f"    Genres : {row['listed_in']}")
            print()

        print("=" * 70)
    except (KeyError, ValueError) as exc:
        logger.error(str(exc))
        sys.exit(1)


if __name__ == '__main__':
    main()
