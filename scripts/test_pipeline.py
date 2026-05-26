"""
test_pipeline.py — End-to-end pipeline test without a real resume.

Tests:
1. ChromaDB health check
2. Embedding model
3. Semantic job search
4. LLM (Gemini) connectivity

Usage:
  cd backend
  python ../scripts/test_pipeline.py
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))
import os
os.chdir(Path(__file__).parent.parent / "backend")

from dotenv import load_dotenv
load_dotenv()


def test_chromadb():
    print("\n[1/4] Testing ChromaDB...")
    from app.rag.vectordb import get_jobs_collection
    col = get_jobs_collection()
    count = col.count()
    if count == 0:
        print("  WARN: ChromaDB is empty. Run scripts/seed_vectordb.py first.")
        return False
    print(f"  OK: {count} document chunks in jobs collection")
    return True


def test_embeddings():
    print("\n[2/4] Testing embedding model...")
    from app.rag.embeddings import embed_text
    vec = embed_text("Test embedding for AI backend engineer")
    assert len(vec) == 384, f"Expected 384 dims, got {len(vec)}"
    print(f"  OK: Embedding generated ({len(vec)} dimensions)")
    return True


def test_semantic_search():
    print("\n[3/4] Testing semantic job search...")
    from app.services.retrieval_service import RetrievalService
    service = RetrievalService()
    results = service.search_jobs("AI backend intern FastAPI LangGraph", top_k=3)
    if not results:
        print("  WARN: No results returned. Is ChromaDB seeded?")
        return False
    for job, score in results:
        print(f"  → {job.title} at {job.company} (score: {score:.3f})")
    print(f"  OK: {len(results)} jobs retrieved")
    return True


def test_llm():
    print("\n[4/4] Testing Gemini LLM connectivity...")
    from app.llm.gateway import get_llm_gateway
    gateway = get_llm_gateway()
    response = gateway.complete("Say 'VectorHire AI is ready!' and nothing else.")
    print(f"  Response: {response[:80]}")
    print("  OK: LLM responding")
    return True


def main():
    print("=" * 50)
    print("VectorHire AI — Pipeline Test")
    print("=" * 50)

    results = {
        "chromadb": False,
        "embeddings": False,
        "search": False,
        "llm": False,
    }

    try:
        results["chromadb"] = test_chromadb()
    except Exception as e:
        print(f"  FAIL: {e}")

    try:
        results["embeddings"] = test_embeddings()
    except Exception as e:
        print(f"  FAIL: {e}")

    if results["chromadb"]:
        try:
            results["search"] = test_semantic_search()
        except Exception as e:
            print(f"  FAIL: {e}")

    try:
        results["llm"] = test_llm()
    except Exception as e:
        print(f"  FAIL: {e}")

    print("\n" + "=" * 50)
    print("Results:")
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {status} {name}")

    all_pass = all(results.values())
    if all_pass:
        print("\n✓ All tests passed! Start the backend with: uvicorn app.main:app --reload")
    else:
        print("\n✗ Some tests failed. Check the output above.")


if __name__ == "__main__":
    main()
