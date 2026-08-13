# Local Development Guide: AI Adaptive Education Platform

This guide details how to run, test, and manage the local development environment for Phase 0 and subsequent phases.

---

## 1. Environment Setup

### Prerequisites
- **Python 3.12+**
- **Node.js 20+** & **npm**
- **Docker Desktop** & **Docker Compose**
- **PostgreSQL 16** (if running outside Docker)
- **Redis 7** (if running outside Docker)

### Environment Variables
Copy `.env.example` to `.env` at the root of the repository:
```bash
cp .env.example .env
```
Copy `frontend/.env.example` to `frontend/.env.local`:
```bash
cp frontend/.env.example frontend/.env.local
```

---

## 2. Starting the Project via Docker Compose (Recommended)

To spin up the full local environment (PostgreSQL + pgvector, Redis, FastAPI Backend, Celery Worker, Next.js Frontend):

```bash
docker compose up --build
```

To stop all services:
```bash
docker compose down
```

### Checking Service Health
- **FastAPI Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **FastAPI Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)

---

## 3. Running Services Individually (Native Development)

### 3.1 Database & Redis Infrastructure Only
Start PostgreSQL and Redis in background via Docker:
```bash
docker compose up -d postgres redis
```

### 3.2 Running Database Migrations
Run Alembic migrations to create tables and apply PostgreSQL Row-Level Security (RLS) policies:
```bash
cd backend
alembic upgrade head
```

To roll back the last migration:
```bash
cd backend
alembic downgrade -1
```

### 3.3 Running the FastAPI Backend
```bash
cd backend
python -m venv venv
# On Windows: venv\Scripts\activate  | On Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3.4 Running the Celery Workers
```bash
# Ensure virtualenv is active and PYTHONPATH includes repo root
celery -A workers.celery_app worker --loglevel=info
```

### 3.5 Running the Next.js Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## 4. Running Automated Tests & Code Quality Tools

### Running Pytest Suite
Run unit tests, API integration tests, and release-blocking cross-tenant RLS isolation tests:
```bash
cd backend
pytest -v
```

To run with coverage:
```bash
pytest --cov=backend --cov-report=term-missing
```

### Type Checking & Linting
Run Ruff linter and MyPy type checker:
```bash
# From backend directory
ruff check .
mypy .
```
