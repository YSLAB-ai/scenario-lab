from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path

import pytest

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.compatibility import compare_belief_states
from forecasting_harness.domain.company_action import CompanyActionPack
from forecasting_harness.domain.election_shock import ElectionShockPack
from forecasting_harness.domain.interstate_crisis import InterstateCrisisPack
from forecasting_harness.domain.regulatory_enforcement import RegulatoryEnforcementPack
from forecasting_harness.models import BeliefState
from forecasting_harness.retrieval import CorpusRegistry
from forecasting_harness.query_api import summarize_top_branches
from forecasting_harness.workflow.compiler import compile_belief_state
from forecasting_harness.workflow.models import (
    ApprovalPacket,
    AssumptionSummary,
    BatchIngestionResult,
    ConversationTurn,
    EvidencePacket,
    EvidencePacketItem,
    IngestionRecommendation,
    IngestionPlan,
    IntakeGuidance,
    IntakeDraft,
    RetrievalPlan,
    RunRecord,
)
from forecasting_harness.workflow.service import WorkflowService


class _FrozenDateTime:
    @classmethod
    def now(cls, tz: timezone | None = None) -> datetime:
        assert tz == timezone.utc
        return datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc)


@dataclass
class _FakeRepository:
    initialized_runs: list[RunRecord] = field(default_factory=list)
    saved_runs: list[RunRecord] = field(default_factory=list)
    saved_revision_records: list[object] = field(default_factory=list)
    written_revision_json: list[tuple[str, str, str, object, bool]] = field(default_factory=list)
    loaded_revision_models: list[tuple[str, str, str, type, bool]] = field(default_factory=list)
    appended_events: list[tuple[str, str, dict[str, object]]] = field(default_factory=list)
    run_record: RunRecord | None = None
    revision_payloads: dict[tuple[str, str, str, bool], object] = field(default_factory=dict)
    revision_records: dict[tuple[str, str], object] = field(default_factory=dict)

    def init_run(self, run: RunRecord) -> None:
        self.initialized_runs.append(run)

    def save_run_record(self, run: RunRecord) -> None:
        self.saved_runs.append(run)
        self.run_record = run

    def load_run_record(self, run_id: str) -> RunRecord:
        assert self.run_record is not None
        assert self.run_record.run_id == run_id
        return self.run_record

    def save_revision_record(self, run_id: str, record: object) -> None:
        self.saved_revision_records.append(record)
        self.revision_records[(run_id, record.revision_id)] = record

    def load_revision_record(self, run_id: str, revision_id: str):
        try:
            return self.revision_records[(run_id, revision_id)]
        except KeyError as exc:
            raise FileNotFoundError(revision_id) from exc

    def write_revision_json(
        self,
        run_id: str,
        section: str,
        revision_id: str,
        payload: object,
        *,
        approved: bool,
    ) -> None:
        self.written_revision_json.append((run_id, section, revision_id, payload, approved))

    def load_revision_model(
        self,
        run_id: str,
        section: str,
        revision_id: str,
        model_type: type,
        *,
        approved: bool,
    ):
        self.loaded_revision_models.append((run_id, section, revision_id, model_type, approved))
        payload = self.revision_payloads[(run_id, section, revision_id, approved)]
        return model_type.model_validate(payload)

    def append_event(self, run_id: str, event_type: str, payload: dict[str, object]) -> None:
        self.appended_events.append((run_id, event_type, payload))


def _make_run(run_id: str = "run-1") -> RunRecord:
    return RunRecord(
        run_id=run_id,
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, 11, 59, tzinfo=timezone.utc),
    )


def _make_intake() -> IntakeDraft:
    return IntakeDraft(
        event_framing="A policy shift is underway.",
        primary_actors=["country-a", "country-b"],
        trigger="policy change",
        current_phase="trigger",
        time_horizon="2026-Q2",
        known_constraints=["sanctions"],
        known_unknowns=["timing"],
        suggested_actors=["country-c"],
    )


def _make_evidence(revision_id: str = "rev-1") -> EvidencePacket:
    return EvidencePacket(revision_id=revision_id)


def _make_revision_inputs(revision_id: str, *, evidence_count: int = 1) -> tuple[IntakeDraft, EvidencePacket, AssumptionSummary]:
    intake = _make_intake()
    evidence = EvidencePacket(
        revision_id=revision_id,
        items=[
            EvidencePacketItem(
                evidence_id=f"{revision_id}-ev-{index}",
                source_id=f"source-{index}",
                source_title=f"Source {index}",
                reason="supports the forecast",
            )
            for index in range(evidence_count)
        ],
    )
    assumptions = AssumptionSummary(summary=["assumption-1"], suggested_actors=["country-c"])
    return intake, evidence, assumptions


def test_start_run_initializes_the_run_and_records_a_started_event(monkeypatch: pytest.MonkeyPatch) -> None:
    from forecasting_harness.workflow import service as workflow_service

    monkeypatch.setattr(workflow_service, "datetime", _FrozenDateTime)
    repository = _FakeRepository()
    service = WorkflowService(repository)

    run = service.start_run("run-1", "interstate-crisis")

    assert run == RunRecord(
        run_id="run-1",
        domain_pack="interstate-crisis",
        created_at=datetime(2026, 4, 20, 12, 0, tzinfo=timezone.utc),
    )
    assert repository.initialized_runs == [run]
    assert repository.appended_events == [("run-1", "run-started", {"run_id": "run-1"})]


def test_start_run_rejects_duplicate_run_ids_with_real_repository(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from forecasting_harness.workflow import service as workflow_service

    monkeypatch.setattr(workflow_service, "datetime", _FrozenDateTime)
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)

    first_run = service.start_run("run-1", "interstate-crisis")

    assert first_run.run_id == "run-1"

    with pytest.raises(FileExistsError):
        service.start_run("run-1", "interstate-crisis")

    loaded = repository.load_run_record("run-1")
    assert loaded == first_run


def test_save_intake_draft_writes_the_intake_snapshot_and_records_an_event() -> None:
    repository = _FakeRepository(run_record=_make_run())
    service = WorkflowService(repository)
    intake = _make_intake()

    service.save_intake_draft("run-1", "rev-1", intake)

    assert repository.written_revision_json == [
        ("run-1", "intake", "rev-1", intake.model_dump(mode="json"), False)
    ]
    assert repository.appended_events == [("run-1", "intake-drafted", {"revision_id": "rev-1"})]


def test_save_intake_draft_rejects_invalid_pack_specific_shape() -> None:
    repository = _FakeRepository(run_record=_make_run())
    service = WorkflowService(repository)
    intake = IntakeDraft(
        event_framing="A policy shift is underway.",
        focus_entities=["country-a"],
        current_development="policy change",
        current_stage="trigger",
        time_horizon="2026-Q2",
    )

    with pytest.raises(ValueError, match="exactly two focus entities"):
        service.save_intake_draft("run-1", "rev-1", intake)


