from __future__ import annotations

from pathlib import Path

import pytest

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.registry import build_default_registry
from forecasting_harness.models import BeliefState
from forecasting_harness.retrieval import CorpusRegistry
from forecasting_harness.workflow.models import AssumptionSummary, IntakeDraft
from forecasting_harness.workflow.service import WorkflowService


SCENARIOS = [
    {
        "run_id": "us-iran-gulf",
        "domain": "interstate-crisis",
        "intake": {
            "event_framing": "Assess 30-day escalation risk after a Gulf shipping strike and retaliatory warnings.",
            "focus_entities": ["United States", "Iran"],
            "current_development": "Iran-backed attacks on Gulf shipping are followed by US retaliatory threats and regional force movement.",
            "current_stage": "trigger",
            "time_horizon": "30d",
            "known_constraints": ["Energy market disruption would hurt both sides", "Regional allies are pressing for restraint"],
            "known_unknowns": ["Whether proxy militias will act independently"],
            "suggested_entities": ["Israel", "Gulf States"],
        },
        "assumptions": ["Neither side wants immediate total war"],
        "docs": {
            "us-iran-warning.md": "The United States warns Iran that any further attacks on Gulf shipping will trigger retaliation while allies push restraint.",
            "iran-mobilization.md": "Iran signals mobilization and missile readiness near the Gulf as regional diplomats attempt backchannel talks.",
        },
        "expected_sources": {"us-iran-warning", "iran-mobilization"},
        "expected_fields": {
            "alliance_pressure",
            "diplomatic_channel",
            "geographic_flashpoint",
            "leader_style",
            "mediation_window",
            "military_posture",
            "tension_index",
        },
    },
    {
        "run_id": "japan-china-strait",
        "domain": "interstate-crisis",
        "intake": {
            "event_framing": "Assess crisis dynamics after a Japanese naval transit through the Taiwan Strait triggers a Chinese military response.",
            "focus_entities": ["Japan", "China"],
            "current_development": "A Japanese naval transit through the Taiwan Strait triggers Chinese intercept threats and emergency diplomacy.",
            "current_stage": "trigger",
            "time_horizon": "21d",
            "known_constraints": ["Commercial shipping lanes must stay open", "US alliance commitments are under scrutiny"],
            "known_unknowns": ["Whether China will intercept directly"],
            "suggested_entities": ["United States", "Taiwan"],
        },
        "assumptions": ["Both parties want to avoid a shooting war"],
        "docs": {
            "japan-transit.md": "Japan defends the Taiwan Strait transit as lawful while China threatens an intercept and raises naval readiness.",
            "china-backchannel.md": "Chinese and Japanese officials keep emergency backchannel talks open to avoid a wider clash in the strait.",
        },
        "expected_sources": {"japan-transit", "china-backchannel"},
        "expected_fields": {
            "alliance_pressure",
            "diplomatic_channel",
            "geographic_flashpoint",
            "leader_style",
            "mediation_window",
            "military_posture",
            "tension_index",
        },
    },
    {
        "run_id": "india-pakistan-crisis",
        "domain": "interstate-crisis",
        "intake": {
            "event_framing": "Estimate escalation paths after a cross-border militant attack and military mobilization.",
            "focus_entities": ["India", "Pakistan"],
            "current_development": "A militant attack near the India-Pakistan border triggers mobilization, retaliatory rhetoric, and mediator pressure.",
            "current_stage": "trigger",
            "time_horizon": "14d",
            "known_constraints": ["Nuclear deterrence constrains open war", "International mediators are active"],
            "known_unknowns": ["Whether militant groups will attempt follow-on attacks"],
            "suggested_entities": ["China", "United States"],
        },
        "assumptions": ["Both governments need to signal resolve domestically"],
        "docs": {
            "border-attack.md": "India accuses Pakistan-linked militants after a border attack and threatens retaliation while both armies mobilize.",
            "mediator-restraint.md": "International mediators urge restraint as India and Pakistan keep diplomatic channels partially open.",
        },
        "expected_sources": {"border-attack", "mediator-restraint"},
        "expected_fields": {
            "alliance_pressure",
            "diplomatic_channel",
            "geographic_flashpoint",
            "leader_style",
            "mediation_window",
            "military_posture",
            "tension_index",
        },
    },
    {
        "run_id": "apple-ceo-transition",
        "domain": "company-action",
        "intake": {
            "event_framing": "Assess Apple strategy after a sudden CEO transition during product delays and margin pressure.",
            "focus_entities": ["Apple"],
            "current_development": "Apple faces a sudden CEO transition after product delays, investor concern, and supplier anxiety.",
            "current_stage": "trigger",
            "time_horizon": "180d",
            "known_constraints": ["Premium brand positioning must be preserved", "China supply exposure remains material"],
            "known_unknowns": ["Whether the board will favor an internal successor"],
            "suggested_entities": ["Board", "Key Customers"],
        },
        "assumptions": ["The board wants stability before the next product cycle"],
        "docs": {
            "apple-succession.md": "Analysts focus on Apple succession clarity, supplier reassurance, and investor concern after product delays.",
            "apple-roadmap.md": "Apple product roadmap credibility and premium brand messaging are central to calming customers and suppliers.",
        },
        "expected_sources": {"apple-succession", "apple-roadmap"},
        "expected_fields": {"board_cohesion", "brand_sentiment", "cash_runway_months", "operational_stability", "regulatory_pressure"},
    },
    {
        "run_id": "boeing-post-reporting",
        "domain": "company-action",
        "intake": {
            "event_framing": "Assess Boeing strategy after another weak quarter and renewed safety scrutiny.",
            "focus_entities": ["Boeing"],
            "current_development": "Boeing reports another weak quarter while safety scrutiny, delivery concerns, and customer anxiety intensify.",
            "current_stage": "trigger",
            "time_horizon": "180d",
            "known_constraints": ["Airline customers need delivery certainty", "Regulators are scrutinizing quality systems"],
            "known_unknowns": ["Whether the company can stabilize production rates quickly"],
            "suggested_entities": ["Regulator", "Key Customers"],
        },
        "assumptions": ["Management needs visible operational credibility quickly"],
        "docs": {
            "boeing-quarter.md": "Boeing faces investor concern, a weak quarter, and cash preservation pressure as delivery concerns mount.",
            "boeing-safety.md": "Safety scrutiny and regulatory pressure are forcing Boeing to reassure customers and defend production recovery.",
        },
        "expected_sources": {"boeing-quarter", "boeing-safety"},
        "expected_fields": {"board_cohesion", "brand_sentiment", "cash_runway_months", "operational_stability", "regulatory_pressure"},
    },
    {
        "run_id": "election-debate-collapse",
        "domain": "election-shock",
        "intake": {
            "event_framing": "Assess how a major debate collapse changes the final month of a national election.",
            "focus_entities": ["Incumbent Party", "Opposition Party"],
            "current_development": "A debate collapse forces both campaigns to reset strategy as party leadership scrambles to stabilize messaging.",
            "current_stage": "trigger",
            "time_horizon": "30d",
            "known_constraints": ["Early voting is already underway", "Donor confidence is volatile"],
            "known_unknowns": ["Whether swing voters interpret the event as a competency issue"],
            "suggested_entities": ["Media", "Party Leadership"],
        },
        "assumptions": ["Turnout effects may matter more than persuasion"],
        "docs": {
            "debate-fallout.md": "Party leadership scrambles to stabilize messaging after the debate while donor confidence softens.",
            "turnout-rescue.md": "Campaign organizers launch a turnout rescue plan to keep early vote mobilization from collapsing.",
        },
        "expected_sources": {"debate-fallout", "turnout-rescue"},
        "expected_fields": {"message_discipline", "poll_margin", "turnout_energy"},
    },
    {
        "run_id": "market-rate-shock",
        "domain": "market-shock",
        "intake": {
            "event_framing": "Assess market scenarios after an unexpected emergency rate hike.",
            "focus_entities": ["Central Bank", "Global Equity Market"],
            "current_development": "An emergency rate hike shocks funding markets, credit spreads, and rate expectations.",
            "current_stage": "trigger",
            "time_horizon": "14d",
            "known_constraints": ["Liquidity must be preserved", "Inflation credibility is at stake"],
            "known_unknowns": ["Whether dealers can absorb the repositioning cleanly"],
            "suggested_entities": ["Banks", "Treasury Market"],
        },
        "assumptions": ["Authorities will prioritize market functioning if stress worsens"],
        "docs": {
            "rate-shock.md": "The emergency rate hike triggers repricing across bonds and equities while liquidity stress rises.",
            "funding-stress.md": "Funding markets widen immediately and investors debate whether policy credibility has improved or deteriorated.",
        },
        "expected_sources": {"rate-shock", "funding-stress"},
        "expected_fields": {
            "contagion_risk",
            "liquidity_stress",
            "policy_credibility",
            "policy_optionality",
            "rate_pressure",
        },
    },
    {
        "run_id": "regulator-adtech",
        "domain": "regulatory-enforcement",
        "intake": {
            "event_framing": "Assess a large ad-tech platform response to an escalating enforcement case.",
            "focus_entities": ["AdTech Platform", "Competition Regulator"],
            "current_development": "A competition regulator escalates an ad-tech case and signals possible structural remedies.",
            "current_stage": "trigger",
            "time_horizon": "120d",
            "known_constraints": ["The company must protect major revenue lines", "Public scrutiny is intense"],
            "known_unknowns": ["Whether internal documents materially worsen the case"],
            "suggested_entities": ["Publishers", "Major Advertisers"],
        },
        "assumptions": ["A negotiated remedy is preferable to protracted litigation"],
        "docs": {
            "adtech-remedies.md": "Regulators signal willingness to seek structural remedies while industry partners brace for disruption.",
            "adtech-remediation.md": "The ad-tech platform expands internal remediation and coordinates with external counsel as enforcement momentum builds.",
        },
        "expected_sources": {"adtech-remedies", "adtech-remediation"},
        "expected_fields": {
            "compliance_posture",
            "enforcement_momentum",
            "litigation_readiness",
            "public_attention",
            "remedy_severity",
        },
    },
    {
        "run_id": "supply-rare-earth",
        "domain": "supply-chain-disruption",
        "intake": {
            "event_framing": "Assess rare-earth supply disruption after export restrictions and port delays.",
            "focus_entities": ["Battery Maker", "Rare Earth Supplier"],
            "current_development": "Export restrictions and port delays disrupt a rare-earth supply corridor for a battery maker.",
            "current_stage": "trigger",
            "time_horizon": "90d",
            "known_constraints": ["Downstream production schedules are inflexible", "Alternative sources are limited"],
            "known_unknowns": ["How quickly substitute processing routes can be certified"],
            "suggested_entities": ["Logistics Partners", "Key Customers"],
        },
        "assumptions": ["Customers will tolerate short delays before switching suppliers"],
        "docs": {
            "rare-earth-ports.md": "Port delays and export restrictions hit rare-earth materials needed by the battery maker.",
            "rare-earth-substitute.md": "Procurement teams scramble to qualify alternate sources for specialized rare-earth processing.",
        },
        "expected_sources": {"rare-earth-ports", "rare-earth-substitute"},
        "expected_fields": {
            "customer_penalty_pressure",
            "inventory_cover_days",
            "substitution_flexibility",
            "supplier_concentration",
            "transport_reliability",
        },
    },
    {
        "run_id": "supplier-flooding",
        "domain": "supply-chain-disruption",
        "intake": {
            "event_framing": "Assess an auto supply chain after flooding shuts a single-source electronics plant.",
            "focus_entities": ["Automaker", "Electronics Supplier"],
            "current_development": "Severe flooding shuts a single-source electronics plant feeding a major automaker.",
            "current_stage": "trigger",
            "time_horizon": "60d",
            "known_constraints": ["Vehicle launches are already committed", "Dealer inventories are thin"],
            "known_unknowns": ["Whether the supplier can restart partial output within two weeks"],
            "suggested_entities": ["Alternate Suppliers", "Logistics Partners"],
        },
        "assumptions": ["The automaker will prioritize its highest-margin models"],
        "docs": {
            "supplier-flood.md": "Flooding disrupts a single-source electronics plant and leaves the automaker with thin inventory cover.",
            "supplier-reroute.md": "The automaker and logistics partners consider rerouting and alternate suppliers to keep launches alive.",
        },
        "expected_sources": {"supplier-flood", "supplier-reroute"},
        "expected_fields": {
            "customer_penalty_pressure",
            "inventory_cover_days",
            "substitution_flexibility",
            "supplier_concentration",
            "transport_reliability",
        },
    },
]


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[scenario["run_id"] for scenario in SCENARIOS])
def test_realistic_scenario_smoke_campaign(tmp_path: Path, scenario: dict[str, object]) -> None:
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    registry = build_default_registry()
    service = WorkflowService(RunRepository(root), corpus_registry=CorpusRegistry(corpus_db), domain_registry=registry)

    pack = registry.resolve(str(scenario["domain"]))
    run_id = str(scenario["run_id"])
    service.start_run(run_id, pack.slug())
    intake = IntakeDraft.model_validate(scenario["intake"])
    service.save_intake_draft(run_id, "r1", intake)

    docs_dir = tmp_path / run_id
    docs_dir.mkdir()
    for filename, content in dict(scenario["docs"]).items():
        (docs_dir / filename).write_text(str(content), encoding="utf-8")

    recommendations = service.recommend_ingestion_files(run_id, "r1", pack=pack, path=docs_dir)
    ingest_result = service.batch_ingest_recommended_files(run_id, "r1", pack=pack, path=docs_dir, max_files=5)
    packet = service.draft_evidence_packet(run_id, "r1", pack=pack)
    assumptions = AssumptionSummary(summary=list(scenario["assumptions"]), suggested_actors=intake.suggested_entities)
    service.approve_revision(run_id, "r1", assumptions)
    simulation = service.simulate_revision(run_id, "r1", pack=pack)
    state = service.repository.load_revision_model(run_id, "belief-state", "r1", BeliefState, approved=True)

    expected_sources = set(scenario["expected_sources"])
    observed_sources = {item.source_id for item in packet.items}

    assert len(recommendations) == len(expected_sources)
    assert ingest_result.ingested_count == len(expected_sources)
    assert observed_sources == expected_sources
    assert simulation["branches"]
    assert simulation["node_count"] > 0
    assert simulation["search_mode"] == "mcts"
    for field_name in scenario["expected_fields"]:
        assert state.fields[field_name].status == "inferred"


