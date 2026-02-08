import json
import os
from pathlib import Path
from typing import Any

import httpx


class ConfigManager:
    """Persist simple key/value config in a local JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path(".user_config.json")

    def load_config(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(k): "" if v is None else str(v) for k, v in data.items()}

    def save_config(self, updates: dict[str, str]) -> None:
        config = self.load_config()
        for key, value in updates.items():
            config[str(key)] = "" if value is None else str(value)
        self.path.write_text(
            json.dumps(config, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def apply_to_environ(self) -> None:
        # Never delete env vars and never override secrets already set by the runtime.
        # This prevents stale UI-saved keys from breaking server deployments.
        for key, value in self.load_config().items():
            if not value:
                continue
            if key.endswith("_API_KEY") and os.environ.get(key):
                continue
            os.environ[key] = value

    @staticmethod
    def fetch_available_models(base_url: str, api_key: str | None = None) -> list[str]:
        """Fetch model IDs from an OpenAI-compatible /models endpoint."""
        if not base_url:
            return []
        url = base_url.rstrip("/")
        if not url.endswith("/v1"):
            url = f"{url}/v1"
        url = f"{url}/models"

        headers: dict[str, str] = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            response = httpx.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
        except httpx.HTTPError:
            return []

        try:
            payload: Any = response.json()
        except ValueError:
            return []

        data = payload.get("data", []) if isinstance(payload, dict) else []
        model_ids = [
            item.get("id")
            for item in data
            if isinstance(item, dict) and item.get("id")
        ]
        return sorted(set(model_ids))
