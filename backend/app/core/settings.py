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

    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-1.5-flash"
    gemini_temperature: float = 0.3
    gemini_max_tokens: int = 2048

    # Embedding
    embedding_model: str = "all-MiniLM-L6-v2"

    # ChromaDB
    chroma_persist_directory: Optional[str] = None  # resolved at runtime from constants

    # Retrieval
    default_top_k: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    return Settings()