def test_interstate_smoke_campaign_uses_more_than_one_root_strategy(tmp_path: Path) -> None:
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    registry = build_default_registry()
    service = WorkflowService(RunRepository(root), corpus_registry=CorpusRegistry(corpus_db), domain_registry=registry)

    top_root_labels: set[str] = set()
    for scenario in SCENARIOS[:3]:
        pack = registry.resolve(str(scenario["domain"]))
        run_id = str(scenario["run_id"])
        service.start_run(run_id, pack.slug())
        intake = IntakeDraft.model_validate(scenario["intake"])
        service.save_intake_draft(run_id, "r1", intake)

        docs_dir = tmp_path / run_id
        docs_dir.mkdir()
        for filename, content in dict(scenario["docs"]).items():
            (docs_dir / filename).write_text(str(content), encoding="utf-8")

        service.batch_ingest_recommended_files(run_id, "r1", pack=pack, path=docs_dir, max_files=5)
        service.draft_evidence_packet(run_id, "r1", pack=pack)
        assumptions = AssumptionSummary(summary=list(scenario["assumptions"]), suggested_actors=intake.suggested_entities)
        service.approve_revision(run_id, "r1", assumptions)
        simulation = service.simulate_revision(run_id, "r1", pack=pack)

        top_label = str(simulation["branches"][0]["label"])
        top_root_labels.add(top_label.split(" (", 1)[0])

    assert len(top_root_labels) >= 2


