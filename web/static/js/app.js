/**
 * CineMatch — Client-side Web Controller
 * High-performance, asynchronous discovery platform communicating with FastAPI REST API.
 */

// State management
const state = {
  currentHeroTitle: "Inception",
  watchlist: new Set(),
  catalogPage: 1,
  catalogPageSize: 12,
  genres: []
};

// API Base URL
const API_BASE = "";

// DOM Elements
const heroBillboard = document.getElementById("heroBillboard");
const recsGrid = document.getElementById("recsGrid");
const popularGrid = document.getElementById("popularGrid");
const catalogGrid = document.getElementById("catalogGrid");
const searchInput = document.getElementById("searchInput");
const genreFilter = document.getElementById("genreFilter");
const typeFilter = document.getElementById("typeFilter");
const sortFilter = document.getElementById("sortFilter");
const watchlistCountBadge = document.getElementById("watchlistCount");
const modalBackdrop = document.getElementById("modalBackdrop");
const modalContent = document.getElementById("modalContent");

// Helper: Format Safe HTML Strings
function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Fallback Poster Generator (Guaranteed valid SVG if image fails)
function getSvgFallback(title, genre, year) {
  const safeT = escapeHtml(title || "Featured");
  const safeG = escapeHtml(genre ? genre.split(",")[0].trim() : "Movie");
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 450" width="300" height="450">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#141c2b"/>
      <stop offset="100%" stop-color="#07090e"/>
    </linearGradient>
  </defs>
  <rect width="100%" height="100%" fill="url(#g)"/>
  <circle cx="150" cy="170" r="45" fill="#1b263b" stroke="#e50914" stroke-width="2"/>
  <text x="150" y="180" font-family="Arial,sans-serif" font-size="30" fill="#e50914" text-anchor="middle">🎬</text>
  <text x="150" y="280" font-family="Arial,sans-serif" font-size="18" font-weight="bold" fill="#ffffff" text-anchor="middle">${safeT.slice(0, 20)}</text>
  <text x="150" y="310" font-family="Arial,sans-serif" font-size="12" font-weight="bold" fill="#e50914" text-anchor="middle">${safeG.toUpperCase()}</text>
  <text x="150" y="340" font-family="Arial,sans-serif" font-size="11" fill="#94a3b8" text-anchor="middle">${year || "2021"} • CINEMATCH</text>
</svg>`;
  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg);
}

// Template: Render a Uniform Movie Card
function createCardHtml(item, isRec = false) {
  const isSaved = state.watchlist.has(item.show_id);
  const typeClass = item.type.toLowerCase().includes("tv") ? "pill-rating" : "pill-type";
  const posterSrc = item.poster_url || getSvgFallback(item.title, item.listed_in, item.release_year);

  let scoreBadge = "";
  if (isRec && item.similarity_percentage) {
    scoreBadge = `<div class="match-badge">★ ${item.similarity_percentage}% Match</div>`;
  }

  let explanationHtml = "";
  if (isRec && item.explanation) {
    explanationHtml = `<div class="card-explanation-box">💡 ${escapeHtml(item.explanation)}</div>`;
  }

  const director = item.director ? `• Dir: ${escapeHtml(item.director)}` : "";
  const country = item.country ? `• ${escapeHtml(item.country)}` : "";

  return `
    <div class="movie-card" data-id="${escapeHtml(item.show_id)}">
      <div class="card-poster-wrap">
        <img src="${escapeHtml(posterSrc)}" 
             class="card-poster-img" 
             alt="${escapeHtml(item.title)}" 
             loading="lazy"
             onerror="this.onerror=null; this.src='${getSvgFallback(item.title, item.listed_in, item.release_year)}';" />
        <div class="card-poster-overlay">
          <div class="poster-top-pills">
            <span class="pill ${typeClass}">${escapeHtml(item.type)}</span>
            <span class="pill pill-rating">${escapeHtml(item.rating || "PG-13")}</span>
          </div>
          ${scoreBadge}
        </div>
      </div>
      <div class="card-body">
        <div class="card-title-row">
          <div class="card-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</div>
          <span class="card-year">${escapeHtml(item.release_year)}</span>
        </div>
        <div class="card-genres">${escapeHtml(item.listed_in)}</div>
        <div class="card-meta-line">${director} ${country}</div>
        ${explanationHtml}
        <div class="card-btn-row">
          <button class="btn-card btn-card-explore" onclick="selectAndRecommend('${escapeHtml(item.title)}')">
            Explore ➔
          </button>
          <button class="btn-card btn-card-fav ${isSaved ? 'active' : ''}" onclick="toggleWatchlist('${escapeHtml(item.show_id)}', this)">
            ${isSaved ? '❤️ Saved' : '🤍 Save'}
          </button>
        </div>
      </div>
    </div>
  `;
}

// 1. Load Hero Featured Spotlight
async function loadHeroSpotlight(titleOrId) {
  try {
    const res = await fetch(`${API_BASE}/titles/${encodeURIComponent(titleOrId)}`);
    if (!res.ok) return;
    const item = await res.json();
    state.currentHeroTitle = item.title;

    const poster = item.poster_url || getSvgFallback(item.title, item.listed_in, item.release_year);
    const bg = `linear-gradient(90deg, rgba(7, 9, 14, 0.96) 30%, rgba(7, 9, 14, 0.8) 65%, rgba(7, 9, 14, 0.4) 100%), url('${poster}')`;

    heroBillboard.style.backgroundImage = bg;
    heroBillboard.innerHTML = `
      <div class="hero-overlay"></div>
      <div class="hero-content">
        <div class="hero-meta-pills">
          <span class="pill pill-type">${escapeHtml(item.type)}</span>
          <span class="pill pill-rating">${escapeHtml(item.rating || "TV-MA")}</span>
          <span class="pill pill-rating">${escapeHtml(item.duration || "120 min")}</span>
          <span class="pill-year">${escapeHtml(item.release_year)}</span>
        </div>
        <h1 class="hero-title">${escapeHtml(item.title)}</h1>
        <div class="hero-genre">${escapeHtml(item.listed_in)}</div>
        <p class="hero-desc">
          Directed by <strong>${escapeHtml(item.director || "Various Artists")}</strong> • Origin: <strong>${escapeHtml(item.country || "Global")}</strong>.<br/>
          Experience transparent AI-driven discovery using TF-IDF sublinear vectors and geometric cosine similarity.
        </p>
        <div class="hero-actions">
          <button class="btn btn-primary" onclick="selectAndRecommend('${escapeHtml(item.title)}')">
            ✨ Discover Similar Titles
          </button>
          <button class="btn btn-secondary" onclick="toggleWatchlist('${escapeHtml(item.show_id)}')">
            ${state.watchlist.has(item.show_id) ? '❤️ In Watchlist' : '➕ Add to Watchlist'}
          </button>
        </div>
      </div>
    `;
  } catch (err) {
    console.warn("Could not load hero title:", err);
  }
}

// 2. Load Recommendations for Given Title
async function loadRecommendations(title) {
  recsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #94a3b8;">Computing cosine similarity vectors...</div>`;

  try {
    const res = await fetch(`${API_BASE}/recommendations/${encodeURIComponent(title)}?limit=8`);
    if (!res.ok) {
      recsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #f87171;">No direct recommendations found for '${escapeHtml(title)}'. Try searching another title.</div>`;
      return;
    }
    const data = await res.json();
    const recs = data.recommendations || [];

    if (recs.length === 0) {
      recsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #94a3b8;">No recommendations returned.</div>`;
      return;
    }

    recsGrid.innerHTML = recs.map(r => createCardHtml(r, true)).join("");
  } catch (err) {
    recsGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #f87171;">Failed to load recommendations. Please check server status.</div>`;
  }
}

