# VectorHire AI — System Architecture

## 0. Big picture

VectorHire is a **multi-user web app** that turns a candidate's resume into ranked job matches and lets them chat with a career coach grounded in those results. The system is composed of **five Docker services** behind one frontend:

```
                          ┌──────────────────────────────┐
                          │       Frontend (Next.js)      │
                          │  Public: /, /login, /register │
                          │  Auth:  /upload, /dashboard,  │
                          │         /analysis/[id]        │
                          └──────────────┬────────────────┘
                                         │ HTTPS / fetch + JWT
                                         ▼
                          ┌──────────────────────────────┐
                          │      Backend (FastAPI)        │
                          │   Routers under /api/v1/*     │
                          └─────┬────────────┬────────────┘
                ┌───────────────┘            └─────────────┐
                ▼                                          ▼
        ┌──────────────┐                          ┌──────────────────┐
        │  PostgreSQL  │                          │     ChromaDB     │
        │   identity,  │                          │     job + (later)│
        │   resumes,   │                          │  resume vectors  │
        │   analyses,  │                          └──────────────────┘
        │   chats,jobs │                                  ▲
        └──────┬───────┘                                  │
               │                                  ┌──────────────────┐
               ▼                                  │      Redis       │
        ┌──────────────┐                          │   LLM + embed +  │
        │     LLM      │◀─────────────────────────│   search cache   │
        │  OpenRouter  │                          └──────────────────┘
        │  (fallback   │
        │   chain x6)  │
        └──────────────┘
```

---

## 1. Layered backend

The backend code is structured top-down — routers are thin; LangGraph orchestrates; services do the work.

```
┌────────────────────────────────────────────────────────────────────┐
│  app/api/routes/      Thin FastAPI routers + JWT dependency       │
│    health, auth, resume, search, analysis, ingestion, eval, debug │
└──────────────────────────────┬─────────────────────────────────────┘
                               │
┌──────────────────────────────▼─────────────────────────────────────┐
│  app/graph/         LangGraph StateGraph (5 nodes)                 │
│    parse → extract → retrieve → rank → explain                     │
└──┬────────────────┬────────────────┬─────────────────┬─────────────┘
   │                │                │                 │
   ▼                ▼                ▼                 ▼
┌────────┐   ┌────────────┐   ┌────────────┐   ┌──────────────┐
│ resume │   │   rag      │   │  services  │   │  llm/        │
│ parser │   │  embeds,   │   │  ranking,  │   │  gateway,    │
│ skill  │   │  vectordb, │   │  retrieval,│   │  prompts,    │
│ extr.  │   │  dense,    │   │  resume,   │   │  chains,     │
│        │   │  sparse,   │   │  ingestion,│   │  openrouter  │
│        │   │  hybrid,   │   │  chat,     │   │  provider    │
│        │   │  rrf       │   │  embedding │   │              │
└────────┘   └────────────┘   └────────────┘   └──────────────┘
                  │
                  ▼
┌────────────────────────────────────────────────────────────────────┐
│  app/db/            SQLAlchemy ORM + repositories + Alembic        │
│  app/core/          Settings, logging, JWT/bcrypt, Redis client    │
└────────────────────────────────────────────────────────────────────┘
```

### Layer responsibilities

| Layer | Owns | Forbidden from |
|-------|------|----------------|
| `api/routes/` | HTTP verbs, request validation, JWT dependency, error mapping | Business logic, ORM details |
| `graph/` | LangGraph state machine + 5 node functions | HTTP types, direct DB writes |
| `services/` | Cross-cutting business logic, transactions, caching | HTTP types |
| `rag/` | Embeddings, ChromaDB, BM25, RRF fusion | LLM calls, business decisions |
| `llm/` | LLM client, fallback chain, prompts, streaming | Domain knowledge |
| `db/` | SQLAlchemy session, models, repositories | HTTP, LLM |
| `core/` | Settings, logging, JWT, Redis client | Anything domain-specific |

---

## 2. The resume → results pipeline (LangGraph)

A single POST to `/api/v1/resume/analyze` triggers `app/graph/workflow.py::run_analysis_workflow`, which executes 5 sequential nodes through a shared `WorkflowState` dict:

