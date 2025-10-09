"""AISHub API provider implementation."""
from __future__ import annotations

import json
import math
from typing import Dict, List, Optional

import requests

from .base import PORT_COORDINATES, VesselDataProvider, normalize_ais_record
from .registry import register_provider
from .utils import parse_bool, parse_env_mapping


@register_provider("aishub", aliases=("aishub_api",))
class AisHubApiProvider(VesselDataProvider):
    """Retrieve AIS data from the documented AISHub API."""

    BASE_URL = "https://data.aishub.net/ws.php"
    provider_name = "aishub"

    def __init__(
        self,
        username: str,
        api_key: Optional[str] = None,
        *,
        output_format: str = "json",
        message_format: str = "1",
        compress: bool = False,
        extra_params: Optional[Dict[str, str]] = None,
        timeout: int = 15,
        session: Optional[requests.Session] = None,
        port_coordinates: Optional[Dict[str, Dict[str, float]]] = None,
    ) -> None:
        if not username:
            raise ValueError("È richiesto un username valido per l'API AISHub")

        self.username = username
        self.api_key = api_key
        self.output_format = output_format
        self.message_format = message_format
        self.compress = compress
        self.extra_params = extra_params or {}
        self.timeout = timeout
        self.session = session or requests.Session()
        self.port_coordinates = port_coordinates or PORT_COORDINATES

    @staticmethod
    def _format_coord(value: float) -> str:
        return f"{value:.5f}"

    @staticmethod
    def _calculate_bbox(lat: float, lon: float, radius_nm: int) -> Dict[str, str]:
        delta_lat = radius_nm / 60.0
        cos_lat = math.cos(math.radians(lat)) or 0.0001
        delta_lon = radius_nm / (60.0 * cos_lat)

        lat_min = lat - delta_lat
        lat_max = lat + delta_lat
        lon_min = lon - delta_lon
        lon_max = lon + delta_lon

        return {
            "latmin": AisHubApiProvider._format_coord(lat_min),
            "latmax": AisHubApiProvider._format_coord(lat_max),
            "lonmin": AisHubApiProvider._format_coord(lon_min),
            "lonmax": AisHubApiProvider._format_coord(lon_max),
        }

    def _build_query(self, port_name: str, radius: int) -> Dict[str, str]:
        params: Dict[str, str] = {
            "username": self.username,
            "format": str(self.message_format),
            "output": self.output_format,
            "compress": "1" if self.compress else "0",
        }

        params.update({str(k): str(v) for k, v in self.extra_params.items()})

        if self.api_key:
            params.setdefault("apikey", str(self.api_key))

        bbox_missing = not all(
            key in params for key in ("latmin", "latmax", "lonmin", "lonmax")
        )

        if bbox_missing:
            coords = self.port_coordinates.get(port_name)
            if not coords:
                raise ValueError(
                    "Coordinate non definite per il porto richiesto e nessun bounding box "
                    "personalizzato fornito in extra_params"
                )

            bbox = self._calculate_bbox(coords["lat"], coords["lon"], max(radius, 1))
            for key, value in bbox.items():
                params.setdefault(key, value)

        return params

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        query = self._build_query(port_name, radius)

        response = self.session.get(self.BASE_URL, params=query, timeout=self.timeout)
        response.raise_for_status()

        try:
            payload = response.json()
        except json.JSONDecodeError as exc:
            text = response.text.strip()
            if text.lower().startswith("error"):
                raise ValueError(f"AISHub ha restituito un errore: {text}") from exc
            raise ValueError("Risposta non valida dal servizio AISHub") from exc

        if isinstance(payload, dict):
            record_keys = ("data", "ais", "rows")
            has_record_container = any(key in payload for key in record_keys)

            error_message = payload.get("ERROR") or payload.get("error")
            if error_message:
                raise ValueError(f"Errore dall'API AISHub: {error_message}")

            status_value = payload.get("status")
            if status_value is not None and not has_record_container:
                status_tokens: List[str] = []
                if isinstance(status_value, dict):
                    status_tokens.extend(
                        str(value) for key, value in status_value.items() if value is not None
                    )
                else:
                    status_tokens.append(str(status_value))

                normalized_tokens = {
                    token.strip().lower() for token in status_tokens if token.strip()
                }

                if not normalized_tokens.intersection({"ok", "success", "0"}):
                    raise ValueError(f"Errore dall'API AISHub: {payload}")

            if "data" in payload and isinstance(payload["data"], list):
                records = [r for r in payload["data"] if isinstance(r, dict)]
            elif "ais" in payload and isinstance(payload["ais"], list):
                records = [r for r in payload["ais"] if isinstance(r, dict)]
            elif "rows" in payload and isinstance(payload["rows"], list):
                records = [r for r in payload["rows"] if isinstance(r, dict)]
            else:
                records = [payload]
        elif isinstance(payload, list):
            records = [r for r in payload if isinstance(r, dict)]
        else:
            raise ValueError("Formato di risposta sconosciuto dal servizio AISHub")

        vessels: List[Dict] = []
        for record in records:
            try:
                vessels.append(normalize_ais_record(record, port_name))
            except ValueError:
                continue

        return vessels

    @classmethod
    def from_env(cls, env: Dict[str, str]):  # type: ignore[override]
        username = (env.get("AIS_HUB_USERNAME") or "").strip()
        if not username:
            return None

        api_key = (env.get("AIS_HUB_API_KEY") or "").strip() or None
        extra_params = parse_env_mapping(env.get("AIS_HUB_EXTRA_PARAMS"))
        output_format = (env.get("AIS_HUB_OUTPUT") or "json").strip() or "json"
        message_format = (env.get("AIS_HUB_MESSAGE_FORMAT") or "1").strip() or "1"
        compress = parse_bool(env.get("AIS_HUB_COMPRESS"))

        try:
            return cls(
                username=username,
                api_key=api_key,
                output_format=output_format,
                message_format=message_format,
                compress=compress,
                extra_params=extra_params,
            )
        except Exception:
            return None


__all__ = ["AisHubApiProvider"]
