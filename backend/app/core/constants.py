"""
Hard-coded constants shared across layers (paths, ChromaDB names, retrieval limits).

What it does:
- Resolves BASE_DIR / DATA_DIR / CHROMA_DIR so file storage works regardless of CWD.
- Names the two ChromaDB collections (jobs + resumes) used everywhere.
- Holds non-tunable numbers: embedding dim, chunk size, top-k caps, file-size limit.

Upstream (who imports this): app.rag.* (vectordb, embeddings, chunking, retrievers),
app.graph.builder, app.graph.workflow, app.graph.nodes.retrieve_jobs_node,
app.utils.file_utils, app.api.dependencies, app.api.routes.debug_routes,
app.services.resume_service, app.services.retrieval_service.
Downstream (what this imports): pathlib.Path only — zero runtime dependencies.
"""
# Path: build absolute filesystem paths anchored at the backend/app package
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
JOBS_DIR = DATA_DIR / "jobs"
RESUMES_DIR = DATA_DIR / "resumes"
CHROMA_DIR = DATA_DIR / "chroma"
SAMPLES_DIR = DATA_DIR / "samples"

# ChromaDB
CHROMA_COLLECTION_JOBS = "vectorhire_jobs"
CHROMA_COLLECTION_RESUMES = "vectorhire_resumes"

# Embedding
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

# Retrieval
DEFAULT_TOP_K = 10
MAX_TOP_K = 20
SIMILARITY_THRESHOLD = 0.3

# LangGraph
WORKFLOW_RECURSION_LIMIT = 10

# File upload
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".pdf"}

# Chunking
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
