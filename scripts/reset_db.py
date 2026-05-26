"""
reset_db.py — Completely reset the ChromaDB vector database.

WARNING: This deletes ALL embedded data. Run seed_vectordb.py after this.

Usage:
  cd backend
  python ../scripts/reset_db.py
"""
import sys
import shutil
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
import os
os.chdir(Path(__file__).parent.parent / "backend")

from dotenv import load_dotenv
load_dotenv()

from app.core.constants import CHROMA_DIR, CHROMA_COLLECTION_JOBS, CHROMA_COLLECTION_RESUMES


def main():
    print("VectorHire AI — ChromaDB Reset")
    print("=" * 40)
    print(f"ChromaDB path: {CHROMA_DIR}")

    if not CHROMA_DIR.exists():
        print("ChromaDB directory doesn't exist. Nothing to reset.")
        return

    answer = input("\nWARNING: This will delete ALL vector data. Continue? [y/N]: ").strip().lower()
    if answer != "y":
        print("Cancelled.")
        return

    # Delete the entire chroma directory and recreate it
    shutil.rmtree(CHROMA_DIR)
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Deleted and recreated {CHROMA_DIR}")
    print("\nRun 'python scripts/seed_vectordb.py' to re-populate the database.")


if __name__ == "__main__":
    main()
