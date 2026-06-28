"""
Project-wide logger factory — one handler, consistent format, stdout sink.

What it does:
- get_logger(name) returns a configured logger with the VectorHire format.
- Guards against duplicate handlers when modules re-import.
- Exposes a default `logger` instance for quick use.

Upstream (who imports this): nearly every module — ingestion, llm, resume, graph,
rag, db, services, api routes, core.redis_client. Anywhere we log.
Downstream (what this imports): stdlib logging + sys (stdout stream) + typing.Optional.
"""
# logging: Python stdlib logger — we build a Logger with a StreamHandler
import logging
# sys: needed to point the StreamHandler at sys.stdout (not the default stderr)
import sys
# Optional: `name` arg may be None → falls back to the "vectorhire" root logger
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    logger = logging.getLogger(name or "vectorhire")
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


logger = get_logger("vectorhire")
