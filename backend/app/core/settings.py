from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    # App
    app_name: str = "VectorHire AI"
    app_version: str = "0.1.0"
    debug: bool = False

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # LLM (OpenRouter)
    openrouter_api_key: str
    llm_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    llm_fallback_model: str = "qwen/qwen3-32b:free"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 2048

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # ChromaDB
    chroma_persist_directory: Optional[str] = None  # resolved at runtime from constants

    # Retrieval
    default_top_k: int = 10

    # Database
    database_url: str = "sqlite:///./app/data/vectorhire.db"

    # Job Ingestion APIs (free tier)
    adzuna_app_id: str = ""
    adzuna_api_key: str = ""
    # arbeitnow requires no key

    # Retrieval mode
    retrieval_mode: str = "hybrid"  # "dense" | "sparse" | "hybrid"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
