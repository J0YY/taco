"""Bootstrap deterministic offline evidence for the TACO MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import default_application, write_json
from taco_demo.maniskill_suite import write_maniskill_suite
from taco_demo.video_utils import create_all_demo_videos


DATA_DIRS = ("applications", "certificates", "traces", "videos", "binders", "maniskill_suite")


def ensure_data_dirs(root: Path) -> Path:
    for name in DATA_DIRS:
        (root / name).mkdir(parents=True, exist_ok=True)
    return root


def _step(x: np.ndarray, center: float, sharpness: float = 14.0) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-sharpness * (x - center)))


def make_trace(certificate_id: str, mode: str, seed: int = 20260604) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed + sum(ord(ch) for ch in certificate_id + mode))
    t = np.linspace(0, 5.0, 140)
    p = np.linspace(0, 1.0, len(t))

    target = 0.84 + 0.02 * np.sin(6 * p)
    grasp = 0.78 + 0.03 * np.cos(5 * p)
    transport = 0.72 + 0.03 * np.sin(4 * p)
    completion = 0.18 + 0.70 * p
    memorized = 0.10 + 0.02 * np.cos(3 * p)
    occlusion = 0.07 + 0.015 * np.sin(4 * p)
    language = 0.06 + 0.015 * np.cos(4 * p)
    distractor = 0.08 + 0.015 * np.sin(5 * p)
    unsafe = 0.12 + 0.025 * np.sin(6 * p)
    action = 0.13 + 0.02 * np.cos(5 * p)

    if certificate_id == "FR-001":
        risk = _step(p, 0.58)
        if mode == "failure":
            occlusion += 0.82 * risk
            target -= 0.30 * risk
            grasp -= 0.25 * risk
            unsafe += 0.15 * risk
            memorized += 0.18 * risk
            action += 0.35 * risk
        elif mode == "mitigated":
            occlusion += 0.70 * risk
            target -= 0.20 * risk
            grasp -= 0.10 * risk
            unsafe += 0.25 * risk
            memorized += 0.20 * risk
            action += 0.02 * risk
    elif certificate_id == "FR-002":
        risk = _step(p, 0.46)
        if mode == "failure":
            language += 0.86 * risk
            unsafe += 0.18 * risk
            action += 0.42 * risk
            memorized += 0.15 * risk
        elif mode == "mitigated":
            language += 0.72 * risk
            unsafe += 0.15 * risk
            action += 0.02 * risk
            memorized += 0.20 * risk
    else:
        risk = _step(p, 0.62)
        if mode == "failure":
            distractor += 0.78 * risk
            memorized += 0.20 * risk
            target -= 0.15 * risk
            unsafe += 0.12 * risk
            action += 0.30 * risk
        elif mode == "mitigated":
            distractor += 0.48 * risk
            memorized += 0.20 * risk
            target -= 0.18 * risk
            unsafe += 0.18 * risk
            action += 0.03 * risk

    def noisy(values: np.ndarray, scale: float = 0.01) -> np.ndarray:
        return np.clip(values + rng.normal(0, scale, len(values)), 0, 1)

    target = noisy(target)
    grasp = noisy(grasp)
    transport = noisy(transport)
    completion = noisy(completion)
    memorized = noisy(memorized)
    occlusion = noisy(occlusion)
    language = noisy(language)
    distractor = noisy(distractor)
    unsafe = noisy(unsafe)
    action = noisy(action)
    if mode == "mitigated":
        action = np.clip(action * (1.0 - 0.85 * risk), 0, 1)
    risk_bundle = np.maximum.reduce([occlusion, language, distractor, unsafe, action, memorized])
    internal = np.clip(0.15 + 0.85 * risk_bundle, 0, 1)
    return {
        "time_s": t,
        "target_feature": target,
        "general_grasp_feature": grasp,
        "transport_feature": transport,
        "task_completion_feature": completion,
        "memorized_trajectory_feature": memorized,
        "occlusion_risk": occlusion,
        "language_override_risk": language,
        "distractor_risk": distractor,
        "unsafe_trajectory_dominance": unsafe,
        "internal_risk_score": internal,
        "action_risk": action,
    }


def bootstrap(root: Path | None = None, force: bool = False) -> Path:
    root = ensure_data_dirs(root or Path(__file__).resolve().parents[1] / "data")
    application_path = root / "applications" / "APP-APEX-001.json"
    if force or not application_path.exists():
        write_json(default_application(), application_path)
    for certificate in DEMO_CERTIFICATES:
        certificate_path = root / "certificates" / f"{certificate.certificate_id}.json"
        if force or not certificate_path.exists():
            write_json(certificate, certificate_path)
        for mode in ("success", "failure", "mitigated"):
            trace_path = root / "traces" / f"{certificate.certificate_id}_{mode}.npz"
            if force or not trace_path.exists():
                np.savez(trace_path, **make_trace(certificate.certificate_id, mode))
    create_all_demo_videos(root)
    write_maniskill_suite(root, force=force)
    return root


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--data-root", type=Path, default=None)
    args = parser.parse_args()
    root = bootstrap(args.data_root, args.force)
    print(f"Bootstrapped TACO demo data under {root}")


if __name__ == "__main__":
    main()
