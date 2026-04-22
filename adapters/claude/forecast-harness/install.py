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


def main() -> None:
    parser = argparse.ArgumentParser(description="Install the local Claude forecasting-harness bundle.")
    parser.add_argument("--target-dir", required=True)
    parser.add_argument("--link", action="store_true")
    args = parser.parse_args()

    bundle_root = Path(__file__).resolve().parent
    manifest = json.loads((bundle_root / "adapter.json").read_text(encoding="utf-8"))
    target_root = Path(args.target_dir).resolve()
    target_root.mkdir(parents=True, exist_ok=True)

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
                "adapter": "claude",
                "bundle_name": manifest["name"],
                "target_dir": str(target_root),
                "installed_paths": installed_paths,
                "mode": "link" if args.link else "copy",
            }
        )
    )


if __name__ == "__main__":
    main()
