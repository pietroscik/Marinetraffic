"""Provider that loads AIS data from local open-data files."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, Iterable, List

from .base import VesselDataProvider, normalize_ais_record
from .registry import register_provider


@register_provider("open_file", aliases=("file", "local"))
class OpenAisFileProvider(VesselDataProvider):
    """Load AIS data from CSV/JSON/GeoJSON datasets."""

    provider_name = "open_file"

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File AIS non trovato: {file_path}")

    def _iter_records(self) -> Iterable[Dict]:
        suffix = self.file_path.suffix.lower()

        if suffix in {".json", ".geojson"}:
            with self.file_path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)

            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        yield item
            elif isinstance(data, dict):
                if "features" in data:
                    for feature in data["features"]:
                        if not isinstance(feature, dict):
                            continue
                        properties = feature.get("properties", {})
                        geometry = feature.get("geometry", {})
                        if isinstance(geometry, dict):
                            coords = geometry.get("coordinates")
                            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                                properties.setdefault("longitude", coords[0])
                                properties.setdefault("latitude", coords[1])
                        if isinstance(properties, dict):
                            yield properties
                elif "data" in data and isinstance(data["data"], list):
                    for item in data["data"]:
                        if isinstance(item, dict):
                            yield item
        elif suffix == ".csv":
            with self.file_path.open("r", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    yield dict(row)
        else:
            raise ValueError(
                "Formato non supportato. Utilizzare file CSV, JSON o GeoJSON."
            )

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        vessels: List[Dict] = []
        for record in self._iter_records():
            try:
                vessels.append(normalize_ais_record(record, port_name))
            except ValueError:
                continue
        return vessels

    @classmethod
    def from_env(cls, env: Dict[str, str]):  # type: ignore[override]
        file_path = env.get("AIS_OPEN_DATA_FILE")
        if not file_path:
            return None
        try:
            return cls(file_path)
        except Exception:
            return None


__all__ = ["OpenAisFileProvider"]
