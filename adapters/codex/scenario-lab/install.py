from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def _copy_entry(source: Path, target: Path) -> None:
    if source.is_dir():
        shutil.copytree(source, target, dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__"))
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _remove_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the local Scenario Lab Codex bundle.")
    parser.add_argument("--target-dir", required=True)
    parser.add_argument("--link", action="store_true")
    args = parser.parse_args()

    bundle_root = Path(__file__).resolve().parent
    manifest = json.loads((bundle_root / "adapter.json").read_text(encoding="utf-8"))
    target_root = Path(args.target_dir).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

    legacy_root = target_root / "forecast-harness"
    for legacy_target in (
        legacy_root / ".codex-plugin",
        legacy_root / "skills",
        legacy_root / "README.md",
    ):
        if legacy_target.exists() or legacy_target.is_symlink():
            _remove_path(legacy_target)
    if legacy_root.exists() and not any(legacy_root.iterdir()):
        legacy_root.rmdir()

    installed_paths: list[str] = []
    for entry in manifest["install_entries"]:
        source = bundle_root / entry["source"]
        target = target_root / entry["target"]
        if target.exists() or target.is_symlink():
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target)
            else:
                target.unlink()
        if args.link:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.symlink_to(source, target_is_directory=source.is_dir())
        else:
            _copy_entry(source, target)
        installed_paths.append(str(target))

    print(
        json.dumps(
            {
                "adapter": "codex",
                "bundle_name": manifest["name"],
                "target_dir": str(target_root),
                "installed_paths": installed_paths,
                "mode": "link" if args.link else "copy",
            }
        )
    )


if __name__ == "__main__":
    main()