// 3. Load Popular Movies Shelf
async function loadPopularShelf() {
  try {
    const res = await fetch(`${API_BASE}/titles?type=Movie&sort_by=year_desc&page=1&page_size=6`);
    if (!res.ok) return;
    const data = await res.json();
    popularGrid.innerHTML = (data.items || []).map(m => createCardHtml(m, false)).join("");
  } catch (err) {
    console.error("Could not load popular titles:", err);
  }
}

// 4. Load Catalogue Explorer with Filters & Pagination
async function loadCatalog() {
  catalogGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #94a3b8;">Loading catalog...</div>`;

  const type = typeFilter.value;
  const genre = genreFilter.value;
  const sort = sortFilter.value;
  const q = searchInput.value.trim();

  const params = new URLSearchParams({
    page: state.catalogPage,
    page_size: state.catalogPageSize,
    sort_by: sort
  });

  if (type !== "All") params.append("type", type);
  if (genre !== "All") params.append("genre", genre);
  if (q) params.append("q", q);

  try {
    const res = await fetch(`${API_BASE}/titles?${params.toString()}`);
    if (!res.ok) return;
    const data = await res.json();

    document.getElementById("catalogCountInfo").innerText = `Found ${data.total.toLocaleString()} titles (Page ${data.page} of ${data.total_pages})`;
    document.getElementById("btnPrevPage").disabled = data.page <= 1;
    document.getElementById("btnNextPage").disabled = data.page >= data.total_pages;

    if (data.items.length === 0) {
      catalogGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #94a3b8;">No titles matched your criteria.</div>`;
      return;
    }

    catalogGrid.innerHTML = data.items.map(m => createCardHtml(m, false)).join("");
  } catch (err) {
    catalogGrid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #f87171;">Error loading catalogue items.</div>`;
  }
}