```
                         ┌──────────────────────┐
                         │  initial state:      │
                         │  resume_bytes,       │
                         │  filename,           │
                         │  search_query?,      │
                         │  top_k, exp_filter?  │
                         └──────────┬───────────┘
                                    │
                                    ▼
        ┌───────────────────────────────────────────────────┐
        │ 1. parse_resume_node    (resume/parser.py)         │
        │    PDF → raw_text + structured ParsedResume        │
        │    WRITES: parsed_resume, raw_text                 │
        └────────────────────┬──────────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ 2. extract_skills_node  (llm/chains.py)            │
        │    Raw text → skills via LLM + heuristic fallback  │
        │    WRITES: skills, experience_level                │
        └────────────────────┬──────────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ 3. retrieve_jobs_node   (rag/hybrid_retriever.py)  │
        │    Query = search_query OR skills-derived prompt   │
        │    Hybrid: BM25 + dense → RRF → top_k jobs         │
        │    WRITES: retrieved_jobs                          │
        └────────────────────┬──────────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ 4. rank_jobs_node       (services/ranking_service) │
        │    Cosine resume_vec ↔ job_vec → match_percentage  │
        │    + matched_skills / missing_skills computation   │
        │    WRITES: ranked_jobs                             │
        └────────────────────┬──────────────────────────────┘
                             ▼
        ┌───────────────────────────────────────────────────┐
        │ 5. explain_match_node  (services/explanation_svc)  │
        │    LLM → per-job explanation + global summary +    │
        │    top_missing_skills + improvement_suggestions    │
        │    WRITES: explained_jobs, overall_summary, ...    │
        └────────────────────┬──────────────────────────────┘
                             ▼
                  final_state → AnalysisResponse
                  persisted to resume_analysis table
```

**Why LangGraph instead of a plain async function?** Each node is a pure `(state) → state` step. Nodes are unit-testable in isolation, can be swapped without touching the others, and the graph builder gives us a single visualizable contract. It also sets us up to add **conditional edges** later (e.g., re-query if retrieval recall is poor) without restructuring the call sites.

---

## 3. Hybrid retrieval (RAG)

```
                       query (text)
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    ┌───────────────┐               ┌───────────────┐
    │  embeddings   │               │  rank-bm25    │
    │  all-MiniLM   │               │  over job     │
    │  -L6-v2       │               │  description  │
    │  (CPU local)  │               │  corpus       │
    └───────┬───────┘               └───────┬───────┘
            ▼                               ▼
    ┌───────────────┐               ┌───────────────┐
    │  ChromaDB     │               │  BM25 ranked  │
    │  cosine top-N │               │  list top-N   │
    └───────┬───────┘               └───────┬───────┘
            └──────────────┬────────────────┘
                           ▼
                ┌──────────────────────┐
                │  Reciprocal Rank     │
                │  Fusion (rrf.py)     │
                │  score = Σ 1/(k+r)   │
                └──────────┬───────────┘
                           ▼
                    ranked job list
                    (with metadata
                    filters applied:
                    remote, exp level)
```

- **Dense retriever** (`rag/dense_retriever.py`): vector cosine over ChromaDB
- **Sparse retriever** (`rag/sparse_retriever.py`): BM25 token overlap
- **RRF** (`rag/rrf.py`): order-only fusion — no need to normalize scores across the two systems
- **Hybrid retriever** (`rag/hybrid_retriever.py`): runs both, fuses, applies filters

---

## 4. LLM gateway

All LLM calls go through one facade. Provider-agnostic on purpose.

```
       services / nodes
              │
              ▼
       ┌─────────────────┐
       │  LLMGateway     │   complete() / complete_structured() / stream_chat()
       └────────┬────────┘
                ▼
       ┌─────────────────────────────────────────────────────────┐
       │  openrouter_provider                                    │
       │  ┌──────────────────────────────────────────────────┐  │
       │  │  Redis cache lookup (temp ≤ 0.15 only)           │  │
       │  └─────────────┬────────────────────────────────────┘  │
       │                ▼                                        │
       │  ┌──────────────────────────────────────────────────┐  │
       │  │  Circuit breaker (skip 60s after total failure)  │  │
       │  └─────────────┬────────────────────────────────────┘  │
       │                ▼                                        │
       │  ┌──────────────────────────────────────────────────┐  │
       │  │  For model in [primary, fallback, … 4 free]:     │  │
       │  │    chat.completions.create(... timeout=15s)      │  │
       │  │    on 429 / 503 / timeout → next model           │  │
       │  └──────────────────────────────────────────────────┘  │
       └─────────────────────────────────────────────────────────┘
```

The chat endpoint streams via `stream()` — same fallback chain, but cache and circuit-breaker are bypassed (chat is non-deterministic; user-blocking call).

---

## 5. Persistence model

```
users (1) ────┬──── (N) resumes (1) ──── (N) resume_analysis (1) ──── (N) chat_messages
              │
              │      file-hash dedup per user           per-analysis chat thread
              │
              └──── owns everything via FK user_id
```

| Table | Notes |
|-------|-------|
| `users` | email unique, `password_hash` bcrypt |
| `resumes` | composite uniqueness via `user_id + hash` lets the same PDF be re-uploaded without duplication |
| `resume_analysis` | full pipeline output as `analysis_json` JSONB + denormalized `top_match_pct` for fast list rendering |
| `chat_messages` | `analysis_id` FK, role ∈ {user, assistant}, content text |
| `jobs` | independent registry for cross-source dedup (SHA-256 + rapidfuzz token_sort_ratio) |

Migrations are managed by Alembic (`backend/alembic/versions/`):
- `001` — initial (users, resumes, resume_analysis, job_searches, evaluations)
- `002` — jobs registry
- `003` — `password_hash` column on users
- `004` — `chat_messages` table

---

## 6. Authentication flow

