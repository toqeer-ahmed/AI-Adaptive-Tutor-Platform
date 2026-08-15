# AI-Powered Adaptive Education Platform (Grades 4–8)

Production-oriented multi-tenant SaaS platform delivering curriculum-grounded AI tutoring, deterministic mastery tracking, rule-based adaptive learning, validated assessment pipelines, and human-in-the-loop curriculum governance.

---


## 🏗 Technology Stack & Architecture

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2
- **Frontend**: Next.js 14, React 18, TypeScript, Vanilla CSS
- **Database & Storage**: PostgreSQL 16 + `pgvector`, Redis 7, S3-compatible MinIO
- **Task Processing**: Celery + Redis Broker
- **Architecture**: Modular Monolith with strict service module boundaries and PostgreSQL Row-Level Security (RLS) multi-tenant isolation.

---

## 📁 Repository Directory Layout

```text
├── docs/                      # Authoritative specifications (PRD, SRS, TDS, Implementation Plan)
├── backend/                   # Python FastAPI application & modular services
│   ├── api/                   # REST routers (/api/v1), schemas, and RLS dependencies
│   ├── services/              # Framework-agnostic business logic services
│   ├── models/                # SQLAlchemy ORM schemas
│   ├── db/                    # Async database session & Alembic migrations
│   └── config/                # Settings & structured JSON logging
├── frontend/                  # Next.js App Router web client
│   ├── app/                   # React components & routes
│   ├── lib/                   # API client abstraction & auth context
│   └── public/                # Static assets
├── workers/                   # Celery task runner & beat scheduler
├── infrastructure/            # Docker Compose orchestration & healthchecks
├── tests/                     # Pytest suite (Unit, Integration, Security RLS Isolation)
├── .env.example               # Environment variable configuration template
├── docker-compose.yml         # Local stack launcher
├── DEVELOPMENT.md             # Local setup, migration, test & execution guide
└── CONTRIBUTING.md            # Pull request rules & architectural principles
```

---

## 🚀 Quick Start Guide

### 1. Launch Environment via Docker Compose
```bash
cp .env.example .env
docker compose up --build
```

### 2. Verify Health Status
- **API Health**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Frontend App**: [http://localhost:3000](http://localhost:3000)

### 3. Run Automated Tests & RLS Isolation Checks
```bash
cd backend
pytest -v
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for full operational instructions.