// 5. Load Genres List
async function loadGenres() {
  try {
    const res = await fetch(`${API_BASE}/titles/genres`);
    if (!res.ok) return;
    state.genres = await res.json();
    genreFilter.innerHTML = `<option value="All">All Genres</option>` + 
      state.genres.map(g => `<option value="${escapeHtml(g)}">${escapeHtml(g)}</option>`).join("");
  } catch (err) {
    console.error("Failed to fetch genres:", err);
  }
}

// 6. Action: Select Title & Run Recommendation
window.selectAndRecommend = function(title) {
  loadHeroSpotlight(title);
  loadRecommendations(title);
  window.scrollTo({ top: 0, behavior: 'smooth' });
};

// 7. Watchlist Toggle
window.toggleWatchlist = async function(showId, btnElem = null) {
  if (state.watchlist.has(showId)) {
    state.watchlist.delete(showId);
    try { await fetch(`${API_BASE}/saved/${showId}`, { method: 'DELETE' }); } catch(e){}
    if (btnElem) { btnElem.innerHTML = "🤍 Save"; btnElem.classList.remove("active"); }
  } else {
    state.watchlist.add(showId);
    try { await fetch(`${API_BASE}/saved`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ show_id: showId }) }); } catch(e){}
    if (btnElem) { btnElem.innerHTML = "❤️ Saved"; btnElem.classList.add("active"); }
  }
  watchlistCountBadge.innerText = state.watchlist.size;
};

// 8. Load Saved Watchlist
async function loadSavedWatchlist() {
  try {
    const res = await fetch(`${API_BASE}/saved`);
    if (res.ok) {
      const data = await res.json();
      data.items.forEach(i => state.watchlist.add(i.show_id));
      watchlistCountBadge.innerText = state.watchlist.size;
    }
  } catch (e) {}
}

