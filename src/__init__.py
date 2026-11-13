"""
Netflix Content Recommendation System
Core Package Modules
"""

from .data_preprocessing import load_and_preprocess_data, clean_dataset
from .feature_engineering import build_metadata_soup, TextVectorizer
from .recommendation_engine import NetflixRecommender
from .evaluation import RecommendationEvaluator

__all__ = [
    'load_and_preprocess_data',
    'clean_dataset',
    'build_metadata_soup',
    'TextVectorizer',
    'NetflixRecommender',
    'RecommendationEvaluator'
]
