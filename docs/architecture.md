# VectorHire AI — System Architecture

## Overview

VectorHire AI is a **modular, production-oriented AI workflow platform**. It uses a strict layered architecture to ensure each concern is isolated and future-extensible.

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 15)                     │
│              Upload → Dashboard → Results Pages              │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP (REST)
┌─────────────────────────▼───────────────────────────────────┐
│                   API Layer (FastAPI)                         │
│           /api/v1/resume  /api/v1/search  /health            │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Orchestration Layer (LangGraph)                  │
│  parse_resume → extract_skills → retrieve_jobs →             │
│  rank_jobs → explain_match                                   │
└──────────┬──────────────┬──────────────┬────────────────────┘
           │              │              │
┌──────────▼───┐  ┌───────▼──────┐  ┌───▼──────────────────┐
│  Resume Layer│  │  RAG Layer   │  │    LLM Layer          │
│  parser      │  │  embeddings  │  │    gateway            │
│  extractor   │  │  vectordb    │  │    prompts            │
└──────────────┘  │  retriever   │  │    chains             │
                  │  chunking    │  │    gemini_provider    │
                  └──────────────┘  └───────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│                   Services Layer                           │
│  ResumeService  RetrievalService  RankingService          │
│  ExplanationService  IngestionService  EmbeddingService   │
└──────────────────────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────────┐
│                  Data / Infrastructure                     │
│  ChromaDB (local)   sentence-transformers   Gemini API   │
└──────────────────────────────────────────────────────────┘
```

## Layer Responsibilities

### API Layer (`app/api/`)
- Thin FastAPI route handlers
- Input validation via Pydantic and dependency injection
- No business logic — delegates directly to services or the LangGraph workflow

### Orchestration Layer (`app/graph/`)
- LangGraph `StateGraph` with typed `WorkflowState`
- 5 nodes, each isolated and independently replaceable
- Future-convertible into autonomous agents

### Services Layer (`app/services/`)
- Business logic, coordination between RAG/LLM layers
- No HTTP concerns, no database ORM

### RAG Layer (`app/rag/`)
- `embeddings.py` — sentence-transformers inference
- `vectordb.py` — ChromaDB client and collection management
- `retriever.py` — query embedding + vector search
- `chunking.py` — document chunking strategy
- `similarity.py` — cosine similarity utilities

### LLM Layer (`app/llm/`)
- `gateway.py` — single entry point for all LLM calls
- `providers/gemini_provider.py` — Gemini API wrapper
- `prompts.py` — all prompt templates
- `chains.py` — prompt + LLM call + output parsing

### Resume Layer (`app/resume/`)
- `parser.py` — PyMuPDF PDF text extraction
- `extractor.py` — skill extraction (LLM + heuristic fallback)

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| LangGraph instead of sequential calls | Future multi-agent extensibility |
| Gateway pattern for LLM | Swap providers without touching business logic |
| ChromaDB local | Zero-infrastructure setup for MVP |
| sentence-transformers local | No API key needed for embeddings |
| Pydantic everywhere | Type safety across all boundaries |
| Async FastAPI | Non-blocking LLM calls |
