import asyncio

from hr_breaker.config import get_settings
from hr_breaker.filters.base import BaseFilter
from hr_breaker.filters.registry import FilterRegistry
from hr_breaker.models import FilterResult, JobPosting, OptimizedResume, ResumeSource
from hr_breaker.openai_keys import get_openai_api_keys


@FilterRegistry.register
class VectorSimilarityMatcher(BaseFilter):
    """Vector similarity filter using OpenAI (or OpenAI-compatible) embeddings."""

    name = "VectorSimilarityMatcher"
    priority = 6

    @property
    def threshold(self) -> float:
        return get_settings().filter_vector_threshold

    async def evaluate(
        self,
        optimized: OptimizedResume,
        job: JobPosting,
        source: ResumeSource,
    ) -> FilterResult:
        settings = get_settings()

        if optimized.pdf_text is None:
            return FilterResult(
                filter_name=self.name,
                passed=False,
                score=0.0,
                threshold=self.threshold,
                issues=["No PDF text available"],
                suggestions=["Ensure PDF compilation succeeds"],
            )

        resume_text = optimized.pdf_text
        job_text = f"{job.title} {job.description} {' '.join(job.requirements)}"

        # Prefer OpenAI keys. For local OpenAI-compatible servers (Ollama),
        # allow a placeholder key and use a local embedding model.
        api_keys = get_openai_api_keys()
        is_local = bool(settings.openai_base_url and "localhost" in settings.openai_base_url)

        embed_model = settings.openai_embedding_model
        embed_dimensions = settings.openai_embedding_dimensions
        if is_local:
            embed_model = "nomic-embed-text"
            embed_dimensions = None
            api_keys = ["ollama"]

        if not api_keys:
            return FilterResult(
                filter_name=self.name,
                passed=True,
                score=1.0,
                threshold=self.threshold,
                issues=["Skipped: No OpenAI API keys provided"],
                suggestions=["Set OPENAI_API_KEYS / OPENAI_API_KEY in .env.openai_keys"],
            )

        last_err: Exception | None = None
        embeddings: list[list[float]] | None = None

        for key in api_keys:
            try:
                from openai import AsyncOpenAI

                client = AsyncOpenAI(api_key=key, base_url=settings.openai_base_url)

                kwargs = {"model": embed_model}
                if embed_dimensions is not None:
                    kwargs["dimensions"] = embed_dimensions

                e1_resp, e2_resp = await asyncio.gather(
                    client.embeddings.create(input=resume_text, **kwargs),
                    client.embeddings.create(input=job_text, **kwargs),
                )
                embeddings = [e1_resp.data[0].embedding, e2_resp.data[0].embedding]
                break
            except Exception as e:
                last_err = e
                continue

        if embeddings is None:
            return FilterResult(
                filter_name=self.name,
                passed=True,
                score=1.0,
                threshold=self.threshold,
                issues=[f"Embedding API error (skipped): {last_err}"],
                suggestions=[],
            )

        # Cosine similarity
        e1, e2 = embeddings[0], embeddings[1]
        dot = sum(a * b for a, b in zip(e1, e2))
        norm1 = sum(a * a for a in e1) ** 0.5
        norm2 = sum(b * b for b in e2) ** 0.5
        similarity = dot / (norm1 * norm2) if norm1 and norm2 else 0.0

        # Normalize to 0-1 (cosine similarity is -1 to 1)
        score = (similarity + 1) / 2

        issues = []
        if score < self.threshold:
            issues.append(
                f"Low semantic vector similarity to job posting ({score:.2f})"
            )

        return FilterResult(
            filter_name=self.name,
            passed=score >= self.threshold,
            score=score,
            threshold=self.threshold,
            issues=issues,
            suggestions=[],
        )
