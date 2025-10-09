import json
from typing import Any, Dict

from data_providers import AisHubApiProvider, MarineTrafficApiProvider


class _MockResponse:
    def __init__(self, payload: Dict[str, Any]):
        self._payload = payload
        self.text = json.dumps(payload)

    def raise_for_status(self) -> None:  # pragma: no cover - no-op
        return None

    def json(self) -> Dict[str, Any]:
        return self._payload


class _MockSession:
    def __init__(self, payload: Dict[str, Any]):
        self._payload = payload
        self.performed_calls = []

    def get(self, *args, **kwargs):
        self.performed_calls.append((args, kwargs))
        return _MockResponse(self._payload)


def test_aishub_provider_parses_payload() -> None:
    payload = {
        "status": "OK",
        "ais": [
            {
                "MMSI": "247039300",
                "SHIPNAME": "TEST VESSEL",
                "LAT": 40.1,
                "LON": 14.2,
                "ETA": "2024-05-01 12:00",
            }
        ],
    }
    session = _MockSession(payload)
    provider = AisHubApiProvider(username="demo", session=session)

    vessels = provider.fetch_vessels("Naples", radius=5)

    assert len(vessels) == 1
    assert vessels[0]["ship_name"] == "TEST VESSEL"
    assert vessels[0]["destination"] == "Naples"


def test_marine_traffic_provider_parses_payload() -> None:
    payload = [
        {
            "MMSI": 247039300,
            "SHIPNAME": "TESTER",
            "LAT": 40.5,
            "LON": 14.3,
            "ETA": "2024-05-01T12:00:00",
        }
    ]
    session = _MockSession(payload)
    provider = MarineTrafficApiProvider(api_key="secret", session=session)

    vessels = provider.fetch_vessels("Naples", radius=5)

    assert len(vessels) == 1
    assert vessels[0]["ship_name"] == "TESTER"
    assert vessels[0]["mmsi"] == 247039300
