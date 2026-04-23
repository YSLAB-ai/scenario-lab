from pathlib import Path


def test_adapter_install_docs_use_scenario_lab_branding_and_public_links() -> None:
    root = Path(__file__).resolve().parents[3]
    docs_root = root / "docs"

    codex_doc = (docs_root / "install-codex.md").read_text(encoding="utf-8")
    claude_doc = (docs_root / "install-claude-code.md").read_text(encoding="utf-8")
    codex_bundle = (
        root / "adapters" / "codex" / "forecast-harness" / "README.md"
    ).read_text(encoding="utf-8")
    claude_bundle = (
        root / "adapters" / "claude" / "forecast-harness" / "README.md"
    ).read_text(encoding="utf-8")

    assert "Python 3.12+" in codex_doc
    assert "Python 3.12+" in claude_doc
    assert "pip install -e 'packages/core[dev]'" in codex_doc
    assert "pip install -e 'packages/core[dev]'" in claude_doc
    assert "# Scenario Lab for Codex" in codex_doc
    assert "# Scenario Lab for Claude" in claude_doc
    assert "PYTHON=/path/to/python3.12" in codex_doc
    assert "PYTHON=/path/to/python3.12" in claude_doc
    assert (
        "adapters/codex/forecast-harness/install.py --target-dir /tmp/codex-plugins"
        in codex_doc
    )
    assert (
        "adapters/claude/forecast-harness/install.py --target-dir /tmp/claude-root"
        in claude_doc
    )
    assert "--link" in codex_doc
    assert "--link" in claude_doc
    assert (
        "adapters/codex/forecast-harness/smoke.py --work-dir /tmp/scenario-lab-codex-smoke"
        in codex_doc
    )
    assert (
        "adapters/claude/forecast-harness/smoke.py --work-dir /tmp/scenario-lab-claude-smoke"
        in claude_doc
    )
    assert "docs/quickstart.md" in codex_doc
    assert "docs/natural-language-workflow.md" in codex_doc
    assert "docs/demo-us-iran.md" in codex_doc
    assert "docs/quickstart.md" in claude_doc
    assert "docs/natural-language-workflow.md" in claude_doc
    assert "docs/demo-us-iran.md" in claude_doc
    assert codex_bundle.startswith("# Scenario Lab Codex Bundle\n")
    assert claude_bundle.startswith("# Scenario Lab Claude Bundle\n")
    assert "Scenario Lab" in codex_bundle
    assert "Scenario Lab" in claude_bundle
    assert "packaged local bundle" in codex_bundle
    assert "packaged local bundle" in claude_bundle
    assert "verifies the end-to-end runtime path" in codex_bundle
    assert "verifies the end-to-end runtime path" in claude_bundle
    assert "packaged smoke flow" in codex_bundle
    assert "packaged smoke flow" in claude_bundle
