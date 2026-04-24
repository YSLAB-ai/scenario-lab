from pathlib import Path


LANGUAGE_SWITCHER = (
    "🌐 Languages: [English](README.md) | [中文](README.zh-CN.md) | "
    "[Español](README.es.md) | [Français](README.fr.md) | "
    "[한국어](README.ko.md) | [日本語](README.ja.md)"
)


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
    release_notes = (root / "docs" / "release-notes" / "public-preview.md").read_text(
        encoding="utf-8"
    )

    assert readme.startswith("# Scenario Lab")
    assert LANGUAGE_SWITCHER in readme
    assert "U.S.-Iran" in readme
    assert "scenario-lab demo-run --root .forecast" in readme
    assert "## Evidence Corpus" in readme
    assert ".forecast/corpus.db" in readme
    assert "Monte Carlo tree search" in readme
    assert "Version: `v0.1.0`" in readme
    assert "[CONTRIBUTORS.md](CONTRIBUTORS.md)" in readme
    assert "## License And Disclaimer" in readme
    assert "MIT License" in readme
    assert "PolyForm" not in readme
    assert "Noncommercial" not in readme
    assert "Heuristic Search Group LLC" not in readme
    assert "not a prediction product" in readme
    assert "No major escalation; allies push talks, then a tense stalemate." in readme
    assert "Engine label: `Alliance consultation (coordinated signaling)`" in readme
    assert "Warnings increase, then a tense stalemate." in readme
    assert "Engine label: `Signal resolve (managed signal)`" in readme
    assert "Talks stay open, but the crisis remains unresolved." in readme
    assert "Engine label: `Open negotiation`" in readme
    assert "Allies push talks, then a tense stalemate." in readme
    assert "Engine label: `Alliance consultation -> settlement-stalemate`" in readme
    assert "In short: outside powers pressure both sides to keep diplomacy open" in readme
    assert "Warnings increase, then a tense stalemate." in readme
    assert "Engine label: `Signal resolve -> settlement-stalemate`" in readme
    assert "Talks stay open, then a tense stalemate." in readme
    assert "Engine label: `Open negotiation -> settlement-stalemate`" in readme
    assert "Plain-English reading:" not in readme
    assert "does not model full-scale war as an explicit terminal outcome" in readme
    assert "the top three branches were very close together" in readme
    assert "it did not find a runaway winner" in readme
    assert "third-party actors carried into the run" in readme
    assert "[docs/quickstart.md](docs/quickstart.md)" in readme
    assert (
        "[docs/natural-language-workflow.md](docs/natural-language-workflow.md)"
        in readme
    )
    assert "[docs/demo-us-iran.md](docs/demo-us-iran.md)" in readme
    assert "[docs/domain-pack-enrichment.md](docs/domain-pack-enrichment.md)" in readme
    assert "[docs/limitations.md](docs/limitations.md)" in readme
    assert "[LICENSE](LICENSE)" in readme
    assert "docs/assets/scenario-lab-workflow.png" in readme
    assert "docs/assets/scenario-lab-runtime-workflow.png" in readme
    assert "/Volumes/" not in readme
    assert "scenario-lab demo-run --root .forecast" in quickstart
    assert "## 4. Build an evidence corpus" in quickstart
    assert "scenario-lab ingest-directory --root .forecast" in quickstart
    assert "scenario-lab draft-evidence-packet --root .forecast" in quickstart
    assert "## Actual runtime phases" in workflow
    assert "batch-ingest-recommended" in workflow
    assert "intake -> evidence -> approval -> simulation -> report" in workflow
    assert "No major escalation; allies push talks, then a tense stalemate." in workflow
    assert "Engine label: `Alliance consultation (coordinated signaling)`" in workflow
    assert "Warnings increase, then a tense stalemate." in workflow
    assert "Engine label: `Signal resolve (managed signal)`" in workflow
    assert "Talks stay open, but the crisis remains unresolved." in workflow
    assert "Engine label: `Open negotiation`" in workflow
    assert "The top three scores stayed very close together" in workflow
    assert "the engine did not find a runaway winner" in workflow
    assert "scenario-lab" in metadata
    assert "YSLAB-ai" in metadata
    assert "Version: `v0.1.0`" in release_notes
    assert "YSLAB-ai" in release_notes
    assert "OpenAI Codex" in release_notes


