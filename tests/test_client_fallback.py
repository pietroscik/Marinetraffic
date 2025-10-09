from typing import Dict, List

import pytest

from data_providers.base import VesselDataProvider
from data_providers.utils import cache_file_path, store_cached_payload
from marine_traffic_client import MarineTrafficClient


class _EmptyProvider(VesselDataProvider):
    provider_name = "empty"

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        return []


class _FailingProvider(VesselDataProvider):
    provider_name = "failing"

    def __init__(self):
        self.calls = 0

    def fetch_vessels(self, port_name: str, radius: int = 50) -> List[Dict]:
        self.calls += 1
        raise RuntimeError("boom")


@pytest.fixture(autouse=True)
def cleanup_cache(tmp_path, monkeypatch):
    monkeypatch.setattr("data_providers.utils.CACHE_DIR", tmp_path)
    tmp_path.mkdir(parents=True, exist_ok=True)
    yield


def test_client_returns_empty_list_when_provider_returns_no_vessels():
    client = MarineTrafficClient("demo", data_provider=_EmptyProvider())

    vessels = client.get_vessels_in_port_area("Naples")

    assert vessels == []


def test_client_uses_sample_on_failure(monkeypatch):
    failing = _FailingProvider()
    client = MarineTrafficClient("demo", data_provider=failing)

    sample_data = [{"mmsi": 1, "ship_name": "SIM"}]
    monkeypatch.setattr(client._fallback_provider, "fetch_vessels", lambda port, radius: sample_data)

    vessels = client.get_vessels_in_port_area("Naples")

    assert vessels == sample_data
    assert failing.calls == 1


def test_client_serves_cached_data_on_error(monkeypatch):
    provider = _FailingProvider()

    cache_file = cache_file_path(provider.provider_name, "Naples", 50)
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    store_cached_payload(provider.provider_name, "Naples", 50, [{"mmsi": 9}])

    client = MarineTrafficClient("demo", data_provider=provider)
    monkeypatch.setattr(client._fallback_provider, "fetch_vessels", lambda *args, **kwargs: [])

    vessels = client.get_vessels_in_port_area("Naples")

    assert vessels == [{"mmsi": 9}]
    assert provider.calls == 0
