# CineMatch — Deployment & Operations Guide

## 1. Local Development (Native Python)

### Prerequisites
- Python 3.10+
- PostgreSQL (optional, falls back gracefully to local SQLite)

### Step 1: Clone and Set Up Virtual Environment
```bash
git clone https://github.com/Samay-P07/netflix-content-recommendation-system.git
cd netflix-content-recommendation-system

# Windows PowerShell:
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux / macOS:
python3 -m venv venv
source venv/bin/activate
```

### Step 2: Install Dependencies
```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Run Database Migrations (Optional if using PostgreSQL)
```bash
alembic upgrade head
```

### Step 4: Run Application
**Option A: Standalone Streamlit (with internal API fallback):**
```bash
streamlit run app.py
```

**Option B: Full Microservice Setup (FastAPI + Streamlit):**
```bash
# Terminal 1 - Backend API:
uvicorn backend.main:app --port 8000 --reload

# Terminal 2 - Frontend UI:
streamlit run app.py --server.port 8501
```

---

## 2. Docker & Docker Compose Deployment

### Full Stack Startup (Web + API + PostgreSQL)
```bash
docker compose up --build
```
- Streamlit Web UI: `http://localhost:8501`
- FastAPI REST Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

### Tear Down
```bash
docker compose down -v
```

---

## 3. Running Automated Tests & Quality Checks

```bash
# Run pytest test suite:
pytest tests/ -v

# Run latency benchmark:
python benchmark.py

# Run CLI evaluation:
python main.py --evaluate --sample_size 100 --top_k 5
```
