from pathlib import Path


def test_adapter_install_docs_mention_demo_run() -> None:
    docs_root = Path(__file__).resolve().parents[3] / "docs"

    codex_doc = (docs_root / "install-codex.md").read_text()
    claude_doc = (docs_root / "install-claude-code.md").read_text()
    codex_skill = (
        Path(__file__).resolve().parents[3]
        / "adapters"
        / "codex"
        / "forecast-harness"
        / "skills"
        / "forecast-harness"
        / "SKILL.md"
    ).read_text()
    claude_skill = (
        Path(__file__).resolve().parents[3]
        / "adapters"
        / "claude"
        / "skills"
        / "forecast-harness"
        / "SKILL.md"
    ).read_text()

    assert "forecast-harness demo-run" in codex_doc
    assert "forecast-harness demo-run" in claude_doc
    assert "Python 3.12+" in codex_doc
    assert "Python 3.12+" in claude_doc
    assert "pip install -e 'packages/core[dev]'" in codex_doc
    assert "pip install -e 'packages/core[dev]'" in claude_doc
    assert "checked-out forecasting harness repo/workspace" in codex_skill
    assert "checked-out forecasting harness repo/workspace" in claude_skill
    assert "Python 3.12+" in codex_skill
    assert "Python 3.12+" in claude_skill
    assert "pip install -e 'packages/core[dev]'" in codex_skill
    assert "pip install -e 'packages/core[dev]'" in claude_skill
    assert "query-style commands" not in codex_skill
    assert "query-style commands" not in claude_skill
    assert "query-style commands" not in codex_doc
    assert "query-style commands" not in claude_doc


def test_adapter_docs_mention_new_workflow_commands() -> None:
    docs_root = Path(__file__).resolve().parents[3] / "docs"

    codex_doc = (docs_root / "install-codex.md").read_text(encoding="utf-8")
    claude_doc = (docs_root / "install-claude-code.md").read_text(encoding="utf-8")
    codex_skill = (
        Path(__file__).resolve().parents[3]
        / "adapters"
        / "codex"
        / "forecast-harness"
        / "skills"
        / "forecast-harness"
        / "SKILL.md"
    ).read_text(encoding="utf-8")
    claude_skill = (
        Path(__file__).resolve().parents[3]
        / "adapters"
        / "claude"
        / "skills"
        / "forecast-harness"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "forecast-harness start-run" in codex_doc
    assert "forecast-harness simulate" in codex_doc
    assert "forecast-harness start-run" in claude_doc
    assert "forecast-harness simulate" in claude_doc
    assert "forecast-harness start-run" in codex_skill
    assert "forecast-harness simulate" in codex_skill
    assert "forecast-harness start-run" in claude_skill
    assert "forecast-harness simulate" in claude_skill
