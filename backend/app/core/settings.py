from __future__ import annotations
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "VectorHire AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # ── API ──────────────────────────────────────────────────────────────────
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # ── LLM (OpenRouter) ─────────────────────────────────────────────────────
    openrouter_api_key: str
    llm_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    llm_fallback_model: str = "google/gemma-4-31b-it:free"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048

    # ── Embeddings ───────────────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    # Local dev: USE_CHROMADB_SERVER=false → PersistentClient (embedded, no Docker needed)
    # Docker:    USE_CHROMADB_SERVER=true  → HttpClient connecting to the chromadb container
    use_chromadb_server: bool = False
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001
    chroma_persist_directory: Optional[str] = None  # resolved from constants when embedded

    # ── Retrieval ────────────────────────────────────────────────────────────
    default_top_k: int = 10
    retrieval_mode: str = "hybrid"  # "dense" | "sparse" | "hybrid"

    # ── PostgreSQL / SQLite ───────────────────────────────────────────────────
    # Local dev:  sqlite:///./app/data/vectorhire.db
    # Docker:     postgresql://vectorhire:vectorhire@postgres:5432/vectorhire
    database_url: str = "sqlite:///./app/data/vectorhire.db"

    # ── Redis ────────────────────────────────────────────────────────────────
    # Empty string = Redis disabled, all caches fall back to in-memory / JSON file.
    # Docker:  redis://redis:6379/0
    # Local:   redis://localhost:6379/0
    redis_url: str = ""

    # Redis TTLs (seconds)
    redis_ttl_resume: int = 604800   # 7 days  — resume skill extraction
    redis_ttl_search: int = 3600     # 1 hour  — job search results
    redis_ttl_llm: int = 86400       # 24 hours — LLM response cache

    # ── Job Ingestion APIs ───────────────────────────────────────────────────
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
