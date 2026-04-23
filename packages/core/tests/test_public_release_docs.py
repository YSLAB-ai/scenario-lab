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
    assert "Experimental preview" in readme
    assert "## What Is It" in readme
    assert "## Quickstart" in readme
    assert "## Workflow And Demo" in readme
    assert "## What Makes It Effective" in readme
    assert "## Current Limits" in readme
    assert "## Others" in readme
    assert "U.S.-Iran" in readme
    assert "actual runtime phases" in readme
    assert "`intake`" in readme
    assert "`evidence`" in readme
    assert "`approval`" in readme
    assert "`simulation`" in readme
    assert "`report`" in readme
    assert "batch-ingest-recommended" in readme
    assert "force posture" in readme
    assert "Open negotiation" in readme
    assert "Monte Carlo tree search" in readme
    assert "Claude Code" in readme
    assert "git clone git@github.com:YSLAB-ai/scenario-lab.git" in readme
    assert "[docs/quickstart.md](docs/quickstart.md)" in readme
    assert (
        "[docs/natural-language-workflow.md](docs/natural-language-workflow.md)"
        in readme
    )
    assert "[docs/demo-us-iran.md](docs/demo-us-iran.md)" in readme
    assert "[docs/limitations.md](docs/limitations.md)" in readme
    assert "docs/assets/scenario-lab-workflow.png" in readme
    assert "docs/assets/scenario-lab-runtime-workflow.png" in readme
    assert "forecast-harness demo-run --root .forecast" in readme
    assert "/Volumes/" not in readme
    assert "forecast-harness demo-run --root .forecast" in quickstart
    assert "## Actual runtime phases" in workflow
    assert "batch-ingest-recommended" in workflow
    assert "intake -> evidence -> approval -> simulation -> report" in workflow
    assert "Current public repository slug: `YSLAB-ai/scenario-lab`" in metadata


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
    assert (
        "packages/core/.venv/bin/python -m forecasting_harness.cli run-adapter-action"
        in demo_doc
    )
    assert "<json-for-one-evidence-item>" not in demo_doc
    assert "exactly as executed" not in demo_doc
    assert "Homepage: `https://github.com/YSLAB-ai/scenario-lab`" in metadata_doc
