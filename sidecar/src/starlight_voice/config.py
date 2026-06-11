from __future__ import annotations

import os
from pathlib import Path


ENV_FILES = (".env.local", ".env")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_local_env(root: Path | None = None) -> list[Path]:
    base = root or repo_root()
    loaded: list[Path] = []

    for name in ENV_FILES:
        path = base / name
        if not path.exists():
            continue

        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value

        loaded.append(path)

    return loaded
