from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.profiles import ModelProfile
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.profiles.qwen import qwen_model_profile

from hr_breaker.config import get_settings


def _get_openai_model(model_name: str) -> OpenAIModel:
    """Helper to create OpenAI model with appropriate profile for Ollama."""
    settings = get_settings()
    provider = OpenAIProvider(
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key or "ollama",
    )

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

    return OpenAIModel(
        model_name,
        provider=provider,
        profile=profile,
    )


def get_agent_model() -> str | Model:
    """Get the smart model for complex tasks (optimization)."""
    settings = get_settings()
    if settings.llm_provider == "openai":
        return _get_openai_model(settings.openai_model)
    return f"google-gla:{settings.gemini_pro_model}"


def get_flash_model() -> str | Model:
    """Get the fast model for simple tasks (name extraction, parsing)."""
    settings = get_settings()
    if settings.llm_provider == "openai":
        return _get_openai_model(settings.openai_flash_model)
    return f"google-gla:{settings.gemini_flash_model}"


def get_vision_model() -> str | Model:
    """Get the vision model for visual reviews."""
    settings = get_settings()
    if settings.llm_provider == "openai":
        return _get_openai_model(settings.openai_vision_model)
    return f"google-gla:{settings.gemini_flash_model}"
