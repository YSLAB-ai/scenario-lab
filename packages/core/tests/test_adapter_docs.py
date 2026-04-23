from pathlib import Path


def test_adapter_install_docs_use_scenario_lab_branding_and_public_links() -> None:
    root = Path(__file__).resolve().parents[3]
    docs_root = root / "docs"

    codex_doc = (docs_root / "install-codex.md").read_text(encoding="utf-8")
    claude_doc = (docs_root / "install-claude-code.md").read_text(encoding="utf-8")
    codex_bundle_path = root / "adapters" / "codex" / "scenario-lab" / "README.md"
    claude_bundle_path = root / "adapters" / "claude" / "scenario-lab" / "README.md"
    codex_bundle = codex_bundle_path.read_text(encoding="utf-8")
    claude_bundle = claude_bundle_path.read_text(encoding="utf-8")

    assert codex_doc
    assert claude_doc
    assert "Scenario Lab" in codex_doc
    assert "Scenario Lab" in claude_doc
    assert "adapters/codex/scenario-lab/install.py" in codex_doc
    assert "adapters/claude/scenario-lab/install.py" in claude_doc
    assert "adapters/codex/scenario-lab/smoke.py" in codex_doc
    assert "adapters/claude/scenario-lab/smoke.py" in claude_doc
    assert "docs/quickstart.md" in codex_doc
    assert "docs/natural-language-workflow.md" in codex_doc
    assert "docs/demo-us-iran.md" in codex_doc
    assert "docs/quickstart.md" in claude_doc
    assert "docs/natural-language-workflow.md" in claude_doc
    assert "docs/demo-us-iran.md" in claude_doc
    assert codex_bundle_path.is_file()
    assert claude_bundle_path.is_file()
    assert "Scenario Lab" in codex_bundle
    assert "Scenario Lab" in claude_bundle
    assert "install" in codex_bundle
    assert "install" in claude_bundle
    assert "smoke" in codex_bundle
    assert "smoke" in claude_bundle
