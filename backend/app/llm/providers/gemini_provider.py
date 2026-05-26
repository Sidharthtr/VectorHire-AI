import google.generativeai as genai
from app.core.settings import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_configured = False


def _ensure_configured() -> None:
    global _configured
    if not _configured:
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        _configured = True


def generate(prompt: str, temperature: float | None = None, max_tokens: int | None = None) -> str:
    _ensure_configured()
    settings = get_settings()
    model = genai.GenerativeModel(settings.gemini_model)
    generation_config = genai.types.GenerationConfig(
        temperature=temperature if temperature is not None else settings.gemini_temperature,
        max_output_tokens=max_tokens if max_tokens is not None else settings.gemini_max_tokens,
    )
    response = model.generate_content(prompt, generation_config=generation_config)
    return response.text


def generate_structured(prompt: str, temperature: float = 0.1) -> str:
    """Lower temperature for structured JSON output."""
    return generate(prompt, temperature=temperature)
