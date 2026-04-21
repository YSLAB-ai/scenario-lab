from forecasting_harness.domain.registry import build_default_registry


def test_default_registry_lists_builtin_domain_packs() -> None:
    registry = build_default_registry()

    assert registry.list_slugs() == ["generic-event", "interstate-crisis"]


def test_default_registry_returns_new_pack_instances() -> None:
    registry = build_default_registry()

    first = registry.resolve("generic-event")
    second = registry.resolve("generic-event")

    assert first.slug() == "generic-event"
    assert second.slug() == "generic-event"
    assert first is not second
