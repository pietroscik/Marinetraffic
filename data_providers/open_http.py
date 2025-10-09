"""Provider that loads AIS data from open HTTP endpoints."""
from __future__ import annotations

from typing import Dict, List, Optional

import requests

from .base import VesselDataProvider, normalize_ais_record
from .registry import register_provider


@register_provider("open_http", aliases=("http", "open_api"))
class OpenAisApiProvider(VesselDataProvider):
    """Fetch AIS data from a configurable HTTP endpoint."""

    provider_name = "open_http"

    def __init__(
        self,
        endpoint: str,
        *,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        port_query_param: Optional[str] = None,
        timeout: int = 10,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.endpoint = endpoint
        self.params = params or {}
        self.headers = headers or {}
        self.port_query_param = port_query_param
        self.timeout = timeout
        self.session = session or requests.Session()

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        query_params = dict(self.params)
        if self.port_query_param:
            query_params[self.port_query_param] = port_name

        response = self.session.get(
            self.endpoint, params=query_params, headers=self.headers, timeout=self.timeout
        )
        response.raise_for_status()

        payload = response.json()

        if isinstance(payload, dict):
            if "data" in payload and isinstance(payload["data"], list):
                records = payload["data"]
            elif "results" in payload and isinstance(payload["results"], list):
                records = payload["results"]
            else:
                records = [payload]
        elif isinstance(payload, list):
            records = payload
        else:
            return []

        vessels: List[Dict] = []
        for record in records:
            if not isinstance(record, dict):
                continue
            try:
                vessels.append(normalize_ais_record(record, port_name))
            except ValueError:
                continue

        return vessels

    @classmethod
    def from_env(cls, env: Dict[str, str]):  # type: ignore[override]
        endpoint = env.get("AIS_OPEN_DATA_URL")
        if not endpoint:
            return None

        headers = _parse_env_mapping(env.get("AIS_OPEN_DATA_HEADERS"))
        params = _parse_env_mapping(env.get("AIS_OPEN_DATA_PARAMS"))
        port_param = env.get("AIS_OPEN_DATA_PORT_PARAM")

        try:
            return cls(
                endpoint,
                headers=headers,
                params=params,
                port_query_param=port_param,
            )
        except Exception:
            return None


def _parse_env_mapping(raw: Optional[str]) -> Optional[Dict[str, str]]:
    if not raw:
        return None
    import json

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict):
        return {str(key): str(value) for key, value in data.items()}
    return None


__all__ = ["OpenAisApiProvider"]
