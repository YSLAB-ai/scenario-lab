from __future__ import annotations

from collections.abc import Callable

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack

PackFactory = Callable[[], DomainPack]


class DomainPackRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, PackFactory] = {}

    def register(self, slug: str, factory: PackFactory) -> None:
        self._factories[slug] = factory

    def list_slugs(self) -> list[str]:
        return sorted(self._factories)

    def resolve(self, slug: str) -> DomainPack:
        try:
            return self._factories[slug]()
        except KeyError as exc:
            raise KeyError(f"unknown domain pack: {slug}") from exc


def build_default_registry() -> DomainPackRegistry:
    registry = DomainPackRegistry()
    registry.register("generic-event", GenericEventPack)
    registry.register("interstate-crisis", InterstateCrisisPack)
    return registry