```
1. POST /auth/register {email, password}
   → bcrypt hash → INSERT users → JWT(sub=user_id) signed with JWT_SECRET_KEY
   → 201 { access_token }

2. Frontend stores token in localStorage["vh_token"]

3. Every subsequent request:
   Authorization: Bearer <jwt>
       │
       ▼
   api/deps.py::get_current_user  (FastAPI dependency)
       │
       ├─ python-jose decode → sub
       ├─ SELECT users WHERE id = sub
       └─ raise 401 on failure / return User on success

4. Protected route handlers depend on get_current_user — anonymous
   requests get a clean 401 with no DB cost beyond the JWT decode.
```

Frontend uses **client-side** `AuthGuard` (a `useEffect`-based redirect) inside the `(app)` route group — not middleware — because middleware runs server-side and can't read `localStorage`.

---

## 7. Streaming chat

```
Browser                  Backend                   LLM
   │                        │                       │
   │  POST /chat            │                       │
   │ ─────────────────────► │                       │
   │                        │  persist user msg     │
   │                        │  (commit)             │
   │                        │  build prompt from    │
   │                        │  analysis_json +      │
   │                        │  prior turns          │
   │                        │ ────────────────────► │
   │                        │                       │
   │                        │ ◄─── token ──── ──── │
   │  ◄── token (chunk) ─── │                       │
   │                        │ ◄─── token ──── ──── │
   │  ◄── token (chunk) ─── │                       │
   │                        │      ...              │
   │                        │ ◄── stream end ────── │
   │                        │  persist assistant    │
   │                        │  msg in fresh session │
   │  ◄── stream close ──── │  (StreamingResponse   │
   │                        │   finalizer)          │
```

Why `text/plain` instead of SSE? Easier to consume on the frontend: a `fetch` + `ReadableStream` + `TextDecoder` loop, no event parsing. The trade-off is no structured "done" / "error" events — we accept that because all error fall-back happens inside the gateway *before* tokens start flowing.

---

## 8. Job ingestion pipeline

A separate flow from the resume pipeline. Triggered via `/api/v1/ingest` or `scripts/ingest_jobs.py`.

```
  adapter (Adzuna / Arbeitnow) ──fetch──▶ raw job dicts
            │
            ▼
  job_normalizer ──map──▶ JobDocument (canonical schema)
            │
            ▼
  job_pipeline ──dedup──▶ (a) SHA-256 of (title|company|source)
                          (b) rapidfuzz token_sort_ratio > 95
            │
            ▼
  jobs table INSERT (skipped if duplicate)
            │
            ▼
  job_embedder ──embed──▶ ChromaDB (with metadata: remote, exp_level, source)
```

---

## 9. Caching strategy

| What | Where | TTL | Why |
|------|-------|-----|-----|
| LLM responses | Redis `llm:<hash(prompt)>` | configurable | Only for temp ≤ 0.15 (deterministic prompts — skill extraction) |
| Embeddings | Redis `emb:<hash(text)>` | configurable | Sentence-transformer inference is ~20–50ms; cache hot strings |
| Parsed resumes | per-user file-hash row in `resumes` | forever | Reuse if user re-uploads same PDF |
| Hybrid search results | Redis | short | Reduce repeated cold queries on the dashboard |

Chat replies are **never** cached (non-deterministic and would break conversational continuity).

---

## 10. Key design decisions

| Decision | Rationale |
|----------|-----------|
| LangGraph for the analysis pipeline | Pure-function nodes, swappable, testable in isolation; cheap on-ramp to add agent loops later |
| Gateway pattern for LLM | Swap providers in one file; the rest of the app never imports a provider |
| 6-model OpenRouter fallback | Free-tier rate limits hit constantly; per-model 15s timeout caps recovery time |
| Circuit breaker (60s) | Prevents the next batch call from re-running the same dead chain |
| Hybrid retrieval (BM25 + dense + RRF) | Dense misses exact-keyword hits; BM25 misses semantics; RRF combines both ranks order-only |
| Pydantic + SQLAlchemy at every boundary | One contract per layer; mismatches fail at parse time, not in production |
| Streaming chat as plain text body | One less abstraction than SSE; works with vanilla `fetch` |
| Route group `(app)` + client AuthGuard | Middleware can't see `localStorage`; AuthGuard runs after hydration |
| Postgres + Chroma instead of one DB | Postgres owns identity/ownership/state; Chroma owns similarity. They never serve the same query |
| Docker Compose for all 5 services | One command from clean machine to running app |

---

## 11. Where to read next

- **[langgraph_workflow.md](langgraph_workflow.md)** — deeper dive into each node's contract.
- **[rag_pipeline.md](rag_pipeline.md)** — how hybrid retrieval is tuned.
- **[future_agents.md](future_agents.md)** — what a real agent loop (with tool calling and self-reflection) would look like in this codebase.
- **[future_mcp.md](future_mcp.md)** — MCP tool integrations (LinkedIn / GitHub / salary) we sketched but didn't ship.
