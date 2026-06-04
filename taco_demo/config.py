"""Configuration helpers for the TACO demo."""

from __future__ import annotations

import os
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parent


def data_root() -> Path:
    return Path(os.environ.get("TACO_DEMO_DATA_ROOT", PACKAGE_ROOT / "data")).resolve()


def dreamaudit_root() -> Path:
    return Path(os.environ.get("DREAMAUDIT_ROOT", REPO_ROOT.parent / "dreamaudit")).resolve()


def ensure_data_dirs(root: Path | None = None) -> Path:
    root = root or data_root()
    for name in ("applications", "dreamaudit_certs", "traces", "videos", "quotes"):
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


DEFAULT_APPLICATION_PATH = data_root() / "applications" / "APP-APEX-001.json"

