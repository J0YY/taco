"""Bootstrap deterministic fallback data for the TACO demo."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from taco_demo.config import ensure_data_dirs
from taco_demo.maniskill_gallery import build_maniskill_gallery
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import dataclass_to_dict, default_application, write_json
from taco_demo.video_utils import create_all_demo_videos


def _smooth_step(x: np.ndarray, center: float, sharpness: float = 10.0) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-sharpness * (x - center)))


def make_trace(certificate_id: str, mode: str, seed: int = 20260604) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed + sum(ord(ch) for ch in certificate_id + mode))
    t = np.linspace(0, 5, 140)
    p = np.linspace(0, 1, len(t))
    target = 0.82 + 0.03 * np.sin(8 * p)
    occ = 0.08 + 0.02 * np.sin(5 * p)
    lang = 0.06 + 0.02 * np.cos(4 * p)
    unsafe = 0.12 + 0.04 * np.sin(6 * p)
    action = 0.14 + 0.03 * np.cos(7 * p)

    if certificate_id == "FR-001":
        risk = _smooth_step(p, 0.58)
        if mode == "failure":
            target -= 0.58 * risk
            occ += 0.78 * risk
            unsafe += 0.72 * risk
            action += 0.70 * risk
        elif mode == "mitigated":
            target -= 0.22 * risk
            occ += 0.62 * risk
            unsafe += 0.35 * risk
            action += 0.18 * risk
    elif certificate_id == "FR-002":
        risk = _smooth_step(p, 0.48)
        if mode == "failure":
            lang += 0.84 * risk
            unsafe += 0.45 * risk
            action += 0.78 * risk
        elif mode == "mitigated":
            lang += 0.66 * risk
            action += 0.16 * risk
            unsafe += 0.22 * risk
    else:
        risk = _smooth_step(p, 0.62)
        if mode == "failure":
            target -= 0.38 * risk
            unsafe += 0.65 * risk
            action += 0.58 * risk
        elif mode == "mitigated":
            target -= 0.22 * risk
            unsafe += 0.38 * risk
            action += 0.30 * risk

    noise = lambda scale: rng.normal(0, scale, len(t))
    target_feature = np.clip(target + noise(0.012), 0, 1)
    occlusion_risk = np.clip(occ + noise(0.012), 0, 1)
    language_override_risk = np.clip(lang + noise(0.012), 0, 1)
    unsafe_trajectory_dominance = np.clip(unsafe + noise(0.014), 0, 1)
    action_risk = np.clip(action + noise(0.012), 0, 1)
    internal = np.clip(
        0.28 * occlusion_risk + 0.24 * language_override_risk + 0.28 * unsafe_trajectory_dominance + 0.20 * action_risk,
        0,
        1,
    )
    layer_16 = rng.normal(0, 0.2, (len(t), 64)) + internal[:, None] * rng.normal(0.4, 0.05, (1, 64))
    layer_24 = rng.normal(0, 0.2, (len(t), 64)) + action_risk[:, None] * rng.normal(0.35, 0.05, (1, 64))
    return {
        "time_s": t,
        "target_feature": target_feature,
        "occlusion_risk": occlusion_risk,
        "language_override_risk": language_override_risk,
        "unsafe_trajectory_dominance": unsafe_trajectory_dominance,
        "internal_risk_score": internal,
        "action_risk": action_risk,
        "layer_16_resid": layer_16,
        "layer_24_resid": layer_24,
    }


def bootstrap(root: Path | None = None, force: bool = False) -> Path:
    root = ensure_data_dirs(root)
    app_path = root / "applications" / "APP-APEX-001.json"
    if force or not app_path.exists():
        write_json(default_application(), app_path)
    names = {
        "FR-001": "FR-001-occlusion.json",
        "FR-002": "FR-002-language-override.json",
        "FR-003": "FR-003-distractor-confusion.json",
    }
    for cert in DEMO_CERTIFICATES:
        path = root / "dreamaudit_certs" / names[cert.certificate_id]
        if force or not path.exists():
            write_json(dataclass_to_dict(cert), path)
        for mode in ("success", "failure", "mitigated"):
            trace_path = root / "traces" / f"{cert.certificate_id}_{mode}.npz"
            if force or not trace_path.exists():
                np.savez(trace_path, **make_trace(cert.certificate_id, mode))
    create_all_demo_videos(root)
    build_maniskill_gallery(root, Path("/Users/joyyang/Projects/dreamaudit"), force=force)
    return root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--data-root", type=Path, default=None)
    args = parser.parse_args()
    root = bootstrap(args.data_root, args.force)
    print(f"Bootstrapped TACO fallback demo data under {root}")


if __name__ == "__main__":
    main()
