from pathlib import Path


def test_public_readme_is_scenario_lab_landing_page() -> None:
    root = Path(__file__).resolve().parents[3]
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert readme.startswith("# Scenario Lab")
    assert "Experimental preview" in readme
    assert "U.S.-Iran" in readme
    assert "[docs/quickstart.md](docs/quickstart.md)" in readme
    assert (
        "[docs/natural-language-workflow.md](docs/natural-language-workflow.md)"
        in readme
    )
    assert "[docs/demo-us-iran.md](docs/demo-us-iran.md)" in readme
    assert "[docs/limitations.md](docs/limitations.md)" in readme
    assert "docs/assets/scenario-lab-workflow.png" in readme
    assert "/Volumes/" not in readme


def test_public_docs_and_assets_exist() -> None:
    root = Path(__file__).resolve().parents[3]
    workflow_asset = root / "docs" / "assets" / "scenario-lab-workflow.png"
    social_preview_asset = root / "docs" / "assets" / "scenario-lab-social-preview.png"

    assert (root / "docs" / "quickstart.md").is_file()
    assert (root / "docs" / "natural-language-workflow.md").is_file()
    assert (root / "docs" / "demo-us-iran.md").is_file()
    assert (root / "docs" / "limitations.md").is_file()
    assert (root / "docs" / "release-notes" / "public-preview.md").is_file()
    assert workflow_asset.is_file()
    assert workflow_asset.stat().st_size > 0
    assert social_preview_asset.is_file()
    assert social_preview_asset.stat().st_size > 0
