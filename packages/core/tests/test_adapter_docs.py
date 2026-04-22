from pathlib import Path


def test_adapter_install_docs_reference_guided_query_style_workflow() -> None:
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
        / "forecast-harness"
        / "skills"
        / "forecast-harness"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

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
    assert "query-style commands" in codex_skill
    assert "query-style commands" in claude_skill
    assert "query-style commands" in codex_doc
    assert "query-style commands" in claude_doc
    assert "direct structured input" in codex_doc
    assert "direct structured input" in claude_doc
    assert "direct structured input" in codex_skill
    assert "direct structured input" in claude_skill
    assert "after each workflow mutation" in codex_doc
    assert "after each workflow mutation" in claude_doc
    assert "after each workflow mutation" in codex_skill
    assert "after each workflow mutation" in claude_skill
    assert "install.py --target-dir" in codex_doc
    assert "install.py --target-dir" in claude_doc
    assert "PYTHON=/path/to/python3.12" in codex_doc
    assert "PYTHON=/path/to/python3.12" in claude_doc
    assert "/tmp/codex-plugins" in codex_doc
    assert "/tmp/claude-root" in claude_doc
    assert "--link" in codex_doc
    assert "--link" in claude_doc
    assert "smoke.py" in codex_doc
    assert "smoke.py" in claude_doc
    assert "forecast-harness demo-run" not in codex_doc
    assert "forecast-harness demo-run" not in claude_doc
    assert "forecast-harness demo-run" not in codex_skill
    assert "forecast-harness demo-run" not in claude_skill


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
        / "forecast-harness"
        / "skills"
        / "forecast-harness"
        / "SKILL.md"
    ).read_text(encoding="utf-8")

    assert "forecast-harness start-run" in codex_doc
    assert "forecast-harness save-intake-draft" in codex_doc
    assert "forecast-harness draft-intake-guidance" in codex_doc
    assert "forecast-harness draft-conversation-turn" in codex_doc
    assert "forecast-harness run-adapter-action" in codex_doc
    assert "forecast-harness draft-evidence-packet" in codex_doc
    assert "forecast-harness save-evidence-draft" in codex_doc
    assert "forecast-harness curate-evidence-draft" in codex_doc
    assert "forecast-harness draft-approval-packet" in codex_doc
    assert "forecast-harness approve-revision" in codex_doc
    assert "forecast-harness begin-revision-update" in codex_doc
    assert "forecast-harness simulate" in codex_doc
    assert "forecast-harness summarize-run" in codex_doc
    assert "forecast-harness summarize-revision" in codex_doc
    assert "forecast-harness generate-report" in codex_doc
    assert "forecast-harness start-run" in claude_doc
    assert "forecast-harness save-intake-draft" in claude_doc
    assert "forecast-harness draft-intake-guidance" in claude_doc
    assert "forecast-harness draft-conversation-turn" in claude_doc
    assert "forecast-harness run-adapter-action" in claude_doc
    assert "forecast-harness draft-evidence-packet" in claude_doc
    assert "forecast-harness save-evidence-draft" in claude_doc
    assert "forecast-harness curate-evidence-draft" in claude_doc
    assert "forecast-harness draft-approval-packet" in claude_doc
    assert "forecast-harness approve-revision" in claude_doc
    assert "forecast-harness begin-revision-update" in claude_doc
    assert "forecast-harness simulate" in claude_doc
    assert "forecast-harness summarize-run" in claude_doc
    assert "forecast-harness summarize-revision" in claude_doc
    assert "forecast-harness generate-report" in claude_doc
    assert "forecast-harness start-run" in codex_skill
    assert "forecast-harness save-intake-draft" in codex_skill
    assert "forecast-harness draft-intake-guidance" in codex_skill
    assert "forecast-harness draft-conversation-turn" in codex_skill
    assert "forecast-harness run-adapter-action" in codex_skill
    assert "forecast-harness draft-evidence-packet" in codex_skill
    assert "forecast-harness save-evidence-draft" in codex_skill
    assert "forecast-harness curate-evidence-draft" in codex_skill
    assert "forecast-harness draft-approval-packet" in codex_skill
    assert "forecast-harness approve-revision" in codex_skill
    assert "forecast-harness begin-revision-update" in codex_skill
    assert "forecast-harness simulate" in codex_skill
    assert "forecast-harness summarize-run" in codex_skill
    assert "forecast-harness summarize-revision" in codex_skill
    assert "forecast-harness generate-report" in codex_skill
    assert "forecast-harness start-run" in claude_skill
    assert "forecast-harness save-intake-draft" in claude_skill
    assert "forecast-harness draft-intake-guidance" in claude_skill
    assert "forecast-harness draft-conversation-turn" in claude_skill
    assert "forecast-harness run-adapter-action" in claude_skill
    assert "forecast-harness draft-evidence-packet" in claude_skill
    assert "forecast-harness save-evidence-draft" in claude_skill
    assert "forecast-harness curate-evidence-draft" in claude_skill
    assert "forecast-harness draft-approval-packet" in claude_skill
    assert "forecast-harness approve-revision" in claude_skill
    assert "forecast-harness begin-revision-update" in claude_skill
    assert "forecast-harness simulate" in claude_skill
    assert "forecast-harness summarize-run" in claude_skill
    assert "forecast-harness summarize-revision" in claude_skill
    assert "forecast-harness generate-report" in claude_skill
