from pathlib import Path

import pytest

from forecasting_harness.knowledge.manifests import DomainManifest, load_domain_manifest


def test_load_domain_manifest_reads_repo_manifest() -> None:
    manifest = load_domain_manifest("interstate-crisis")

    assert isinstance(manifest, DomainManifest)
    assert manifest.slug == "interstate-crisis"
    assert "force posture" in manifest.evidence_categories
    assert manifest.semantic_alias_groups


def test_load_domain_manifest_rejects_unknown_slugs() -> None:
    with pytest.raises(FileNotFoundError):
        load_domain_manifest("does-not-exist")


def test_all_repo_domain_manifests_load() -> None:
    manifest_dir = Path(__file__).resolve().parents[3] / "knowledge" / "domains"
    slugs = sorted(path.stem for path in manifest_dir.glob("*.json"))

    manifests = [load_domain_manifest(slug) for slug in slugs]

    assert [manifest.slug for manifest in manifests] == slugs
