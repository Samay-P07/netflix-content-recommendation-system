"""
CineMatch — AI-Powered Movie & TV Recommendation Platform
Full-stack Streamlit Application.
"""

import os
import html
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from frontend.api_client import CineMatchClient
from frontend.components.movie_card import render_movie_card

# Page Configuration
st.set_page_config(
    page_title="CineMatch — AI Movie & TV Discovery",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom Cinematic CSS
css_path = os.path.join(os.path.dirname(__file__), "styles", "cinematic.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_client() -> CineMatchClient:
    return CineMatchClient()


client = get_client()

# Sidebar Brand & Navigation
with st.sidebar:
    st.markdown("""
    <div class="cinematch-brand">
        <div class="cinematch-logo">Cine<span>Match</span></div>
    </div>
    <div class="cinematch-tagline">Find your next favourite story.</div>
    """, unsafe_allow_html=True)

    nav = st.radio(
        "Navigation",
        [
            "🎬 Discover & Recommend",
            "🔍 Browse Catalogue",
            "📊 Catalogue Insights",
            "🕒 Search History & Favourites",
            "📖 How It Works & Methodology"
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    health = client.get_health()
    status_icon = "🟢" if health.get("catalog_loaded") else "🔴"
    db_status = "🟢 Connected" if health.get("database_connected") else "🟡 Fallback / Local"

    st.caption(f"**System Status:** {status_icon} Operational")
    st.caption(f"**Titles Indexed:** {health.get('total_titles', 0):,}")
    st.caption(f"**Database:** {db_status}")
    st.caption(f"**Version:** {health.get('version', '1.0.0')}")


# ==============================================================================
# PAGE 1: DISCOVER & RECOMMEND
# ==============================================================================
if nav == "🎬 Discover & Recommend":
    st.markdown("""
    <div class="hero-card">
        <div class="hero-title">Discover Movies & TV Shows by Metadata Similarity</div>
        <div class="hero-desc">
            Select or search for any title in the catalogue. CineMatch transforms metadata (genres, director, country, rating)
            into TF-IDF feature vectors to compute mathematically similar recommendations.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_search, col_filter, col_k = st.columns([3, 1, 1])

    with col_search:
        # Pre-seed popular titles for quick demo selection
        demo_titles = [
            "Inception", "Stranger Things", "The Dark Knight", "Breaking Bad",
            "Narcos", "Interstellar", "The Witcher", "The Queen's Gambit",
            "Peaky Blinders", "Black Mirror", "The Matrix", "Pulp Fiction"
        ]
        query_input = st.text_input(
            "Search or enter a title:",
            value=st.session_state.get("selected_title_query", "Inception"),
            placeholder="e.g. Inception, Stranger Things, Narcos..."
        )

    with col_filter:
        format_filter = st.selectbox("Content Format", ["All", "Movie", "TV Show"])

    with col_k:
        top_k = st.slider("Recommendations (K)", min_value=3, max_value=20, value=5)

    btn_recommend = st.button("✨ Get Recommendations", type="primary", use_container_width=True)

    if query_input:
        client.record_search(query_input)

    if btn_recommend or query_input:
        with st.spinner("Finding mathematically similar titles..."):
            recs_data = client.get_recommendations(
                title_id=query_input,
                limit=top_k,
                type=format_filter if format_filter != "All" else None
            )

        if recs_data and recs_data.get("recommendations"):
            matched_title = recs_data.get("query_title")
            query_details = client.get_title_details(recs_data.get("query_id", query_input))

            # Query Title Details Banner
            if query_details:
                st.markdown(f"### 🎯 Recommendations based on **'{matched_title}'**")
                st.markdown(render_movie_card(query_details), unsafe_allow_html=True)

            st.markdown(f"#### Top {len(recs_data['recommendations'])} Recommendations:")
            st.caption(f"ℹ️ {recs_data.get('disclaimer')}")

            saved_titles = set(client.get_saved_titles())

            for item in recs_data["recommendations"]:
                col_card, col_action = st.columns([5, 1])
                with col_card:
                    st.markdown(
                        render_movie_card(item, is_recommendation=True),
                        unsafe_allow_html=True
                    )
                with col_action:
                    st.write("")
                    st.write("")
                    show_id = item["show_id"]
                    is_saved = show_id in saved_titles
                    btn_label = "❤️ Saved" if is_saved else "🤍 Save"
                    if st.button(btn_label, key=f"fav_btn_{show_id}"):
                        if is_saved:
                            client.remove_saved_title(show_id)
                            st.toast(f"Removed '{item['title']}' from saved.")
                        else:
                            client.save_title(show_id)
                            st.toast(f"Saved '{item['title']}' to favourites!")
                        st.rerun()

                    if st.button("Explore ➔", key=f"exp_btn_{show_id}"):
                        st.session_state["selected_title_query"] = item["title"]
                        st.rerun()
        else:
            st.warning(
                f"No recommendations could be generated for '{query_input}'. "
                "Please check the spelling or browse the catalogue tab to find valid titles."
            )


# ==============================================================================
# PAGE 2: BROWSE CATALOGUE & SEARCH
# ==============================================================================
elif nav == "🔍 Browse Catalogue":
    st.markdown("## 🔍 Browse & Filter Catalogue")
    st.caption("Explore titles with multi-attribute filtering, sorting, and instant recommendation launch.")

    genres_list = ["All"] + client.get_genres()

    col_q, col_type, col_genre, col_sort = st.columns([2, 1, 1.5, 1.5])
    with col_q:
        browse_q = st.text_input("Filter by keyword / title / director:", placeholder="Type a keyword...")
    with col_type:
        browse_type = st.selectbox("Type", ["All", "Movie", "TV Show"], key="browse_type_sel")
    with col_genre:
        browse_genre = st.selectbox("Genre", genres_list, key="browse_genre_sel")
    with col_sort:
        browse_sort = st.selectbox(
            "Sort by",
            ["Title (A-Z)", "Title (Z-A)", "Release Year (Newest)", "Release Year (Oldest)"]
        )

    sort_mapping = {
        "Title (A-Z)": "title_asc",
        "Title (Z-A)": "title_desc",
        "Release Year (Newest)": "year_desc",
        "Release Year (Oldest)": "year_asc"
    }

    # Pagination state
    if "catalog_page" not in st.session_state:
        st.session_state["catalog_page"] = 1

    page_size = 15
    res = client.list_titles(
        q=browse_q,
        type=browse_type,
        genre=browse_genre,
        sort_by=sort_mapping.get(browse_sort, "title_asc"),
        page=st.session_state["catalog_page"],
        page_size=page_size
    )

    total_items = res.get("total", 0)
    total_pages = res.get("total_pages", 1)
    current_page = res.get("page", 1)

    st.markdown(f"**Found {total_items:,} titles** (Page {current_page} of {total_pages})")

    if res.get("items"):
        for item in res["items"]:
            col_c, col_act = st.columns([5, 1.2])
            with col_c:
                st.markdown(render_movie_card(item), unsafe_allow_html=True)
            with col_act:
                st.write("")
                st.write("")
                if st.button("Find Similar ➔", key=f"cat_rec_{item['show_id']}", use_container_width=True):
                    st.session_state["selected_title_query"] = item["title"]
                    # Switch to Discover
                    st.toast(f"Loading recommendations for {item['title']}...")

        # Pagination controls
        col_prev, col_num, col_next = st.columns([1, 2, 1])
        with col_prev:
            if current_page > 1:
                if st.button("⬅️ Previous Page"):
                    st.session_state["catalog_page"] = current_page - 1
                    st.rerun()
        with col_num:
            st.write(f"<center>Page {current_page} of {total_pages}</center>", unsafe_allow_html=True)
        with col_next:
            if current_page < total_pages:
                if st.button("Next Page ➡️"):
                    st.session_state["catalog_page"] = current_page + 1
                    st.rerun()
    else:
        st.info("No titles matched your filter criteria.")


# ==============================================================================
# PAGE 3: CATALOGUE INSIGHTS
# ==============================================================================
elif nav == "📊 Catalogue Insights":
    st.markdown("## 📊 Catalogue Insights & Analytics")
    st.caption("Descriptive exploratory statistics computed from actual dataset records.")

    insights = client.get_insights()

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{insights.get('total_titles', 0):,}</div>
            <div class="stat-label">Total Titles</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{insights.get('movies_count', 0):,}</div>
            <div class="stat-label">Movies Available</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{insights.get('tv_shows_count', 0):,}</div>
            <div class="stat-label">TV Shows Available</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    col_ch1, col_ch2 = st.columns(2)

    with col_ch1:
        st.markdown("#### 🎭 Top 10 Most Common Genres")
        top_genres = insights.get("top_genres", [])
        if top_genres:
            gdf = pd.DataFrame([{"Genre": g["name"], "Count": g["count"]} for g in top_genres])
            gdf = gdf.sort_values(by="Count", ascending=True)

            fig, ax = plt.subplots(figsize=(7, 4.5), facecolor='#0f1117')
            ax.set_facecolor('#181c25')
            bars = ax.barh(gdf["Genre"], gdf["Count"], color='#e50914', edgecolor='#2b3242')
            ax.tick_params(colors='#d0d7de', labelsize=9)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#2b3242')
            ax.spines['bottom'].set_color('#2b3242')
            ax.xaxis.label.set_color('#d0d7de')
            plt.tight_layout()
            st.pyplot(fig)

    with col_ch2:
        st.markdown("#### 🌍 Top 10 Producing Countries")
        top_countries = insights.get("top_countries", [])
        if top_countries:
            cdf = pd.DataFrame([{"Country": c["name"], "Count": c["count"]} for c in top_countries])
            cdf = cdf.sort_values(by="Count", ascending=True)

            fig2, ax2 = plt.subplots(figsize=(7, 4.5), facecolor='#0f1117')
            ax2.set_facecolor('#181c25')
            ax2.barh(cdf["Country"], cdf["Count"], color='#1971c2', edgecolor='#2b3242')
            ax2.tick_params(colors='#d0d7de', labelsize=9)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            ax2.spines['left'].set_color('#2b3242')
            ax2.spines['bottom'].set_color('#2b3242')
            plt.tight_layout()
            st.pyplot(fig2)

    st.markdown("#### 📅 Titles by Release Year (Recent 20 Years)")
    year_dist = insights.get("release_year_distribution", [])
    if year_dist:
        ydf = pd.DataFrame([{"Year": y["name"], "Titles": y["count"]} for y in year_dist])
        st.bar_chart(ydf.set_index("Year"))


# ==============================================================================
# PAGE 4: SEARCH HISTORY & FAVOURITES
# ==============================================================================
elif nav == "🕒 Search History & Favourites":
    st.markdown("## 🕒 Search History & Saved Favourites")

    tab_history, tab_saved = st.tabs(["Search History", "Saved Favourites"])

    with tab_history:
        col_th, col_clr = st.columns([4, 1])
        with col_th:
            st.caption("Recent user queries recorded in the database.")
        with col_clr:
            if st.button("🗑️ Clear History", type="secondary"):
                client.clear_history()
                st.toast("Search history cleared.")
                st.rerun()

        history_items = client.get_history(limit=25)
        if history_items:
            for h in history_items:
                st.markdown(f"- **'{html.escape(h['query'])}'** — *{h.get('created_at', '')[:19]}*")
        else:
            st.info("No search history recorded yet.")

    with tab_saved:
        st.caption("Your bookmarked titles stored in PostgreSQL.")
        saved_ids = client.get_saved_titles(limit=50)

        if saved_ids:
            for sid in saved_ids:
                details = client.get_title_details(sid)
                if details:
                    col_s_card, col_s_act = st.columns([5, 1])
                    with col_s_card:
                        st.markdown(render_movie_card(details), unsafe_allow_html=True)
                    with col_s_act:
                        st.write("")
                        st.write("")
                        if st.button("Remove ✕", key=f"del_saved_{sid}"):
                            client.remove_saved_title(sid)
                            st.toast(f"Removed '{details['title']}'")
                            st.rerun()
        else:
            st.info("No favourites saved yet. Click the '🤍 Save' button on any recommendation card to bookmark it!")


# ==============================================================================
# PAGE 5: HOW IT WORKS & METHODOLOGY
# ==============================================================================
elif nav == "📖 How It Works & Methodology":
    st.markdown("## 📖 How CineMatch Recommendations Work")

    st.markdown("""
    ### 1. The Core Recommendation Algorithm: Content-Based Filtering
    CineMatch is a **content-based discovery platform**. Rather than tracking user watch histories or building collaborative-filtering matrices (which require private user interaction data), CineMatch constructs rich numerical profiles representing each title's verifiable metadata:
    - **Genres (`listed_in`):** Doubly weighted ($2\\times$) to emphasize thematic category matching.
    - **Director & Country:** Tokenized with underscore bindings (e.g., `christopher_nolan`, `united_states`) to prevent false partial word matches.
    - **Content Format & Rating:** Normalised tokens (e.g., `movie`, `pg_13`).

    ### 2. TF-IDF (Term Frequency - Inverse Document Frequency)
    $$\\text{TF-IDF}(t, d, D) = \\text{TF}(t, d) \\times \\log\\left(\\frac{1 + |D|}{1 + |\\{d \\in D : t \\in d\\}|}\\right) + 1$$
    - Sublinear term-frequency scaling ($\\log(1 + \\text{TF})$) dampens the influence of overly repetitive keywords.
    - Features are $L_2$-normalised into sparse unit vectors.

    ### 3. Cosine Similarity & On-the-Fly Ranking
    $$\\text{Cosine Similarity}(\\mathbf{u}, \\mathbf{v}) = \\frac{\\mathbf{u} \\cdot \\mathbf{v}}{\\|\\mathbf{u}\\| \\|\\mathbf{v}\\|} = \\mathbf{u} \\cdot \\mathbf{v} \\quad (\\text{for } L_2 \\text{-normalised vectors})$$
    - Because the feature vectors are $L_2$-normalised, the cosine similarity between the query vector and catalogue candidates is computed as an instantaneous linear dot-product.
    - **Query Title Self-Exclusion:** The query title is strictly excluded from its own recommendations.
    - **Query Latency:** Operates in $\\approx 1.16$ ms on standard CPU hardware without precomputing dense $N \\times N$ distance matrices in memory.

    ### 4. Interpretation of Similarity Scores
    > ⚠️ **Important:** A 89% match score indicates high geometric alignment across catalogue attributes (e.g., shared genres, directors, and country). **It is NOT a probability of user enjoyment, and NOT an ML classification accuracy metric.**

    ### 5. Dataset Provenance & Data Limitations
    - Based on the curated **Netflix Movies & TV Shows** dataset by Shivam Bansal (Kaggle).
    - Contains 8,790 raw rows cleaned to 8,786 canonical records.
    - No streaming video playback is provided; titles reflect catalogue metadata.
    """)
