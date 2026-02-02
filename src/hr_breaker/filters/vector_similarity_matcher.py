from google import genai
from google.genai import types

from hr_breaker.config import get_settings
from hr_breaker.filters.base import BaseFilter
from hr_breaker.filters.registry import FilterRegistry
from hr_breaker.models import FilterResult, JobPosting, OptimizedResume, ResumeSource


@FilterRegistry.register
class VectorSimilarityMatcher(BaseFilter):
    """Vector similarity filter using Google Gemini embeddings."""

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

        if not settings.google_api_key:
            # Fallback to local Ollama embeddings if available
            if settings.openai_base_url and "localhost" in settings.openai_base_url:
                try:
                    from openai import AsyncOpenAI

                    client = AsyncOpenAI(
                        base_url=settings.openai_base_url, api_key="ollama"
                    )

                    resume_text = optimized.pdf_text
                    job_text = (
                        f"{job.title} {job.description} {' '.join(job.requirements)}"
                    )

                    # Get embeddings in parallel
                    import asyncio

                    # Use nomic-embed-text which is standard for local RAG
                    model = "nomic-embed-text"

                    e1_resp, e2_resp = await asyncio.gather(
                        client.embeddings.create(input=resume_text, model=model),
                        client.embeddings.create(input=job_text, model=model),
                    )

                    embeddings = [e1_resp.data[0].embedding, e2_resp.data[0].embedding]

                except Exception as e:
                    return FilterResult(
                        filter_name=self.name,
                        passed=True,
                        score=1.0,
                        threshold=self.threshold,
                        issues=[
                            f"Skipped: No Google API key and local fallback failed: {e}"
                        ],
                        suggestions=[
                            "Add GOOGLE_API_KEY to .env to enable semantic matching"
                        ],
                    )
            else:
                return FilterResult(
                    filter_name=self.name,
                    passed=True,
                    score=1.0,
                    threshold=self.threshold,
                    issues=["Skipped: No Google API key provided"],
                    suggestions=[
                        "Add GOOGLE_API_KEY to .env to enable semantic matching"
                    ],
                )
        else:
            client = genai.Client(api_key=settings.google_api_key)
            resume_text = optimized.pdf_text
            job_text = f"{job.title} {job.description} {' '.join(job.requirements)}"

            try:
                result = client.models.embed_content(
                    model=settings.embedding_model,
                    contents=[resume_text, job_text],
                    config=types.EmbedContentConfig(
                        task_type="SEMANTIC_SIMILARITY",
                        output_dimensionality=settings.embedding_output_dimensionality,
                    ),
                )
                embeddings = [emb.values for emb in result.embeddings]
            except Exception as e:
                return FilterResult(
                    filter_name=self.name,
                    passed=True,
                    score=1.0,
                    threshold=self.threshold,
                    issues=[f"Embedding API error: {e}"],
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
