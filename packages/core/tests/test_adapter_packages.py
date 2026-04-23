from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _python_bin() -> str:
    return sys.executable


def _run_json(command: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> dict[str, object]:
    result = subprocess.run(command, cwd=cwd, env=env, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def test_codex_adapter_bundle_installs_into_target_dir(tmp_path: Path) -> None:
    repo_root = _repo_root()
    target_dir = tmp_path / "codex-plugins"
    payload = _run_json(
        [_python_bin(), str(repo_root / "adapters" / "codex" / "scenario-lab" / "install.py"), "--target-dir", str(target_dir)],
        cwd=repo_root,
    )

    assert payload["adapter"] == "codex"
    assert (target_dir / "scenario-lab" / ".codex-plugin" / "plugin.json").exists()
    assert (target_dir / "scenario-lab" / "skills" / "scenario-lab" / "SKILL.md").exists()


def test_claude_adapter_bundle_installs_into_target_dir(tmp_path: Path) -> None:
    repo_root = _repo_root()
    target_dir = tmp_path / ".claude"
    payload = _run_json(
        [_python_bin(), str(repo_root / "adapters" / "claude" / "scenario-lab" / "install.py"), "--target-dir", str(target_dir)],
        cwd=repo_root,
    )

    assert payload["adapter"] == "claude"
    assert (target_dir / "skills" / "scenario-lab" / "SKILL.md").exists()


def test_codex_adapter_smoke_script_runs_end_to_end(tmp_path: Path) -> None:
    repo_root = _repo_root()
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    package_src = str(repo_root / "packages" / "core" / "src")
    env["PYTHONPATH"] = package_src if not existing else f"{package_src}{os.pathsep}{existing}"
    payload = _run_json(
        [
            _python_bin(),
            str(repo_root / "adapters" / "codex" / "scenario-lab" / "smoke.py"),
            "--work-dir",
            str(tmp_path / "codex-smoke"),
        ],
        cwd=repo_root,
        env=env,
    )

    assert payload["adapter"] == "codex"
    assert payload["stages"] == ["intake", "evidence", "evidence", "approval", "simulation", "report"]
    assert payload["recommended_runtime_actions"][-1] == "begin-revision-update"
    assert payload["run_summary"]["current_revision_id"] == "r1"
    assert payload["revision_summary"]["revision_id"] == "r1"
    assert "simulation" in payload["revision_summary"]["available_sections"]
    assert payload["report_result"].startswith("reported r1 ")
    assert payload["report_result"].endswith("/r1.report.md")
    assert payload["report_exists"] is True


def test_claude_adapter_smoke_script_runs_end_to_end(tmp_path: Path) -> None:
    repo_root = _repo_root()
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    package_src = str(repo_root / "packages" / "core" / "src")
    env["PYTHONPATH"] = package_src if not existing else f"{package_src}{os.pathsep}{existing}"
    payload = _run_json(
        [
            _python_bin(),
            str(repo_root / "adapters" / "claude" / "scenario-lab" / "smoke.py"),
            "--work-dir",
            str(tmp_path / "claude-smoke"),
        ],
        cwd=repo_root,
        env=env,
    )

    assert payload["adapter"] == "claude"
    assert payload["stages"] == ["intake", "evidence", "evidence", "approval", "simulation", "report"]
    assert payload["recommended_runtime_actions"][-1] == "begin-revision-update"
    assert payload["run_summary"]["current_revision_id"] == "r1"
    assert payload["revision_summary"]["revision_id"] == "r1"
    assert "simulation" in payload["revision_summary"]["available_sections"]
    assert payload["report_result"].startswith("reported r1 ")
    assert payload["report_result"].endswith("/r1.report.md")
    assert payload["report_exists"] is True
