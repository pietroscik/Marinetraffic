"""Utility per l'approvvigionamento di dati AIS da fonti alternative.

Questo modulo introduce un insieme di provider che permettono di alimentare
il sistema anche senza ricorrere all'API proprietaria di Marine Traffic. Sono
supportati sia dataset open-data locali (CSV/JSON/GeoJSON) sia endpoint HTTP
gratuiti che espongono informazioni AIS. Quando nessuna fonte esterna è
disponibile, viene utilizzato un generatore di dati simulati.
"""

from __future__ import annotations

import csv
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import requests


# Coordinate di riferimento per i principali porti del Tirreno centrale.
# Possono essere ampliate o personalizzate tramite file open-data.
PORT_COORDINATES: Dict[str, Dict[str, float]] = {
    "Naples": {"lat": 40.8394, "lon": 14.2520},
    "Salerno": {"lat": 40.6741, "lon": 14.7697},
    "Civitavecchia": {"lat": 42.0942, "lon": 11.7961},
    "Gaeta": {"lat": 41.2131, "lon": 13.5722},
}


def _parse_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _parse_int(value: object, default: int = 0) -> int:
    try:
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _normalize_eta(raw_eta: object) -> Optional[str]:
    """Prova a convertire il campo ETA nelle varie rappresentazioni comuni."""

    if raw_eta in (None, "", "0000-00-00 00:00", "0000-00-00T00:00:00"):
        return None

    if isinstance(raw_eta, (int, float)):
        eta_dt = datetime.now() + timedelta(hours=float(raw_eta))
        return eta_dt.isoformat()

    if isinstance(raw_eta, datetime):
        return raw_eta.isoformat()

    if not isinstance(raw_eta, str):
        return None

    eta_str = raw_eta.strip()
    if not eta_str:
        return None

    known_formats = (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M",
        "%m-%d %H:%M",
        "%d-%m %H:%M",
    )

    for fmt in known_formats:
        try:
            eta_dt = datetime.strptime(eta_str, fmt)
            if eta_dt.year == 1900:
                eta_dt = eta_dt.replace(year=datetime.now().year)
            return eta_dt.isoformat()
        except ValueError:
            continue

    # Alcune fonti espongono ETA in formato HHMM (es. "1200").
    if eta_str.isdigit() and len(eta_str) in {3, 4}:
        hours = int(eta_str[:-2])
        minutes = int(eta_str[-2:])
        eta_dt = datetime.now().replace(minute=minutes, second=0, microsecond=0)
        eta_dt += timedelta(hours=max(hours - eta_dt.hour, 0))
        return eta_dt.isoformat()

    return None


def normalize_ais_record(raw: Dict, default_destination: str) -> Dict:
    """Uniforma i campi principali di un record AIS alle chiavi usate dal sistema."""

    mmsi = _parse_int(raw.get("mmsi") or raw.get("MMSI"))
    if not mmsi:
        # Ogni record deve avere un identificativo; in caso contrario viene scartato.
        raise ValueError("Record AIS privo di MMSI")

    latitude = raw.get("latitude") or raw.get("LAT") or raw.get("lat")
    longitude = raw.get("longitude") or raw.get("LON") or raw.get("lon")

    dim_a = _parse_float(raw.get("dim_a"))
    dim_b = _parse_float(raw.get("dim_b"))
    dim_c = _parse_float(raw.get("dim_c"))
    dim_d = _parse_float(raw.get("dim_d"))

    vessel = {
        "mmsi": mmsi,
        "imo": _parse_int(raw.get("imo") or raw.get("IMO")),
        "ship_name": raw.get("ship_name")
        or raw.get("SHIPNAME")
        or raw.get("name")
        or "Unknown",
        "ship_type": raw.get("ship_type")
        or raw.get("SHIPTYPE")
        or raw.get("type")
        or "Unknown",
        "destination": raw.get("destination")
        or raw.get("DESTINATION")
        or default_destination,
        "eta": _normalize_eta(raw.get("eta") or raw.get("ETA")),
        "speed": round(
            _parse_float(raw.get("speed") or raw.get("SOG") or raw.get("sog"), 0.0),
            1,
        ),
        "course": int(
            round(
                _parse_float(
                    raw.get("course") or raw.get("COG") or raw.get("cog"), 0.0
                )
            )
        ),
        "latitude": _parse_float(latitude, 0.0),
        "longitude": _parse_float(longitude, 0.0),
        "draught": round(
            _parse_float(raw.get("draught") or raw.get("DRAUGHT") or raw.get("draught_m"), 0.0),
            1,
        ),
        "length": int(
            round(
                _parse_float(
                    raw.get("length")
                    or raw.get("LENGTH")
                    or raw.get("length_m"),
                    dim_a + dim_b,
                )
            )
        ),
        "width": int(
            round(
                _parse_float(
                    raw.get("width")
                    or raw.get("WIDTH")
                    or raw.get("width_m"),
                    dim_c + dim_d,
                )
            )
        ),
        "status": raw.get("status")
        or raw.get("STATUS")
        or raw.get("nav_status")
        or "Unknown",
    }

    return vessel


