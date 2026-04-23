from pathlib import Path


def test_public_readme_is_scenario_lab_landing_page() -> None:
    root = Path(__file__).resolve().parents[3]
    readme = (root / "README.md").read_text(encoding="utf-8")
    quickstart = (root / "docs" / "quickstart.md").read_text(encoding="utf-8")
    workflow = (root / "docs" / "natural-language-workflow.md").read_text(
        encoding="utf-8"
    )
    metadata = (root / "docs" / "github-public-metadata.md").read_text(
        encoding="utf-8"
    )

    assert readme.startswith("# Scenario Lab")
    assert "U.S.-Iran" in readme
    assert "scenario-lab demo-run --root .forecast" in readme
    assert "Monte Carlo tree search" in readme
    assert "Alliance consultation (coordinated signaling)" in readme
    assert "third-party actors carried into the run" in readme
    assert "[docs/quickstart.md](docs/quickstart.md)" in readme
    assert (
        "[docs/natural-language-workflow.md](docs/natural-language-workflow.md)"
        in readme
    )
    assert "[docs/demo-us-iran.md](docs/demo-us-iran.md)" in readme
    assert "[docs/limitations.md](docs/limitations.md)" in readme
    assert "docs/assets/scenario-lab-workflow.png" in readme
    assert "docs/assets/scenario-lab-runtime-workflow.png" in readme
    assert "/Volumes/" not in readme
    assert "scenario-lab demo-run --root .forecast" in quickstart
    assert "## Actual runtime phases" in workflow
    assert "batch-ingest-recommended" in workflow
    assert "intake -> evidence -> approval -> simulation -> report" in workflow
    assert "Alliance consultation (coordinated signaling)" in workflow
    assert "scenario-lab" in metadata
    assert "YSLAB-ai" in metadata


def test_public_docs_and_assets_exist() -> None:
    root = Path(__file__).resolve().parents[3]
    demo_doc = (root / "docs" / "demo-us-iran.md").read_text(encoding="utf-8")
    metadata_doc = (root / "docs" / "github-public-metadata.md").read_text(
        encoding="utf-8"
    )
    workflow_asset = root / "docs" / "assets" / "scenario-lab-workflow.png"
    runtime_workflow_asset = root / "docs" / "assets" / "scenario-lab-runtime-workflow.png"
    social_preview_asset = root / "docs" / "assets" / "scenario-lab-social-preview.png"

    assert (root / "docs" / "quickstart.md").is_file()
    assert (root / "docs" / "natural-language-workflow.md").is_file()
    assert (root / "docs" / "demo-us-iran.md").is_file()
    assert (root / "docs" / "limitations.md").is_file()
    assert (root / "docs" / "release-notes" / "public-preview.md").is_file()
    assert (root / "docs" / "github-public-metadata.md").is_file()
    assert workflow_asset.is_file()
    assert workflow_asset.stat().st_size > 0
    assert runtime_workflow_asset.is_file()
    assert runtime_workflow_asset.stat().st_size > 0
    assert social_preview_asset.is_file()
    assert social_preview_asset.stat().st_size > 0
    assert "/Volumes/" not in demo_doc
    assert "run-adapter-action" in demo_doc
    assert "<json-for-one-evidence-item>" not in demo_doc
    assert "AP Apr. 23, 2026: U.S. threat posture around Hormuz shipping attacks" in demo_doc
    assert "Alliance consultation (coordinated signaling)" in demo_doc
    assert "Open negotiation" in demo_doc
    assert "scenario-lab" in metadata_doc
    assert "github.com/YSLAB-ai/scenario-lab" in metadata_doc
