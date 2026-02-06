from pydantic_ai import Agent, PromptedOutput

from hr_breaker.config import get_model_settings
from hr_breaker.models import JobPosting
from hr_breaker.provider import get_flash_model


SYSTEM_PROMPT = """You are a job posting parser. Extract structured information from job postings.

Extract:
- title: The job title
- company: Company name
- requirements: List of specific requirements (skills, experience, education)
- keywords: Technical keywords, tools, technologies mentioned
- description: Brief summary of the role

EXAMPLE JSON OUTPUT:
{
  "title": "Software Engineer",
  "company": "Google",
  "requirements": ["Python", "3+ years experience"],
  "keywords": ["Python", "FastAPI", "Docker"],
  "description": "Building great software."
}

Be thorough in extracting keywords - include all technologies, tools, frameworks, methodologies mentioned.
"""


def get_job_parser_agent() -> Agent:
    return Agent(
        get_flash_model(),
        output_type=PromptedOutput(JobPosting),
        system_prompt=SYSTEM_PROMPT
        + "\nIMPORTANT: Return ONLY a JSON object matching the requested schema.",
        model_settings=get_model_settings(),
        retries=5,
    )


async def parse_job_posting(text: str) -> JobPosting:
    """Parse job posting text into structured data."""
    agent = get_job_parser_agent()
    result = await agent.run(f"Parse this job posting:\n\n{text}")
    job = result.output
    job.raw_text = text
    return job
