from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from forecasting_harness.evolution.models import DomainSuggestion


class EvolutionStorage:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _suggestions_path(self, domain_slug: str) -> Path:
        return self.root / "suggestions" / f"{domain_slug}.jsonl"

    def _ensure_parent(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

    def _reports_path(self, domain_slug: str, filename: str) -> Path:
        return self.root / "reports" / domain_slug / filename

    def _failed_path(self, domain_slug: str, filename: str) -> Path:
        return self.root / "failed" / domain_slug / filename

    def append_suggestion(self, suggestion: DomainSuggestion) -> DomainSuggestion:
        path = self._suggestions_path(suggestion.domain_slug)
        self._ensure_parent(path)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(suggestion.model_dump(mode="json"), sort_keys=True) + "\n")
        return suggestion

    def load_suggestions(self, domain_slug: str) -> list[DomainSuggestion]:
        path = self._suggestions_path(domain_slug)
        if not path.exists():
            return []
        return [
            DomainSuggestion.model_validate(json.loads(line))
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def write_baseline(self, domain_slug: str, filename: str, payload: dict[str, Any]) -> Path:
        path = self.root / "baselines" / domain_slug / filename
        self._ensure_parent(path)
        path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
        return path

    def write_report(self, domain_slug: str, filename: str, payload: dict[str, Any]) -> Path:
        path = self._reports_path(domain_slug, filename)
        self._ensure_parent(path)
        path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
        return path

    def write_failed(self, domain_slug: str, filename: str, payload: dict[str, Any]) -> Path:
        path = self._failed_path(domain_slug, filename)
        self._ensure_parent(path)
        path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
        return path

    def save_suggestions(self, domain_slug: str, suggestions: list[DomainSuggestion]) -> Path:
        path = self._suggestions_path(domain_slug)
        self._ensure_parent(path)
        lines = [json.dumps(item.model_dump(mode="json"), sort_keys=True) for item in suggestions]
        path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return path
