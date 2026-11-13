"""
CineMatch — AI-Powered Movie & TV Recommendation Platform
Modern Cinematic Streaming Interface (Inspired by Movier & Cinemate).
"""

import os
import html
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

from frontend.api_client import CineMatchClient
from frontend.components.movie_card import render_movie_card, render_hero_spotlight

# Streamlit Page Setup
st.set_page_config(
    page_title="CineMatch — AI Movie & TV Discovery",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Custom Streaming Theme CSS
css_path = os.path.join(os.path.dirname(__file__), "styles", "cinematic.css")
if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_client() -> CineMatchClient:
    return CineMatchClient()


client = get_client()

# Initialize session state variables
if "selected_title_query" not in st.session_state:
    st.session_state["selected_title_query"] = "Inception"

if "catalog_page" not in st.session_state:
    st.session_state["catalog_page"] = 1


def main():
    # Sidebar Navigation & Platform Status
    with st.sidebar:
        st.markdown("""
        <div style="padding: 0.5rem 0 1.2rem 0;">
            <div style="font-size: 2rem; font-weight: 900; color: #ffffff; display: flex; align-items: center; gap: 8px;">
                🎬 Cine<span style="color: #e50914;">Match</span>
            </div>
            <div style="font-size: 0.88rem; color: #a0aec0; margin-top: 4px;">AI-Powered Discovery Platform</div>
        </div>
        """, unsafe_allow_html=True)

        nav = st.radio(
            "Navigation",
            [
                "🏠 Streaming Dashboard",
                "🎯 AI Recommendations",
                "🔍 Browse & Filter Catalogue",
                "📊 Catalogue Insights",
                "❤️ Watchlist & History",
                "📖 Algorithm & Methodology"
            ],
            label_visibility="collapsed"
        )

        st.markdown("---")
        health = client.get_health()
        loaded = health.get("catalog_loaded", False)
        status_dot = "🟢" if loaded else "🔴"
        db_label = "🟢 PostgreSQL" if health.get("database_connected") else "🟡 Local Storage"

        st.caption(f"**Catalogue:** {status_dot} {health.get('total_titles', 0):,} Titles Live")
        st.caption(f"**Database:** {db_label}")
        st.caption("**Engine:** TF-IDF + Cosine Similarity")
        st.caption("**Model Latency:** ~1.16 ms (CPU)")

    # ==========================================================================
    # VIEW 1: STREAMING DASHBOARD (Modern Homepage matching reference designs)
    # ==========================================================================
    if nav == "🏠 Streaming Dashboard":
        # Top Brand & Search Bar
        st.markdown("""
        <div class="cinematch-top-brand">
            <div class="brand-title">
                Cine<span>Match</span>
                <span class="brand-badge">PRO DISCOVERY</span>
            </div>
            <div style="color: #a0aec0; font-size: 0.9rem;">
                Explore 8,786 Movies & TV Shows with transparent AI metadata matching.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Quick title selector & search
        col_input, col_fmt, col_btn = st.columns([3.5, 1.2, 1.2])
        with col_input:
            search_val = st.text_input(
                "Search or choose a title:",
                value=st.session_state["selected_title_query"],
                placeholder="Search Inception, Stranger Things, Narcos, Breaking Bad...",
                label_visibility="collapsed"
            )
        with col_fmt:
            fmt_filter = st.selectbox("Format", ["All", "Movie", "TV Show"], label_visibility="collapsed")
        with col_btn:
            btn_search = st.button("🔍 Recommend", type="primary", use_container_width=True)

        if search_val:
            st.session_state["selected_title_query"] = search_val
            client.record_search(search_val)

        active_title = st.session_state["selected_title_query"]
        hero_details = client.get_title_details(active_title)

        # 1. Hero Spotlight Featured Banner
        if hero_details:
            st.markdown(render_hero_spotlight(hero_details), unsafe_allow_html=True)

        # 2. Recommended for You Section (Grid of 4 cards per row)
        st.markdown("""
        <div class="section-header">
            <h3 class="section-title">✨ Recommended for You (AI Metadata Match)</h3>
            <span style="color: #64748b; font-size: 0.85rem;">Ranked by Cosine Similarity & Genre Weighting</span>
        </div>
        """, unsafe_allow_html=True)

        recs_data = client.get_recommendations(
            title_id=active_title,
            limit=8,
            type=fmt_filter if fmt_filter != "All" else None
        )

        saved_titles = set(client.get_saved_titles())

        if recs_data and recs_data.get("recommendations"):
            recs_list = recs_data["recommendations"]
            # Render in a clean 4-column responsive grid
            for row_start in range(0, len(recs_list), 4):
                cols = st.columns(4)
                for i, col in enumerate(cols):
                    idx = row_start + i
                    if idx < len(recs_list):
                        rec_item = recs_list[idx]
                        show_id = rec_item["show_id"]
                        is_saved = show_id in saved_titles

                        with col:
                            st.markdown(
                                render_movie_card(rec_item, is_recommendation=True),
                                unsafe_allow_html=True
                            )
                            # Card Action buttons
                            bcol1, bcol2 = st.columns(2)
                            with bcol1:
                                if st.button("Explore ➔", key=f"dash_exp_{show_id}", use_container_width=True):
                                    st.session_state["selected_title_query"] = rec_item["title"]
                                    st.rerun()
                            with bcol2:
                                fav_label = "❤️ Saved" if is_saved else "🤍 Save"
                                if st.button(fav_label, key=f"dash_fav_{show_id}", use_container_width=True):
                                    if is_saved:
                                        client.remove_saved_title(show_id)
                                        st.toast(f"Removed '{rec_item['title']}'")
                                    else:
                                        client.save_title(show_id)
                                        st.toast(f"Saved '{rec_item['title']}' to Watchlist!")
                                    st.rerun()
        else:
            st.info("No matching recommendations found for this query. Try another title from the catalogue!")

        # 3. Trending & Popular Highlights from Dataset
        st.markdown("""
        <div class="section-header">
            <h3 class="section-title">🔥 Popular Catalogue Highlights</h3>
            <span style="color: #64748b; font-size: 0.85rem;">Curated titles from Netflix catalogue</span>
        </div>
        """, unsafe_allow_html=True)

        popular_picks = client.list_titles(page=1, page_size=4, sort_by="year_desc")
        if popular_picks.get("items"):
            cols_pop = st.columns(4)
            for i, p_item in enumerate(popular_picks["items"]):
                with cols_pop[i]:
                    st.markdown(render_movie_card(p_item), unsafe_allow_html=True)
                    if st.button("Find Similar ➔", key=f"pop_btn_{p_item['show_id']}", use_container_width=True):
                        st.session_state["selected_title_query"] = p_item["title"]
                        st.rerun()

    # ==========================================================================
    # VIEW 2: AI RECOMMENDATIONS (Deep dive & Custom Tuning)
    # ==========================================================================
    elif nav == "🎯 AI Recommendations":
        st.markdown("## 🎯 AI Recommendation Engine")
        st.caption("Fine-tune your recommendation settings with adjustable top-K, format constraints, and similarity breakdowns.")

        c_t, c_f, c_k = st.columns([3, 1.2, 1.2])
        with c_t:
            query_t = st.text_input("Enter Query Title:", value=st.session_state["selected_title_query"])
        with c_f:
            filter_fmt = st.selectbox("Format Filter", ["All", "Movie", "TV Show"], key="rec_fmt_sel")
        with c_k:
            k_val = st.slider("Result Count (K)", min_value=3, max_value=20, value=6)

        if st.button("✨ Generate Recommendations", type="primary", use_container_width=True):
            st.session_state["selected_title_query"] = query_t
            st.rerun()

        recs = client.get_recommendations(
            title_id=query_t,
            limit=k_val,
            type=filter_fmt if filter_fmt != "All" else None
        )

        if recs and recs.get("recommendations"):
            q_det = client.get_title_details(recs.get("query_id", query_t))
            if q_det:
                st.markdown(f"### Query Item: **{recs.get('query_title')}**")
                st.markdown(render_hero_spotlight(q_det), unsafe_allow_html=True)

            st.caption(f"ℹ️ {recs.get('disclaimer')}")

            items = recs["recommendations"]
            for i in range(0, len(items), 3):
                row_cols = st.columns(3)
                for j, c in enumerate(row_cols):
                    idx = i + j
                    if idx < len(items):
                        r_item = items[idx]
                        with c:
                            st.markdown(
                                render_movie_card(r_item, is_recommendation=True),
                                unsafe_allow_html=True
                            )
                            if st.button(f"Recommend '{r_item['title']}' ➔", key=f"rec_page_btn_{r_item['show_id']}", use_container_width=True):
                                st.session_state["selected_title_query"] = r_item["title"]
                                st.rerun()
        else:
            st.warning(f"Could not resolve recommendations for '{query_t}'.")

    # ==========================================================================
    # VIEW 3: BROWSE CATALOGUE (Sleek Grid with Pagination)
    # ==========================================================================
    elif nav == "🔍 Browse & Filter Catalogue":
        st.markdown("## 🔍 Catalogue Browser")
        st.caption("Search across 8,786 titles with real-time multi-filter queries.")

        all_genres = ["All"] + client.get_genres()
        c_search, c_t, c_g, c_s = st.columns([2, 1, 1.5, 1.5])
        with c_search:
            q_text = st.text_input("Search Title or Director:", placeholder="Keyword...")
        with c_t:
            q_type = st.selectbox("Content Type", ["All", "Movie", "TV Show"], key="browse_t")
        with c_g:
            q_genre = st.selectbox("Genre Filter", all_genres, key="browse_g")
        with c_s:
            q_sort = st.selectbox(
                "Sort by",
                ["Title (A-Z)", "Title (Z-A)", "Release Year (Newest)", "Release Year (Oldest)"],
                key="browse_s"
            )

        sort_dict = {
            "Title (A-Z)": "title_asc",
            "Title (Z-A)": "title_desc",
            "Release Year (Newest)": "year_desc",
            "Release Year (Oldest)": "year_asc"
        }

        page_size = 12
        catalog_res = client.list_titles(
            q=q_text,
            type=q_type,
            genre=q_genre,
            sort_by=sort_dict.get(q_sort, "title_asc"),
            page=st.session_state["catalog_page"],
            page_size=page_size
        )

        total_cnt = catalog_res.get("total", 0)
        tot_pages = catalog_res.get("total_pages", 1)
        curr_page = catalog_res.get("page", 1)

        st.markdown(f"**Found {total_cnt:,} titles** (Page {curr_page} of {tot_pages})")

        items_list = catalog_res.get("items", [])
        if items_list:
            for i in range(0, len(items_list), 4):
                cols = st.columns(4)
                for j, col in enumerate(cols):
                    idx = i + j
                    if idx < len(items_list):
                        item = items_list[idx]
                        with col:
                            st.markdown(render_movie_card(item), unsafe_allow_html=True)
                            if st.button("Find Similar ➔", key=f"cat_browse_{item['show_id']}", use_container_width=True):
                                st.session_state["selected_title_query"] = item["title"]
                                st.toast(f"Switching to {item['title']}...")

            # Pagination Controls
            cp1, cp2, cp3 = st.columns([1, 2, 1])
            with cp1:
                if curr_page > 1:
                    if st.button("⬅️ Previous"):
                        st.session_state["catalog_page"] = curr_page - 1
                        st.rerun()
            with cp2:
                st.write(f"<center style='color:#a0aec0;'>Page {curr_page} of {tot_pages}</center>", unsafe_allow_html=True)
            with cp3:
                if curr_page < tot_pages:
                    if st.button("Next ➡️"):
                        st.session_state["catalog_page"] = curr_page + 1
                        st.rerun()
        else:
            st.info("No titles matched your filter criteria.")

    # ==========================================================================
    # VIEW 4: CATALOGUE INSIGHTS
    # ==========================================================================
    elif nav == "📊 Catalogue Insights":
        st.markdown("## 📊 Catalogue Insights & Analytics")
        st.caption("Verifiable descriptive analytics computed on the 8,786 canonical records.")

        insights = client.get_insights()

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("Total Titles Indexed", f"{insights.get('total_titles', 0):,}")
        with m2:
            st.metric("Movies in Catalogue", f"{insights.get('movies_count', 0):,}")
        with m3:
            st.metric("TV Shows in Catalogue", f"{insights.get('tv_shows_count', 0):,}")

        st.markdown("---")

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🎭 Top 10 Genres in Catalogue")
            genres = insights.get("top_genres", [])
            if genres:
                gdf = pd.DataFrame([{"Genre": g["name"], "Count": g["count"]} for g in genres]).sort_values(by="Count")
                fig, ax = plt.subplots(figsize=(6.5, 4.2), facecolor='#0b0f19')
                ax.set_facecolor('#121826')
                ax.barh(gdf["Genre"], gdf["Count"], color='#e50914', edgecolor='#232d42')
                ax.tick_params(colors='#e2e8f0', labelsize=9)
                for spine in ax.spines.values():
                    spine.set_color('#232d42')
                plt.tight_layout()
                st.pyplot(fig)

        with c2:
            st.markdown("#### 🌍 Top Producing Countries")
            countries = insights.get("top_countries", [])
            if countries:
                cdf = pd.DataFrame([{"Country": c["name"], "Count": c["count"]} for c in countries]).sort_values(by="Count")
                fig2, ax2 = plt.subplots(figsize=(6.5, 4.2), facecolor='#0b0f19')
                ax2.set_facecolor('#121826')
                ax2.barh(cdf["Country"], cdf["Count"], color='#1971c2', edgecolor='#232d42')
                ax2.tick_params(colors='#e2e8f0', labelsize=9)
                for spine in ax2.spines.values():
                    spine.set_color('#232d42')
                plt.tight_layout()
                st.pyplot(fig2)

        st.markdown("#### 📅 Release Year Distribution (Recent Decades)")
        year_dist = insights.get("release_year_distribution", [])
        if year_dist:
            ydf = pd.DataFrame([{"Year": y["name"], "Titles": y["count"]} for y in year_dist])
            st.bar_chart(ydf.set_index("Year"))

    # ==========================================================================
    # VIEW 5: WATCHLIST & HISTORY
    # ==========================================================================
    elif nav == "❤️ Watchlist & History":
        st.markdown("## ❤️ Saved Watchlist & Search History")

        tab_fav, tab_hist = st.tabs(["My Watchlist", "Search History"])

        with tab_fav:
            st.caption("Titles you've saved to your watchlist stored in PostgreSQL.")
            saved_ids = client.get_saved_titles(limit=50)

            if saved_ids:
                cols_fav = st.columns(3)
                for idx, sid in enumerate(saved_ids):
                    item = client.get_title_details(sid)
                    if item:
                        with cols_fav[idx % 3]:
                            st.markdown(render_movie_card(item), unsafe_allow_html=True)
                            if st.button("Remove ✕", key=f"remove_fav_{sid}", use_container_width=True):
                                client.remove_saved_title(sid)
                                st.toast(f"Removed '{item['title']}' from Watchlist.")
                                st.rerun()
            else:
                st.info("Your Watchlist is empty. Click the '🤍 Save' button on any movie card to add it here!")

        with tab_hist:
            col_h, col_del = st.columns([4, 1.2])
            with col_h:
                st.caption("Recent user searches logged in the database.")
            with col_del:
                if st.button("🗑️ Clear History", use_container_width=True):
                    client.clear_history()
                    st.toast("Search history cleared.")
                    st.rerun()

            hist = client.get_history(limit=25)
            if hist:
                for h in hist:
                    st.markdown(f"- 🔍 **'{html.escape(h['query'])}'** — <span style='color:#64748b; font-size:0.85rem;'>{h.get('created_at', '')[:19]}</span>", unsafe_allow_html=True)
            else:
                st.info("No search history logged yet.")

    # ==========================================================================
    # VIEW 6: ALGORITHM & METHODOLOGY
    # ==========================================================================
    elif nav == "📖 Algorithm & Methodology":
        st.markdown("## 📖 Recommendation Algorithm & Mathematical Methodology")

        st.markdown("""
        ### 1. Content-Based Recommendation Architecture
        CineMatch compares titles using verifiable catalogue metadata:
        - **Genres (`listed_in`):** Doubly weighted ($2\\times$) in the feature soup to emphasize thematic genre overlap.
        - **Director & Country:** Tokenized with underscore bindings (e.g. `christopher_nolan`, `united_states`) to prevent accidental partial word collisions.
        - **Content Format & Rating:** Standardized categorical tokens (e.g. `movie`, `pg_13`).

        ### 2. TF-IDF (Term Frequency - Inverse Document Frequency)
        $$\\text{TF-IDF}(t, d, D) = \\text{TF}(t, d) \\times \\log\\left(\\frac{1 + |D|}{1 + |\\{d \\in D : t \\in d\\}|}\\right) + 1$$
        - Sublinear term-frequency scaling is applied: $\\log(1 + \\text{TF})$.
        - Output vectors are $L_2$-normalised into sparse unit vectors.

        ### 3. Cosine Similarity & Query Latency
        Because vectors are $L_2$-normalised, cosine similarity is equivalent to a fast dot-product:
        $$\\text{Cosine Similarity}(\\mathbf{u}, \\mathbf{v}) = \\mathbf{u} \\cdot \\mathbf{v}$$
        - **Zero Precomputed Dense Matrix:** Operates on-demand on the sparse CSR matrix, keeping memory footprint $< 1$ MB and query latency at $\\approx 1.16$ ms on standard CPU hardware.
        - **Self-Exclusion:** The query title is strictly excluded from recommendations.

        ### 4. Interpretation of Match Scores
        > ⚠️ **Important Disclosure:** A match score of 89% represents mathematical geometric proximity across metadata features (shared genres, director, origin country). It does **not** indicate a prediction of user satisfaction, viewing probability, or ML classification accuracy.
        """)


if __name__ == "__main__":
    main()