def test_public_docs_and_assets_exist() -> None:
    root = Path(__file__).resolve().parents[3]
    demo_doc = (root / "docs" / "demo-us-iran.md").read_text(encoding="utf-8")
    metadata_doc = (root / "docs" / "github-public-metadata.md").read_text(
        encoding="utf-8"
    )
    limitations_doc = (root / "docs" / "limitations.md").read_text(encoding="utf-8")
    enrichment_doc = (root / "docs" / "domain-pack-enrichment.md").read_text(
        encoding="utf-8"
    )
    workflow_asset = root / "docs" / "assets" / "scenario-lab-workflow.png"
    runtime_workflow_asset = root / "docs" / "assets" / "scenario-lab-runtime-workflow.png"
    social_preview_asset = root / "docs" / "assets" / "scenario-lab-social-preview.png"

    assert (root / "docs" / "quickstart.md").is_file()
    assert (root / "docs" / "natural-language-workflow.md").is_file()
    assert (root / "docs" / "demo-us-iran.md").is_file()
    assert (root / "docs" / "domain-pack-enrichment.md").is_file()
    assert (root / "docs" / "limitations.md").is_file()
    assert (root / "LICENSE").is_file()
    assert not (root / "NOTICE").exists()
    assert (root / "CONTRIBUTORS.md").is_file()
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
    assert "No major escalation; allies push talks, then a tense stalemate." in demo_doc
    assert "Engine label: `Alliance consultation (coordinated signaling)`" in demo_doc
    assert "Warnings increase, then a tense stalemate." in demo_doc
    assert "Engine label: `Signal resolve (managed signal)`" in demo_doc
    assert "Talks stay open, but the crisis remains unresolved." in demo_doc
    assert "Engine label: `Open negotiation`" in demo_doc
    assert "Allies push talks, then a tense stalemate." in demo_doc
    assert "Engine label: `Alliance consultation -> settlement-stalemate`" in demo_doc
    assert "In short: outside powers pressure both sides to keep diplomacy open" in demo_doc
    assert "Warnings increase, then a tense stalemate." in demo_doc
    assert "Engine label: `Signal resolve -> settlement-stalemate`" in demo_doc
    assert "Talks stay open, then a tense stalemate." in demo_doc
    assert "Engine label: `Open negotiation -> settlement-stalemate`" in demo_doc
    assert "Plain-English reading:" not in demo_doc
    assert "does not model full-scale war as an explicit terminal outcome" in demo_doc
    assert "the top of the ranking stayed tight rather than decisive" in demo_doc
    assert "MIT License" in limitations_doc
    assert "PolyForm" not in limitations_doc
    assert "Noncommercial" not in limitations_doc
    assert "Heuristic Search Group LLC" not in limitations_doc
    assert "not a prediction product" in limitations_doc
    assert "scenario-lab" in metadata_doc
    assert "github.com/YSLAB-ai/scenario-lab" in metadata_doc
    assert "stock-market-prediction" in metadata_doc
    assert "stock-market prediction research" in metadata_doc
    assert "not financial advice" in metadata_doc
    assert "How To Improve A Domain Pack" in enrichment_doc
    assert "compile-revision-knowledge" in enrichment_doc
    assert "compile-replay-knowledge" in enrichment_doc
    assert "run-replay-retuning" in enrichment_doc
    assert "run-domain-evolution" in enrichment_doc
    assert "Do not edit shared simulation code" in enrichment_doc
    contributors_doc = (root / "CONTRIBUTORS.md").read_text(encoding="utf-8")
    assert "YSLAB-ai" in contributors_doc
    assert "OpenAI Codex" in contributors_doc
    assert "AI coding agent" in contributors_doc
    assert "Heuristic Search Group LLC" not in contributors_doc


def test_multilingual_readmes_exist_and_link_to_canonical_english_readme() -> None:
    root = Path(__file__).resolve().parents[3]
    localized_readmes = {
        "README.zh-CN.md": {
            "language": "中文",
            "domain_pack": "领域包",
            "interstate_crisis": "国家间危机",
            "market_shock": "市场冲击",
            "financial_advice": "不是金融建议",
        },
        "README.es.md": {
            "language": "Español",
            "domain_pack": "paquete de dominio",
            "interstate_crisis": "crisis interestatal",
            "market_shock": "choque de mercado",
            "financial_advice": "no es asesoramiento financiero",
        },
        "README.fr.md": {
            "language": "Français",
            "domain_pack": "paquet de domaine",
            "interstate_crisis": "crise interétatique",
            "market_shock": "choc de marché",
            "financial_advice": "ne constitue pas un conseil financier",
        },
        "README.ko.md": {
            "language": "한국어",
            "domain_pack": "도메인 팩",
            "interstate_crisis": "국가 간 위기",
            "market_shock": "시장 충격",
            "financial_advice": "금융 조언이 아닙니다",
        },
        "README.ja.md": {
            "language": "日本語",
            "domain_pack": "ドメインパック",
            "interstate_crisis": "国家間危機",
            "market_shock": "市場ショック",
            "financial_advice": "金融助言ではありません",
        },
    }
    untranslated_phrases = [
        "domain pack",
        "interstate crisis",
        "market shock",
        "company decision",
        "evidence packet",
        "belief state",
        "actor behavior profiles",
        "simulation engine",
        "scenario families",
        "calibrated confidence",
        "bounded crisis paths",
        "terminal outcome",
        "prediction product",
        "financial advice",
        "public preview",
    ]

    for filename, expected in localized_readmes.items():
        content = (root / filename).read_text(encoding="utf-8")
        assert content.startswith("# Scenario Lab")
        assert LANGUAGE_SWITCHER in content
        assert expected["language"] in content
        assert "English README is canonical" in content
        assert "v0.1.0" in content
        assert "MIT License" in content
        assert "PolyForm" not in content
        assert "Noncommercial" not in content
        assert "Heuristic Search Group LLC" not in content
        assert expected["domain_pack"] in content
        assert expected["interstate_crisis"] in content
        assert expected["market_shock"] in content
        assert expected["financial_advice"] in content
        assert "[CONTRIBUTORS.md](CONTRIBUTORS.md)" in content
        lower_content = content.lower()
        for phrase in untranslated_phrases:
            assert phrase not in lower_content, f"{filename} still contains {phrase!r}"
