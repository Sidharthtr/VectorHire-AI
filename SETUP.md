# VectorHire AI — Setup Guide

There are two ways to run VectorHire:

1. **Docker (recommended)** — one command, identical on Mac / Windows / Linux. ✅
2. **Local install** — run Python + Node directly on your machine (more setup, useful for hacking on the codebase).

---

## Path 1 — Docker (recommended, ~5 minutes)

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Mac / Windows) or Docker Engine + Compose plugin (Linux)
- An **OpenRouter API key** — free, sign up at https://openrouter.ai
- ~4 GB free RAM, ~3 GB disk

### Steps

```bash
# 1. Clone (or unzip) the project, then cd into it
cd vectorhire-ai

# 2. Configure backend secrets
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set at minimum:

```
OPENROUTER_API_KEY=sk-or-v1-...
JWT_SECRET_KEY=<paste output of: openssl rand -hex 32>
```

```bash
# 3. Bring everything up (first run: ~3 min while images build)
docker compose up -d

# 4. Wait for healthchecks to pass
docker compose ps
# All 5 services should show "Up (healthy)"

# 5. Apply DB migrations (first run only)
docker exec vectorhire_backend alembic upgrade head

# 6. Seed the job vector DB with sample data
docker exec vectorhire_backend python scripts/seed_vectordb.py

# 7. Open the app
open http://localhost:3000      # or just browse to it
```

That's it. Register a user, upload a resume, and play with the chat.

### Useful commands

```bash
docker compose logs -f backend         # tail backend logs
docker compose logs -f frontend        # tail frontend logs
docker compose restart backend         # restart after .env change
docker compose down                    # stop (keeps data)
docker compose down -v                 # stop + wipe ALL data
docker exec -it vectorhire_postgres psql -U vectorhire -d vectorhire
```

---

## Path 2 — Local install (no Docker)

### 2.1 Prerequisites

- **Python 3.11** (`python --version` should print 3.11.x)
- **Node.js 20 LTS** (`node --version` should print v20.x.x)
- **PostgreSQL 16** running on `localhost:5432`
- **Redis 7** running on `localhost:6379`
- **ChromaDB** running on `localhost:8001` (or local file persistence — see settings)
- An **OpenRouter API key**

On Windows, install Python and Node from python.org / nodejs.org and tick "Add to PATH" during install. For Postgres/Redis/Chroma the easiest path is still Docker (run *just* those three via `docker compose up -d postgres redis chromadb`).

### 2.2 Backend

```bash
cd backend
python -m venv venv

# Mac/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env: OPENROUTER_API_KEY, JWT_SECRET_KEY, DATABASE_URL, REDIS_URL, CHROMA_HOST

alembic upgrade head
python ../scripts/seed_vectordb.py
uvicorn app.main:app --reload --port 8000
```

Backend will be live at http://localhost:8000 (interactive docs at `/docs`).

### 2.3 Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend lives at http://localhost:3000.

---

## Environment variables (`backend/.env`)

The full list lives in [backend/app/core/settings.py](backend/app/core/settings.py). The ones you actually need to set:

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENROUTER_API_KEY` | ✅ | LLM access |
| `JWT_SECRET_KEY` | ✅ | Sign JWTs — use `openssl rand -hex 32` |
| `DATABASE_URL` | optional | Defaults to the Docker Postgres |
| `REDIS_URL` | optional | Defaults to the Docker Redis |
| `CHROMA_HOST` / `CHROMA_PORT` | optional | Default to Docker Chroma |
| `LLM_MODEL` / `LLM_FALLBACK_MODEL` | optional | OpenRouter model IDs |
| `JWT_EXPIRE_MINUTES` | optional | Default 7 days |

Sensible defaults are baked in, so an `.env` with just the two secrets is enough for a Docker run.

---

## Verifying the install

```bash
# Health endpoint should return {"status": "ok", ...}
curl http://localhost:8000/api/v1/health

# Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"changeme123"}'
```

Then open http://localhost:3000, register the same account in the UI, and upload a PDF resume.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `connection refused` on first run | Wait — image builds take 2–3 min. `docker compose ps` until all 5 are healthy. |
| Backend logs say `Circuit breaker open — all models rate-limited` | All free OpenRouter models are temporarily exhausted. Wait 60s; the breaker auto-resets. |
| `relation "users" does not exist` | You skipped `alembic upgrade head`. Run it. |
| Frontend can't reach backend | Check `NEXT_PUBLIC_API_URL` matches the backend port. Default `http://localhost:8000/api/v1`. |
| `permission denied` on macOS Docker | Open Docker Desktop → Settings → Resources → File sharing, add the project directory. |
| Bcrypt error during register | `bcrypt` is pinned to `4.0.1` because passlib 1.7.4 breaks on 4.1+. Don't upgrade it. |
