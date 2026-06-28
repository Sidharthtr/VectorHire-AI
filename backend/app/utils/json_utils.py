"""
JSON read/write helpers plus a tolerant LLM-output parser.

What it does:
- load_json / save_json: simple UTF-8 file IO with parent dir auto-create
- safe_parse_json(): strip markdown code fences before json.loads so messy LLM output still parses
- Returns (parsed, error_message) so callers can degrade gracefully on malformed JSON

Upstream (who imports this): app/llm/chains.py, app/evaluation/{ragas_evaluator,deepeval_evaluator}.py
Downstream (what this imports): json, pathlib, typing
"""
# json: standard library encoder/decoder for both file IO and LLM-response parsing
import json
# Path: typed filesystem operations for load_json / save_json
from pathlib import Path
# Any: JSON shape isn't statically known; Optional: error string is nullable
from typing import Any, Optional


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: Any, path: Path, indent: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def safe_parse_json(text: str) -> tuple[Any, Optional[str]]:
    """Parse JSON from LLM output that may contain markdown fences."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        cleaned = "\n".join(lines[1:-1]) if len(lines) > 2 else cleaned
    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as e:
        return None, str(e)
