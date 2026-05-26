# VectorHire AI — Backend

FastAPI + LangGraph + ChromaDB + Gemini backend.

## Quick Start

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env         # then add GEMINI_API_KEY
python ..\scripts\seed_vectordb.py
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Layer Map

```
app/api/       → FastAPI routes (thin controllers)
app/graph/     → LangGraph workflow (5 nodes)
app/services/  → Business logic
app/rag/       → Embeddings + ChromaDB
app/llm/       → Gemini API gateway + prompts
app/resume/    → PDF parsing + skill extraction
app/schemas/   → Pydantic models
app/utils/     → File, text, JSON utilities
```

See [../docs/architecture.md](../docs/architecture.md) for full architecture.
