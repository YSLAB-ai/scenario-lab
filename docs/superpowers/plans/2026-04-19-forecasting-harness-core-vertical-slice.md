# Forecasting Harness Core Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable local-first vertical slice that can register curated sources, compile an approved belief state, run an event-driven heuristic search with one generic domain pack, and emit reusable forecast artifacts plus thin Codex/Claude adapter scaffolding.

**Architecture:** The implementation uses a shared Python core under `packages/core/` and keeps all run artifacts in project-local `.forecast/`. The first slice implements typed state normalization, schema-aware warm-start compatibility, lexical retrieval plus a pluggable retrieval surface, event-driven simulation, and a CLI/API surface that thin agent adapters can call without loading the full workbench into context.

**Tech Stack:** Python 3.12, Pydantic 2, Typer, pytest, sqlite3/FTS5

---

## Scope

This plan intentionally covers the first executable slice, not the full long-term roadmap. It delivers:

- shared core package
- typed belief-state and artifact models
- local corpus registry and pluggable retrieval interface
- event-driven simulation engine with objective-profile scalarization
- schema-aware warm-start compatibility and dependency-aware invalidation
- one generic event domain pack
- CLI entrypoints for run creation, approval, simulation, and inspection
- thin Codex and Claude adapter scaffolding plus install docs

Follow-on plans should add richer domain packs, larger corpus tooling, historical replay suites, and automatic rule extraction.

## File Structure

### Repository and packaging

- Create: `/.gitignore`
- Create: `/README.md`
- Create: `/packages/core/pyproject.toml`
- Create: `/packages/core/src/forecasting_harness/__init__.py`
- Create: `/packages/core/src/forecasting_harness/cli.py`
- Create: `/packages/core/tests/conftest.py`

### Core models and interfaces

- Create: `/packages/core/src/forecasting_harness/models.py`
- Create: `/packages/core/src/forecasting_harness/domain/base.py`
- Create: `/packages/core/src/forecasting_harness/objectives.py`
- Create: `/packages/core/tests/test_models.py`

### Artifact store and compatibility

- Create: `/packages/core/src/forecasting_harness/artifacts.py`
- Create: `/packages/core/src/forecasting_harness/compatibility.py`
- Create: `/packages/core/tests/test_artifacts.py`
- Create: `/packages/core/tests/test_compatibility.py`

### Retrieval

- Create: `/packages/core/src/forecasting_harness/retrieval/__init__.py`
- Create: `/packages/core/src/forecasting_harness/retrieval/registry.py`
- Create: `/packages/core/src/forecasting_harness/retrieval/search.py`
- Create: `/packages/core/src/forecasting_harness/query_api.py`
- Create: `/packages/core/tests/test_retrieval.py`

### Simulation

- Create: `/packages/core/src/forecasting_harness/simulation/__init__.py`
- Create: `/packages/core/src/forecasting_harness/simulation/engine.py`
- Create: `/packages/core/src/forecasting_harness/simulation/cache.py`
- Create: `/packages/core/tests/test_simulation.py`

### Domain pack and CLI workflow

- Create: `/packages/core/src/forecasting_harness/domain/generic_event.py`
- Create: `/packages/core/tests/test_generic_event_pack.py`
- Create: `/packages/core/tests/test_cli_workflow.py`

### Adapter scaffolding and docs

