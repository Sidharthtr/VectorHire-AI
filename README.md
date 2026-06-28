# VectorHire AI

**A multi-user AI Career Copilot — upload a resume, get LLM-explained job matches, then chat with a career coach grounded in your results.**

Built as a production-style multi-service app: **FastAPI · Next.js 14 · LangGraph · ChromaDB · PostgreSQL · Redis · Docker Compose**.

---

## What it does

1. **Sign up** with email + password (JWT auth).
2. **Upload a PDF resume** — backend parses it, extracts skills with an LLM, runs **hybrid retrieval** (BM25 + dense embeddings fused via Reciprocal Rank Fusion) against a ChromaDB job index, ranks the results, and asks an LLM to explain each match.
3. **Browse saved analyses** in the sidebar — every analysis is persisted per user.
4. **Chat with a Career Coach** about any saved analysis. Replies are **streamed token-by-token** and grounded in your matched jobs / skill gaps.

The full resume-to-results flow is orchestrated as a 5-step **LangGraph pipeline**:

```
PDF → parse_resume → extract_skills → retrieve_jobs → rank_jobs → explain_match → Results
```

---

## Tech stack

| Layer | Tech |
|-------|------|
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS · lucide-react |
| Backend | FastAPI · SQLAlchemy 2 · Alembic · Pydantic v2 |
| Orchestration | LangGraph (5-node `StateGraph`) |
| LLM | OpenRouter (OpenAI-compatible) with 6-model fallback chain |
| Embeddings | sentence-transformers `all-MiniLM-L6-v2` (local, CPU) |
| Retrieval | Hybrid: BM25 (rank-bm25) + dense vectors (ChromaDB) fused via RRF |
| Database | PostgreSQL 16 (users, resumes, analyses, jobs, chat messages) |
| Cache | Redis 7 (LLM cache, embeddings cache, search results) |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Job ingestion | Adzuna + Arbeitnow adapters with SHA-256 + rapidfuzz dedup |
| Infra | Docker Compose (5 services) |

---

## Quick start (Docker — recommended)

```bash
# 1. Clone, then add your OpenRouter API key
cp backend/.env.example backend/.env
# edit backend/.env and set OPENROUTER_API_KEY and JWT_SECRET_KEY

# 2. Bring everything up
docker compose up -d

# 3. (One-time) Seed the job vector DB with sample data
docker exec vectorhire_backend python scripts/seed_vectordb.py

# 4. Open the app
open http://localhost:3000
```

Services & ports:

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend (FastAPI + interactive docs) | http://localhost:8000/docs |
| ChromaDB | http://localhost:8001 |
| PostgreSQL | `localhost:5432` (user/pass `vectorhire`/`vectorhire`) |
| Redis | `localhost:6379` |

The full local-install (no-Docker, Windows-first) walk-through lives in **[SETUP.md](SETUP.md)**.

---

## Project structure

```
vectorhire-ai/
├── frontend/                   Next.js 14 App Router
│   ├── app/                    Routes (route-grouped: public vs (app)-protected)
│   ├── components/             auth, chat, jobs, layout, results, upload
│   ├── contexts/               AuthContext, HistoryContext
│   ├── hooks/                  useAnalysis, useJobSearch
│   ├── lib/                    api.ts (typed fetch client), auth-storage.ts
│   └── types/                  TS mirrors of backend Pydantic schemas
│
├── backend/
│   ├── app/
│   │   ├── main.py             FastAPI entry point — mounts every router
│   │   ├── core/               settings, logging, JWT/bcrypt security, Redis client
│   │   ├── api/                Thin routers (auth, resume, search, analysis, …)
│   │   ├── db/                 SQLAlchemy models, sessions, repositories
│   │   ├── schemas/            Pydantic request/response models
│   │   ├── resume/             PDF parser (PyMuPDF) + skill extractor
│   │   ├── rag/                Embeddings, ChromaDB client, dense/sparse/hybrid retrievers, RRF
│   │   ├── llm/                Gateway + OpenRouter provider + prompts + chains
│   │   ├── graph/              LangGraph workflow (state, builder, 5 nodes)
│   │   ├── services/           Business logic between routes and infrastructure
│   │   ├── ingestion/          Job board pipeline (adapters → normalize → embed → dedup)
│   │   ├── evaluation/         Optional RAG quality (RAGAS, DeepEval)
│   │   └── utils/              File/JSON/text helpers
│   ├── alembic/versions/       001 → 004 migrations
│   └── requirements.txt
│
├── docs/                       architecture.md, langgraph_workflow.md, rag_pipeline.md
├── scripts/                    seed_vectordb, ingest_jobs, reset_db, generate_resumes
├── docker-compose.yml          5-service orchestrator
└── SETUP.md                    local-install guide
```

