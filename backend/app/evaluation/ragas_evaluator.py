"""
Ragas-style retrieval evaluation with a graceful LLM-only fallback.

What it does:
- evaluate_with_ragas(): scores faithfulness, context_precision, context_recall in [0, 1]
- Uses real ragas library if installed, otherwise falls back to LLM judge prompts
- Returns a RagasMetrics dataclass consumed by EvaluationService

Upstream (who imports this): app/evaluation/evaluation_service.py
Downstream (what this imports): dataclasses, app.core.logging; (lazy) ragas/datasets, app.llm.gateway, app.utils.json_utils
"""
from __future__ import annotations

# dataclass: lightweight, typed RagasMetrics return container
from dataclasses import dataclass
# Optional: ground_truth is optional (needed for context_recall only)
from typing import Optional

# get_logger: log fallback transitions and evaluator errors
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RagasMetrics:
    faithfulness: float
    context_precision: float
    context_recall: float


def evaluate_with_ragas(
    query: str,
    retrieved_context: list[str],
    response: str,
    ground_truth: Optional[str] = None,
) -> RagasMetrics:
    """
    Evaluate RAG quality using Ragas metrics.

    Args:
        query:              the original search query
        retrieved_context:  list of text chunks returned by retrieval
        response:           the LLM's generated answer/explanation
        ground_truth:       optional reference answer (improves recall measurement)

    Returns:
        RagasMetrics with scores in [0.0, 1.0]. Higher = better.
    """
    try:
        return _evaluate_ragas_native(query, retrieved_context, response, ground_truth)
    except ImportError:
        logger.info("ragas not installed — using LLM-based approximation")
        return _evaluate_ragas_llm_fallback(query, retrieved_context, response)
    except Exception as e:
        logger.warning(f"Ragas evaluation failed: {e} — using fallback")
        return _evaluate_ragas_llm_fallback(query, retrieved_context, response)


def _evaluate_ragas_native(
    query: str,
    retrieved_context: list[str],
    response: str,
    ground_truth: Optional[str],
) -> RagasMetrics:
    """Use the real ragas library when available."""
    from ragas import evaluate
    from ragas.metrics import faithfulness, context_precision, context_recall
    from datasets import Dataset

    data = {
        "question":  [query],
        "answer":    [response],
        "contexts":  [retrieved_context],
    }
    if ground_truth:
        data["ground_truth"] = [ground_truth]
        metrics = [faithfulness, context_precision, context_recall]
    else:
        metrics = [faithfulness, context_precision]

    dataset = Dataset.from_dict(data)
    result = evaluate(dataset, metrics=metrics)

    return RagasMetrics(
        faithfulness=float(result.get("faithfulness", 0.0)),
        context_precision=float(result.get("context_precision", 0.0)),
        context_recall=float(result.get("context_recall", 0.0)) if ground_truth else 0.0,
    )


def _evaluate_ragas_llm_fallback(
    query: str,
    retrieved_context: list[str],
    response: str,
) -> RagasMetrics:
    """
    LLM-based approximation of Ragas metrics.
    Three separate prompts, one per metric. Scores are 0.0–1.0 floats.
    Not as rigorous as real Ragas but good enough for development feedback.
    """
    from app.llm.gateway import generate_structured
    from app.utils.json_utils import safe_parse_json

    context_text = "\n---\n".join(retrieved_context[:5])  # cap to avoid token overflow

    # --- Faithfulness: does the response only say things the context supports? ---
    faithfulness_prompt = f"""
You are a RAG evaluation judge. Score whether the RESPONSE is faithful to the CONTEXT.
Faithful means: every factual claim in the response can be found in the context.

QUERY: {query}
CONTEXT: {context_text}
RESPONSE: {response}

Return JSON only: {{"score": <float 0.0-1.0>, "reason": "<one sentence>"}}
Score 1.0 = fully faithful, 0.0 = contradicts context.
"""

    # --- Context Precision: are retrieved chunks relevant to the query? ---
    precision_prompt = f"""
You are a RAG evaluation judge. Score how relevant the CONTEXT chunks are to the QUERY.

QUERY: {query}
CONTEXT: {context_text}

Return JSON only: {{"score": <float 0.0-1.0>, "reason": "<one sentence>"}}
Score 1.0 = all chunks are highly relevant, 0.0 = irrelevant noise.
"""

    def _score(prompt: str) -> float:
        try:
            raw = generate_structured(prompt)
            data = safe_parse_json(raw)
            if data:
                return max(0.0, min(1.0, float(data.get("score", 0.5))))
        except Exception as e:
            logger.warning(f"LLM eval scoring error: {e}")
        return 0.5  # neutral fallback

    return RagasMetrics(
        faithfulness=_score(faithfulness_prompt),
        context_precision=_score(precision_prompt),
        context_recall=0.0,  # recall needs ground truth, omit in fallback
    )