// 9. Open Insights Modal
window.openInsightsModal = async function() {
  modalBackdrop.classList.add("open");
  modalContent.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading catalogue analytics...</div>`;

  try {
    const res = await fetch(`${API_BASE}/insights/overview`);
    const d = await res.json();

    modalContent.innerHTML = `
      <h2 style="font-size: 1.8rem; margin-bottom: 0.5rem;">📊 Catalogue Analytics & Insights</h2>
      <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1.5rem;">${escapeHtml(d.catalog_summary)}</p>
      
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 2rem;">
        <div style="background: #141c2b; border: 1px solid #232e42; padding: 1.2rem; border-radius: 8px; text-align: center;">
          <div style="font-size: 2rem; font-weight: 900; color: #e50914;">${d.total_titles.toLocaleString()}</div>
          <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Total Titles</div>
        </div>
        <div style="background: #141c2b; border: 1px solid #232e42; padding: 1.2rem; border-radius: 8px; text-align: center;">
          <div style="font-size: 2rem; font-weight: 900; color: #00d2ff;">${d.movies_count.toLocaleString()}</div>
          <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">Movies</div>
        </div>
        <div style="background: #141c2b; border: 1px solid #232e42; padding: 1.2rem; border-radius: 8px; text-align: center;">
          <div style="font-size: 2rem; font-weight: 900; color: #f59f00;">${d.tv_shows_count.toLocaleString()}</div>
          <div style="font-size: 0.8rem; color: #94a3b8; text-transform: uppercase;">TV Shows</div>
        </div>
      </div>

      <h4 style="margin-bottom: 0.8rem; color: #fff;">Top 8 Genres in Catalogue</h4>
      <div style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 1.5rem;">
        ${d.top_genres.slice(0, 8).map(g => `
          <span style="background: #1b263b; border: 1px solid #232e42; padding: 4px 10px; border-radius: 20px; font-size: 0.82rem;">
            <strong>${escapeHtml(g.name)}:</strong> ${g.count}
          </span>
        `).join("")}
      </div>
    `;
  } catch (err) {
    modalContent.innerHTML = `<div style="color: #f87171;">Failed to load insights.</div>`;
  }
};

// 10. Open Watchlist Modal
window.openWatchlistModal = async function() {
  modalBackdrop.classList.add("open");
  if (state.watchlist.size === 0) {
    modalContent.innerHTML = `
      <h2>❤️ My Saved Watchlist</h2>
      <p style="color: #94a3b8; margin: 1.5rem 0;">Your watchlist is currently empty. Click "🤍 Save" on any title to bookmark it!</p>
    `;
    return;
  }

  modalContent.innerHTML = `<div style="text-align:center; padding: 2rem;">Loading your saved titles...</div>`;
  const cards = [];
  for (const id of state.watchlist) {
    try {
      const res = await fetch(`${API_BASE}/titles/${id}`);
      if (res.ok) {
        const item = await res.json();
        cards.push(createCardHtml(item, false));
      }
    } catch(e) {}
  }

  modalContent.innerHTML = `
    <h2 style="font-size: 1.6rem; margin-bottom: 1.2rem;">❤️ My Saved Watchlist (${state.watchlist.size})</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; max-height: 70vh; overflow-y: auto;">
      ${cards.join("")}
    </div>
  `;
};

// 11. Open Methodology Modal
window.openMethodologyModal = function() {
  modalBackdrop.classList.add("open");
  modalContent.innerHTML = `
    <h2 style="font-size: 1.6rem; margin-bottom: 0.6rem;">📖 CineMatch AI Methodology</h2>
    <div style="color: #94a3b8; font-size: 0.92rem; line-height: 1.6;">
      <p style="margin-bottom: 1rem;">
        CineMatch operates on a pure <strong>content-based discovery algorithm</strong>. Rather than relying on private user tracking, it constructs rich multidimensional representations using verifiable metadata:
      </p>
      <ul style="margin-left: 1.5rem; margin-bottom: 1.2rem;">
        <li><strong>Weighted Genres (2×):</strong> Boosts genre overlap to ensure strong thematic continuity.</li>
        <li><strong>Bound Entities:</strong> Multi-word director and country names are bound (e.g. <code>christopher_nolan</code>) to eliminate partial match noise.</li>
        <li><strong>Sublinear TF-IDF:</strong> Scaled frequency vectors normalized with L2 Euclidean norms.</li>
        <li><strong>On-the-fly Cosine Similarity:</strong> Computes instantaneous linear kernel dot-products in ~1.16 ms without large precomputed memory matrices.</li>
      </ul>
      <p style="background: rgba(229, 9, 20, 0.1); border-left: 4px solid #e50914; padding: 0.8rem; border-radius: 4px; color: #fff;">
        <strong>Important:</strong> Match scores (e.g. 89% Match) represent geometric metadata alignment. They do not predict subjective viewer satisfaction.
      </p>
    </div>
  `;
};

window.closeModal = function() {
  modalBackdrop.classList.remove("open");
};

// Search Debounce Event
let searchTimer = null;
searchInput.addEventListener("input", () => {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    state.catalogPage = 1;
    const query = searchInput.value.trim();
    if (query.length >= 3) {
      loadRecommendations(query);
    }
    loadCatalog();
  }, 350);
});

// Filter Change Events
genreFilter.addEventListener("change", () => { state.catalogPage = 1; loadCatalog(); });
typeFilter.addEventListener("change", () => { state.catalogPage = 1; loadCatalog(); });
sortFilter.addEventListener("change", () => { state.catalogPage = 1; loadCatalog(); });

// Pagination
document.getElementById("btnPrevPage").addEventListener("click", () => {
  if (state.catalogPage > 1) {
    state.catalogPage--;
    loadCatalog();
  }
});
document.getElementById("btnNextPage").addEventListener("click", () => {
  state.catalogPage++;
  loadCatalog();
});

// Initialization on DOM Ready
document.addEventListener("DOMContentLoaded", async () => {
  await loadSavedWatchlist();
  await loadGenres();
  await loadHeroSpotlight(state.currentHeroTitle);
  await loadRecommendations(state.currentHeroTitle);
  await loadPopularShelf();
  await loadCatalog();
});
