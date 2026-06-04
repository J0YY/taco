"""Internal trace metrics for TACO underwriting evidence."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .schemas import FailureCertificate, InternalRiskMetrics, clamp01


REQUIRED_SIGNALS = [
    "target_feature",
    "general_grasp_feature",
    "transport_feature",
    "memorized_trajectory_feature",
    "unsafe_trajectory_dominance",
    "action_risk",
]


def load_trace(path: Path) -> dict[str, np.ndarray]:
    with np.load(path) as data:
        return {key: np.asarray(data[key]) for key in data.files}


def _pre_window(trace: dict[str, np.ndarray], key: str, failure_timestep: int, size: int = 25) -> np.ndarray:
    arr = np.asarray(trace.get(key, np.zeros(failure_timestep + 1)), dtype=float)
    end = min(len(arr), max(1, failure_timestep))
    start = max(0, end - size)
    return arr[start:end]


def compute_concept_coverage(trace: dict[str, np.ndarray]) -> float:
    available = 0
    for signal in REQUIRED_SIGNALS:
        arr = np.asarray(trace.get(signal, []), dtype=float)
        if arr.size and np.nanstd(arr) > 0.01:
            available += 1
    return clamp01(available / len(REQUIRED_SIGNALS))


def compute_feature_stability(success_trace: dict[str, np.ndarray], failure_trace: dict[str, np.ndarray], failure_timestep: int) -> float:
    success_mean = float(np.mean(_pre_window(success_trace, "target_feature", failure_timestep)))
    failure_mean = float(np.mean(_pre_window(failure_trace, "target_feature", failure_timestep)))
    collapse = max(0.0, success_mean - failure_mean)
    return clamp01(1.0 - collapse)


def compute_unsafe_dominance(failure_trace: dict[str, np.ndarray], failure_timestep: int) -> float:
    unsafe = float(np.mean(_pre_window(failure_trace, "unsafe_trajectory_dominance", failure_timestep)))
    action = float(np.mean(_pre_window(failure_trace, "action_risk", failure_timestep)))
    memorized = float(np.mean(_pre_window(failure_trace, "memorized_trajectory_feature", failure_timestep)))
    return clamp01(max(unsafe, action, memorized))


def compute_early_warning_margin(failure_trace: dict[str, np.ndarray], failure_timestep: int, threshold: float = 0.65) -> float:
    risk = np.asarray(failure_trace.get("internal_risk_score", []), dtype=float)
    time_s = np.asarray(failure_trace.get("time_s", np.arange(len(risk)) / 20.0), dtype=float)
    end = min(failure_timestep, len(risk) - 1, len(time_s) - 1)
    if end <= 0:
        return 0.0
    crossings = np.where(risk[:end] > threshold)[0]
    if len(crossings) == 0:
        return 0.0
    return max(0.0, float(time_s[end] - time_s[int(crossings[0])]))


def compute_causal_mitigability(
    failure_trace: dict[str, np.ndarray],
    mitigated_trace: dict[str, np.ndarray],
    failure_timestep: int,
) -> float:
    start = max(0, failure_timestep - 15)
    stop = failure_timestep + 25
    failure_action = np.asarray(failure_trace.get("action_risk", []), dtype=float)[start:stop]
    mitigated_action = np.asarray(mitigated_trace.get("action_risk", []), dtype=float)[start:stop]
    if len(failure_action) == 0 or len(mitigated_action) == 0:
        return 0.0
    n = min(len(failure_action), len(mitigated_action))
    original = float(np.mean(failure_action[:n]))
    mitigated = float(np.mean(mitigated_action[:n]))
    return clamp01((original - mitigated) / max(original, 1e-6))


def compute_internal_risk_score(
    concept_coverage_score: float,
    feature_stability_score: float,
    unsafe_dominance_score: float,
    causal_mitigability_score: float,
    early_warning_margin_seconds: float,
) -> float:
    early_warning_penalty = 0.0 if early_warning_margin_seconds >= 0.5 else 1.0 - early_warning_margin_seconds / 0.5
    return clamp01(
        0.20 * (1.0 - concept_coverage_score)
        + 0.25 * (1.0 - feature_stability_score)
        + 0.25 * unsafe_dominance_score
        + 0.20 * (1.0 - causal_mitigability_score)
        + 0.10 * early_warning_penalty
    )


def dominant_risk_signature(failure_type: str) -> str:
    if failure_type == "occlusion_induced_wrong_grasp":
        return "target_feature_collapse_under_occlusion"
    if failure_type == "language_override_instruction_conflict":
        return "language_override_dominates_action_selection"
    if failure_type == "distractor_object_confusion":
        return "semantic_distractor_dominance"
    return "internal_failure_precursor_detected"


def _metrics_source(trace: dict[str, np.ndarray]) -> str:
    raw = trace.get("trace_source")
    if raw is None:
        return "deterministic_generated_npz_trace"
    value = np.asarray(raw).reshape(-1)
    if value.size == 0:
        return "deterministic_generated_npz_trace"
    return str(value[0])


def compute_internal_metrics(
    certificate: FailureCertificate,
    success_trace: dict[str, np.ndarray],
    failure_trace: dict[str, np.ndarray],
    mitigated_trace: dict[str, np.ndarray],
) -> InternalRiskMetrics:
    coverage = compute_concept_coverage(failure_trace)
    stability = compute_feature_stability(success_trace, failure_trace, certificate.failure_timestep)
    unsafe = compute_unsafe_dominance(failure_trace, certificate.failure_timestep)
    margin = compute_early_warning_margin(failure_trace, certificate.failure_timestep)
    mitigability = compute_causal_mitigability(failure_trace, mitigated_trace, certificate.failure_timestep)
    score = compute_internal_risk_score(coverage, stability, unsafe, mitigability, margin)
    return InternalRiskMetrics(
        certificate_id=certificate.certificate_id,
        concept_coverage_score=coverage,
        feature_stability_score=stability,
        unsafe_dominance_score=unsafe,
        early_warning_margin_seconds=round(margin, 3),
        causal_mitigability_score=mitigability,
        internal_risk_score=score,
        dominant_risk_signature=dominant_risk_signature(certificate.failure_type),
        monitor_possible=margin >= 0.25,
        metrics_source=_metrics_source(failure_trace),
        details={
            "failure_timestep": certificate.failure_timestep,
            "required_signals": REQUIRED_SIGNALS,
            "recorded_required_signal_count": int(np.asarray(failure_trace.get("recorded_required_signal_count", [0])).reshape(-1)[0]),
        },
    )