def test_save_intake_draft_rejects_unknown_pack_fields() -> None:
    repository = _FakeRepository(run_record=_make_run())
    service = WorkflowService(repository)
    intake = IntakeDraft(
        event_framing="A policy shift is underway.",
        focus_entities=["country-a", "country-b"],
        current_development="policy change",
        current_stage="trigger",
        time_horizon="2026-Q2",
        pack_fields={"unexpected_field": "value"},
    )

    with pytest.raises(ValueError, match="unknown pack_fields"):
        service.save_intake_draft("run-1", "rev-1", intake)


def test_save_evidence_draft_writes_the_evidence_snapshot_and_records_an_event() -> None:
    repository = _FakeRepository()
    service = WorkflowService(repository)
    packet = _make_evidence()

    service.save_evidence_draft("run-1", "rev-1", packet)

    assert repository.written_revision_json == [
        ("run-1", "evidence", "rev-1", packet.model_dump(mode="json"), False)
    ]
    assert repository.appended_events == [("run-1", "evidence-drafted", {"revision_id": "rev-1"})]


def test_save_evidence_draft_rejects_revision_id_mismatches() -> None:
    repository = _FakeRepository()
    service = WorkflowService(repository)
    packet = _make_evidence(revision_id="rev-2")

    with pytest.raises(ValueError, match="revision_id"):
        service.save_evidence_draft("run-1", "rev-1", packet)

    assert repository.written_revision_json == []
    assert repository.appended_events == []


def test_draft_intake_guidance_uses_domain_pack_hooks(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess escalation",
        primary_actors=["US", "Iran"],
        trigger="Exchange of strikes",
        current_phase="trigger",
        time_horizon="30d",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)

    guidance = service.draft_intake_guidance("crisis-1", "r1")

    assert isinstance(guidance, IntakeGuidance)
    assert guidance.domain_pack == "interstate-crisis"
    assert guidance.current_stage == "trigger"
    assert "China" in guidance.suggested_entities
    assert "military_posture" in guidance.pack_field_schema


def test_compile_belief_state_infers_actor_behavior_profiles_from_interstate_signals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess whether domestic resolve and alliance signaling drive the next Taiwan Strait phase.",
            focus_entities=["China", "Taiwan"],
            current_development=(
                "Beijing is signaling resolve ahead of domestic political meetings while Taipei emphasizes"
                " alliance coordination and US security support."
            ),
            current_stage="signaling",
            time_horizon="30d",
            known_constraints=["Leaders face domestic audience costs."],
            suggested_entities=["US"],
        ),
        assumptions=AssumptionSummary(
            summary=[
                "Chinese leaders are sensitive to domestic resolve narratives.",
                "Taiwan is relying on alliance signaling and US backing."
            ],
            suggested_actors=["Japan"],
        ),
        approved_evidence_ids=["ev-1", "ev-2"],
        approved_evidence_items=[
            EvidencePacketItem(
                evidence_id="ev-1",
                source_id="src-1",
                source_title="Resolve signal",
                reason="Supports domestic resolve pressure",
                raw_passages=[
                    "Chinese officials framed the exercise as a resolve signal for domestic audiences before party meetings."
                ],
            ),
            EvidencePacketItem(
                evidence_id="ev-2",
                source_id="src-2",
                source_title="Alliance signal",
                reason="Supports alliance dependence",
                raw_passages=[
                    "Taiwanese officials highlighted alliance coordination, US support, and broader security commitments."
                ],
            ),
        ],
    )

    actors = {actor.name: actor for actor in state.actors}

    assert actors["China"].behavior_profile is not None
    assert actors["China"].behavior_profile.domestic_sensitivity is not None
    assert actors["China"].behavior_profile.domestic_sensitivity > 0.6
    assert actors["Taiwan"].behavior_profile is not None
    assert actors["Taiwan"].behavior_profile.alliance_dependence is not None
    assert actors["Taiwan"].behavior_profile.alliance_dependence > 0.6


def test_compile_belief_state_does_not_match_us_actor_from_russia_substring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess alliance signaling.",
            focus_entities=["US", "Russia"],
            current_development="Russia is discussing alliance coordination and domestic resolve.",
            current_stage="signaling",
            time_horizon="30d",
        ),
        assumptions=AssumptionSummary(),
        approved_evidence_ids=["ev-1"],
        approved_evidence_items=[
            EvidencePacketItem(
                evidence_id="ev-1",
                source_id="src-1",
                source_title="Russia note",
                reason="Only mentions Russia",
                raw_passages=[
                    "Russia signaled domestic resolve and alliance coordination after the latest move."
                ],
            )
        ],
    )

    actors = {actor.name: actor for actor in state.actors}

    assert actors["Russia"].behavior_profile is not None
    assert actors["US"].behavior_profile is None


def test_compile_belief_state_does_not_fabricate_profile_from_suggested_entity_listing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess escalation around the strait.",
            focus_entities=["China", "Taiwan"],
            current_development="Military signaling continues without naming outside backers.",
            current_stage="signaling",
            time_horizon="30d",
            suggested_entities=["United States"],
        ),
        assumptions=AssumptionSummary(),
        approved_evidence_ids=[],
        approved_evidence_items=[],
    )

    actors = {actor.name: actor for actor in state.actors}

    assert actors["United States"].behavior_profile is None


def test_compile_belief_state_matches_united_states_and_us_aliases_symmetrically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    united_states_state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess alliance signaling and security support.",
            focus_entities=["United States", "Taiwan"],
            current_development="Taipei is emphasizing alliance coordination.",
            current_stage="signaling",
            time_horizon="30d",
        ),
        assumptions=AssumptionSummary(
            summary=["US security support and alliance coordination remain central."]
        ),
        approved_evidence_ids=[],
        approved_evidence_items=[],
    )
    us_state = compile_belief_state(
        run_id="crisis-2",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess alliance signaling and security support.",
            focus_entities=["US", "Taiwan"],
            current_development="Taipei is emphasizing alliance coordination.",
            current_stage="signaling",
            time_horizon="30d",
        ),
        assumptions=AssumptionSummary(
            summary=["United States security support and alliance coordination remain central."]
        ),
        approved_evidence_ids=[],
        approved_evidence_items=[],
    )

    united_states_actor = {actor.name: actor for actor in united_states_state.actors}["United States"]
    us_actor = {actor.name: actor for actor in us_state.actors}["US"]

    assert united_states_actor.behavior_profile is not None
    assert united_states_actor.behavior_profile.alliance_dependence is not None
    assert us_actor.behavior_profile is not None
    assert us_actor.behavior_profile.alliance_dependence is not None


