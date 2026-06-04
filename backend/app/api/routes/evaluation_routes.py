"""
Evaluation routes — RAG quality metrics endpoint.

POST /api/v1/evaluate
  Run Ragas + DeepEval on a query/context/response triple.
  Returns faithfulness, context_precision, context_recall, hallucination_score.

GET /api/v1/evaluate/history
  Return past evaluation results stored in the database.

Use cases:
  - Monitor RAG quality as you add more jobs to ChromaDB
  - Catch prompt regressions when you change LLM prompts
  - Demonstrate evaluation framework to interviewers / senior engineers
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

from app.evaluation.evaluation_service import get_evaluation_service
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["evaluation"])


class EvaluationRequest(BaseModel):
    query: str = Field(..., description="The search query that triggered retrieval")
    retrieved_context: list[str] = Field(
        ...,
        description="List of job description chunks returned by retrieval",
        min_length=1,
    )
    response: str = Field(
        ...,
        description="LLM-generated explanation / answer based on the context",
    )
    ground_truth: Optional[str] = Field(
        default=None,
        description="Optional ideal reference answer (improves context_recall accuracy)",
    )
    search_id: Optional[str] = Field(
        default=None,
        description="Optional job_searches.id to link this evaluation to a search",
    )


class EvaluationResponse(BaseModel):
    query: str
    faithfulness: float           # [0,1] — how well response sticks to context
    context_precision: float      # [0,1] — how relevant the retrieved chunks are
    context_recall: float         # [0,1] — coverage of needed context (needs ground_truth)
    hallucination_score: float    # [0,1] — lower is better
    evaluator_used: str


@router.post("/evaluate", response_model=EvaluationResponse)
def run_evaluation(request: EvaluationRequest):
    """
    Evaluate RAG quality for a query/context/response triple.

    Runs Ragas (faithfulness, precision, recall) and DeepEval (hallucination)
    in parallel. Falls back to LLM-based approximation if the evaluation
    libraries are not installed.
    """
    try:
        service = get_evaluation_service()
        result = service.evaluate(
            query=request.query,
            retrieved_context=request.retrieved_context,
            response=request.response,
            ground_truth=request.ground_truth,
            search_id=request.search_id,
        )
        return EvaluationResponse(
            query=result.query,
            faithfulness=result.faithfulness,
            context_precision=result.context_precision,
            context_recall=result.context_recall,
            hallucination_score=result.hallucination_score,
            evaluator_used=result.evaluator_used,
        )
    except Exception as e:
        logger.error(f"Evaluation endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get("/evaluate/history")
def evaluation_history(limit: int = 20):
    """Return the last N evaluation results from the database."""
    try:
        from app.db.session import SessionLocal
        from app.db.models import Evaluation

        with SessionLocal() as db:
            rows = (
                db.query(Evaluation)
                .order_by(Evaluation.created_at.desc())
                .limit(limit)
                .all()
            )
            return [
                {
                    "id": r.id,
                    "query": r.query,
                    "faithfulness": r.faithfulness,
                    "context_precision": r.context_precision,
                    "context_recall": r.context_recall,
                    "hallucination_score": r.hallucination_score,
                    "evaluator_used": r.evaluator_used,
                    "created_at": r.created_at.isoformat(),
                }
                for r in rows
            ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
