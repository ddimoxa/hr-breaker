import os
import re
from typing import Iterable


_SPLIT_RE = re.compile(r"[,\n;\t ]+")


def _split_keys(raw: str) -> list[str]:
    parts = [p.strip() for p in _SPLIT_RE.split(raw or "") if p.strip()]
    # Preserve order but drop duplicates
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def get_openai_api_keys(env: dict[str, str] | None = None) -> list[str]:
    """Return OpenAI API keys from environment.

    Supported formats:
    - OPENAI_API_KEYS="k1,k2,k3" (comma/space/newline separated)
    - OPENAI_API_KEY="k1" (single key fallback)
    - OPENAI_API_KEY_1 / OPENAI_API_KEY_2 / ... (ordered)
    """
    env = env or os.environ  # type: ignore[assignment]

    keys: list[str] = []

    numbered: list[tuple[int, str]] = []
    for k, v in env.items():
        if not k.startswith("OPENAI_API_KEY_"):
            continue
        suffix = k.removeprefix("OPENAI_API_KEY_")
        if not suffix.isdigit():
            continue
        if not v:
            continue
        numbered.append((int(suffix), v))
    for _, v in sorted(numbered, key=lambda t: t[0]):
        keys.append(v)

    keys.extend(_split_keys(env.get("OPENAI_API_KEYS", "")))

    single = env.get("OPENAI_API_KEY", "")
    if single:
        keys.append(single)

    # Preserve order but drop duplicates again across sources
    seen: set[str] = set()
    out: list[str] = []
    for k in keys:
        if not k:
            continue
        if k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def mask_key(key: str) -> str:
    """Return a safe display representation of a secret key."""
    if not key:
        return ""
    if len(key) <= 10:
        return "*" * len(key)
    return f"{key[:7]}{'*' * (len(key) - 11)}{key[-4:]}"


def mask_keys(keys: Iterable[str]) -> list[str]:
    return [mask_key(k) for k in keys]