def test_compile_belief_state_matches_us_punctuation_variant_symmetrically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    punctuated_state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess alliance signaling and security support.",
            focus_entities=["U.S.", "Taiwan"],
            current_development="Taipei is emphasizing alliance coordination.",
            current_stage="signaling",
            time_horizon="30d",
        ),
        assumptions=AssumptionSummary(
            summary=["United States security support and alliance coordination remain central."]
        ),
        approved_evidence_ids=[],
        approved_evidence_items=[],
    )
    united_states_state = compile_belief_state(
        run_id="crisis-2",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess alliance signaling and security support.",
            focus_entities=["United States", "Taiwan"],
            current_development="Taipei is emphasizing alliance coordination.",
            current_stage="signaling",
            time_horizon="30d",
        ),
        assumptions=AssumptionSummary(
            summary=["U.S. security support and alliance coordination remain central."]
        ),
        approved_evidence_ids=[],
        approved_evidence_items=[],
    )

    punctuated_actor = {actor.name: actor for actor in punctuated_state.actors}["U.S."]
    united_states_actor = {actor.name: actor for actor in united_states_state.actors}["United States"]

    assert punctuated_actor.behavior_profile is not None
    assert punctuated_actor.behavior_profile.alliance_dependence is not None
    assert united_states_actor.behavior_profile is not None
    assert united_states_actor.behavior_profile.alliance_dependence is not None


def test_compile_belief_state_dedupes_united_states_alias_family_to_one_actor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    state = compile_belief_state(
        run_id="crisis-1",
        revision_id="r1",
        pack=InterstateCrisisPack(),
        intake=IntakeDraft(
            event_framing="Assess alliance signaling and security support.",
            focus_entities=["US", "Taiwan"],
            current_development="Taipei is emphasizing alliance coordination.",
            current_stage="signaling",
            time_horizon="30d",
            suggested_entities=["United States", "U.S."],
        ),
        assumptions=AssumptionSummary(
            suggested_actors=["United States", "U.S.", "Japan"],
        ),
        approved_evidence_ids=[],
        approved_evidence_items=[],
    )

    assert [actor.name for actor in state.actors] == ["US", "Taiwan", "Japan"]


def test_compile_belief_state_persists_canonical_actor_ids_for_united_states_aliases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from forecasting_harness.workflow import compiler as workflow_compiler

    monkeypatch.setattr(workflow_compiler, "datetime", _FrozenDateTime)

    def _compile(alias: str, run_id: str) -> BeliefState:
        return compile_belief_state(
            run_id=run_id,
            revision_id="r1",
            pack=InterstateCrisisPack(),
            intake=IntakeDraft(
                event_framing="Assess alliance signaling and security support.",
                focus_entities=[alias, "China"],
                current_development="Alliance coordination and security support remain central.",
                current_stage="signaling",
                time_horizon="30d",
            ),
            assumptions=AssumptionSummary(
                summary=["United States security support and alliance coordination remain central."]
            ),
            approved_evidence_ids=[],
            approved_evidence_items=[],
        )

    united_states_state = _compile("United States", "crisis-1")
    us_state = _compile("US", "crisis-2")
    punctuated_state = _compile("U.S.", "crisis-3")

    for state in (united_states_state, us_state, punctuated_state):
        actor = next(item for item in state.actors if item.name != "China")
        assert actor.actor_id == "united-states"

    assert compare_belief_states(united_states_state, us_state, tolerances={})["reasons"] == []
    assert compare_belief_states(united_states_state, punctuated_state, tolerances={})["reasons"] == []


def test_draft_approval_packet_summarizes_evidence_and_warnings(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, _ = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)

    packet = service.draft_approval_packet("crisis-1", "r1")

    assert isinstance(packet, ApprovalPacket)
    assert packet.revision_id == "r1"
    assert packet.evidence_summary[0]["source_id"] == "source-0"
    assert "known unknowns remain unresolved" in packet.warnings


def test_draft_approval_packet_includes_actor_preferences_and_recommended_run_lens(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess domestic resolve and alliance security after the exchange of strikes.",
        primary_actors=["United States", "Iran"],
        trigger="U.S. leaders weigh domestic resolve and alliance security commitments after the exchange of strikes.",
        current_phase="trigger",
        time_horizon="30d",
        known_constraints=["United States alliance security backing remains visible."],
        known_unknowns=["United States domestic audience response is still uncertain."],
    )
    evidence = EvidencePacket(
        revision_id="r1",
        items=[
            EvidencePacketItem(
                evidence_id="r1-ev-1",
                source_id="doc-1",
                source_title="Doc 1",
                reason="Relevant context",
                raw_passages=[
                    (
                        "United States officials described domestic political pressure, public resolve, "
                        "and alliance security backing as the main constraints."
                    )
                ],
            )
        ],
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)

    packet = service.draft_approval_packet("crisis-1", "r1")

    assert packet.actor_preferences
    united_states = next(item for item in packet.actor_preferences if item["actor_id"] == "united-states")
    assert united_states["preferences"]["domestic_sensitivity"] >= 0.7
    assert united_states["preferences"]["alliance_dependence"] >= 0.7
    assert packet.recommended_run_lens["name"] == "domestic-politics-first"
    assert packet.recommended_run_lens["aggregation_mode"] == "focal-actor"
    assert packet.recommended_run_lens["focal_actor_id"] == "united-states"