def test_company_smoke_campaign_uses_more_than_one_root_strategy(tmp_path: Path) -> None:
    root = tmp_path / ".forecast"
    corpus_db = tmp_path / "corpus.db"
    registry = build_default_registry()
    service = WorkflowService(RunRepository(root), corpus_registry=CorpusRegistry(corpus_db), domain_registry=registry)

    top_root_labels: set[str] = set()
    for scenario in SCENARIOS[3:5]:
        pack = registry.resolve(str(scenario["domain"]))
        run_id = str(scenario["run_id"])
        service.start_run(run_id, pack.slug())
        intake = IntakeDraft.model_validate(scenario["intake"])
        service.save_intake_draft(run_id, "r1", intake)

        docs_dir = tmp_path / run_id
        docs_dir.mkdir()
        for filename, content in dict(scenario["docs"]).items():
            (docs_dir / filename).write_text(str(content), encoding="utf-8")

        service.batch_ingest_recommended_files(run_id, "r1", pack=pack, path=docs_dir, max_files=5)
        service.draft_evidence_packet(run_id, "r1", pack=pack)
        assumptions = AssumptionSummary(summary=list(scenario["assumptions"]), suggested_actors=intake.suggested_entities)
        service.approve_revision(run_id, "r1", assumptions)
        simulation = service.simulate_revision(run_id, "r1", pack=pack)

        top_label = str(simulation["branches"][0]["label"])
        top_root_labels.add(top_label.split(" (", 1)[0])

    assert len(top_root_labels) >= 2
