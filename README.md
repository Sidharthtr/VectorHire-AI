# VectorHire AI

**Agentic AI-powered career copilot platform built with LangGraph, RAG, ChromaDB, and Gemini.**

> Upload your resume → Get semantically matched AI/engineering jobs → Understand your skill gaps → Get a personalized improvement roadmap.

---

## What It Does

VectorHire AI is a **production-style AI workflow orchestration platform** — not a chatbot. It runs your resume through a full multi-stage AI pipeline:

```
Resume PDF
    ↓
Parse (PyMuPDF)
    ↓
Extract Skills (Gemini AI)
    ↓
Semantic Search (ChromaDB + sentence-transformers)
    ↓
Rank Matches (Gemini AI)
    ↓
Explain & Suggest (Gemini AI)
    ↓
Results Dashboard
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 15, Tailwind CSS, ShadCN UI, TypeScript |
| Backend | FastAPI, Python 3.11+ |
| Orchestration | LangGraph, LangChain |
| LLM | Gemini 1.5 Flash (free tier) |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) — local |
| Vector DB | ChromaDB (local) |
| PDF Parsing | PyMuPDF |

## Quick Start (Windows)

See **[SETUP.md](SETUP.md)** for the complete Windows step-by-step guide.

**Short version:**
```bash
# 1. Install Python 3.11, Node.js 20, Git

# 2. Backend
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
python ..\scripts\generate_resumes.py
python ..\scripts\seed_vectordb.py
uvicorn app.main:app --reload

# 3. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

## Project Structure

```
vectorhire-ai/
├── frontend/           Next.js 15 app
├── backend/
│   ├── app/
│   │   ├── api/        FastAPI routes (thin)
│   │   ├── core/       Config, settings, constants
│   │   ├── graph/      LangGraph workflow + 5 nodes
│   │   ├── services/   Business logic (6 services)
│   │   ├── rag/        ChromaDB + embeddings + retriever
│   │   ├── llm/        Gemini gateway + prompts + chains
│   │   ├── resume/     PDF parser + skill extractor
│   │   ├── schemas/    Pydantic models
│   │   ├── data/       Job data + ChromaDB storage
│   │   ├── agents/     [FUTURE] Multi-agent stubs
│   │   └── mcp/        [FUTURE] MCP tool stubs
│   └── requirements.txt
├── scripts/            Setup + utility scripts
├── docs/               Architecture docs
├── SETUP.md            Windows setup guide ← start here
└── README.md
```

## Key Scripts

| Script | Purpose |
|--------|---------|
| `scripts/generate_resumes.py` | Generate 5 sample PDF resumes |
| `scripts/seed_vectordb.py` | Populate ChromaDB (run before backend) |
| `scripts/test_pipeline.py` | Verify all components work |
| `scripts/reset_db.py` | Reset ChromaDB |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Service health check |
| `/api/v1/resume/upload` | POST | Parse resume PDF |
| `/api/v1/resume/analyze` | POST | Full AI analysis pipeline |
| `/api/v1/search/jobs` | POST | Semantic job search |

Interactive docs: http://localhost:8000/docs

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full layered architecture diagram.

## Future Roadmap

- Phase 2: Multi-agent orchestration (see [docs/future_agents.md](docs/future_agents.md))
- Phase 2: MCP tool integrations — LinkedIn live search, GitHub analysis (see [docs/future_mcp.md](docs/future_mcp.md))
- Phase 3: Browser-use autonomous job tracking
- Phase 3: Interview preparation agents
- Phase 4: Authentication + PostgreSQL persistence

## License

MIT — see [LICENSE](LICENSE)
