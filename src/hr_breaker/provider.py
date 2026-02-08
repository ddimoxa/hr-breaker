from pydantic_ai.models import Model
from pydantic_ai.profiles import ModelProfile
from pydantic_ai.profiles.qwen import qwen_model_profile

from hr_breaker.config import get_settings
from hr_breaker.openai_keys import get_openai_api_keys
from hr_breaker.openai_rotating_model import RotatingOpenAIModel


def _get_openai_model(model_name: str) -> Model:
    """Create an OpenAI-compatible model with API key rotation."""
    settings = get_settings()
    api_keys = get_openai_api_keys()

    # Detect if we should use a specific profile
    profile = None

    # Force disable tools for specific local models that hallucinate tool calls
    is_local = settings.openai_api_key == "ollama" or (
        settings.openai_base_url and "localhost" in settings.openai_base_url
    )

    # Models like Llama 3.2 3B or Vision models often fail at tool calling via Ollama's OpenAI API
    # Qwen 2.5 7B+ is generally okay.
    disable_tools = False
    if is_local:
        if "vision" in model_name.lower() or "llama3.2" in model_name.lower():
            disable_tools = True
    elif "vision" in model_name.lower():
        disable_tools = True

    if disable_tools:
        profile = ModelProfile(supports_tools=False)
    elif "qwen" in model_name.lower():
        profile = qwen_model_profile(model_name)

    # For local OpenAI-compatible servers (e.g. Ollama), allow empty keys.
    if not api_keys and not settings.openai_base_url:
        raise RuntimeError(
            "No OpenAI API keys found. Set OPENAI_API_KEYS / OPENAI_API_KEY in env."
        )

    return RotatingOpenAIModel(
        model_name,
        api_keys=api_keys,
        base_url=settings.openai_base_url,
        profile=profile,
    )


def get_agent_model() -> str | Model:
    """Get the smart model for complex tasks (optimization)."""
    settings = get_settings()
    return _get_openai_model(settings.openai_model)


def get_flash_model() -> str | Model:
    """Get the fast model for simple tasks (name extraction, parsing)."""
    settings = get_settings()
    return _get_openai_model(settings.openai_flash_model)


def get_vision_model() -> str | Model:
    """Get the vision model for visual reviews."""
    settings = get_settings()
    return _get_openai_model(settings.openai_vision_model)
