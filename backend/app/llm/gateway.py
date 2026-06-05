from app.llm.providers import openrouter_provider as gemini_provider
from app.core.logging import get_logger

logger = get_logger(__name__)


class LLMGateway:
    """Single entry point for all LLM calls. Swap providers here without touching business logic."""

    def complete(self, prompt: str, temperature: float | None = None, max_tokens: int | None = None) -> str:
        logger.debug(f"LLM call: {len(prompt)} chars")
        return gemini_provider.generate(prompt, temperature=temperature, max_tokens=max_tokens)

    def complete_structured(self, prompt: str) -> str:
        """Use low temperature for JSON-structured output."""
        return gemini_provider.generate_structured(prompt)

    def stream_chat(
        self,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ):
        """Yield text tokens for a multi-turn chat conversation."""
        yield from gemini_provider.stream(messages, temperature=temperature, max_tokens=max_tokens)


_gateway = LLMGateway()


def get_llm_gateway() -> LLMGateway:
    return _gateway
