"""
Latency and Performance Benchmark for Netflix Recommendation System
Measures model fit time and query recommendation latency across multiple runs.
"""

import os
import sys
import time
import platform
import numpy as np
import pandas as pd

from src.data_preprocessing import load_and_preprocess_data
from src.recommendation_engine import NetflixRecommender


def run_benchmark(data_path: str = "data/Dataset.csv", n_queries: int = 100):
    print("=" * 68)
    print(" NETFLIX RECOMMENDATION SYSTEM - PERFORMANCE BENCHMARK")
    print("=" * 68)

    # 1. Environment & Hardware Detection
    print("\n--- Environment Specifications ---")
    print(f"OS Platform          : {platform.platform()}")
    print(f"Python Version       : {platform.python_version()}")
    print(f"Processor / CPU      : {platform.processor() or 'x86_64 Compatible'}")
    print(f"Machine Architecture : {platform.machine()}")

    # 2. Data Loading & Preprocessing Benchmark
    t0 = time.perf_counter()
    df = load_and_preprocess_data(data_path)
    t_load = (time.perf_counter() - t0) * 1000.0
    print(f"\n[+] Dataset Ingestion & Cleaning : {t_load:.2f} ms ({len(df)} titles)")

    # 3. Model Initialization (Fit) Benchmark
    t0 = time.perf_counter()
    recommender = NetflixRecommender(genre_weight=2)
    recommender.fit(df)
    t_fit = (time.perf_counter() - t0) * 1000.0
    print(f"[+] Recommender Fit Latency       : {t_fit:.2f} ms (TF-IDF Feature Space: {recommender.tfidf_matrix.shape})")

    # 4. Warm-up
    sample_titles = df['title'].sample(n=min(n_queries, len(df)), random_state=42).tolist()
    for title in sample_titles[:5]:
        _ = recommender.recommend(title, top_k=5)

    # 5. Recommendation Latency Measurement
    latencies = []
    for title in sample_titles:
        start_time = time.perf_counter()
        _ = recommender.recommend(title, top_k=5)
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        latencies.append(duration_ms)

    latencies = np.array(latencies)

    print("\n--- Query Recommendation Latency (Top-5 Nearest Neighbors) ---")
    print(f"Number of Queries Tested : {len(latencies)}")
    print(f"Mean Latency             : {np.mean(latencies):.2f} ms")
    print(f"Median Latency           : {np.median(latencies):.2f} ms")
    print(f"P95 Latency              : {np.percentile(latencies, 95):.2f} ms")
    print(f"Min Latency              : {np.min(latencies):.2f} ms")
    print(f"Max Latency              : {np.max(latencies):.2f} ms")
    print("=" * 68)
    print("Benchmark complete. Results are reproducible using fixed sample seed.\n")


if __name__ == '__main__':
    data_file = os.path.join('data', 'Dataset.csv') if os.path.exists(os.path.join('data', 'Dataset.csv')) else 'Dataset.csv'
    run_benchmark(data_path=data_file, n_queries=100)