- Create: `/adapters/codex/forecast-harness/.codex-plugin/plugin.json`
- Create: `/adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Create: `/adapters/claude/skills/forecast-harness/SKILL.md`
- Create: `/docs/install-codex.md`
- Create: `/docs/install-claude-code.md`

## Task 1: Bootstrap the Repository and Python Core Package

**Files:**
- Create: `/.gitignore`
- Create: `/README.md`
- Create: `/packages/core/pyproject.toml`
- Create: `/packages/core/src/forecasting_harness/__init__.py`
- Create: `/packages/core/src/forecasting_harness/cli.py`
- Create: `/packages/core/tests/conftest.py`
- Test: `/packages/core/tests/test_bootstrap.py`

- [ ] **Step 1: Initialize git and write the first failing bootstrap test**

```bash
git init
mkdir -p packages/core/src/forecasting_harness packages/core/tests
```

```python
# packages/core/tests/test_bootstrap.py
from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_version_command_prints_package_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
```

- [ ] **Step 2: Run the bootstrap test to verify it fails**

Run: `cd packages/core && python -m pytest tests/test_bootstrap.py -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'forecasting_harness'`

- [ ] **Step 3: Write the minimal package, CLI, and project scaffolding**

```toml
# packages/core/pyproject.toml
[build-system]
requires = ["setuptools>=69", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "forecasting-harness"
version = "0.1.0"
description = "Local-first forecasting harness core"
requires-python = ">=3.12"
dependencies = [
  "pydantic>=2.7,<3",
  "typer>=0.12,<1",
]

[project.optional-dependencies]
dev = ["pytest>=8.2,<9"]

[project.scripts]
forecast-harness = "forecasting_harness.cli:main"

[tool.setuptools.packages.find]
where = ["src"]
```

```python
# packages/core/src/forecasting_harness/__init__.py
__all__ = ["__version__"]

__version__ = "0.1.0"
```

```python
# packages/core/src/forecasting_harness/cli.py
import typer

from forecasting_harness import __version__

app = typer.Typer(no_args_is_help=True)


@app.command("version")
def version() -> None:
    typer.echo(__version__)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

```python
# packages/core/tests/conftest.py
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
```

```gitignore
# /.gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
.forecast/
```

```md
# /README.md
# Forecasting Harness

Local-first forecasting harness for Codex and Claude Code.
```

- [ ] **Step 4: Run the bootstrap test to verify it passes**

Run: `cd packages/core && python -m pytest tests/test_bootstrap.py -v`

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit the bootstrap**

```bash
git add .gitignore README.md packages/core
git commit -m "chore: bootstrap forecasting harness core package"
```

## Task 2: Define Typed Belief-State Models, Objective Profiles, and Domain Interfaces

**Files:**
- Create: `/packages/core/src/forecasting_harness/models.py`
- Create: `/packages/core/src/forecasting_harness/objectives.py`
- Create: `/packages/core/src/forecasting_harness/domain/base.py`
- Test: `/packages/core/tests/test_models.py`

- [ ] **Step 1: Write failing tests for normalized fields, objective scalarization, and interaction models**

```python
# packages/core/tests/test_models.py
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import Actor, BeliefField, BeliefState, ObjectiveProfile


def test_belief_field_preserves_display_and_normalized_value() -> None:
    field = BeliefField(
        value="very high",
        normalized_value=0.9,
        status="inferred",
        supporting_evidence_ids=["ev-1"],
        confidence=0.7,
        last_updated_at="2026-04-19T00:00:00Z",
    )
    assert field.value == "very high"
    assert field.normalized_value == 0.9


def test_objective_profile_scalarizes_metric_vector() -> None:
    profile = ObjectiveProfile(
        name="de-escalation",
        metric_weights={"escalation": -0.7, "negotiation": 0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
    score = profile.scalarize({"escalation": 0.8, "negotiation": 0.2})
    assert round(score, 3) == -0.5


def test_belief_state_tracks_interaction_model() -> None:
    state = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[Actor(actor_id="a1", name="Actor 1")],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
    )
    assert state.interaction_model is InteractionModel.EVENT_DRIVEN
```

- [ ] **Step 2: Run the model tests to verify they fail**

Run: `cd packages/core && python -m pytest tests/test_models.py -v`

Expected: FAIL with import errors for `forecasting_harness.models` and `forecasting_harness.domain.base`

- [ ] **Step 3: Write the typed models and domain interfaces**

```python
# packages/core/src/forecasting_harness/domain/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any


class InteractionModel(StrEnum):
    EVENT_DRIVEN = "event_driven"
    SEQUENTIAL_TURN = "sequential_turn"
    SIMULTANEOUS_MOVE = "simultaneous_move"


class DomainPack(ABC):
    @abstractmethod
    def slug(self) -> str: ...

    @abstractmethod
    def interaction_model(self) -> InteractionModel: ...

    @abstractmethod
    def extend_schema(self) -> dict[str, Any]: ...

    @abstractmethod
    def suggest_questions(self) -> list[str]: ...

    @abstractmethod
    def propose_actions(self, state: "BeliefState") -> list[dict[str, Any]]: ...

    @abstractmethod
    def sample_transition(self, state: "BeliefState", action_context: dict[str, Any]) -> list["BeliefState"]: ...

    @abstractmethod
    def score_state(self, state: "BeliefState") -> dict[str, float]: ...

    @abstractmethod
    def validate_state(self, state: "BeliefState") -> list[str]: ...

    def freshness_policy(self) -> dict[str, float]:
        return {}

    def default_objective_profile(self) -> dict[str, Any]:
        return {}
```

```python
# packages/core/src/forecasting_harness/models.py
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from forecasting_harness.domain.base import InteractionModel

FieldStatus = Literal["observed", "inferred", "unknown"]


class BehaviorProfile(BaseModel):
    risk_tolerance: float | None = None
    escalation_tolerance: float | None = None
    notes: str | None = None


class Actor(BaseModel):
    actor_id: str
    name: str
    behavior_profile: BehaviorProfile | None = None


class BeliefField(BaseModel):
    value: str | float | int | dict | list | None
    normalized_value: str | float | int | dict | list | None
    status: FieldStatus
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    confidence: float
    last_updated_at: str
    evidence_type: str | None = None
    time_scope: str | None = None
    applicability_notes: str | None = None


class ObjectiveProfile(BaseModel):
    name: str
    metric_weights: dict[str, float]
    veto_thresholds: dict[str, float]
    risk_tolerance: float
    asymmetry_penalties: dict[str, float]

    def scalarize(self, metrics: dict[str, float]) -> float:
        total = 0.0
        for metric, value in metrics.items():
            total += self.metric_weights.get(metric, 0.0) * value
        return total


class BeliefState(BaseModel):
    run_id: str
    interaction_model: InteractionModel
    actors: list[Actor]
    fields: dict[str, BeliefField]
    objectives: dict[str, str]
    capabilities: dict[str, str]
    constraints: dict[str, str]
    unknowns: list[str]
    current_epoch: str
    horizon: str
```

```python
# packages/core/src/forecasting_harness/objectives.py
from forecasting_harness.models import ObjectiveProfile


def default_objective_profile() -> ObjectiveProfile:
    return ObjectiveProfile(
        name="balanced",
        metric_weights={"escalation": -0.4, "negotiation": 0.3, "economic_stress": -0.3},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
```

- [ ] **Step 4: Run the model tests to verify they pass**

Run: `cd packages/core && python -m pytest tests/test_models.py -v`

Expected: PASS with `3 passed`

- [ ] **Step 5: Commit the models and interfaces**

```bash
git add packages/core/src/forecasting_harness/models.py packages/core/src/forecasting_harness/objectives.py packages/core/src/forecasting_harness/domain/base.py packages/core/tests/test_models.py
git commit -m "feat: add typed belief state and domain interfaces"
```

## Task 3: Implement the Artifact Store and Schema-Aware Compatibility Primitives

**Files:**
- Create: `/packages/core/src/forecasting_harness/artifacts.py`
- Create: `/packages/core/src/forecasting_harness/compatibility.py`
- Test: `/packages/core/tests/test_artifacts.py`
- Test: `/packages/core/tests/test_compatibility.py`

- [ ] **Step 1: Write failing tests for run persistence and normalized compatibility**

```python
# packages/core/tests/test_artifacts.py
from pathlib import Path

from forecasting_harness.artifacts import RunRepository
from forecasting_harness.models import BeliefState
from forecasting_harness.domain.base import InteractionModel


def test_run_repository_persists_belief_state(tmp_path: Path) -> None:
    repo = RunRepository(tmp_path / ".forecast")
    state = BeliefState(
        run_id="run-1",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
    )
    repo.save_belief_state("run-1", state)
    loaded = repo.load_belief_state("run-1")
    assert loaded.run_id == "run-1"
```

```python
# packages/core/tests/test_compatibility.py
from forecasting_harness.compatibility import compare_state_slices


def test_compatibility_uses_normalized_values_not_display_text() -> None:
    previous = {"morale": {"normalized_value": 0.8}, "fuel_days": {"normalized_value": 12}}
    current = {"morale": {"normalized_value": 0.9}, "fuel_days": {"normalized_value": 12}}
    result = compare_state_slices(previous, current, tolerances={"morale": 0.2, "fuel_days": 0.0})
    assert result["compatible"] is True
    assert result["changed_fields"] == ["morale"]
```

- [ ] **Step 2: Run the artifact tests to verify they fail**

Run: `cd packages/core && python -m pytest tests/test_artifacts.py tests/test_compatibility.py -v`

Expected: FAIL with import errors for `forecasting_harness.artifacts` and `forecasting_harness.compatibility`

- [ ] **Step 3: Write the run repository and compatibility helpers**

```python
# packages/core/src/forecasting_harness/artifacts.py
from __future__ import annotations

import json
from pathlib import Path

from forecasting_harness.models import BeliefState


class RunRepository:
    def __init__(self, root: Path) -> None:
        self.root = root

    def run_dir(self, run_id: str) -> Path:
        return self.root / "runs" / run_id

    def save_belief_state(self, run_id: str, state: BeliefState) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "belief-state.json"
        path.write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def load_belief_state(self, run_id: str) -> BeliefState:
        path = self.run_dir(run_id) / "belief-state.json"
        return BeliefState.model_validate_json(path.read_text(encoding="utf-8"))

    def write_markdown(self, run_id: str, name: str, content: str) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_text(content, encoding="utf-8")

    def write_json(self, run_id: str, name: str, payload: dict) -> None:
        run_dir = self.run_dir(run_id)
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
```

```python
# packages/core/src/forecasting_harness/compatibility.py
from __future__ import annotations

from typing import Any


def compare_state_slices(previous: dict[str, Any], current: dict[str, Any], tolerances: dict[str, float]) -> dict[str, Any]:
    changed_fields: list[str] = []
    compatible = True

    for field_name, current_value in current.items():
        previous_value = previous.get(field_name)
        if previous_value is None:
            compatible = False
            changed_fields.append(field_name)
            continue

        left = previous_value.get("normalized_value")
        right = current_value.get("normalized_value")
        tolerance = tolerances.get(field_name, 0.0)

        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if abs(left - right) > tolerance:
                compatible = False
                changed_fields.append(field_name)
            elif left != right:
                changed_fields.append(field_name)
        elif left != right:
            compatible = False
            changed_fields.append(field_name)

    return {"compatible": compatible, "changed_fields": changed_fields}
```

- [ ] **Step 4: Run the artifact tests to verify they pass**

Run: `cd packages/core && python -m pytest tests/test_artifacts.py tests/test_compatibility.py -v`

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit the artifact and compatibility layer**

```bash
git add packages/core/src/forecasting_harness/artifacts.py packages/core/src/forecasting_harness/compatibility.py packages/core/tests/test_artifacts.py packages/core/tests/test_compatibility.py
git commit -m "feat: add artifact store and normalized compatibility checks"
```

## Task 4: Build the Corpus Registry, Hybrid Retrieval Surface, and Query API

**Files:**
- Create: `/packages/core/src/forecasting_harness/retrieval/__init__.py`
- Create: `/packages/core/src/forecasting_harness/retrieval/registry.py`
- Create: `/packages/core/src/forecasting_harness/retrieval/search.py`
- Create: `/packages/core/src/forecasting_harness/query_api.py`
- Test: `/packages/core/tests/test_retrieval.py`

- [ ] **Step 1: Write failing tests for corpus registration, freshness weighting, and progressive-disclosure queries**

```python
# packages/core/tests/test_retrieval.py
from pathlib import Path

from forecasting_harness.query_api import summarize_top_branches
from forecasting_harness.retrieval.registry import CorpusRegistry
from forecasting_harness.retrieval.search import RetrievalQuery, SearchEngine


def test_registry_registers_documents_and_returns_chunk_hits(tmp_path: Path) -> None:
    registry = CorpusRegistry(tmp_path / "corpus.db")
    registry.register_document(
        source_id="src-1",
        title="Recent logistics report",
        source_type="markdown",
        published_at="2026-04-18",
        tags={"domain": "conflict", "actor": "state-a"},
        content="# Report\nFuel stockpiles are strained.\n",
    )
    engine = SearchEngine(registry)
    hits = engine.search(RetrievalQuery(text="fuel stockpiles", filters={"domain": "conflict"}))
    assert hits[0]["source_id"] == "src-1"


def test_query_api_summarizes_top_branches_without_loading_full_tree() -> None:
    summary = summarize_top_branches(
        [
            {"branch_id": "b1", "score": 0.7, "label": "de-escalation"},
            {"branch_id": "b2", "score": 0.3, "label": "limited strike"},
        ],
        limit=1,
    )
    assert summary == [{"branch_id": "b1", "label": "de-escalation", "score": 0.7}]
```

- [ ] **Step 2: Run the retrieval tests to verify they fail**

Run: `cd packages/core && python -m pytest tests/test_retrieval.py -v`

Expected: FAIL with import errors for retrieval modules

- [ ] **Step 3: Implement the registry, hybrid search surface, and query helpers**

```python
# packages/core/src/forecasting_harness/retrieval/registry.py
from __future__ import annotations

import sqlite3
from pathlib import Path


class CorpusRegistry:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS chunks
            USING fts5(source_id, title, published_at, source_type, tags, content)
            """
        )

    def register_document(
        self,
        *,
        source_id: str,
        title: str,
        source_type: str,
        published_at: str,
        tags: dict[str, str],
        content: str,
    ) -> None:
        self.conn.execute(
            "INSERT INTO chunks(source_id, title, published_at, source_type, tags, content) VALUES (?, ?, ?, ?, ?, ?)",
            (source_id, title, published_at, source_type, str(tags), content),
        )
        self.conn.commit()

    def search_chunks(self, text: str) -> list[dict[str, str]]:
        rows = self.conn.execute(
            "SELECT source_id, title, published_at, source_type, tags, content FROM chunks WHERE chunks MATCH ?",
            (text,),
        ).fetchall()
        return [
            {
                "source_id": row[0],
                "title": row[1],
                "published_at": row[2],
                "source_type": row[3],
                "tags": row[4],
                "content": row[5],
            }
            for row in rows
        ]
```

```python
# packages/core/src/forecasting_harness/retrieval/search.py
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from forecasting_harness.retrieval.registry import CorpusRegistry


@dataclass
class RetrievalQuery:
    text: str
    filters: dict[str, str] = field(default_factory=dict)


class SearchEngine:
    def __init__(self, registry: CorpusRegistry) -> None:
        self.registry = registry

    def freshness_multiplier(self, published_at: str) -> float:
        age_days = max((date.today() - date.fromisoformat(published_at)).days, 0)
        return max(0.2, 1 - (age_days / 365))

    def search(self, query: RetrievalQuery) -> list[dict]:
        hits = self.registry.search_chunks(query.text)
        filtered = []
        for hit in hits:
            tags = hit["tags"]
            if all(f"{key}': '{value}" in tags for key, value in query.filters.items()):
                hit["score"] = self.freshness_multiplier(hit["published_at"])
                filtered.append(hit)
        return sorted(filtered, key=lambda item: item["score"], reverse=True)
```

```python
# packages/core/src/forecasting_harness/query_api.py
from __future__ import annotations


def summarize_top_branches(branches: list[dict], limit: int = 3) -> list[dict]:
    ordered = sorted(branches, key=lambda branch: branch["score"], reverse=True)
    return [
        {"branch_id": branch["branch_id"], "label": branch["label"], "score": branch["score"]}
        for branch in ordered[:limit]
    ]


def get_evidence_for_assumption(evidence_items: list[dict], assumption_id: str) -> list[dict]:
    return [item for item in evidence_items if assumption_id in item.get("assumption_ids", [])]
```

```python
# packages/core/src/forecasting_harness/retrieval/__init__.py
from forecasting_harness.retrieval.registry import CorpusRegistry
from forecasting_harness.retrieval.search import RetrievalQuery, SearchEngine

__all__ = ["CorpusRegistry", "RetrievalQuery", "SearchEngine"]
```

- [ ] **Step 4: Run the retrieval tests to verify they pass**

Run: `cd packages/core && python -m pytest tests/test_retrieval.py -v`

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit the retrieval and query surface**

```bash
git add packages/core/src/forecasting_harness/retrieval packages/core/src/forecasting_harness/query_api.py packages/core/tests/test_retrieval.py
git commit -m "feat: add local corpus registry and progressive disclosure query api"
```

## Task 5: Implement the Event-Driven Simulation Engine, Objective Scalarization, and Warm-Start Cache Rules

**Files:**
- Create: `/packages/core/src/forecasting_harness/simulation/__init__.py`
- Create: `/packages/core/src/forecasting_harness/simulation/engine.py`
- Create: `/packages/core/src/forecasting_harness/simulation/cache.py`
- Test: `/packages/core/tests/test_simulation.py`

- [ ] **Step 1: Write failing tests for event-driven expansion, scalarized node values, and dependency-aware invalidation**

```python
# packages/core/tests/test_simulation.py
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.models import BeliefState, ObjectiveProfile
from forecasting_harness.simulation.cache import should_reuse_node
from forecasting_harness.simulation.engine import scalarize_node_value


def test_scalarize_node_value_uses_objective_profile_weights() -> None:
    profile = ObjectiveProfile(
        name="avoid-escalation",
        metric_weights={"escalation": -1.0, "negotiation": 0.5},
        veto_thresholds={},
        risk_tolerance=0.5,
        asymmetry_penalties={},
    )
    assert scalarize_node_value({"escalation": 0.6, "negotiation": 0.2}, profile) == -0.5


def test_should_reuse_node_respects_dependency_masks() -> None:
    node = {
        "node_id": "n1",
        "dependencies": {"fields": ["fuel_days"], "metrics": ["economic_stress"]},
    }
    compatibility = {"changed_fields": ["morale"], "compatible": True}
    assert should_reuse_node(node, compatibility) is True
```

- [ ] **Step 2: Run the simulation tests to verify they fail**

Run: `cd packages/core && python -m pytest tests/test_simulation.py -v`

Expected: FAIL with import errors for `forecasting_harness.simulation`

- [ ] **Step 3: Implement the first event-driven simulation and cache helpers**

```python
# packages/core/src/forecasting_harness/simulation/engine.py
from __future__ import annotations

from forecasting_harness.models import BeliefState, ObjectiveProfile


def scalarize_node_value(metrics: dict[str, float], profile: ObjectiveProfile) -> float:
    return profile.scalarize(metrics)


class SimulationEngine:
    def __init__(self, domain_pack, objective_profile: ObjectiveProfile) -> None:
        self.domain_pack = domain_pack
        self.objective_profile = objective_profile

    def run(self, state: BeliefState) -> dict:
        assert state.interaction_model == self.domain_pack.interaction_model()
        branches = []
        for action_context in self.domain_pack.propose_actions(state):
            next_states = self.domain_pack.sample_transition(state, action_context)
            for next_state in next_states:
                metrics = self.domain_pack.score_state(next_state)
                branches.append(
                    {
                        "branch_id": f"{state.run_id}:{action_context['action_id']}",
                        "label": action_context["label"],
                        "metrics": metrics,
                        "score": scalarize_node_value(metrics, self.objective_profile),
                        "dependencies": action_context.get("dependencies", {"fields": []}),
                    }
                )
        return {"branches": sorted(branches, key=lambda item: item["score"], reverse=True)}
```

```python
# packages/core/src/forecasting_harness/simulation/cache.py
from __future__ import annotations


def should_reuse_node(node: dict, compatibility: dict) -> bool:
    if not compatibility.get("compatible", False):
        return False
    changed_fields = set(compatibility.get("changed_fields", []))
    dependencies = set(node.get("dependencies", {}).get("fields", []))
    return changed_fields.isdisjoint(dependencies)
```

```python
# packages/core/src/forecasting_harness/simulation/__init__.py
from forecasting_harness.simulation.engine import SimulationEngine, scalarize_node_value

__all__ = ["SimulationEngine", "scalarize_node_value"]
```

- [ ] **Step 4: Run the simulation tests to verify they pass**

Run: `cd packages/core && python -m pytest tests/test_simulation.py -v`

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit the simulation engine**

```bash
git add packages/core/src/forecasting_harness/simulation packages/core/tests/test_simulation.py
git commit -m "feat: add event-driven simulation engine and cache reuse rules"
```

## Task 6: Add a Generic Event Domain Pack and the End-to-End CLI Workflow

**Files:**
- Create: `/packages/core/src/forecasting_harness/domain/generic_event.py`
- Modify: `/packages/core/src/forecasting_harness/cli.py`
- Test: `/packages/core/tests/test_generic_event_pack.py`
- Test: `/packages/core/tests/test_cli_workflow.py`

- [ ] **Step 1: Write failing tests for the generic event pack and CLI run command**

```python
# packages/core/tests/test_generic_event_pack.py
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.domain.generic_event import GenericEventPack


def test_generic_event_pack_defaults_to_event_driven() -> None:
    pack = GenericEventPack()
    assert pack.interaction_model() is InteractionModel.EVENT_DRIVEN
    assert pack.propose_actions(None)[0]["action_id"] == "maintain-course"
```

```python
# packages/core/tests/test_cli_workflow.py
from pathlib import Path

from typer.testing import CliRunner

from forecasting_harness.cli import app


def test_demo_run_creates_report_and_workbench(tmp_path: Path) -> None:
    result = CliRunner().invoke(app, ["demo-run", "--root", str(tmp_path / ".forecast")])
    assert result.exit_code == 0
    assert (tmp_path / ".forecast" / "runs" / "demo-run" / "report.md").exists()
    assert (tmp_path / ".forecast" / "runs" / "demo-run" / "workbench.md").exists()
```

- [ ] **Step 2: Run the domain-pack and CLI tests to verify they fail**

Run: `cd packages/core && python -m pytest tests/test_generic_event_pack.py tests/test_cli_workflow.py -v`

Expected: FAIL with import error for `forecasting_harness.domain.generic_event` and missing `demo-run` command

- [ ] **Step 3: Implement the generic pack and CLI workflow**

```python
# packages/core/src/forecasting_harness/domain/generic_event.py
from __future__ import annotations

from forecasting_harness.domain.base import DomainPack, InteractionModel
from forecasting_harness.models import BeliefState


class GenericEventPack(DomainPack):
    def slug(self) -> str:
        return "generic-event"

    def interaction_model(self) -> InteractionModel:
        return InteractionModel.EVENT_DRIVEN

    def extend_schema(self) -> dict[str, str]:
        return {"morale": "float", "fuel_days": "int"}

    def suggest_questions(self) -> list[str]:
        return ["What changed most recently?", "Which actor has the most immediate leverage?"]

    def propose_actions(self, state: BeliefState | None) -> list[dict]:
        return [
            {
                "action_id": "maintain-course",
                "label": "Maintain current posture",
                "dependencies": {"fields": ["morale"]},
            },
            {
                "action_id": "signal-negotiation",
                "label": "Signal negotiation opening",
                "dependencies": {"fields": ["morale", "fuel_days"]},
            },
        ]

    def sample_transition(self, state: BeliefState, action_context: dict) -> list[BeliefState]:
        return [state]

    def score_state(self, state: BeliefState) -> dict[str, float]:
        return {"escalation": 0.2, "negotiation": 0.4, "economic_stress": 0.3}

    def validate_state(self, state: BeliefState) -> list[str]:
        return []
```

```python
# packages/core/src/forecasting_harness/cli.py
from pathlib import Path

import typer

from forecasting_harness import __version__
from forecasting_harness.artifacts import RunRepository
from forecasting_harness.domain.base import InteractionModel
from forecasting_harness.domain.generic_event import GenericEventPack
from forecasting_harness.models import BeliefState
from forecasting_harness.objectives import default_objective_profile
from forecasting_harness.simulation.engine import SimulationEngine

app = typer.Typer(no_args_is_help=True)


@app.command("version")
def version() -> None:
    typer.echo(__version__)


@app.command("demo-run")
def demo_run(root: Path = typer.Option(Path(".forecast"))) -> None:
    repo = RunRepository(root)
    state = BeliefState(
        run_id="demo-run",
        interaction_model=InteractionModel.EVENT_DRIVEN,
        actors=[],
        fields={},
        objectives={},
        capabilities={},
        constraints={},
        unknowns=[],
        current_epoch="2026-W16",
        horizon="2026-W20",
    )
    pack = GenericEventPack()
    engine = SimulationEngine(pack, default_objective_profile())
    result = engine.run(state)
    repo.save_belief_state("demo-run", state)
    repo.write_json("demo-run", "tree-summary.json", result)
    repo.write_markdown("demo-run", "report.md", "# Scenario Report\n\n- Top branch: Maintain current posture\n")
    repo.write_markdown("demo-run", "workbench.md", "# Analyst Workbench\n\n- Objective profile: balanced\n")
    typer.echo("demo-run complete")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run the domain-pack and CLI tests to verify they pass**

Run: `cd packages/core && python -m pytest tests/test_generic_event_pack.py tests/test_cli_workflow.py -v`

Expected: PASS with `2 passed`

- [ ] **Step 5: Commit the vertical-slice workflow**

```bash
git add packages/core/src/forecasting_harness/domain/generic_event.py packages/core/src/forecasting_harness/cli.py packages/core/tests/test_generic_event_pack.py packages/core/tests/test_cli_workflow.py
git commit -m "feat: add generic event pack and end-to-end demo workflow"
```

## Task 7: Add Thin Codex and Claude Adapter Scaffolding and Installation Docs

**Files:**
- Create: `/adapters/codex/forecast-harness/.codex-plugin/plugin.json`
- Create: `/adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md`
- Create: `/adapters/claude/skills/forecast-harness/SKILL.md`
- Create: `/docs/install-codex.md`
- Create: `/docs/install-claude-code.md`
- Test: `/packages/core/tests/test_adapter_docs.py`

- [ ] **Step 1: Write a failing test that checks the adapter docs point at the shared core CLI**

```python
# packages/core/tests/test_adapter_docs.py
from pathlib import Path


def test_install_docs_reference_shared_cli() -> None:
    codex_doc = Path(__file__).resolve().parents[3] / "docs" / "install-codex.md"
    claude_doc = Path(__file__).resolve().parents[3] / "docs" / "install-claude-code.md"
    assert "forecast-harness demo-run" in codex_doc.read_text(encoding="utf-8")
    assert "forecast-harness demo-run" in claude_doc.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run the adapter-doc test to verify it fails**

Run: `cd packages/core && python -m pytest tests/test_adapter_docs.py -v`

Expected: FAIL with `FileNotFoundError` for install docs

- [ ] **Step 3: Create the adapter scaffolding and install docs**

```json
{
  "name": "forecast-harness",
  "version": "0.1.0",
  "description": "Codex adapter for the forecasting harness",
  "interface": {
    "displayName": "Forecast Harness"
  }
}
```

```md
# adapters/codex/forecast-harness/skills/forecast-harness/SKILL.md
---
name: forecast-harness
description: Use the local forecasting harness CLI to create and inspect forecast runs from curated evidence.
---

1. Confirm the project has `packages/core` installed in a local virtualenv.
2. Run `forecast-harness demo-run`.
3. Read `.forecast/runs/<run-id>/report.md` or use query-style commands rather than loading the full workbench by default.
```

```md
# adapters/claude/skills/forecast-harness/SKILL.md
---
name: forecast-harness
description: Use the local forecasting harness CLI from Claude Code without loading full run artifacts into active context.
---

1. Install the shared core package from `packages/core`.
2. Run `forecast-harness demo-run`.
3. Prefer narrow artifact reads over loading full workbench content.
```

```md
# docs/install-codex.md
# Install in Codex

1. Create and activate a virtualenv at the repo root.
2. Run `pip install -e packages/core[dev]`.
3. Copy `adapters/codex/forecast-harness` into your local Codex plugins directory or link it from your workspace.
4. Verify the shared CLI works with `forecast-harness demo-run`.
```

```md
# docs/install-claude-code.md
# Install in Claude Code

1. Create and activate a virtualenv at the repo root.
2. Run `pip install -e packages/core[dev]`.
3. Copy `adapters/claude/skills/forecast-harness` into `.claude/skills/` for the target workspace or personal Claude directory.
4. Verify the shared CLI works with `forecast-harness demo-run`.
```

- [ ] **Step 4: Run the adapter-doc test to verify it passes**

Run: `cd packages/core && python -m pytest tests/test_adapter_docs.py -v`

Expected: PASS with `1 passed`

- [ ] **Step 5: Commit the adapter scaffolding**

```bash
git add adapters/codex adapters/claude docs/install-codex.md docs/install-claude-code.md packages/core/tests/test_adapter_docs.py
git commit -m "feat: add codex and claude adapter scaffolding"
```

## Task 8: Run the Full Test Suite and Smoke-Test the Vertical Slice

**Files:**
- Modify: `/README.md`

- [ ] **Step 1: Add a concise quickstart section to the README**

````md
# /README.md
# Forecasting Harness

Local-first forecasting harness for Codex and Claude Code.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e packages/core[dev]
forecast-harness demo-run
```
````

- [ ] **Step 2: Run the full package test suite**

Run: `cd packages/core && python -m pytest tests -v`

Expected: PASS with all tests green

- [ ] **Step 3: Run the CLI smoke test**

Run: `source .venv/bin/activate && forecast-harness demo-run`

Expected: command prints `demo-run complete` and creates `.forecast/runs/demo-run/`

- [ ] **Step 4: Inspect the generated artifacts**

Run: `ls -R .forecast/runs/demo-run`

Expected: includes `belief-state.json`, `tree-summary.json`, `report.md`, and `workbench.md`

- [ ] **Step 5: Commit the verified vertical slice**

```bash
git add README.md
git commit -m "docs: add quickstart and verify vertical slice"
```
