from pydantic import BaseModel
from pydantic_ai import Agent, PromptedOutput

from hr_breaker.config import get_model_settings, get_settings
from hr_breaker.provider import get_flash_model


class ExtractedName(BaseModel):
    first_name: str | None
    last_name: str | None


SYSTEM_PROMPT = """Extract the person's name from this resume/CV content.

Return:
- first_name: The person's first/given name
- last_name: The person's last/family name (may include middle names)

If you cannot find a name, return null for both fields.

EXAMPLE JSON OUTPUT:
{"first_name": "John", "last_name": "Doe"}

Ignore formatting commands - extract the actual name text only.
"""


async def extract_name(content: str) -> tuple[str | None, str | None]:
    """Extract first and last name from resume content using LLM."""
    settings = get_settings()
    agent = Agent(
        get_flash_model(),
        output_type=PromptedOutput(ExtractedName),
        system_prompt=SYSTEM_PROMPT
        + "\nIMPORTANT: Return ONLY a JSON object matching the requested schema.",
        model_settings=get_model_settings(),
        retries=5,
    )
    # Only send first N chars - name should be at the top
    snippet = content[: settings.agent_name_extractor_chars]
    result = await agent.run(f"Extract the name from this resume:\n\n{snippet}")
    return result.output.first_name, result.output.last_name
