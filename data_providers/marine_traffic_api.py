"""Commercial MarineTraffic API provider implementation."""
from __future__ import annotations

import json
from typing import Dict, List, Optional

import requests

from .base import VesselDataProvider, normalize_ais_record
from .registry import register_provider


@register_provider("commercial", aliases=("marinetraffic", "marine_traffic"))
class MarineTrafficApiProvider(VesselDataProvider):
    """Query the commercial MarineTraffic API."""

    BASE_URL = "https://services.marinetraffic.com/api"
    provider_name = "commercial"

    def __init__(
        self,
        api_key: str,
        *,
        service: str = "exportvessel",
        version: str = "v:5",
        protocol: str = "jsono",
        filters: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        session: Optional[requests.Session] = None,
    ) -> None:
        if not api_key:
            raise ValueError("È richiesta una chiave API valida per MarineTraffic")

        self.api_key = api_key
        self.service = service.strip("/")
        self.version = version
        self.protocol = protocol
        self.filters = filters or {"timespan": "24"}
        self.timeout = timeout
        self.session = session or requests.Session()

    def _build_url(self, port_name: str, radius: int) -> str:
        segments = [
            self.service,
            self.version,
            self.api_key,
        ]

        for key, value in self.filters.items():
            if value is None:
                continue
            segments.append(f"{key}:{value}")

        segments.append(f"portname:{port_name}")
        if radius:
            segments.append(f"radius:{radius}")
        segments.append(f"protocol:{self.protocol}")

        return "/".join([self.BASE_URL, *segments])

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        if self.api_key.lower() == "demo_key":
            raise ValueError(
                "La chiave API demo non consente il recupero dei dati commerciali"
            )

        url = self._build_url(port_name, radius)
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            raise ValueError(f"Risposta non valida dall'API MarineTraffic: {exc}") from exc

        if isinstance(payload, list):
            records = [r for r in payload if isinstance(r, dict)]
        elif isinstance(payload, dict):
            if "data" in payload and isinstance(payload["data"], list):
                records = [r for r in payload["data"] if isinstance(r, dict)]
            else:
                records = [payload]
        else:
            raise ValueError("Formato di risposta sconosciuto dall'API MarineTraffic")

        vessels: List[Dict] = []
        for record in records:
            try:
                vessels.append(normalize_ais_record(record, port_name))
            except ValueError:
                continue

        return vessels

    @classmethod
    def from_env(cls, env: Dict[str, str]):  # type: ignore[override]
        api_key = (env.get("MARINETRAFFIC_API_KEY") or "").strip()
        if not api_key:
            return None
        try:
            return cls(api_key)
        except Exception:
            return None


__all__ = ["MarineTrafficApiProvider"]
