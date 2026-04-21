from __future__ import annotations

import json
import pprint
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from forecasting_harness.domain.template_utils import tokenize_text
from forecasting_harness.evolution.models import DomainBlueprint, DomainEvolutionCandidate, DomainSuggestion, DomainWeaknessBrief
from forecasting_harness.evolution.storage import EvolutionStorage
from forecasting_harness.replay import ReplayCase, ReplaySuiteResult, run_replay_suite, summarize_calibration


class DomainEvolutionService:
    def __init__(self, *, evolution_storage: EvolutionStorage, manifest_root: Path) -> None:
        self.evolution_storage = evolution_storage
        self.manifest_root = Path(manifest_root)
        self.workspace_root = self.manifest_root.parents[1]

    def _manifest_path(self, domain_slug: str) -> Path:
        return self.manifest_root / f"{domain_slug}.json"

    def _replay_path(self, domain_slug: str) -> Path:
        return self.workspace_root / "knowledge" / "replays" / f"{domain_slug}.json"

    def _domain_dir(self) -> Path:
        return self.workspace_root / "packages" / "core" / "src" / "forecasting_harness" / "domain"

    def _registry_path(self) -> Path:
        return self._domain_dir() / "registry.py"

    def _tests_dir(self) -> Path:
        return self.workspace_root / "packages" / "core" / "tests"

    def _load_manifest(self, domain_slug: str) -> dict[str, object]:
        path = self._manifest_path(domain_slug)
        if not path.exists():
            raise FileNotFoundError(path)
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_manifest(self, domain_slug: str, payload: dict[str, object]) -> Path:
        path = self._manifest_path(domain_slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, sort_keys=True, indent=2), encoding="utf-8")
        return path

    def _replay_root(self) -> Path:
        return self.workspace_root / "knowledge" / "replays"

    def _load_replay_cases(self, domain_slug: str) -> list[ReplayCase]:
        replay_root = self._replay_root()
        if not replay_root.exists():
            return []
        cases: list[ReplayCase] = []
        for replay_path in sorted(replay_root.glob("*.json")):
            payload = json.loads(replay_path.read_text(encoding="utf-8"))
            for item in payload:
                case = ReplayCase.model_validate(item)
                if case.domain_pack == domain_slug:
                    cases.append(case)
        return cases

    def _replay_summary(self, domain_slug: str) -> dict[str, object]:
        cases = self._load_replay_cases(domain_slug)
        if not cases:
            return {
                "case_count": 0,
                "top_branch_accuracy": 0.0,
                "root_strategy_accuracy": 0.0,
                "evidence_source_accuracy": 0.0,
                "average_inferred_field_coverage": 0.0,
                "domains_needing_attention": [],
            }
        result = run_replay_suite(cases)
        calibration = summarize_calibration(result)
        domain_metrics = calibration.domain_breakdown.get(domain_slug, {})
        return {
            "case_count": len(cases),
            "top_branch_accuracy": float(domain_metrics.get("top_branch_accuracy", 0.0)),
            "root_strategy_accuracy": float(domain_metrics.get("root_strategy_accuracy", 0.0)),
            "evidence_source_accuracy": float(domain_metrics.get("evidence_source_accuracy", 0.0)),
            "average_inferred_field_coverage": float(domain_metrics.get("average_inferred_field_coverage", 0.0)),
            "domains_needing_attention": calibration.domains_needing_attention,
        }

    def record_suggestion(
        self,
        domain_slug: str,
        *,
        text: str,
        category: str | None = None,
        target: str | None = None,
        terms: list[str] | None = None,
        provenance: str = "user",
    ) -> DomainSuggestion:
        normalized_category = category or self._classify_category(text=text, target=target)
        suggestion = DomainSuggestion(
            suggestion_id=f"{provenance}-{domain_slug}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            timestamp=datetime.now(timezone.utc),
            domain_slug=domain_slug,
            provenance=provenance,  # type: ignore[arg-type]
            category=normalized_category,  # type: ignore[arg-type]
            target=target,
            text=text,
            terms=terms or self._extract_terms(text),
            status="pending",
        )
        return self.evolution_storage.append_suggestion(suggestion)

    def synthesize_domain(self, blueprint: DomainBlueprint, *, create_branch: bool = True) -> dict[str, object]:
        slug = blueprint.slug
        file_stem = slug.replace("-", "_")
        manifest_payload = {
            "slug": blueprint.slug,
            "description": blueprint.description,
            "actor_categories": blueprint.actor_categories,
            "evidence_categories": blueprint.evidence_categories,
            "evidence_category_terms": blueprint.evidence_category_terms,
            "key_state_fields": sorted(blueprint.field_schema),
            "canonical_stages": blueprint.canonical_stages,
            "recommended_source_types": sorted({item.get("kind", "document") for item in blueprint.starter_sources}),
            "starter_sources": blueprint.starter_sources,
            "semantic_alias_groups": blueprint.semantic_alias_groups,
        }

        manifest_path = self._write_manifest(slug, manifest_payload)
        replay_path = self._replay_path(slug)
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        replay_path.write_text(json.dumps(blueprint.replay_seed_cases, indent=2, sort_keys=True), encoding="utf-8")

        pack_path = self._domain_dir() / f"{file_stem}.py"
        pack_path.parent.mkdir(parents=True, exist_ok=True)
        pack_path.write_text(self._render_pack_file(blueprint), encoding="utf-8")

        test_path = self._tests_dir() / f"test_{file_stem}_pack.py"
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text(self._render_pack_test(blueprint), encoding="utf-8")

        self._update_registry(blueprint)

        branch_name = None
        if create_branch:
            branch_name = self._promote_synthesis_branch(slug)
            self._commit_synthesis_changes(slug, branch_name, paths=[manifest_path, replay_path, pack_path, test_path, self._registry_path()])

        return {
            "domain_slug": slug,
            "branch_name": branch_name,
            "generated_files": [
                str(manifest_path),
                str(replay_path),
                str(pack_path),
                str(test_path),
                str(self._registry_path()),
            ],
        }

    def _render_pack_file(self, blueprint: DomainBlueprint) -> str:
        payload = pprint.pformat(blueprint.model_dump(mode="python"), sort_dicts=True, width=100)
        return (
            "from forecasting_harness.domain.generated_template import GeneratedTemplatePack\n"
            "from forecasting_harness.evolution.models import DomainBlueprint\n\n\n"
            f"class {blueprint.class_name}(GeneratedTemplatePack):\n"
            f"    BLUEPRINT = DomainBlueprint.model_validate({payload})\n"
        )

    def _render_pack_test(self, blueprint: DomainBlueprint) -> str:
        module_name = blueprint.slug.replace("-", "_")
        return (
            "from forecasting_harness.workflow.models import IntakeDraft\n\n\n"
            f"def test_{module_name}_pack_imports_and_validates() -> None:\n"
            f"    from forecasting_harness.domain.{module_name} import {blueprint.class_name}\n\n"
            f"    pack = {blueprint.class_name}()\n"
            "    intake = IntakeDraft(\n"
            "        event_framing='Assess scenario evolution',\n"
            f"        focus_entities={['Entity A'] * max(blueprint.focus_entity_rule.min_count, blueprint.focus_entity_rule.exact_count or blueprint.focus_entity_rule.min_count)},\n"
            f"        current_development='A material development occurred',\n"
            f"        current_stage={blueprint.canonical_stages!r}[0],\n"
            "        time_horizon='30d',\n"
            "        pack_fields={},\n"
            "    )\n\n"
            f"    assert pack.slug() == {blueprint.slug!r}\n"
            "    assert pack.validate_intake(intake) == []\n"
        )

    def _update_registry(self, blueprint: DomainBlueprint) -> None:
        registry_path = self._registry_path()
        registry_text = registry_path.read_text(encoding="utf-8")
        module_name = blueprint.slug.replace("-", "_")
        import_line = f"from forecasting_harness.domain.{module_name} import {blueprint.class_name}"
        register_line = f'    registry.register("{blueprint.slug}", {blueprint.class_name})'

        if import_line not in registry_text:
            match = re.search(r"(from forecasting_harness\.domain\.[^\n]+\n)+", registry_text)
            if match:
                import_block = match.group(0) + import_line + "\n"
                registry_text = registry_text[: match.start()] + import_block + registry_text[match.end() :]
            else:
                registry_text = import_line + "\n" + registry_text

        if register_line not in registry_text:
            anchor = "    return registry"
            registry_text = registry_text.replace(anchor, f"{register_line}\n{anchor}")

        registry_path.write_text(registry_text, encoding="utf-8")

    def _classify_category(self, *, text: str, target: str | None) -> str:
        lower = text.lower()
        if target:
            return "action-bias"
        if "synonym" in lower or "alias" in lower:
            return "semantic-alias"
        if "evidence" in lower or "category" in lower:
            return "evidence-category"
        if "field" in lower or "state" in lower:
            return "state-field"
        return "action-bias"

    def analyze_domain_weakness(self, domain_slug: str, *, replay_result: ReplaySuiteResult) -> DomainWeaknessBrief:
        domain_results = [result for result in replay_result.results if result.domain_pack == domain_slug]
        weak_cases = [
            result.run_id
            for result in domain_results
            if result.top_branch_match is False or result.root_strategy_match is False
        ]
        suggested_targets = sorted(
            {
                result.expected_root_strategy.lower().replace(" ", "-")
                for result in domain_results
                if result.root_strategy_match is False and result.expected_root_strategy
            }
        )
        reasons: list[str] = []
        if weak_cases:
            reasons.append(f"{len(weak_cases)} replay cases missed expected top branch or root strategy")

        brief = DomainWeaknessBrief(
            domain_slug=domain_slug,
            reasons=reasons,
            weak_cases=weak_cases,
            suggested_targets=suggested_targets,
        )

        for result in domain_results:
            if result.root_strategy_match is not False or not result.expected_root_strategy:
                continue
            terms = self._extract_terms(" ".join(result.evidence_sources + [result.expected_root_strategy]))
            suggestion = DomainSuggestion(
                suggestion_id=f"self-{domain_slug}-{result.run_id}",
                timestamp=datetime.now(timezone.utc),
                domain_slug=domain_slug,
                provenance="self-detected",
                category="action-bias",
                target=result.expected_root_strategy.lower().replace(" ", "-"),
                text=f"Replay miss for {result.run_id}: bias toward {result.expected_root_strategy}.",
                terms=terms,
                status="pending",
            )
            self.evolution_storage.append_suggestion(suggestion)
        return brief

    def synthesize_candidate(
        self,
        domain_slug: str,
        *,
        suggestions: list[DomainSuggestion],
        weakness_brief: DomainWeaknessBrief | None,
    ) -> DomainEvolutionCandidate:
        manifest = self._load_manifest(domain_slug)
        changed = False
        applied_ids: list[str] = []

        adaptive_action_biases = list(manifest.get("adaptive_action_biases", []))
        adaptive_state_terms = dict(manifest.get("adaptive_state_terms", {}))
        semantic_alias_groups = list(manifest.get("semantic_alias_groups", []))
        evidence_category_terms = dict(manifest.get("evidence_category_terms", {}))

        for suggestion in suggestions:
            if suggestion.domain_slug != domain_slug or suggestion.status != "pending":
                continue
            if suggestion.category == "action-bias" and suggestion.target:
                candidate = {
                    "target": suggestion.target,
                    "terms": suggestion.terms or self._extract_terms(suggestion.text),
                    "delta": 0.12,
                }
                if candidate not in adaptive_action_biases:
                    adaptive_action_biases.append(candidate)
                    changed = True
                    applied_ids.append(suggestion.suggestion_id)
            elif suggestion.category == "state-field" and suggestion.target:
                rules = list(adaptive_state_terms.get(suggestion.target, []))
                candidate = {"terms": suggestion.terms or self._extract_terms(suggestion.text), "delta": 0.08}
                if candidate not in rules:
                    rules.append(candidate)
                    adaptive_state_terms[suggestion.target] = rules
                    changed = True
                    applied_ids.append(suggestion.suggestion_id)
            elif suggestion.category == "semantic-alias":
                alias_group = suggestion.terms or self._extract_terms(suggestion.text)
                if alias_group and alias_group not in semantic_alias_groups:
                    semantic_alias_groups.append(alias_group)
                    changed = True
                    applied_ids.append(suggestion.suggestion_id)
            elif suggestion.category == "evidence-category":
                category_name = suggestion.target or "general"
                existing_terms = list(evidence_category_terms.get(category_name, []))
                for term in suggestion.terms or self._extract_terms(suggestion.text):
                    if term not in existing_terms:
                        existing_terms.append(term)
                if existing_terms != evidence_category_terms.get(category_name, []):
                    evidence_category_terms[category_name] = existing_terms
                    changed = True
                    applied_ids.append(suggestion.suggestion_id)

        if weakness_brief and weakness_brief.suggested_targets:
            manifest.setdefault("evolution_notes", [])
            note = f"weak replay targets: {', '.join(weakness_brief.suggested_targets)}"
            if note not in manifest["evolution_notes"]:
                manifest["evolution_notes"].append(note)
                changed = True

        if adaptive_action_biases:
            manifest["adaptive_action_biases"] = adaptive_action_biases
        if adaptive_state_terms:
            manifest["adaptive_state_terms"] = adaptive_state_terms
        if semantic_alias_groups:
            manifest["semantic_alias_groups"] = semantic_alias_groups
        if evidence_category_terms:
            manifest["evidence_category_terms"] = evidence_category_terms

        return DomainEvolutionCandidate(
            domain_slug=domain_slug,
            updated_manifest=manifest,
            changed=changed,
            applied_suggestion_ids=applied_ids,
        )

    def summarize_domain_evolution(self, domain_slug: str) -> dict[str, object]:
        suggestions = self.evolution_storage.load_suggestions(domain_slug)
        latest_report = self.evolution_storage.root / "reports" / domain_slug / "latest.json"
        payload = {
            "domain_slug": domain_slug,
            "pending_suggestions": sum(item.status == "pending" for item in suggestions),
            "suggestion_count": len(suggestions),
        }
        if latest_report.exists():
            payload["latest_report"] = json.loads(latest_report.read_text(encoding="utf-8"))
        return payload

    def run_domain_evolution(self, domain_slug: str, *, create_branch: bool = True) -> dict[str, object]:
        suggestions = self.evolution_storage.load_suggestions(domain_slug)
        pre_metrics = self._replay_summary(domain_slug)
        self.evolution_storage.write_baseline(domain_slug, "before.json", pre_metrics)

        replay_cases = self._load_replay_cases(domain_slug)
        replay_result = run_replay_suite(replay_cases) if replay_cases else ReplaySuiteResult(
            case_count=0,
            top_branch_accuracy=0.0,
            root_strategy_accuracy=0.0,
            evidence_source_accuracy=0.0,
            average_inferred_field_coverage=0.0,
            domain_breakdown={},
            results=[],
        )
        weakness = self.analyze_domain_weakness(domain_slug, replay_result=replay_result)
        suggestions = self.evolution_storage.load_suggestions(domain_slug)
        candidate = self.synthesize_candidate(domain_slug, suggestions=suggestions, weakness_brief=weakness)
        if not candidate.changed:
            summary = {
                "domain_slug": domain_slug,
                "promotion_decision": "rejected",
                "reason": "no candidate changes",
                "pre_metrics": pre_metrics,
            }
            self.evolution_storage.write_failed(domain_slug, "latest.json", summary)
            return summary

        manifest_path = self._manifest_path(domain_slug)
        original_manifest = manifest_path.read_text(encoding="utf-8")
        try:
            self._write_manifest(domain_slug, candidate.updated_manifest)
            post_metrics = self._replay_summary(domain_slug)
            self.evolution_storage.write_baseline(domain_slug, "after.json", post_metrics)
            decision = self._promotion_decision(pre_metrics=pre_metrics, post_metrics=post_metrics, candidate=candidate)
            branch_name = None
            if decision == "promoted" and create_branch:
                branch_name = self._promote_branch(domain_slug)
                self._commit_domain_changes(domain_slug, branch_name)
            elif decision != "promoted":
                manifest_path.write_text(original_manifest, encoding="utf-8")

            suggestions = [
                suggestion.model_copy(
                    update={
                        "status": (
                            "promoted"
                            if suggestion.suggestion_id in candidate.applied_suggestion_ids and decision == "promoted"
                            else "rejected"
                            if suggestion.suggestion_id in candidate.applied_suggestion_ids and decision == "rejected"
                            else "accepted"
                            if suggestion.suggestion_id in candidate.applied_suggestion_ids
                            else suggestion.status
                        )
                    }
                )
                for suggestion in suggestions
            ]
            self.evolution_storage.save_suggestions(domain_slug, suggestions)

            summary = {
                "domain_slug": domain_slug,
                "promotion_decision": decision,
                "branch_name": branch_name,
                "applied_suggestion_ids": candidate.applied_suggestion_ids,
                "pre_metrics": pre_metrics,
                "post_metrics": post_metrics,
            }
            self.evolution_storage.write_report(domain_slug, "latest.json", summary)
            return summary
        finally:
            if not create_branch:
                # In test/no-branch mode, leave the synthesized manifest in place so callers can inspect the result.
                pass

    def _promotion_decision(
        self,
        *,
        pre_metrics: dict[str, object],
        post_metrics: dict[str, object],
        candidate: DomainEvolutionCandidate,
    ) -> str:
        for key in ("top_branch_accuracy", "root_strategy_accuracy", "evidence_source_accuracy"):
            if float(post_metrics.get(key, 0.0)) < float(pre_metrics.get(key, 0.0)):
                return "rejected"
        improved = any(
            float(post_metrics.get(key, 0.0)) > float(pre_metrics.get(key, 0.0))
            for key in ("top_branch_accuracy", "root_strategy_accuracy", "average_inferred_field_coverage")
        )
        expanded = bool(candidate.applied_suggestion_ids)
        return "promoted" if improved or expanded else "rejected"

    def _promote_branch(self, domain_slug: str) -> str:
        branch_name = f"codex/domain-evolution-{domain_slug}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        subprocess.run(["git", "checkout", "-B", branch_name], cwd=self.workspace_root, check=True)
        return branch_name

    def _promote_synthesis_branch(self, domain_slug: str) -> str:
        branch_name = f"codex/domain-synthesis-{domain_slug}-{datetime.now(timezone.utc).strftime('%Y%m%d')}"
        subprocess.run(["git", "checkout", "-B", branch_name], cwd=self.workspace_root, check=True)
        return branch_name

    def _commit_domain_changes(self, domain_slug: str, branch_name: str) -> None:
        report_path = self.evolution_storage.write_report(
            domain_slug,
            f"{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}.json",
            {"branch_name": branch_name, "domain_slug": domain_slug},
        )
        baseline_dir = self.evolution_storage.root / "baselines" / domain_slug
        subprocess.run(
            [
                "git",
                "add",
                str(self._manifest_path(domain_slug)),
                str(report_path),
                str(baseline_dir / "before.json"),
                str(baseline_dir / "after.json"),
                str(self.evolution_storage._suggestions_path(domain_slug)),
            ],
            cwd=self.workspace_root,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"feat: evolve {domain_slug} domain knowledge"],
            cwd=self.workspace_root,
            check=True,
        )

    def _commit_synthesis_changes(self, domain_slug: str, branch_name: str, *, paths: list[Path]) -> None:
        subprocess.run(["git", "add", *[str(path) for path in paths]], cwd=self.workspace_root, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: synthesize {domain_slug} domain"],
            cwd=self.workspace_root,
            check=True,
        )

    def _extract_terms(self, text: str) -> list[str]:
        stopwords = {
            "a",
            "an",
            "and",
            "as",
            "bias",
            "for",
            "from",
            "into",
            "of",
            "or",
            "replay",
            "should",
            "the",
            "toward",
        }
        tokens = [token for token in tokenize_text(text) if len(token) >= 4 and token not in stopwords]
        if not tokens:
            return []
        return [" ".join(tokens[:2])] if len(tokens) >= 2 else [tokens[0]]
