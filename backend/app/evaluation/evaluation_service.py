"""
Top-level RAG evaluation service combining Ragas + DeepEval into one call.

What it does:
- Runs Ragas (faithfulness/precision/recall) and DeepEval (hallucination) concurrently
- Merges metrics into EvaluationResult and persists a row to the evaluations table
- Exposes get_evaluation_service() factory for FastAPI dependency injection

Upstream (who imports this): app/api/routes/evaluation_routes.py
Downstream (what this imports): concurrent.futures, app.evaluation.{ragas_evaluator,deepeval_evaluator}, app.db.{session,models}, app.core.logging
"""
from __future__ import annotations

# ThreadPoolExecutor/as_completed: run Ragas + DeepEval in parallel to cut wall time
from concurrent.futures import ThreadPoolExecutor, as_completed
# dataclass/asdict: typed EvaluationResult container with easy dict export for JSON responses
from dataclasses import dataclass, asdict
# Optional: ground_truth and search_id are nullable arguments
from typing import Optional

# evaluate_with_ragas / RagasMetrics: faithfulness + precision + recall scorer
from app.evaluation.ragas_evaluator import evaluate_with_ragas, RagasMetrics
# evaluate_hallucination / DeepEvalMetrics: hallucination scorer (lower is better)
from app.evaluation.deepeval_evaluator import evaluate_hallucination, DeepEvalMetrics
# get_logger: warn on evaluator failures and DB persistence errors
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class EvaluationResult:
    """Combined evaluation output from Ragas + DeepEval."""
    query: str
    faithfulness: float          # Ragas — [0,1] higher is better
    context_precision: float     # Ragas — [0,1] higher is better
    context_recall: float        # Ragas — [0,1] higher is better (needs ground truth)
    hallucination_score: float   # DeepEval — [0,1] LOWER is better
    evaluator_used: str          # "ragas+deepeval" or "llm_based"

    def to_dict(self) -> dict:
        return asdict(self)


class EvaluationService:
    def evaluate(
        self,
        query: str,
        retrieved_context: list[str],
        response: str,
        ground_truth: Optional[str] = None,
        search_id: Optional[str] = None,
    ) -> EvaluationResult:
        """
        Run Ragas and DeepEval in parallel and combine results.

        Args:
            query:              the search query
            retrieved_context:  list of retrieved job descriptions / text chunks
            response:           LLM's generated response/explanation
            ground_truth:       optional reference answer (improves recall)
            search_id:          optional DB foreign key to link to a job_searches row

        Returns:
            EvaluationResult with all metrics filled in.
        """
        ragas_metrics: Optional[RagasMetrics] = None
        deepeval_metrics: Optional[DeepEvalMetrics] = None

        # Run both evaluators in parallel to cut latency in half
        with ThreadPoolExecutor(max_workers=2) as executor:
            fut_ragas = executor.submit(
                evaluate_with_ragas, query, retrieved_context, response, ground_truth
            )
            fut_deep = executor.submit(
                evaluate_hallucination, query, retrieved_context, response
            )

            for future in as_completed([fut_ragas, fut_deep]):
                if future is fut_ragas:
                    try:
                        ragas_metrics = future.result()
                    except Exception as e:
                        logger.warning(f"Ragas evaluation error: {e}")
                        ragas_metrics = RagasMetrics(
                            faithfulness=0.0,
                            context_precision=0.0,
                            context_recall=0.0,
                        )
                else:
                    try:
                        deepeval_metrics = future.result()
                    except Exception as e:
                        logger.warning(f"DeepEval evaluation error: {e}")
                        deepeval_metrics = DeepEvalMetrics(hallucination_score=0.1)

        result = EvaluationResult(
            query=query,
            faithfulness=ragas_metrics.faithfulness if ragas_metrics else 0.0,
            context_precision=ragas_metrics.context_precision if ragas_metrics else 0.0,
            context_recall=ragas_metrics.context_recall if ragas_metrics else 0.0,
            hallucination_score=deepeval_metrics.hallucination_score if deepeval_metrics else 0.1,
            evaluator_used="llm_based",
        )

        # Persist to DB (non-blocking — log and continue on failure)
        self._persist(result, search_id)
        return result

    def _persist(self, result: EvaluationResult, search_id: Optional[str]) -> None:
        """Save evaluation metrics to the evaluations table."""
        try:
            from app.db.session import SessionLocal
            from app.db.models import Evaluation

            with SessionLocal() as db:
                row = Evaluation(
                    search_id=search_id,
                    query=result.query,
                    faithfulness=result.faithfulness,
                    context_precision=result.context_precision,
                    context_recall=result.context_recall,
                    hallucination_score=result.hallucination_score,
                    evaluator_used=result.evaluator_used,
                )
                db.add(row)
                db.commit()
                logger.debug(f"Evaluation saved (search_id={search_id})")
        except Exception as e:
            logger.warning(f"Failed to persist evaluation: {e}")


def get_evaluation_service() -> EvaluationService:
    return EvaluationService()