# Alias retrocompatibile finché i moduli interni non vengono aggiornati
_normalize_record = normalize_ais_record


class VesselDataProvider:
    """Interfaccia base per fornire dati sui vettori."""

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        raise NotImplementedError


@dataclass
class SampleDataProvider(VesselDataProvider):
    """Generatore di dati sintetici, utile come fallback o per test locali."""

    seed: Optional[int] = None

    def __post_init__(self) -> None:
        if self.seed is not None:
            random.seed(self.seed)

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        vessel_types = [
            "Cargo",
            "Tanker",
            "Container Ship",
            "Bulk Carrier",
            "Passenger Ship",
        ]
        vessel_names = [
            "MEDITERRANEAN STAR",
            "OCEAN VOYAGER",
            "TYRRHENIAN EXPRESS",
            "ATLANTIC HORIZON",
            "NEPTUNE CARRIER",
            "POSEIDON TRADER",
            "ADRIATIC QUEEN",
            "ITALIA MARINE",
            "BLUE WAVE",
            "SEA SPIRIT",
        ]

        vessels: List[Dict] = []
        num_vessels = random.randint(5, 12)

        coords = PORT_COORDINATES.get(port_name, {"lat": 40.5, "lon": 14.0})

        for i in range(num_vessels):
            eta_hours = random.randint(1, 48)
            eta_dt = datetime.now() + timedelta(hours=eta_hours)
            vessels.append(
                {
                    "mmsi": 200_000_000 + random.randint(1_000, 9_999) * 100 + i,
                    "imo": 9_000_000 + random.randint(100_000, 999_999),
                    "ship_name": random.choice(vessel_names),
                    "ship_type": random.choice(vessel_types),
                    "destination": port_name,
                    "eta": eta_dt.isoformat(),
                    "speed": round(random.uniform(8.0, 18.0), 1),
                    "course": random.randint(0, 360),
                    "latitude": coords["lat"] + random.uniform(-0.6, 0.6),
                    "longitude": coords["lon"] + random.uniform(-0.6, 0.6),
                    "draught": round(random.uniform(6.0, 14.0), 1),
                    "length": random.randint(120, 350),
                    "width": random.randint(22, 50),
                    "status": random.choice(
                        ["Under way using engine", "At anchor", "Moored"]
                    ),
                }
            )

        return vessels


class OpenAisFileProvider(VesselDataProvider):
    """Carica dati AIS da file open-data (CSV/JSON/GeoJSON)."""

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
                if "features" in data:  # GeoJSON
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


class OpenAisApiProvider(VesselDataProvider):
    """Recupera dati AIS da un endpoint HTTP pubblico o gratuito."""

    def __init__(
        self,
        endpoint: str,
        *,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        port_query_param: Optional[str] = None,
        timeout: int = 10,
        session: Optional[requests.Session] = None,
    ):
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


class AisHubApiProvider(VesselDataProvider):
    """Recupera dati AIS dal servizio API documentato da AISHub."""

    BASE_URL = "https://data.aishub.net/ws.php"

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
        # 1° di latitudine ≈ 60 NM; per la longitudine correggiamo con il coseno
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
            if any(key in payload for key in ("ERROR", "error", "status")) and not payload.get("data"):
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


class MarineTrafficApiProvider(VesselDataProvider):
    """Interroga direttamente l'API commerciale di MarineTraffic."""

    BASE_URL = "https://services.marinetraffic.com/api"

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
    ):
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

        records: List[Dict]
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

