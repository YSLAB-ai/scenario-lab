from __future__ import annotations

from collections.abc import Callable

from forecasting_harness.domain.base import DomainPack
from forecasting_harness.domain.company_action import CompanyActionPack
from forecasting_harness.domain.election_shock import ElectionShockPack
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.domain.market_shock import MarketShockPack
from forecasting_harness.domain.pandemic_response import PandemicResponsePack
from forecasting_harness.domain.regulatory_enforcement import RegulatoryEnforcementPack
from forecasting_harness.domain.supply_chain_disruption import SupplyChainDisruptionPack

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
    registry.register("company-action", CompanyActionPack)
    registry.register("election-shock", ElectionShockPack)
    registry.register("generic-event", GenericEventPack)
    registry.register("interstate-crisis", InterstateCrisisPack)
    registry.register("market-shock", MarketShockPack)
    registry.register("pandemic-response", PandemicResponsePack)
    registry.register("regulatory-enforcement", RegulatoryEnforcementPack)
    registry.register("supply-chain-disruption", SupplyChainDisruptionPack)
    return registry
