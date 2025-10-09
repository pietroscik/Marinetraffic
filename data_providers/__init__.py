"""Dynamic data provider registry with auto-discovery."""
from __future__ import annotations

from typing import Dict, Type

from .base import PORT_COORDINATES, SampleDataProvider, VesselDataProvider, normalize_ais_record
from .registry import discover_builtin_providers, provider_registry, register_provider

# Automatically load bundled providers when the package is imported.
discover_builtin_providers()

# Expose registered classes for backwards compatibility.
REGISTERED_CLASSES: Dict[str, Type[VesselDataProvider]] = provider_registry.list_classes()

globals().update(REGISTERED_CLASSES)

__all__ = [
    "PORT_COORDINATES",
    "SampleDataProvider",
    "VesselDataProvider",
    "normalize_ais_record",
    "provider_registry",
    "register_provider",
    *REGISTERED_CLASSES.keys(),
]
