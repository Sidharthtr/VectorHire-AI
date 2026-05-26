# VectorHire AI — RAG Pipeline

## Overview

VectorHire uses a two-phase RAG pipeline:

1. **Offline Ingestion** — runs once to populate ChromaDB
2. **Online Retrieval** — runs on every resume analysis request

---

## Offline Ingestion Pipeline

```
jobs.json
    │
    ▼
IngestionService.ingest_jobs_from_json()
    │
    ▼
Build job text (title + company + skills + description)
    │
    ▼
chunking.chunk_document()
    │  chunks text into 500-word segments with 50-word overlap
    ▼
embeddings.embed_batch()
    │  sentence-transformers all-MiniLM-L6-v2
    │  output: 384-dimensional float vectors
    ▼
vectordb.upsert_documents()
    │  stores in ChromaDB collection: vectorhire_jobs
    │  with metadata: title, company, skills, location, experience_level
    ▼
ChromaDB (local persistence at app/data/chroma/)
```

**Run this pipeline:** `python scripts/seed_vectordb.py`

---

## Online Retrieval Pipeline

```
Resume PDF + User Query
    │
    ▼
[Node 1] parse_resume_node
    │  PyMuPDF → raw text
    ▼
[Node 2] extract_skills_node
    │  Gemini API → ParsedResume (skills, experience, education)
    │  Fallback: heuristic skill matching against known skills list
    ▼
[Node 3] retrieve_jobs_node
    │  Build combined query: user query + resume summary + skills
    │  embed_text() → 384-dim query vector
    │  ChromaDB cosine similarity search → top-K job chunks
    ▼
[Node 4] rank_jobs_node
    │  For each retrieved job:
    │  Gemini API → matched_skills, missing_skills, fit_score
    │  Sort by fit_score descending
    ▼
[Node 5] explain_match_node
    │  Top 5 jobs: Gemini API → personalized explanation
    │  All jobs: aggregate missing skills
    │  Generate improvement suggestions
    │  Generate overall career summary
    ▼
AnalysisResponse (JSON)
```

---

## Embedding Model

- **Model:** `all-MiniLM-L6-v2`
- **Dimensions:** 384
- **Downloaded:** automatically on first run (~90MB)
- **Location:** cached in `~/.cache/huggingface/`
- **Similarity metric:** Cosine similarity

## ChromaDB Collections

| Collection | Contents | Count (approx) |
|------------|----------|----------------|
| `vectorhire_jobs` | Job description chunks + metadata | ~40-80 chunks (20 jobs × 2-4 chunks each) |
| `vectorhire_resumes` | Reserved for future resume indexing | — |

## Chunking Strategy

- **Chunk size:** 500 words
- **Overlap:** 50 words
- **Rationale:** Keeps each chunk semantically coherent while providing context overlap for boundary terms
