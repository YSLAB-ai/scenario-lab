from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from forecasting_harness.evolution.models import DomainSuggestion
from forecasting_harness.evolution.storage import EvolutionStorage


def test_record_suggestion_round_trips(tmp_path: Path) -> None:
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")
    record = DomainSuggestion(
        suggestion_id="s1",
        timestamp=datetime(2026, 4, 21, tzinfo=timezone.utc),
        domain_slug="company-action",
        provenance="user",
        category="action-bias",
        target="contain-message",
        text="Board reassurance should favor containment messaging.",
        terms=["board reassurance"],
        status="pending",
    )

    stored = storage.append_suggestion(record)
    loaded = storage.load_suggestions("company-action")

    assert stored == record
    assert loaded == [record]


def test_write_baseline_snapshot(tmp_path: Path) -> None:
    storage = EvolutionStorage(tmp_path / "knowledge" / "evolution")

    storage.write_baseline("company-action", "baseline.json", {"top_branch_accuracy": 1.0})

    path = tmp_path / "knowledge" / "evolution" / "baselines" / "company-action" / "baseline.json"
    assert json.loads(path.read_text(encoding="utf-8"))["top_branch_accuracy"] == 1.0

