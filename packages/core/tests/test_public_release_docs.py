from pathlib import Path


def test_public_readme_is_scenario_lab_landing_page() -> None:
    root = Path(__file__).resolve().parents[3]
    readme = (root / "README.md").read_text(encoding="utf-8")

    assert readme.startswith("# Scenario Lab")
    assert "Experimental preview" in readme
    assert "U.S.-Iran" in readme
    assert "docs/quickstart.md" in readme
    assert "docs/natural-language-workflow.md" in readme
    assert "docs/demo-us-iran.md" in readme
    assert "docs/limitations.md" in readme


def test_public_docs_and_assets_exist() -> None:
    root = Path(__file__).resolve().parents[3]

    assert (root / "docs" / "quickstart.md").exists()
    assert (root / "docs" / "natural-language-workflow.md").exists()
    assert (root / "docs" / "demo-us-iran.md").exists()
    assert (root / "docs" / "limitations.md").exists()
    assert (root / "docs" / "release-notes" / "public-preview.md").exists()
    assert (root / "docs" / "assets" / "scenario-lab-social-preview.png").exists()
    assert (root / "docs" / "assets" / "scenario-lab-workflow.png").exists()
