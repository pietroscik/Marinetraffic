"""Utility helpers shared by provider implementations."""
from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

CACHE_DIR = Path(__file__).resolve().parent.parent / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SENSITIVE_TOKENS = {"api", "token", "key", "secret", "password"}


def parse_env_mapping(raw: Optional[str]) -> Optional[Dict[str, str]]:
    """Parse JSON mapping stored in an environment variable."""

    if not raw:
        return None

    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return None

    if isinstance(value, dict):
        return {str(key): str(val) for key, val in value.items()}
    return None


def parse_bool(raw: Optional[str], *, default: bool = False) -> bool:
    """Parse truthy textual values from environment variables."""

    if raw is None:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def mask_sensitive(value: Optional[str]) -> str:
    """Mask sensitive tokens so they do not leak in logs."""

    if not value:
        return ""
    trimmed = value.strip()
    if len(trimmed) <= 4:
        return "*" * len(trimmed)
    return f"{trimmed[:2]}…{trimmed[-2:]}"


def mask_env(env: Dict[str, str], *, keys: Optional[Iterable[str]] = None) -> Dict[str, str]:
    """Return a masked copy of *env* for logging purposes."""

    masked: Dict[str, str] = {}
    lowered_keys = {key.lower() for key in (keys or env.keys())}
    for key in env:
        value = env[key]
        if any(token in key.lower() for token in SENSITIVE_TOKENS) or key.lower() in lowered_keys:
            masked[key] = mask_sensitive(value)
        else:
            masked[key] = value
    return masked


def cache_file_path(provider: str, port_name: str, radius: int) -> Path:
    safe_provider = provider.replace("/", "_")
    safe_port = port_name.replace("/", "_")
    return CACHE_DIR / f"{safe_provider}__{safe_port}__{radius}.json"


def load_cached_payload(
    provider: str,
    port_name: str,
    radius: int,
    *,
    max_age_minutes: Optional[int] = 5,
) -> Optional[Dict[str, Any]]:
    """Return cached vessel payload if not expired."""

    cache_path = cache_file_path(provider, port_name, radius)
    if not cache_path.exists():
        return None

    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None

    timestamp = payload.get("timestamp")
    if not isinstance(timestamp, str):
        return None

    try:
        cached_at = datetime.fromisoformat(timestamp)
    except ValueError:
        return None

    if max_age_minutes is not None:
        if cached_at < datetime.utcnow() - timedelta(minutes=max_age_minutes):
            return None

    return payload


def store_cached_payload(
    provider: str,
    port_name: str,
    radius: int,
    vessels: Any,
) -> None:
    """Persist *vessels* to the cache directory."""

    cache_path = cache_file_path(provider, port_name, radius)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider": provider,
        "port": port_name,
        "radius": radius,
        "timestamp": datetime.utcnow().isoformat(),
        "vessels": vessels,
    }
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def cache_ttl_minutes() -> int:
    try:
        raw = os.getenv("DATA_CACHE_TTL_MINUTES")
        if not raw:
            raise ValueError
        ttl = int(raw)
        return ttl if ttl > 0 else 5
    except (TypeError, ValueError):
        return 5
