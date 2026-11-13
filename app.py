"""
Streamlit Web Application for Netflix Content Recommendation System
Provides an interactive, Netflix-themed dashboard for exploring content recommendations.
"""

import os
import html
import streamlit as st
import pandas as pd
from src.data_preprocessing import load_and_preprocess_data
from src.recommendation_engine import NetflixRecommender
from src.evaluation import RecommendationEvaluator

# Page Configuration
st.set_page_config(
    page_title="Netflix Content Recommender",
    page_icon="🍿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Netflix Dark Aesthetic
st.markdown("""
<style>
    .stApp {
        background-color: #141414;
        color: #FFFFFF;
    }
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        color: #E50914;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.02rem;
        color: #B3B3B3;
        margin-bottom: 1.4rem;
    }
    .query-card {
        background-color: #1f1f1f;
        border-left: 5px solid #E50914;
        padding: 1.2rem;
        border-radius: 6px;
        margin-bottom: 1.5rem;
    }
    .rec-card {
        background-color: #1e1e1e;
        border: 1px solid #333333;
        border-radius: 8px;
        padding: 1.1rem;
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .rec-card:hover {
        border-color: #E50914;
        transform: translateY(-2px);
    }
    .badge {
        display: inline-block;
        padding: 0.2rem 0.55rem;
        font-size: 0.75rem;
        font-weight: 600;
        border-radius: 4px;
        margin-right: 0.4rem;
    }
    .badge-movie { background-color: #0071eb; color: #fff; }
    .badge-tv { background-color: #b81d24; color: #fff; }
    .badge-rating { background-color: #333333; color: #e5e5e5; }
    .score-badge {
        font-weight: 700;
        color: #46d369;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading and indexing Netflix catalog...")
def get_recommender(data_path: str = "data/Dataset.csv") -> NetflixRecommender:
    """Loads and caches the fitted recommender instance."""
    resolved_path = None
    candidate_paths = [data_path, "Dataset.csv", os.path.join("..", "Dataset.csv")]
    for p in candidate_paths:
        if os.path.exists(p):
            resolved_path = p
            break

    if resolved_path is None:
        raise FileNotFoundError(
            f"Dataset not found at '{data_path}'. Please ensure 'Dataset.csv' is placed "
            "in the 'data/' directory as described in data/README.md."
        )

    df = load_and_preprocess_data(resolved_path)
    recommender = NetflixRecommender(genre_weight=2)
    recommender.fit(df)
    return recommender


def main():
    st.markdown('<div class="main-header">🍿 Netflix Content Recommendation System</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Content-Based Filtering via NLP Metadata Embeddings & Cosine Similarity</div>', unsafe_allow_html=True)

    try:
        recommender = get_recommender()
    except FileNotFoundError as fnf_err:
        st.error(f"⚠️ {fnf_err}")
        st.info("Instructions: Download the Netflix CSV from Kaggle and place it at `data/Dataset.csv`.")
        return
    except Exception as exc:
        st.error(f"Failed to initialize recommendation engine: {exc}")
        return

    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Recommendation Filters")

        # Content format filter
        format_filter = st.selectbox(
            "Filter Content Format",
            options=["All Formats", "Movie Only", "TV Show Only"],
            index=0
        )
        filter_type = None
        if format_filter == "Movie Only":
            filter_type = "Movie"
        elif format_filter == "TV Show Only":
            filter_type = "TV Show"

        # Top K Slider
        top_k = st.slider("Number of Recommendations (K)", min_value=3, max_value=20, value=5, step=1)

        st.markdown("---")
        st.markdown("### 📌 Project Context")
        st.markdown(
            "This application uses **TF-IDF Vector Space Embeddings** and **Cosine Similarity** "
            "to surface titles sharing thematic genres, creators, country of origin, and age ratings. "
            "No personal user data or interaction logs are required, solving the **Cold-Start Problem**."
        )

    # Main Selection Area
    all_titles = sorted(recommender.titles_list)
    default_idx = all_titles.index("Stranger Things") if "Stranger Things" in all_titles else 0

    st.markdown("#### 🔍 Search or Select a Title")
    selected_title = st.selectbox(
        "Start typing a movie or TV show name:",
        options=all_titles,
        index=default_idx,
        help="Type any Netflix title to find similar catalog recommendations."
    )

    # Display Selected Query Details safely using html.escape
    try:
        q_details = recommender.get_title_details(selected_title)

        safe_title = html.escape(str(q_details['title']))
        safe_type = html.escape(str(q_details['type']))
        safe_year = html.escape(str(q_details['release_year']))
        safe_rating = html.escape(str(q_details['rating']) or 'Not Rated')
        safe_duration = html.escape(str(q_details['duration']))
        safe_country = html.escape(str(q_details['country']) or 'Global / Multi-country')
        safe_genres = html.escape(str(q_details['listed_in']))
        safe_director = html.escape(str(q_details['director']) or 'Not Listed')

        type_badge = "badge-movie" if q_details['type'] == 'Movie' else "badge-tv"

        st.markdown(f"""
        <div class="query-card">
            <h3 style="margin-top:0; color:#FFFFFF;">🎬 Selected Title: {safe_title} ({safe_year})</h3>
            <p style="margin-bottom:0.5rem;">
                <span class="badge {type_badge}">{safe_type}</span>
                <span class="badge badge-rating">{safe_rating}</span>
                <span class="badge badge-rating">⏱️ {safe_duration}</span>
                <span class="badge badge-rating">📍 {safe_country}</span>
            </p>
            <p style="color:#DDD; margin-bottom:0.3rem;"><strong>Genres:</strong> {safe_genres}</p>
            <p style="color:#AAA; margin-bottom:0;"><strong>Director:</strong> {safe_director}</p>
        </div>
        """, unsafe_allow_html=True)

        # Generate Recommendations
        recs = recommender.recommend(selected_title, top_k=top_k, filter_type=filter_type)

        st.markdown(f"### 🎯 Top {len(recs)} Recommendations for *{safe_title}*")

        if recs.empty:
            st.warning("No similar titles found matching the specified filters.")
        else:
            cols = st.columns(2)
            for idx, row in recs.iterrows():
                col = cols[idx % 2]
                score_pct = int(round(row['similarity_score'] * 100))

                rec_title = html.escape(str(row['title']))
                rec_type = html.escape(str(row['type']))
                rec_year = html.escape(str(row['release_year']))
                rec_rating = html.escape(str(row['rating']) or 'Not Rated')
                rec_duration = html.escape(str(row['duration']))
                rec_genres = html.escape(str(row['listed_in']))
                rec_country = html.escape(str(row['country']) or 'Global')
                rec_director = html.escape(str(row['director']) or 'Not Listed')
                rec_badge = "badge-movie" if row['type'] == 'Movie' else "badge-tv"

                with col:
                    st.markdown(f"""
                    <div class="rec-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                            <h4 style="margin:0; color:#FFFFFF;">{idx+1}. {rec_title}</h4>
                            <span class="score-badge">★ {score_pct}% Match</span>
                        </div>
                        <p style="margin-bottom:0.5rem;">
                            <span class="badge {rec_badge}">{rec_type}</span>
                            <span class="badge badge-rating">{rec_year}</span>
                            <span class="badge badge-rating">{rec_rating}</span>
                            <span class="badge badge-rating">⏱️ {rec_duration}</span>
                        </p>
                        <p style="color:#BBB; font-size:0.85rem; margin-bottom:0.3rem;">
                            <strong>Genres:</strong> {rec_genres}
                        </p>
                        <p style="color:#888; font-size:0.8rem; margin-bottom:0;">
                            <strong>Country:</strong> {rec_country} | <strong>Director:</strong> {rec_director}
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

    except KeyError:
        st.error(f"Title '{selected_title}' was not found in the catalog.")

    # Educational & Technical Details Accordions
    st.markdown("---")

    with st.expander("🔬 Technical Methodology: TF-IDF & Cosine Similarity"):
        st.markdown("""
        #### 1. Feature Engineering
        - **Entity Binding**: Multi-word creators and countries (e.g. *Christopher Nolan* $\\rightarrow$ `christopher_nolan`, *United States* $\\rightarrow$ `united_states`) are bound with underscores to prevent fragmented token overlap.
        - **Thematic Weighting**: Genre strings are tokenized and duplicated $2\\times$ relative to secondary metadata to prioritize thematic genre coherence.
        - **Placeholder Purging**: Entries with `'Not Given'` or `'Unknown'` are mapped to empty strings to avoid false token matches.

        #### 2. Vectorization & Similarity
        - **Sublinear TF-IDF**: Term frequencies are scaled as $\\text{tf} = 1 + \\log(\\text{tf})$ to dampen high-frequency tokens.
        - **On-Demand Dot Products**: For $L_2$-normalized sparse TF-IDF vectors, cosine similarity simplifies to the vector dot product $\\mathbf{q} \\cdot \\mathbf{d}_i$. Top-$K$ items are computed dynamically on-the-fly without allocating a static dense matrix.
        """)

    with st.expander("📊 Offline Benchmark Evaluation (Genre Relevance Proxy)"):
        st.markdown("""
        > **⚠️ Notice on Proxy Evaluation**: In metadata-only catalogs without user clickstreams or watch-session logs, true user preference data does not exist. In accordance with Information Retrieval literature, recommendation quality is evaluated using a **Thematic Relevance Proxy**: an item is considered relevant to the query if it shares at least one core genre.

        #### Verified Benchmark Results ($N = 100$ queries, $K = 5$, random_state = 42)
        """)

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Precision@5", "99.20%", help="Fraction of top-5 recommendations sharing the query's core genres.")
        col2.metric("Recall@5", "0.47%", help="Fraction of all matching catalog genre items retrieved in the top 5.")
        col3.metric("F1@5", "0.0091", help="Harmonic mean of Precision@5 and Recall@5.")
        col4.metric("Catalog Coverage", "5.27%", help="Percentage of unique catalog titles surfaced across 100 sample queries.")
        col5.metric("Diversity (ILD)", "0.1318", help="1 - mean pairwise cosine similarity within top-5 recommendations.")

        st.markdown("""
        *Note*: Cosine similarity represents distance in feature space, **not recommendation accuracy**. Low Recall@5 is the expected mathematical consequence of retrieving only 5 items out of a catalog containing thousands of matching genre entries.
        """)

    with st.expander("⚠️ System Limitations & Future Scope"):
        st.markdown("""
        - **Cold-Start Only**: Content-based filtering is ideal for new platforms and unauthenticated users, but cannot track personal user taste evolution over time.
        - **Absence of User Feedback**: Implicit feedback (completion rate, skips) is unavailable in static metadata catalogs.
        - **Filter Bubbles**: Content similarity naturally clusters items with identical genre tags.
        - **Future Roadmap**: Hybridizing with collaborative filtering (Matrix Factorization / LightFM) and fine-tuning Transformer sentence embeddings (`all-MiniLM-L6-v2`) on plot descriptions.
        """)


if __name__ == '__main__':
    main()