---

## API endpoints

All routes are mounted under `/api/v1`. Authenticated endpoints require a `Authorization: Bearer <token>` header.

### Auth
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/auth/register` | POST | — | Create account, returns JWT |
| `/auth/login` | POST | — | Exchange email/password for JWT |
| `/auth/me` | GET | ✓ | Current user from token |

### Resume & analysis
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/resume/upload` | POST | ✓ | Parse PDF, return skills (no persistence) |
| `/resume/analyze` | POST | ✓ | Full pipeline + persist Resume + ResumeAnalysis |
| `/analysis/history` | GET | ✓ | List of the user's prior analyses |
| `/analysis/{id}` | GET | ✓ | Reopen a saved analysis |
| `/analysis/{id}/messages` | GET | ✓ | Chat history for one analysis |
| `/analysis/{id}/chat` | POST | ✓ | **Streaming** career-coach reply (text/plain) |

### Search
| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/search/jobs` | POST | — | Semantic + BM25 hybrid job search |
| `/search/jobs/sample` | GET | — | A handful of jobs from the index |

### Ops / debug
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | DB/Redis/Chroma health check |
| `/ingest` | POST | Trigger a job-board ingestion cycle |
| `/admin/stats` | GET | Per-source job counts |
| `/evaluate` | POST | RAG quality metrics (optional) |
| `/debug/retrieval`, `/debug/db` | GET | Dev inspection |

Interactive docs (Swagger): **http://localhost:8000/docs**

---

## Database schema (PostgreSQL)

| Table | Purpose |
|-------|---------|
| `users` | email + bcrypt password hash |
| `resumes` | one row per (user, file-hash) — dedupes re-uploads |
| `resume_analysis` | full pipeline output as JSON + `top_match_pct` |
| `chat_messages` | per-analysis chat turns (role + content) |
| `jobs` | canonical job registry for dedup across ingestion sources |
| `job_searches` | search query history (for debugging / evaluation) |
| `evaluations` | optional RAGAS / DeepEval scores |

Vectors live in **ChromaDB**, keyed by job ID. The two stores are complementary — Postgres owns identity/ownership/state, Chroma owns similarity.

---

## Key design decisions

| Decision | Why |
|----------|-----|
| LangGraph for the pipeline | Each node is independently replaceable / testable; sets us up for future agent loops |
| Single `LLMGateway` facade | Swap providers without touching business logic |
| 6-model OpenRouter fallback chain | Free-tier rate limits hit constantly; cycle through models with 15s per-model timeout |
| Process-wide circuit breaker | After all models fail, skip LLM calls for 60s — don't burn another 90s cycling |
| Hybrid retrieval (BM25 + dense + RRF) | Dense alone misses exact keyword hits; BM25 alone misses semantic matches |
| Redis cache for deterministic prompts only | Temp ≤ 0.15 calls (skill extraction) are cached; creative calls (explanations) are not |
| Streaming chat via plain `text/plain` body | Simpler than SSE on the client (no parsing) and works with `fetch` + `ReadableStream` |
| Route group `(app)` for protected pages | Client-side `AuthGuard` instead of middleware (middleware can't read `localStorage`) |

---

## What's NOT in here yet (honest list)

- True **agent loop** with tool calling — what we have today is a deterministic 5-step LangGraph DAG, not an agent. Hooks for it live in [docs/future_agents.md](docs/future_agents.md).
- **MCP tool integrations** (LinkedIn live search, GitHub analysis, salary lookups). See [docs/future_mcp.md](docs/future_mcp.md).
- Email verification / password reset / OAuth.
- Resume → JD tailoring suggestions (per-job rewrites).
- Production deployment manifests (k8s / Fly / Render).

---

## Common operator commands

```bash
# Tail backend logs
docker compose logs -f backend

# Open a psql shell
docker exec -it vectorhire_postgres psql -U vectorhire -d vectorhire

# Re-seed Chroma from JSON sample data
docker exec vectorhire_backend python scripts/seed_vectordb.py

# Run an ingestion cycle (Adzuna + Arbeitnow)
docker exec vectorhire_backend python scripts/ingest_jobs.py

# Apply migrations after a schema change
docker exec vectorhire_backend alembic upgrade head

# Wipe everything (containers + volumes)
docker compose down -v
```

---

## License

MIT — see [LICENSE](LICENSE).
