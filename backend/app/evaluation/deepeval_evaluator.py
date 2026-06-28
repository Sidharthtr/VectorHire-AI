"""
Hallucination scorer for LLM responses with a graceful LLM-only fallback.

What it does:
- evaluate_hallucination(): returns DeepEvalMetrics.hallucination_score in [0, 1] (lower is better)
- Uses real deepeval library if installed, otherwise falls back to an LLM judge prompt
- Mirrors ragas_evaluator.py's fallback pattern so the app runs without optional deps

Upstream (who imports this): app/evaluation/evaluation_service.py
Downstream (what this imports): dataclasses, app.core.logging; (lazy) deepeval, app.llm.gateway, app.utils.json_utils
"""
from __future__ import annotations

# dataclass: typed return container for hallucination_score
from dataclasses import dataclass

# get_logger: log fallback transitions and scoring failures
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class DeepEvalMetrics:
    hallucination_score: float  # [0, 1] — lower is better


def evaluate_hallucination(
    query: str,
    retrieved_context: list[str],
    response: str,
) -> DeepEvalMetrics:
    """
    Measure how much the LLM response hallucinates beyond the retrieved context.

    Args:
        query:              original search query
        retrieved_context:  list of retrieved text chunks fed to the LLM
        response:           LLM's generated answer

    Returns:
        DeepEvalMetrics with hallucination_score in [0.0, 1.0].
        Lower is better (0 = no hallucination).
    """
    try:
        return _evaluate_deepeval_native(query, retrieved_context, response)
    except ImportError:
        logger.info("deepeval not installed — using LLM-based hallucination approximation")
        return _evaluate_deepeval_llm_fallback(query, retrieved_context, response)
    except Exception as e:
        logger.warning(f"DeepEval hallucination check failed: {e} — using fallback")
        return _evaluate_deepeval_llm_fallback(query, retrieved_context, response)


def _evaluate_deepeval_native(
    query: str,
    retrieved_context: list[str],
    response: str,
) -> DeepEvalMetrics:
    """Use the real deepeval library when available."""
    from deepeval import evaluate as deval
    from deepeval.metrics import HallucinationMetric
    from deepeval.test_case import LLMTestCase

    test_case = LLMTestCase(
        input=query,
        actual_output=response,
        context=retrieved_context,
    )
    metric = HallucinationMetric(threshold=0.5)
    metric.measure(test_case)
    return DeepEvalMetrics(hallucination_score=float(metric.score))


def _evaluate_deepeval_llm_fallback(
    query: str,
    retrieved_context: list[str],
    response: str,
) -> DeepEvalMetrics:
    """
    LLM-based hallucination approximation.
    Asks the LLM to identify claims in the response NOT supported by the context.
    """
    from app.llm.gateway import generate_structured
    from app.utils.json_utils import safe_parse_json

    context_text = "\n---\n".join(retrieved_context[:5])

    prompt = f"""
You are a hallucination detection judge.

TASK: Check whether the RESPONSE contains facts NOT supported by the CONTEXT.

QUERY: {query}
CONTEXT: {context_text}
RESPONSE: {response}

Count the number of factual claims in the response.
Count how many of those claims are NOT in the context (hallucinated).

Return JSON only:
{{
  "total_claims": <int>,
  "hallucinated_claims": <int>,
  "hallucination_score": <float 0.0-1.0>,
  "examples": ["<hallucinated claim if any>"]
}}

hallucination_score = hallucinated_claims / total_claims (0 if total_claims = 0).
"""
    try:
        raw = generate_structured(prompt)
        data = safe_parse_json(raw)
        if data:
            score = max(0.0, min(1.0, float(data.get("hallucination_score", 0.1))))
            return DeepEvalMetrics(hallucination_score=score)
    except Exception as e:
        logger.warning(f"LLM hallucination scoring error: {e}")

    return DeepEvalMetrics(hallucination_score=0.1)  # optimistic default
