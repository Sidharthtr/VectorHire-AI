"""
seed_vectordb.py — Ingest all jobs into ChromaDB.

Run this BEFORE starting the backend server:
  cd backend
  python ../scripts/seed_vectordb.py
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
os.chdir(Path(__file__).parent.parent / "backend")

from dotenv import load_dotenv
load_dotenv()

from app.services.ingestion_service import IngestionService
from app.rag.vectordb import get_jobs_collection
from app.core.constants import JOBS_DIR

JOBS_JSON = JOBS_DIR / "jobs.json"


def main():
    print("=" * 50)
    print("VectorHire AI — ChromaDB Seeder")
    print("=" * 50)

    if not JOBS_JSON.exists():
        print(f"ERROR: jobs.json not found at {JOBS_JSON}")
        sys.exit(1)

    print(f"\nJob data: {JOBS_JSON}")

    col = get_jobs_collection()
    existing = col.count()
    if existing > 0:
        print(f"\nFound {existing} existing documents in ChromaDB.")
        answer = input("Re-seed? This will replace all existing data. [y/N]: ").strip().lower()
        if answer != "y":
            print("Skipping. Use scripts/reset_db.py first if you want a fresh seed.")
            return

        from app.rag.vectordb import reset_collection
        from app.core.constants import CHROMA_COLLECTION_JOBS
        reset_collection(CHROMA_COLLECTION_JOBS)
        print("Collection reset.")

    print("\nEmbedding model loading (first run downloads ~90MB)...")
    service = IngestionService()
    count = service.ingest_jobs_from_json(JOBS_JSON)

    final_count = get_jobs_collection().count()
    print(f"\n✓ Ingested {count} jobs → {final_count} document chunks in ChromaDB")
    print("\nReady! You can now start the backend server.")


if __name__ == "__main__":
    main()
