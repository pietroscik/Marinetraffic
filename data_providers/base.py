"""Shared base classes and utilities for AIS data providers."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

PORT_COORDINATES: Dict[str, Dict[str, float]] = {
    "Naples": {"lat": 40.8394, "lon": 14.2520},
    "Salerno": {"lat": 40.6741, "lon": 14.7697},
    "Civitavecchia": {"lat": 42.0942, "lon": 11.7961},
    "Gaeta": {"lat": 41.2131, "lon": 13.5722},
}


def _parse_float(value: object, default: float = 0.0) -> float:
    """Safely parse *value* as a float returning *default* on failure."""
    try:
        return float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _parse_int(value: object, default: int = 0) -> int:
    """Safely parse *value* as an int returning *default* on failure."""
    try:
        return int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return default


def _normalize_eta(raw_eta: object) -> Optional[str]:
    """Convert the ETA field into an ISO formatted timestamp when possible."""

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

    if eta_str.isdigit() and len(eta_str) in {3, 4}:
        hours = int(eta_str[:-2])
        minutes = int(eta_str[-2:])
        eta_dt = datetime.now().replace(minute=minutes, second=0, microsecond=0)
        eta_dt += timedelta(hours=max(hours - eta_dt.hour, 0))
        return eta_dt.isoformat()

    return None


def normalize_ais_record(raw: Dict, default_destination: str) -> Dict:
    """Normalize raw AIS payloads into the unified vessel schema."""

    mmsi = _parse_int(raw.get("mmsi") or raw.get("MMSI"))
    if not mmsi:
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


class VesselDataProvider:
    """Base class for every AIS data provider implementation."""

    provider_name: Optional[str] = None

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        """Return a list of normalized vessels for *port_name* within *radius*."""
        raise NotImplementedError

    @classmethod
    def from_env(cls, env: Dict[str, str]) -> Optional["VesselDataProvider"]:
        """Build a provider instance from environment variables if available."""
        return None


@dataclass
class SampleDataProvider(VesselDataProvider):
    """Deterministic synthetic provider useful as fallback/offline feed."""

    seed: Optional[int] = None
    provider_name: Optional[str] = "simulated"

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
