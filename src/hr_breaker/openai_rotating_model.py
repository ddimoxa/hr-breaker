from __future__ import annotations

import itertools
from collections.abc import AsyncIterator
from typing import Any

from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models import Model
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.profiles import ModelProfile
from pydantic_ai.providers.openai import OpenAIProvider


def _is_retryable_openai_http_error(e: ModelHTTPError) -> bool:
    # Common retry candidates for key rotation: auth issues, rate limits, inactive billing.
    if e.status_code in (401, 403, 429):
        return True
    body = e.body
    if isinstance(body, dict):
        code = body.get("code") or body.get("type")
        if code in {"billing_not_active", "insufficient_quota", "rate_limit_exceeded"}:
            return True
        msg = body.get("message") or ""
        if isinstance(msg, str) and "billing" in msg.lower():
            return True
    return False


class RotatingOpenAIModel(Model):
    """OpenAI model wrapper that retries the same request with multiple API keys.

    This solves the "single source of truth" requirement by taking keys from env_file
    and avoids UI/config persistence issues. Rotation happens per request, round-robin.
    """

    def __init__(
        self,
        model_name: str,
        *,
        api_keys: list[str],
        base_url: str | None,
        profile: ModelProfile | None = None,
    ) -> None:
        super().__init__(profile=profile)
        self._model_name = model_name
        self._api_keys = [k for k in api_keys if k]
        self._base_url = base_url
        self._rr = itertools.count()

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def system(self) -> str:
        return "openai"

    @property
    def base_url(self) -> str | None:
        return self._base_url

    def _make_model(self, api_key: str | None) -> OpenAIModel:
        provider = OpenAIProvider(
            base_url=self._base_url,
            api_key=api_key,
        )
        return OpenAIModel(self._model_name, provider=provider, profile=self.profile)

    def _iter_keys(self) -> list[str | None]:
        # If no keys provided (local OpenAI-compatible), still create a provider.
        if not self._api_keys:
            return [None]
        n = len(self._api_keys)
        start = next(self._rr) % n
        return [self._api_keys[(start + i) % n] for i in range(n)]

    async def request(  # type: ignore[override]
        self,
        messages: list[Any],
        model_settings: Any,
        model_request_parameters: Any,
    ) -> Any:
        last_err: Exception | None = None
        for key in self._iter_keys():
            try:
                model = self._make_model(key)
                return await model.request(messages, model_settings, model_request_parameters)
            except ModelHTTPError as e:
                last_err = e
                if _is_retryable_openai_http_error(e):
                    continue
                raise
        assert last_err is not None
        raise last_err

    async def request_stream(  # type: ignore[override]
        self,
        messages: list[Any],
        model_settings: Any,
        model_request_parameters: Any,
        run_context: Any = None,
    ) -> AsyncIterator[Any]:
        last_err: Exception | None = None
        for key in self._iter_keys():
            try:
                model = self._make_model(key)
                async for chunk in model.request_stream(
                    messages, model_settings, model_request_parameters, run_context=run_context
                ):
                    yield chunk
                return
            except ModelHTTPError as e:
                last_err = e
                if _is_retryable_openai_http_error(e):
                    continue
                raise
        assert last_err is not None
        raise last_err
