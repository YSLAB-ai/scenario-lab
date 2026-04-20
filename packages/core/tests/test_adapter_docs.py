from pathlib import Path


def test_adapter_install_docs_mention_demo_run() -> None:
    docs_root = Path(__file__).resolve().parents[3] / "docs"

    codex_doc = (docs_root / "install-codex.md").read_text()
    claude_doc = (docs_root / "install-claude-code.md").read_text()

    assert "forecast-harness demo-run" in codex_doc
    assert "forecast-harness demo-run" in claude_doc
