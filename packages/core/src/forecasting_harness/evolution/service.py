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
from forecasting_harness.knowledge.compiler import (
    CompiledKnowledgeCandidate,
    KnowledgeCompilerResult,
    compile_replay_miss_knowledge,
    suggestion_from_compiled_candidate,
)
from forecasting_harness.knowledge.manifests import load_domain_manifest
from forecasting_harness.knowledge import load_builtin_replay_cases
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
            try:
                return load_domain_manifest(domain_slug).model_dump(mode="json")
            except FileNotFoundError:
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
            return self._empty_replay_summary()
        result = run_replay_suite(cases)
        return self._replay_summary_from_result(domain_slug, result)

    def _empty_replay_summary(self) -> dict[str, object]:
        return {
            "case_count": 0,
            "top_branch_accuracy": 0.0,
            "root_strategy_accuracy": 0.0,
            "evidence_source_accuracy": 0.0,
            "average_inferred_field_coverage": 0.0,
            "domains_needing_attention": [],
        }

    def _replay_summary_from_result(self, domain_slug: str, result: ReplaySuiteResult) -> dict[str, object]:
        calibration = summarize_calibration(result)
        domain_metrics = calibration.domain_breakdown.get(domain_slug, {})
        return {
            "case_count": len([item for item in result.results if item.domain_pack == domain_slug]),
            "top_branch_accuracy": float(domain_metrics.get("top_branch_accuracy", 0.0)),
            "root_strategy_accuracy": float(domain_metrics.get("root_strategy_accuracy", 0.0)),
            "evidence_source_accuracy": float(domain_metrics.get("evidence_source_accuracy", 0.0)),
            "average_inferred_field_coverage": float(domain_metrics.get("average_inferred_field_coverage", 0.0)),
            "domains_needing_attention": calibration.domains_needing_attention,
        }

    def _replay_suite_for_domain(self, domain_slug: str, replay_cases: list[ReplayCase] | None = None) -> ReplaySuiteResult:
        cases = replay_cases if replay_cases is not None else self._load_replay_cases(domain_slug)
        if not cases:
            return ReplaySuiteResult(
                case_count=0,
                top_branch_accuracy=0.0,
                root_strategy_accuracy=0.0,
                evidence_source_accuracy=0.0,
                average_inferred_field_coverage=0.0,
                domain_breakdown={},
                results=[],
            )
        return run_replay_suite(cases)

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

    def record_compiler_candidates(
        self,
        domain_slug: str,
        *,
        candidates: list[CompiledKnowledgeCandidate],
    ) -> dict[str, object]:
        before_ids = {item.suggestion_id for item in self.evolution_storage.load_suggestions(domain_slug)}
        timestamp = datetime.now(timezone.utc)
        stored: list[DomainSuggestion] = []
        for candidate in candidates:
            suggestion = suggestion_from_compiled_candidate(
                domain_slug=domain_slug,
                candidate=candidate,
                timestamp=timestamp,
            )
            stored.append(self.evolution_storage.append_suggestion(suggestion))
        after = self.evolution_storage.load_suggestions(domain_slug)
        new_ids = sorted({item.suggestion_id for item in after}.difference(before_ids))
        return {
            "domain_slug": domain_slug,
            "candidate_count": len(candidates),
            "recorded_count": len(new_ids),
            "recorded_suggestion_ids": new_ids,
            "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
        }

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
            if result.top_branch_match is False
            or result.root_strategy_match is False
            or result.evidence_source_match is False
            or (
                bool(result.expected_inferred_fields)
                and result.inferred_field_coverage < 1.0
            )
        ]
        suggested_targets = sorted(
            {
                result.expected_root_strategy.lower().replace(" ", "-")
                for result in domain_results
                if result.root_strategy_match is False and result.expected_root_strategy
            }
        )
        reasons: list[str] = []
        top_or_root_misses = sum(
            1
            for result in domain_results
            if result.top_branch_match is False or result.root_strategy_match is False
        )
        evidence_misses = sum(1 for result in domain_results if result.evidence_source_match is False)
        field_gaps = sum(
            1
            for result in domain_results
            if result.expected_inferred_fields and result.inferred_field_coverage < 1.0
        )
        if top_or_root_misses:
            reasons.append(f"{top_or_root_misses} replay cases missed expected top branch or root strategy")
        if evidence_misses:
            reasons.append(f"{evidence_misses} replay cases missed expected evidence-source coverage")
        if field_gaps:
            reasons.append(f"{field_gaps} replay cases still have inferred-field gaps")

        brief = DomainWeaknessBrief(
            domain_slug=domain_slug,
            reasons=reasons,
            weak_cases=weak_cases,
            suggested_targets=suggested_targets,
        )
        return brief

    def compile_replay_knowledge(
        self,
        domain_slug: str,
        *,
        replay_result: ReplaySuiteResult,
    ) -> dict[str, object]:
        try:
            manifest = load_domain_manifest(domain_slug, root_override=self.manifest_root)
        except FileNotFoundError:
            manifest = load_domain_manifest(domain_slug)
        compiled = compile_replay_miss_knowledge(
            domain_slug=domain_slug,
            manifest=manifest,
            replay_result=replay_result,
        )
        record_summary = self.record_compiler_candidates(domain_slug, candidates=compiled.candidates)
        return {
            "domain_slug": domain_slug,
            "source_kind": compiled.source_kind,
            "candidate_count": compiled.candidate_count,
            **record_summary,
        }

    def run_replay_retuning(
        self,
        domain_slug: str,
        *,
        replay_cases: list[ReplayCase | dict[str, object]] | None = None,
        create_branch: bool = True,
    ) -> dict[str, object]:
        normalized_cases = (
            [case if isinstance(case, ReplayCase) else ReplayCase.model_validate(case) for case in replay_cases]
            if replay_cases is not None
            else self._load_replay_cases(domain_slug)
        )
        mixed_domains = sorted({case.domain_pack for case in normalized_cases if case.domain_pack != domain_slug})
        if mixed_domains:
            raise ValueError(
                f"mixed-domain replay payload for {domain_slug}: {', '.join(mixed_domains)}"
            )
        if not normalized_cases:
            summary = {
                "domain_slug": domain_slug,
                "case_count": 0,
                "weak_case_count": 0,
                "generated_suggestion_count": 0,
                "calibration_summary": self._empty_replay_summary(),
                "evolution_summary": None,
            }
            self.evolution_storage.write_report(domain_slug, "retuning-latest.json", summary)
            return summary

        before_suggestion_ids = {item.suggestion_id for item in self.evolution_storage.load_suggestions(domain_slug)}
        replay_result = self._replay_suite_for_domain(domain_slug, normalized_cases)
        calibration_summary = self._replay_summary_from_result(domain_slug, replay_result)
        compiler_summary = self.compile_replay_knowledge(domain_slug, replay_result=replay_result)
        weakness = self.analyze_domain_weakness(domain_slug, replay_result=replay_result)
        after_suggestions = self.evolution_storage.load_suggestions(domain_slug)
        generated_suggestion_count = len({item.suggestion_id for item in after_suggestions}.difference(before_suggestion_ids))

        evolution_summary = None
        if weakness.weak_cases:
            evolution_summary = self.run_domain_evolution(
                domain_slug,
                create_branch=create_branch,
                replay_cases=normalized_cases,
                replay_result=replay_result,
            )

        summary = {
            "domain_slug": domain_slug,
            "case_count": len(normalized_cases),
            "weak_case_count": len(weakness.weak_cases),
            "generated_suggestion_count": generated_suggestion_count,
            "calibration_summary": calibration_summary,
            "compiler_summary": compiler_summary,
            "weakness_brief": weakness.model_dump(mode="json"),
            "evolution_summary": evolution_summary,
        }
        self.evolution_storage.write_report(domain_slug, "retuning-latest.json", summary)
        return summary

    def _retuning_priority_key(self, summary: dict[str, object]) -> tuple[float, float, float, float, int, int, str]:
        calibration_summary = summary.get("calibration_summary", {})
        compiler_summary = summary.get("compiler_summary", {})
        if not isinstance(calibration_summary, dict):
            calibration_summary = {}
        if not isinstance(compiler_summary, dict):
            compiler_summary = {}
        return (
            float(calibration_summary.get("top_branch_accuracy", 0.0)),
            float(calibration_summary.get("root_strategy_accuracy", 0.0)),
            float(calibration_summary.get("evidence_source_accuracy", 0.0)),
            float(calibration_summary.get("average_inferred_field_coverage", 0.0)),
            -int(compiler_summary.get("candidate_count", 0)),
            int(summary.get("case_count", 0)),
            str(summary.get("domain_slug", "")),
        )

    def run_builtin_replay_retuning(
        self,
        *,
        domain_slugs: list[str] | None = None,
        create_branch: bool = True,
    ) -> dict[str, object]:
        builtin_cases = load_builtin_replay_cases(domain_packs=domain_slugs)
        grouped_cases: dict[str, list[ReplayCase]] = {}
        for case in builtin_cases:
            grouped_cases.setdefault(case.domain_pack, []).append(case)

        ordered_domains = sorted(grouped_cases)
        per_domain: dict[str, dict[str, object]] = {}
        case_count = 0
        weak_domain_count = 0
        generated_suggestion_count = 0
        for domain_slug in ordered_domains:
            summary = self.run_replay_retuning(
                domain_slug,
                replay_cases=grouped_cases[domain_slug],
                create_branch=create_branch,
            )
            per_domain[domain_slug] = summary
            case_count += int(summary["case_count"])
            generated_suggestion_count += int(summary["generated_suggestion_count"])
            if int(summary["weak_case_count"]) > 0:
                weak_domain_count += 1

        result = {
            "domains": ordered_domains,
            "prioritized_domains": sorted(ordered_domains, key=lambda slug: self._retuning_priority_key(per_domain[slug])),
            "domain_count": len(ordered_domains),
            "case_count": case_count,
            "weak_domain_count": weak_domain_count,
            "generated_suggestion_count": generated_suggestion_count,
            "per_domain": per_domain,
        }
        self.evolution_storage.write_report("_builtin", "retuning-latest.json", result)
        return result

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

    def run_domain_evolution(
        self,
        domain_slug: str,
        *,
        create_branch: bool = True,
        replay_cases: list[ReplayCase] | None = None,
        replay_result: ReplaySuiteResult | None = None,
    ) -> dict[str, object]:
        suggestions = self.evolution_storage.load_suggestions(domain_slug)
        replay_result = replay_result or self._replay_suite_for_domain(domain_slug, replay_cases)
        pre_metrics = self._replay_summary_from_result(domain_slug, replay_result)
        self.evolution_storage.write_baseline(domain_slug, "before.json", pre_metrics)
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
            post_result = self._replay_suite_for_domain(domain_slug, replay_cases)
            post_metrics = self._replay_summary_from_result(domain_slug, post_result)
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
        for key in (
            "top_branch_accuracy",
            "root_strategy_accuracy",
            "evidence_source_accuracy",
            "average_inferred_field_coverage",
        ):
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
