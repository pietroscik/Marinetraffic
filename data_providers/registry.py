"""Dynamic provider registry used to instantiate AIS providers."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple, Type, TypeVar

from .base import SampleDataProvider, VesselDataProvider

ProviderFactory = Callable[..., VesselDataProvider]
T = TypeVar("T", bound=VesselDataProvider)


@dataclass
class ProviderMetadata:
    """Metadata describing a registered provider."""

    name: str
    cls: Type[VesselDataProvider]
    factory: ProviderFactory
    aliases: Tuple[str, ...]


class ProviderRegistry:
    """Registry that exposes providers via a factory pattern."""

    def __init__(self) -> None:
        self._providers: Dict[str, ProviderMetadata] = {}
        self._metadata_by_name: Dict[str, ProviderMetadata] = {}
        self._classes: Dict[str, Type[VesselDataProvider]] = {}

    def register(
        self,
        name: str,
        cls: Type[T],
        *,
        factory: Optional[ProviderFactory] = None,
        aliases: Optional[Iterable[str]] = None,
    ) -> Type[T]:
        """Register *cls* under *name* and optional *aliases*."""

        normalized_name = name.lower()
        if factory is None:
            factory = cls  # type: ignore[assignment]

        metadata = ProviderMetadata(
            name=normalized_name,
            cls=cls,
            factory=factory,
            aliases=tuple(alias.lower() for alias in (aliases or ())),
        )

        keys = {normalized_name, *(alias.lower() for alias in metadata.aliases)}
        for key in keys:
            self._providers[key] = metadata

        self._metadata_by_name[normalized_name] = metadata

        self._classes[cls.__name__] = cls
        if cls.provider_name is None:
            cls.provider_name = normalized_name
        return cls

    def get(self, name: str) -> ProviderMetadata:
        """Return provider metadata for *name* or raise ``KeyError``."""

        normalized = name.lower()
        if normalized not in self._providers:
            raise KeyError(f"Provider '{name}' non registrato")
        return self._providers[normalized]

    def create(self, name: str, **kwargs) -> VesselDataProvider:
        """Instantiate the provider registered under *name*."""

        metadata = self.get(name)
        return metadata.factory(**kwargs)

    def create_from_env(
        self, name: str, env: Optional[Dict[str, str]] = None
    ) -> Optional[VesselDataProvider]:
        """Build provider *name* using its ``from_env`` classmethod."""

        metadata = self.get(name)
        env_mapping = env or {}
        instance = metadata.cls.from_env(env_mapping)
        return instance

    def discover_from_env(
        self, env: Dict[str, str], *, priority: Optional[List[str]] = None
    ) -> Optional[VesselDataProvider]:
        """Try all providers in *priority* order using ``from_env`` hooks."""

        ordered: List[ProviderMetadata]
        if priority:
            ordered = []
            seen = set()
            for name in priority:
                try:
                    metadata = self.get(name)
                except KeyError:
                    continue
                ordered.append(metadata)
                seen.update({metadata.name, *metadata.aliases})
            for metadata in self._metadata_by_name.values():
                if metadata.name in seen:
                    continue
                ordered.append(metadata)
        else:
            ordered = list(self._metadata_by_name.values())

        for metadata in ordered:
            instance = metadata.cls.from_env(env)
            if instance is not None:
                return instance
        return None

    def list_classes(self) -> Dict[str, Type[VesselDataProvider]]:
        """Return all registered classes keyed by their public name."""

        result: Dict[str, Type[VesselDataProvider]] = {}
        for metadata in self._metadata_by_name.values():
            result[metadata.cls.__name__] = metadata.cls
        return result


provider_registry = ProviderRegistry()


def register_provider(
    name: str,
    *,
    aliases: Optional[Iterable[str]] = None,
    factory: Optional[ProviderFactory] = None,
) -> Callable[[Type[T]], Type[T]]:
    """Decorator used by provider modules to register themselves."""

    def decorator(cls: Type[T]) -> Type[T]:
        provider_registry.register(name, cls, factory=factory, aliases=aliases)
        return cls

    return decorator


def discover_builtin_providers() -> None:
    """Import every provider module within the package."""

    package_path = Path(__file__).resolve().parent
    package_name = __name__.rsplit(".", 1)[0]

    for module in pkgutil.iter_modules([str(package_path)]):
        module_name = module.name
        if module_name.startswith("_"):
            continue
        if module_name in {"__init__", "base", "registry", "utils"}:
            continue
        importlib.import_module(f"{package_name}.{module_name}")


# Ensure the simulated provider is always present.
provider_registry.register("simulated", SampleDataProvider, aliases=("sample",))
