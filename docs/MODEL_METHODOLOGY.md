# CineMatch — Recommendation Methodology & ML Architecture

## 1. Algorithmic Paradigm: Content-Based Filtering

CineMatch is a **content-based recommendation system**. It does not require user accounts, ratings, or watch histories to generate recommendations. Instead, it measures thematic alignment between candidate titles based on catalogue metadata:
- **Genres (`listed_in`):** The primary thematic signal. Weight multiplier $2\times$ boosts term frequency in the feature soup.
- **Director (`director`):** Normalized to underscore-bound tokens (e.g. `christopher_nolan`) to prevent partial name collision.
- **Country (`country`):** Normalized to underscore-bound tokens (e.g. `united_states`, `united_kingdom`).
- **Format (`type`):** `movie` or `tv_show`.
- **Maturity Rating (`rating`):** Normalised (e.g. `tv_ma`, `pg_13`).

---

## 2. Feature Pipeline

### 2.1 Metadata Normalisation & Feature Soup
```python
soup = (
    weighted_genres + " " +
    type_tokens + " " +
    director_tokens + " " +
    country_tokens + " " +
    rating_tokens
)
```

### 2.2 TF-IDF Transformation
Using `scikit-learn`'s `TfidfVectorizer`:
- **Sublinear TF Scaling:** Replaces raw term frequency with $1 + \log(\text{TF})$ to prevent frequent terms from dominating the sparse space.
- **Token Pattern:** `r'(?u)\b[\w_]+\b'` preserving underscore-bound multi-word entities.
- **Stopwords:** English stopwords removed.
- **Output:** Sparse CSR matrix of shape `(8786, 1147)` taking less than 1 MB of memory.

---

## 3. Cosine Similarity & Query Latency

Cosine similarity between query vector $\mathbf{q}$ and catalogue matrix $\mathbf{X}$:
$$\text{Sim}(\mathbf{q}, \mathbf{x}_i) = \frac{\mathbf{q} \cdot \mathbf{x}_i}{\|\mathbf{q}\|_2 \|\mathbf{x}_i\|_2} = \mathbf{q} \cdot \mathbf{x}_i$$

Because feature vectors are $L_2$-normalised during TF-IDF vectorization, cosine similarity is computed directly via a fast linear kernel / dot product:
$$\text{sim\_scores} = \text{linear\_kernel}(\mathbf{q}, \mathbf{X})$$

**Performance Benchmarks (Windows 11 CPU, Python 3.14):**
- Ingestion and Cleaning: **51.8 ms**
- TF-IDF Model Fitting: **102.1 ms**
- Single Query Top-5 Latency: **1.16 ms** (Median: 1.08 ms, P95: 1.55 ms)

---

## 4. Offline Evaluation Methodology

Evaluated on 100 sampled titles with $K=5$, seed 42:

| Metric | Measured Value | Meaning |
|---|---|---|
| **Precision@5** | 99.20% | Proportion of top-5 recommendations sharing at least one core genre with query |
| **Recall@5** | 0.47% | Proportion of all relevant catalogue items retrieved within top-5 |
| **F1@5** | 0.0091 | Harmonic mean of Precision and Recall |
| **Catalog Coverage** | 5.27% | Share of unique catalogue items recommended across 100 queries |
| **Intra-List Diversity (ILD)** | 0.1318 | Average pairwise cosine distance within top-5 recommendations |

> ⚠️ **Methodological Boundary:** Evaluation metrics represent genre coherence proxy metrics and do not measure live user satisfaction. Cosine similarity is a geometric distance, not a classification confidence or probability of viewer enjoyment.