def test_approve_revision_defaults_to_recommended_run_lens_when_none_selected(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess domestic resolve and alliance security after the exchange of strikes.",
        focus_entities=["United States", "Iran"],
        current_development="U.S. leaders weigh domestic resolve and alliance security commitments after the exchange of strikes.",
        current_stage="trigger",
        time_horizon="30d",
        known_constraints=["United States alliance security backing remains visible."],
        known_unknowns=["United States domestic audience response is still uncertain."],
    )
    evidence = EvidencePacket(
        revision_id="r1",
        items=[
            EvidencePacketItem(
                evidence_id="r1-ev-1",
                source_id="doc-1",
                source_title="Doc 1",
                reason="Relevant context",
                raw_passages=[
                    (
                        "United States officials described domestic political pressure, public resolve, "
                        "and alliance security backing as the main constraints."
                    )
                ],
            )
        ],
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", AssumptionSummary())

    approved_assumptions = repository.load_revision_model(
        "crisis-1", "assumptions", "r1", AssumptionSummary, approved=True
    )
    result = service.simulate_revision("crisis-1", "r1", pack=pack)
    approved_state = repository.load_revision_model(
        "crisis-1", "belief-state", "r1", BeliefState, approved=True
    )

    assert approved_assumptions.objective_profile_name == ""
    assert approved_state.objectives["selected_run_lens"] == "domestic-politics-first"
    assert approved_state.objectives["focal_actor_id"] == "united-states"
    assert result["aggregation_lens"]["name"] == "domestic-politics-first"
    assert result["aggregation_lens"]["focal_actor_id"] == "united-states"


def test_summarize_run_returns_revision_statuses(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    intake_r1, evidence_r1, assumptions_r1 = _make_revision_inputs("r1")
    service.save_intake_draft("crisis-1", "r1", intake_r1)
    service.save_evidence_draft("crisis-1", "r1", evidence_r1)
    service.approve_revision("crisis-1", "r1", assumptions_r1)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    intake_r2, evidence_r2, assumptions_r2 = _make_revision_inputs("r2")
    service.save_intake_draft("crisis-1", "r2", intake_r2, parent_revision_id="r1")
    service.save_evidence_draft("crisis-1", "r2", evidence_r2, parent_revision_id="r1")
    service.approve_revision("crisis-1", "r2", assumptions_r2)

    summary = service.summarize_run("crisis-1")

    assert summary.current_revision_id == "r2"
    assert [item["status"] for item in summary.revisions] == ["simulated", "approved"]


def test_summarize_revision_returns_available_sections_and_top_branches(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    summary = service.summarize_revision("crisis-1", "r1")

    assert "intake" in summary.available_sections
    assert "simulation" in summary.available_sections
    assert summary.top_branches[0]["label"] == summarize_top_branches(
        json.loads((repository.run_dir("crisis-1") / "simulation" / "r1.approved.json").read_text(encoding="utf-8"))["branches"]
    )[0]["label"]
    assert "calibrated_confidence" in summary.top_branches[0]
    assert "confidence_bucket" in summary.top_branches[0]
    assert summary.scenario_families
    assert summary.scenario_families[0]["terminal_phase"]
    assert "calibrated_confidence" in summary.scenario_families[0]


def test_draft_conversation_turn_returns_intake_stage_when_revision_is_empty(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r0", _make_intake())
    turn = service.draft_conversation_turn("crisis-1", "r-empty")

    assert isinstance(turn, ConversationTurn)
    assert turn.stage == "intake"
    assert turn.recommended_command == "forecast-harness save-intake-draft"
    assert turn.available_sections == []


def test_draft_conversation_turn_returns_evidence_stage_from_intake_draft(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake = _make_intake()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)

    turn = service.draft_conversation_turn("crisis-1", "r1")

    assert turn.stage == "evidence"
    assert turn.recommended_command == "forecast-harness draft-evidence-packet"
    assert turn.context["domain_pack"] == "interstate-crisis"


def test_draft_conversation_turn_embeds_native_adapter_payloads_for_evidence_stage(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()
    intake = _make_intake()
    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)

    turn = service.draft_conversation_turn("crisis-1", "r1", candidate_path=source_dir)

    assert turn.stage == "evidence"
    assert turn.recommended_command == "forecast-harness batch-ingest-recommended"
    assert [action.command for action in turn.actions] == [
        "forecast-harness batch-ingest-recommended",
        "forecast-harness draft-evidence-packet",
        "forecast-harness save-evidence-draft",
    ]
    assert [action.runtime_action for action in turn.actions] == [
        "batch-ingest-recommended",
        "draft-evidence-packet",
        "save-evidence-draft",
    ]
    assert turn.context["intake_guidance"]["domain_pack"] == "interstate-crisis"
    assert "force posture" in turn.context["retrieval_plan"]["target_evidence_categories"]
    assert "diplomatic signaling" in turn.context["ingestion_plan"]["missing_evidence_categories"]
    assert turn.context["ingestion_recommendations"][0]["source_role"] == "official communications"


def test_draft_conversation_turn_returns_approval_stage_from_evidence_draft(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, _ = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)

    turn = service.draft_conversation_turn("crisis-1", "r1")

    assert turn.stage == "approval"
    assert turn.recommended_command == "forecast-harness approve-revision"
    assert turn.context["revision_id"] == "r1"
    assert turn.actions[0].command == "forecast-harness approve-revision"
    assert turn.actions[0].runtime_action == "approve-revision"


def test_draft_conversation_turn_returns_simulation_stage_from_approved_revision(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)

    turn = service.draft_conversation_turn("crisis-1", "r1")

    assert turn.stage == "simulation"
    assert turn.recommended_command == "forecast-harness simulate"
    assert turn.context["evidence_item_count"] == 1


def test_draft_conversation_turn_returns_report_stage_from_simulated_revision(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    turn = service.draft_conversation_turn("crisis-1", "r1")

    assert turn.stage == "report"
    assert turn.recommended_command == "forecast-harness begin-revision-update"
    assert turn.context["revision_id"] == "r1"
    assert turn.context["top_branches"][0]["label"] == service.summarize_revision("crisis-1", "r1").top_branches[0]["label"]
    assert turn.context["scenario_families"]


def test_approve_revision_freezes_revision_artifacts_and_advances_the_run() -> None:
    repository = _FakeRepository(run_record=_make_run())
    intake = _make_intake()
    evidence = _make_evidence()
    assumptions = AssumptionSummary(summary=["assumption-1"], suggested_actors=["country-c"])
    repository.revision_payloads[("run-1", "intake", "rev-1", False)] = intake.model_dump(mode="json")
    repository.revision_payloads[("run-1", "evidence", "rev-1", False)] = evidence.model_dump(mode="json")
    service = WorkflowService(repository)

    run = service.approve_revision("run-1", "rev-1", assumptions)

    assert run.current_revision_id == "rev-1"
    assert repository.loaded_revision_models == [
        ("run-1", "intake", "rev-1", IntakeDraft, False),
        ("run-1", "evidence", "rev-1", EvidencePacket, False),
    ]
    assert repository.written_revision_json == [
        ("run-1", "intake", "rev-1", intake.model_dump(mode="json"), True),
        ("run-1", "evidence", "rev-1", evidence.model_dump(mode="json"), True),
        (
            "run-1",
            "assumptions",
            "rev-1",
            assumptions.model_dump(mode="json"),
            True,
        ),
    ]
    assert repository.saved_runs == [run]
    assert repository.appended_events == [("run-1", "revision-approved", {"revision_id": "rev-1"})]


def test_simulate_revision_writes_belief_state_summary_and_report(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)

    result = service.simulate_revision("crisis-1", "r1", pack=pack)

    assert result["branches"]
    branch_labels = {branch["label"] for branch in result["branches"]}
    assert any(label.startswith("Signal resolve") for label in branch_labels)
    assert any(label.startswith("Limited response") for label in branch_labels)
    assert any(label.startswith("Alliance consultation") for label in branch_labels)
    assert any(label.startswith("Open negotiation") for label in branch_labels)
    assert repository.run_dir("crisis-1").joinpath("belief-state", "r1.approved.json").exists()
    assert repository.run_dir("crisis-1").joinpath("simulation", "r1.approved.json").exists()
    report_path = repository.run_dir("crisis-1").joinpath("reports", "r1.report.md")
    assert report_path.exists()
    report = report_path.read_text(encoding="utf-8")
    assert "# Scenario Report" in report
    assert "- Revision: r1" in report
    assert "- Unsupported assumptions: 1" in report
    assert "## Actor Utility Summary" in report
    assert "## Aggregation Lens" in report
    assert "## Top Branch Aggregate Breakdown" in report
    assert "## Scenario Families" in report
    assert "low-credibility exploratory run" not in report


def test_simulate_revision_honors_approved_objective_profile_over_recommended_lens(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess domestic resolve and alliance security after the exchange of strikes.",
        primary_actors=["United States", "Iran"],
        trigger="U.S. leaders weigh domestic resolve and alliance security commitments after the exchange of strikes.",
        current_phase="trigger",
        time_horizon="30d",
        known_constraints=["United States alliance security backing remains visible."],
        known_unknowns=["United States domestic audience response is still uncertain."],
    )
    evidence = EvidencePacket(
        revision_id="r1",
        items=[
            EvidencePacketItem(
                evidence_id="r1-ev-1",
                source_id="doc-1",
                source_title="Doc 1",
                reason="Relevant context",
                raw_passages=[
                    (
                        "United States officials described domestic political pressure, public resolve, "
                        "and alliance security backing as the main constraints."
                    )
                ],
            )
        ],
    )
    assumptions = AssumptionSummary(summary=["assumption-1"], objective_profile_name="balanced")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)

    result = service.simulate_revision("crisis-1", "r1", pack=pack)

    assert result["aggregation_lens"]["name"] == "balanced-system"
    assert result["aggregation_lens"]["aggregation_mode"] == "balanced-system"
    assert result["recommended_run_lens"]["name"] == "domestic-politics-first"
    assert result["recommended_run_lens"]["focal_actor_id"] == "united-states"
    report = (repository.run_dir("crisis-1") / "reports" / "r1.report.md").read_text(encoding="utf-8")
    assert "Lens: balanced-system" in report
    assert "Recommended lens: domestic-politics-first" in report


def test_approve_revision_rejects_invalid_objective_profile_name_before_simulation(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, _ = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)

    with pytest.raises(ValueError, match="unknown objective profile: typo-lens"):
        service.approve_revision(
            "crisis-1",
            "r1",
            AssumptionSummary(summary=["assumption-1"], objective_profile_name="typo-lens"),
        )

    assumptions_path = repository.run_dir("crisis-1") / "assumptions" / "r1.approved.json"
    assert not assumptions_path.exists()


def test_generate_report_writes_revision_specific_reports_and_credibility_note(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    service.start_run(run_id="crisis-1", domain_pack="interstate-crisis")

    first_report = service.generate_report(
        "crisis-1",
        "r1",
        simulation={
            "branches": [
                {"branch_id": "signal", "label": "Signal resolve", "score": 0.8},
                {"branch_id": "negotiation", "label": "Open negotiation", "score": 0.9},
            ]
        },
        evidence_count=0,
        unsupported_count=1,
    )
    second_report = service.generate_report(
        "crisis-1",
        "r2",
        simulation={"branches": []},
        evidence_count=2,
        unsupported_count=0,
    )

    report_dir = repository.run_dir("crisis-1") / "reports"
    assert report_dir.joinpath("r1.report.md").exists()
    assert report_dir.joinpath("r2.report.md").exists()
    assert first_report != second_report
    assert "low-credibility exploratory run" in first_report
    assert "low-credibility exploratory run" not in second_report


def test_draft_evidence_packet_from_corpus_persists_a_revision_draft(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    corpus.register_document(
        source_id="doc-1",
        title="Taiwan Strait Signals",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Japan and China exchange warnings in the Taiwan Strait.",
    )
    corpus.register_document(
        source_id="doc-2",
        title="Unrelated Market Note",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "market-shock"},
        content="Oil futures rise after unrelated macro news.",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    packet = service.draft_evidence_packet(
        "crisis-1",
        "r1",
        pack=pack,
        query_text="Taiwan Strait warnings",
    )

    assert [item.source_id for item in packet.items] == ["doc-1"]
    stored_packet = repository.load_revision_model("crisis-1", "evidence", "r1", EvidencePacket, approved=False)
    assert [item.source_id for item in stored_packet.items] == ["doc-1"]


def test_draft_evidence_packet_uses_manifest_categories_for_diverse_packet_reasons(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    corpus.register_document(
        source_id="doc-1",
        title="Posture shift",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Force posture hardens near the strait after the naval transit.",
    )
    corpus.register_document(
        source_id="doc-2",
        title="Backchannel warning",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Diplomatic signaling intensifies through private backchannel warnings.",
    )
    corpus.register_document(
        source_id="doc-3",
        title="Second posture note",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Additional force posture changes are visible around the theater.",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    packet = service.draft_evidence_packet(
        "crisis-1",
        "r1",
        pack=pack,
        query_text="military buildup and backchannel warnings",
        max_total=2,
    )

    assert "doc-2" in [item.source_id for item in packet.items]
    assert any(item.source_id in {"doc-1", "doc-3"} for item in packet.items)
    assert {item.reason for item in packet.items} == {
        "Candidate passage for approved evidence packet: diplomatic signaling",
        "Candidate passage for approved evidence packet: force posture",
    }


def test_draft_evidence_packet_prefers_current_run_documents_over_same_domain_history(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="A Japan-China naval incident raises confrontation risk",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    corpus.register_document(
        source_id="older-doc",
        title="Older domain note",
        source_type="markdown",
        path="/tmp/older.md",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis", "run_id": "other-run"},
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "United States and Iran warn of retaliation in the Gulf."}],
    )
    corpus.register_document(
        source_id="current-doc",
        title="Current run note",
        source_type="markdown",
        path="/tmp/current.md",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis", "run_id": "crisis-1"},
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "Japan and China exchange warnings after a naval transit in the Taiwan Strait."}],
    )

    packet = service.draft_evidence_packet(
        "crisis-1",
        "r1",
        pack=pack,
        query_text=None,
    )

    assert [item.source_id for item in packet.items] == ["current-doc"]


def test_draft_evidence_packet_does_not_use_only_suggested_entity_overlap_from_other_runs(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            suggested_entities=["United States", "Taiwan"],
            current_development="A Japan-China naval incident raises confrontation risk",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    corpus.register_document(
        source_id="other-run-doc",
        title="Foreign run note",
        source_type="markdown",
        path="/tmp/other-run.md",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis", "run_id": "other-run"},
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "The United States warns Iran of retaliation in the Gulf."}],
    )

    packet = service.draft_evidence_packet(
        "crisis-1",
        "r1",
        pack=pack,
        query_text=None,
    )

    assert packet.items == []


def test_draft_retrieval_plan_uses_manifest_categories_and_entities(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    plan = service.draft_retrieval_plan("crisis-1", "r1", pack=pack)

    assert isinstance(plan, RetrievalPlan)
    assert plan.domain_pack == "interstate-crisis"
    assert plan.filters == {"domain": "interstate-crisis"}
    assert "force posture" in plan.target_evidence_categories
    assert plan.query_variants[0] == "Japan China Naval transit through the Taiwan Strait trigger"
    assert "Japan China Naval transit through the Taiwan Strait force posture" in plan.query_variants


def test_draft_ingestion_plan_reports_missing_manifest_categories(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    corpus.register_document(
        source_id="doc-1",
        title="Posture shift",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Japan and China harden force posture near the Taiwan Strait after the naval transit.",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    plan = service.draft_ingestion_plan("crisis-1", "r1", pack=pack)

    assert isinstance(plan, IngestionPlan)
    assert plan.domain_pack == "interstate-crisis"
    assert plan.corpus_source_count == 1
    assert plan.covered_evidence_categories == ["force posture"]
    assert "diplomatic signaling" in plan.missing_evidence_categories
    assert plan.starter_sources[0]["kind"] == "official communications"
    assert plan.ingest_tasks[0].evidence_category == "diplomatic signaling"
    assert plan.ingest_tasks[0].source_role == "official communications"


def test_draft_ingestion_plan_ignores_other_run_domain_coverage(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    corpus.register_document(
        source_id="other-doc",
        title="Foreign run note",
        source_type="markdown",
        path="/tmp/other-run.md",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis", "run_id": "other-run"},
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "The United States warns Iran of retaliation while both sides mobilize."}],
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    plan = service.draft_ingestion_plan("crisis-1", "r1", pack=pack)

    assert plan.corpus_source_count == 0
    assert plan.current_sources == []
    assert "force posture" in plan.missing_evidence_categories
    assert "diplomatic signaling" in plan.missing_evidence_categories


def test_recommend_ingestion_files_uses_run_scoped_plan_not_prior_domain_coverage(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    corpus.register_document(
        source_id="other-doc",
        title="Foreign run note",
        source_type="markdown",
        path="/tmp/other-run.md",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis", "run_id": "other-run"},
        chunks=[{"chunk_id": "1", "location": "heading:Overview", "content": "The United States warns Iran of retaliation while both sides mobilize."}],
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="A Japanese naval transit through the Taiwan Strait triggers Chinese intercept threats and emergency diplomacy.",
            current_stage="trigger",
            time_horizon="21d",
        ),
    )

    docs_dir = tmp_path / "japan-run"
    docs_dir.mkdir()
    (docs_dir / "japan-transit.md").write_text(
        "Japan defends the Taiwan Strait transit as lawful while China threatens an intercept and raises naval readiness.",
        encoding="utf-8",
    )
    (docs_dir / "china-backchannel.md").write_text(
        "Chinese and Japanese officials keep emergency backchannel talks open to avoid a wider clash in the strait.",
        encoding="utf-8",
    )

    recommendations = service.recommend_ingestion_files("crisis-1", "r1", pack=pack, path=docs_dir)

    assert {item.source_id for item in recommendations} == {"japan-transit", "china-backchannel"}


def test_draft_evidence_packet_can_generate_query_variants_without_explicit_query_text(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    corpus.register_document(
        source_id="doc-1",
        title="Posture shift",
        source_type="markdown",
        published_at="2026-04-20",
        tags={"domain": "interstate-crisis"},
        content="Force posture hardens near the strait after the naval transit.",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    packet = service.draft_evidence_packet("crisis-1", "r1", pack=pack, query_text=None)

    assert [item.source_id for item in packet.items] == ["doc-1"]
    assert packet.items[0].reason == "Candidate passage for approved evidence packet: force posture"


def test_recommend_ingestion_files_maps_local_files_to_source_roles(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )
    (source_dir / "deployment-notes.md").write_text(
        "# Deployment\nForce posture and readiness changed near the theater.\n",
        encoding="utf-8",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    recommendations = service.recommend_ingestion_files(
        "crisis-1",
        "r1",
        pack=pack,
        path=source_dir,
    )

    assert all(isinstance(item, IngestionRecommendation) for item in recommendations)
    by_source_id = {item.source_id: item for item in recommendations}
    assert by_source_id["official-warning"].source_role == "official communications"
    assert by_source_id["official-warning"].recommended_tags["domain"] == "interstate-crisis"
    assert "diplomatic signaling" in by_source_id["official-warning"].matched_evidence_categories
    assert by_source_id["deployment-notes"].source_role == "force and capability references"
    assert "force posture" in by_source_id["deployment-notes"].matched_evidence_categories


def test_recommend_ingestion_files_matches_company_docs_with_natural_language_wording(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = CompanyActionPack()

    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "apple-transition.md").write_text(
        "Analysts focus on succession clarity, supplier reassurance, and investor concern after product delays.\n",
        encoding="utf-8",
    )

    service.start_run(run_id="company-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "company-1",
        "r1",
        IntakeDraft(
            event_framing="Assess strategy after a CEO change",
            focus_entities=["Apple"],
            current_development="A sudden CEO transition follows product delays and investor concern",
            current_stage="trigger",
            time_horizon="180d",
        ),
    )

    recommendations = service.recommend_ingestion_files(
        "company-1",
        "r1",
        pack=pack,
        path=source_dir,
    )

    assert recommendations
    assert recommendations[0].source_role in {"management communications", "market reaction"}
    assert set(recommendations[0].matched_evidence_categories) & {"leadership behavior", "operational resilience"}


def test_recommend_ingestion_files_matches_election_docs_with_natural_language_wording(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = ElectionShockPack()

    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "debate-collapse.md").write_text(
        "Party leadership scrambles to stabilize messaging after the debate while donor confidence softens.\n",
        encoding="utf-8",
    )

    service.start_run(run_id="election-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "election-1",
        "r1",
        IntakeDraft(
            event_framing="Assess election shock dynamics",
            focus_entities=["Incumbent Party", "Opposition Party"],
            current_development="A debate collapse forces both campaigns to reset strategy",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    recommendations = service.recommend_ingestion_files(
        "election-1",
        "r1",
        pack=pack,
        path=source_dir,
    )

    assert recommendations
    assert set(recommendations[0].matched_evidence_categories) & {"message discipline", "campaign resources"}


def test_recommend_ingestion_files_matches_regulatory_docs_with_pluralized_remedy_terms(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = RegulatoryEnforcementPack()

    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "adtech-remedy.md").write_text(
        "Regulators signal willingness to seek structural remedies while industry partners brace for disruption.\n",
        encoding="utf-8",
    )

    service.start_run(run_id="reg-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "reg-1",
        "r1",
        IntakeDraft(
            event_framing="Assess enforcement response",
            focus_entities=["AdTech Platform", "Competition Regulator"],
            current_development="A regulator escalates an ad-tech case after new evidence appears",
            current_stage="trigger",
            time_horizon="120d",
        ),
    )

    recommendations = service.recommend_ingestion_files(
        "reg-1",
        "r1",
        pack=pack,
        path=source_dir,
    )

    assert recommendations
    assert set(recommendations[0].matched_evidence_categories) & {"remedy severity"}


def test_batch_ingest_recommended_files_registers_prioritized_sources_with_role_tags(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    corpus = CorpusRegistry(tmp_path / "corpus.db")
    service = WorkflowService(repository, corpus_registry=corpus)
    pack = InterstateCrisisPack()

    source_dir = tmp_path / "incoming"
    source_dir.mkdir()
    (source_dir / "official-warning.md").write_text(
        "# Foreign Ministry\nOfficial statement and warning to the other state.\n",
        encoding="utf-8",
    )
    (source_dir / "deployment-notes.md").write_text(
        "# Deployment\nForce posture and readiness changed near the theater.\n",
        encoding="utf-8",
    )
    (source_dir / "ignore.txt").write_text("general note without useful signal\n", encoding="utf-8")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft(
        "crisis-1",
        "r1",
        IntakeDraft(
            event_framing="Assess escalation",
            focus_entities=["Japan", "China"],
            current_development="Naval transit through the Taiwan Strait",
            current_stage="trigger",
            time_horizon="30d",
        ),
    )

    result = service.batch_ingest_recommended_files(
        "crisis-1",
        "r1",
        pack=pack,
        path=source_dir,
        max_files=2,
    )

    assert isinstance(result, BatchIngestionResult)
    assert result.ingested_count == 2
    assert result.skipped_count == 1
    assert set(result.ingested_source_ids) == {"official-warning", "deployment-notes"}

    documents = corpus.list_documents()
    assert documents[0]["tags"]["source_role"] == "force and capability references"
    assert documents[0]["tags"]["domain"] == "interstate-crisis"
    assert documents[1]["tags"]["source_role"] == "official communications"


def test_curate_evidence_draft_keeps_requested_ids_and_records_event() -> None:
    repository = _FakeRepository(run_record=_make_run("crisis-1"))
    packet = EvidencePacket(
        revision_id="r1",
        items=[
            EvidencePacketItem(
                evidence_id="r1-ev-1",
                source_id="source-1",
                source_title="Source 1",
                reason="First",
            ),
            EvidencePacketItem(
                evidence_id="r1-ev-2",
                source_id="source-2",
                source_title="Source 2",
                reason="Second",
            ),
        ],
    )
    repository.revision_payloads[("crisis-1", "evidence", "r1", False)] = packet.model_dump(mode="json")
    service = WorkflowService(repository)

    curated = service.curate_evidence_draft("crisis-1", "r1", ["r1-ev-2"])

    assert [item.evidence_id for item in curated.items] == ["r1-ev-2"]
    assert repository.written_revision_json[-1] == (
        "crisis-1",
        "evidence",
        "r1",
        curated.model_dump(mode="json"),
        False,
    )
    assert repository.appended_events[-1] == (
        "crisis-1",
        "evidence-curated",
        {"revision_id": "r1", "evidence_ids": ["r1-ev-2"]},
    )


def test_curate_evidence_draft_rejects_unknown_ids() -> None:
    repository = _FakeRepository(run_record=_make_run("crisis-1"))
    repository.revision_payloads[("crisis-1", "evidence", "r1", False)] = EvidencePacket(
        revision_id="r1",
        items=[
            EvidencePacketItem(
                evidence_id="r1-ev-1",
                source_id="source-1",
                source_title="Source 1",
                reason="First",
            )
        ],
    ).model_dump(mode="json")
    service = WorkflowService(repository)

    with pytest.raises(ValueError, match="unknown evidence ids"):
        service.curate_evidence_draft("crisis-1", "r1", ["missing-id"])


def test_begin_revision_update_copies_parent_artifacts_and_preserves_lineage(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake_r1, evidence_r1, assumptions_r1 = _make_revision_inputs("r1", evidence_count=2)

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake_r1)
    service.save_evidence_draft("crisis-1", "r1", evidence_r1)
    service.approve_revision("crisis-1", "r1", assumptions_r1)

    payload = service.begin_revision_update("crisis-1", "r2", parent_revision_id="r1")

    assert payload == {
        "revision_id": "r2",
        "parent_revision_id": "r1",
        "copied_sections": ["intake", "evidence"],
    }
    copied_intake = repository.load_revision_model("crisis-1", "intake", "r2", IntakeDraft, approved=False)
    copied_evidence = repository.load_revision_model("crisis-1", "evidence", "r2", EvidencePacket, approved=False)
    assert copied_intake == intake_r1
    assert copied_evidence.revision_id == "r2"
    assert [item.evidence_id for item in copied_evidence.items] == [item.evidence_id for item in evidence_r1.items]
    assert repository.load_revision_record("crisis-1", "r2").parent_revision_id == "r1"
    assert not (repository.run_dir("crisis-1") / "assumptions" / "r2.approved.json").exists()


def test_begin_revision_update_requires_approved_parent_sections(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", _make_intake())

    with pytest.raises(FileNotFoundError):
        service.begin_revision_update("crisis-1", "r2", parent_revision_id="r1")


def test_revision_preserving_rerun_keeps_previous_report(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    intake_r1, evidence_r1, assumptions_r1 = _make_revision_inputs("r1")
    service.save_intake_draft("crisis-1", "r1", intake_r1)
    service.save_evidence_draft("crisis-1", "r1", evidence_r1)
    service.approve_revision("crisis-1", "r1", assumptions_r1)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    intake_r2, evidence_r2, assumptions_r2 = _make_revision_inputs("r2", evidence_count=2)
    service.save_intake_draft("crisis-1", "r2", intake_r2)
    service.save_evidence_draft("crisis-1", "r2", evidence_r2)
    service.approve_revision("crisis-1", "r2", assumptions_r2)
    service.simulate_revision("crisis-1", "r2", pack=pack)

    report_dir = repository.run_dir("crisis-1") / "reports"
    assert report_dir.joinpath("r1.report.md").exists()
    assert report_dir.joinpath("r2.report.md").exists()
    assert repository.load_run_record("crisis-1").current_revision_id == "r2"


def test_simulate_revision_reuses_parent_tree_when_child_revision_is_compatible(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake_r1 = IntakeDraft(
        event_framing="Assess escalation",
        focus_entities=["Japan", "China"],
        current_development="Naval transit through the Taiwan Strait",
        current_stage="trigger",
        time_horizon="30d",
        pack_fields={"leader_style": "cautious", "military_posture": "forward"},
    )
    evidence_r1, assumptions_r1 = _make_revision_inputs("r1", evidence_count=2)[1:]

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake_r1)
    service.save_evidence_draft("crisis-1", "r1", evidence_r1)
    service.approve_revision("crisis-1", "r1", assumptions_r1)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    service.begin_revision_update("crisis-1", "r2", parent_revision_id="r1")
    intake_r2 = intake_r1.model_copy(update={"pack_fields": {"leader_style": "cautious", "military_posture": "reserve"}})
    service.save_intake_draft("crisis-1", "r2", intake_r2, parent_revision_id="r1")
    service.approve_revision("crisis-1", "r2", assumptions_r1.model_copy())

    result = service.simulate_revision("crisis-1", "r2", pack=pack)

    assert result["reuse_summary"]["enabled"] is True
    assert result["reuse_summary"]["source_revision_id"] == "r1"
    assert result["reuse_summary"]["reused_nodes"] > 0
    assert result["reuse_summary"]["skipped_nodes"] > 0


def test_simulate_revision_reuses_parent_tree_when_only_recommended_lens_changes(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess escalation",
        focus_entities=["Japan", "China"],
        current_development="Naval transit through the Taiwan Strait",
        current_stage="trigger",
        time_horizon="30d",
    )
    evidence = _make_revision_inputs("r1", evidence_count=2)[1]
    assumptions = AssumptionSummary(summary=["assumption-1"], objective_profile_name="balanced")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    service.begin_revision_update("crisis-1", "r2", parent_revision_id="r1")
    service.approve_revision("crisis-1", "r2", assumptions.model_copy())

    original_recommend = pack.recommend_objective_profile

    def _alternate_recommendation(intake_arg, state_arg):
        if state_arg.revision_id == "r2":
            from forecasting_harness.objectives import objective_profile_by_name

            return objective_profile_by_name("domestic-politics-first").model_copy(
                update={"focal_actor_id": "japan"}
            )
        return original_recommend(intake_arg, state_arg)

    pack.recommend_objective_profile = _alternate_recommendation  # type: ignore[method-assign]
    try:
        result = service.simulate_revision("crisis-1", "r2", pack=pack)
    finally:
        pack.recommend_objective_profile = original_recommend  # type: ignore[method-assign]

    child_state = repository.load_revision_model("crisis-1", "belief-state", "r2", BeliefState, approved=True)
    assert child_state.objectives["selected_run_lens"] == "balanced-system"
    assert "recommended_run_lens" not in child_state.objectives
    assert result["aggregation_lens"]["name"] == "balanced-system"
    assert result["recommended_run_lens"]["name"] == "domestic-politics-first"
    assert result["reuse_summary"]["enabled"] is True
    assert result["reuse_summary"]["source_revision_id"] == "r1"
    assert result["reuse_summary"]["reused_nodes"] > 0


def test_simulate_revision_preserves_focal_actor_for_explicit_domestic_lens_selection(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake = IntakeDraft(
        event_framing="Assess domestic resolve pressure.",
        focus_entities=["China", "Taiwan"],
        current_development="Beijing is signaling resolve ahead of domestic political meetings.",
        current_stage="signaling",
        time_horizon="30d",
    )
    evidence = EvidencePacket(
        revision_id="r1",
        items=[
            EvidencePacketItem(
                evidence_id="r1-ev-0",
                source_id="src-1",
                source_title="Resolve signal",
                reason="Supports domestic resolve pressure",
                raw_passages=[
                    "Chinese officials framed the latest move as a resolve signal for domestic audiences."
                ],
            )
        ],
    )
    assumptions = AssumptionSummary(
        summary=["China remains highly sensitive to domestic resolve narratives."],
        objective_profile_name="domestic-politics-first",
    )

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)

    result = service.simulate_revision("crisis-1", "r1", pack=pack)

    approved_state = repository.load_revision_model("crisis-1", "belief-state", "r1", BeliefState, approved=True)
    assert approved_state.objectives["selected_run_lens"] == "domestic-politics-first"
    assert approved_state.objectives["focal_actor_id"] == "china"
    assert result["aggregation_lens"]["name"] == "domestic-politics-first"
    assert result["aggregation_lens"]["focal_actor_id"] == "china"
    assert result["recommended_run_lens"]["name"] == "balanced-system"
    assert result["recommended_run_lens"]["focal_actor_id"] is None


def test_revision_record_tracks_lifecycle_timestamps(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)
    service.simulate_revision("crisis-1", "r1", pack=pack)

    revision = repository.load_revision_record("crisis-1", "r1")

    assert revision.status == "simulated"
    assert revision.created_at is not None
    assert revision.approved_at is not None
    assert revision.simulated_at is not None


def test_simulate_revision_accepts_iteration_override(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)

    result = service.simulate_revision("crisis-1", "r1", pack=pack, iterations=250)

    assert result["iterations"] == 250


def test_revision_record_preserves_parent_revision_id(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", _make_intake())
    service.save_intake_draft("crisis-1", "r2", _make_intake(), parent_revision_id="r1")

    revision = repository.load_revision_record("crisis-1", "r2")
    assert revision.parent_revision_id == "r1"


def test_simulate_revision_uses_approved_snapshots_after_draft_changes(tmp_path: Path) -> None:
    repository = RunRepository(tmp_path / ".forecast")
    service = WorkflowService(repository)
    pack = InterstateCrisisPack()
    intake, evidence, assumptions = _make_revision_inputs("r1")

    service.start_run(run_id="crisis-1", domain_pack=pack.slug())
    service.save_intake_draft("crisis-1", "r1", intake)
    service.save_evidence_draft("crisis-1", "r1", evidence)
    service.approve_revision("crisis-1", "r1", assumptions)

    mutated_intake = intake.model_copy(update={"current_stage": "escalation", "current_development": "mutated trigger"})
    mutated_evidence = EvidencePacket(revision_id="r1", items=[])
    service.save_intake_draft("crisis-1", "r1", mutated_intake)
    service.save_evidence_draft("crisis-1", "r1", mutated_evidence)

    service.simulate_revision("crisis-1", "r1", pack=pack)

    approved_state = repository.load_revision_model("crisis-1", "belief-state", "r1", BeliefState, approved=True)
    report = repository.run_dir("crisis-1").joinpath("reports", "r1.report.md").read_text(encoding="utf-8")

    assert approved_state.phase == "trigger"
    assert approved_state.fields["current_development"].value == "policy change"
    assert approved_state.approved_evidence_ids == ["r1-ev-0"]
    assert "- Approved evidence items: 1" in report
