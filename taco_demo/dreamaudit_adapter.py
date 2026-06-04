"""DreamAudit certificate adapter for TACO failure evidence.

The adapter intentionally does not import DreamAudit. It accepts DreamAudit-style
JSON dictionaries from disk and normalizes them into TACO's stable
FailureCertificate schema.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from .schemas import FailureCertificate, clamp01


JsonDict = dict[str, Any]


def _as_dict(value: Any) -> JsonDict:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, dict):
        return value
    if hasattr(value, "to_dict"):
        converted = value.to_dict()
        if isinstance(converted, dict):
            return converted
    raise TypeError(f"Expected a dictionary-like DreamAudit certificate, got {type(value)!r}")


def _get(payload: JsonDict, *path: str, default: Any = None) -> Any:
    node: Any = payload
    for key in path:
        if not isinstance(node, dict) or key not in node:
            return default
        node = node[key]
    return node


def _first_present(*values: Any, default: Any = None) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _normalized_failure_type(raw_failure_type: str, perturbation: JsonDict, task: JsonDict) -> str:
    raw = raw_failure_type.lower()
    if "wrong_object" in raw or "distractor" in raw:
        return "distractor_object_confusion"
    if any(token in raw for token in ["collision", "contact", "force", "overshoot"]):
        return "contact_force_overshoot"
    if any(token in raw for token in ["grasp_miss", "grasp_mismatch"]):
        return "grasp_miss"
    if "calibration" in raw:
        return "calibration_sensitivity"
    perturbation_text = " ".join(
        str(value).lower()
        for value in [
            perturbation.get("type"),
            perturbation.get("perturbation_name"),
            perturbation.get("semantic_rationale"),
            task.get("instruction_original"),
            task.get("instruction_tested"),
        ]
        if value is not None
    )
    signal = f"{raw} {perturbation_text}"
    if any(token in signal for token in ["occlusion", "_occ", " occ", "masked", "blocked"]):
        return "occlusion_induced_wrong_grasp"
    if any(token in signal for token in ["language", "instruction", "prompt"]):
        return "language_override_instruction_conflict"
    if any(token in signal for token in ["distractor", "semantic", "confusion", "wrong_object"]):
        return "distractor_object_confusion"
    if any(token in signal for token in ["collision", "contact", "force", "overshoot"]):
        return "contact_force_overshoot"
    if any(token in signal for token in ["blur", "bright", "dim", "shift", "vision", "observation"]):
        return "vision_perturbation_counterfactual_failure"
    if raw:
        return raw.replace(" ", "_")
    return "counterfactual_policy_failure"


def _policy_id(payload: JsonDict) -> str:
    return str(_first_present(_get(payload, "policy", "name"), _get(payload, "policy", "adapter"), default="unknown_policy"))


def _task_id(payload: JsonDict) -> str:
    task = _get(payload, "task", default={}) or {}
    task_name = _first_present(task.get("task_name"), task.get("task_id"), task.get("instruction_original"), default="unknown_task")
    suite = task.get("suite")
    task_idx = task.get("task_idx")
    episode_idx = task.get("episode_idx")
    benchmark = task.get("benchmark")
    parts = []
    if benchmark:
        parts.append(str(benchmark))
    if suite:
        parts.append(str(suite))
    if task_idx is not None:
        parts.append(f"task_{task_idx}")
    if episode_idx is not None:
        parts.append(f"episode_{episode_idx}")
    parts.append(str(task_name))
    return ":".join(parts)


def _failure_mode(payload: JsonDict) -> str:
    return str(
        _first_present(
            _get(payload, "simulator_validation", "failure_mode"),
            _get(payload, "perturbed_validation", "failure_mode"),
            _get(payload, "world_model_discovery", "predicted_failure"),
            default="counterfactual_policy_failure",
        )
    )


def _minimal_cost(payload: JsonDict) -> float:
    perturbation = _get(payload, "perturbation", default={}) or {}
    candidates = [
        _get(payload, "minimality", "smallest_failing_cost_found"),
        perturbation.get("perturbation_cost"),
        perturbation.get("mean_image_l1"),
        perturbation.get("mean_image_mse"),
        _get(payload, "minimality", "failure_cost"),
    ]
    for candidate in candidates:
        if candidate is not None:
            return max(0.0, _float(candidate))
    params = perturbation.get("perturbation_params")
    if isinstance(params, dict):
        for key in ("fraction", "magnitude", "severity", "shift_px", "brightness_delta"):
            if key in params:
                return max(0.0, _float(params[key]))
    return 0.5


def _failure_rate(payload: JsonDict) -> float:
    explicit = _get(payload, "minimality", "failure_rate_at_0_75_cost")
    if explicit is not None:
        return clamp01(_float(explicit, default=0.0))
    perturbed_success = _get(payload, "perturbed_validation", "success")
    simulator_success = _get(payload, "simulator_validation", "simulator_success")
    native_success = _get(payload, "native_validation", "success")
    if perturbed_success is False and native_success is True:
        return 1.0
    if simulator_success is False:
        return 0.75
    return 0.5


def _severity(minimal_cost: float, failure_rate: float, failure_type: str) -> str:
    if failure_rate >= 0.75 or minimal_cost <= 0.08:
        return "high"
    if failure_rate >= 0.45 or failure_type in {"contact_force_overshoot", "occlusion_induced_wrong_grasp"}:
        return "medium"
    return "low"


def _failure_timestep(payload: JsonDict) -> int:
    return _int(
        _first_present(
            _get(payload, "simulator_validation", "failure_frame"),
            _get(payload, "perturbed_validation", "steps"),
            _get(payload, "native_validation", "steps"),
            default=0,
        )
    )


def _replay_command(payload: JsonDict, source_path: Path | None) -> str:
    replay_uri = _get(payload, "simulator_validation", "replay_video_uri")
    if replay_uri:
        return f"open {replay_uri}"
    if source_path is not None:
        return f"python -m json.tool {source_path}"
    certificate_id = payload.get("certificate_id", "<certificate_id>")
    return f"dreamaudit replay --certificate {certificate_id}"


def _patch_recipe(payload: JsonDict, failure_type: str) -> JsonDict:
    recipe = dict(_get(payload, "patch_recipe", default={}) or {})
    controls_by_failure = {
        "occlusion_induced_wrong_grasp": "occlusion-risk monitor with target identity confirmation",
        "language_override_instruction_conflict": "language override sanitizer with instruction provenance logging",
        "distractor_object_confusion": "target identity confirmation before irreversible grasp",
        "contact_force_overshoot": "force-envelope monitor with automatic slowdown",
        "vision_perturbation_counterfactual_failure": "vision-shift monitor with re-audit trigger",
    }
    recipe.setdefault("taco_required_control", controls_by_failure.get(failure_type, "known-failure runtime monitor"))
    recipe.setdefault("underwriting_use", "Required control and exclusion text for learned-policy liability quote.")
    return recipe


def load_dreamaudit_certificate(path: Path | str) -> JsonDict:
    """Load one DreamAudit certificate JSON from disk."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def adapt_dreamaudit_certificate(path_or_payload: Path | str | JsonDict | Any, source_path: Path | None = None) -> FailureCertificate:
    """Normalize one DreamAudit certificate into a TACO FailureCertificate."""

    if isinstance(path_or_payload, (str, Path)) and Path(path_or_payload).exists():
        source_path = Path(path_or_payload)
        payload = load_dreamaudit_certificate(source_path)
    else:
        payload = _as_dict(path_or_payload)
    perturbation = dict(_get(payload, "perturbation", default={}) or {})
    task = dict(_get(payload, "task", default={}) or {})
    raw_failure_type = _failure_mode(payload)
    failure_type = _normalized_failure_type(raw_failure_type, perturbation, task)
    minimal_cost = _minimal_cost(payload)
    rate = _failure_rate(payload)
    source = f"dreamaudit:{source_path}" if source_path is not None else "dreamaudit_certificate"
    certificate_id = str(_first_present(payload.get("certificate_id"), source_path.stem if source_path else None, default="dreamaudit-certificate"))
    return FailureCertificate(
        certificate_id=certificate_id,
        policy_id=_policy_id(payload),
        task_id=_task_id(payload),
        failure_type=failure_type,
        severity=_severity(minimal_cost, rate, failure_type),
        perturbation={
            "type": perturbation.get("type", "unknown"),
            "name": _first_present(perturbation.get("perturbation_name"), perturbation.get("semantic_rationale"), default="unknown"),
            "cost": minimal_cost,
            "raw": perturbation,
        },
        minimal_failure_cost=round(minimal_cost, 6),
        failure_rate_neighborhood=round(rate, 6),
        failure_timestep=_failure_timestep(payload),
        replay_command=_replay_command(payload, source_path),
        patch_recipe=_patch_recipe(payload, failure_type),
        source=source,
        metadata={
            "original_path": str(source_path) if source_path is not None else None,
            "backend": payload.get("backend"),
            "native_validation": _get(payload, "native_validation", default={}),
            "perturbed_validation": _get(payload, "perturbed_validation", default={}),
            "simulator_validation": _get(payload, "simulator_validation", default={}),
            "minimality": _get(payload, "minimality", default={}),
            "world_model_discovery": _get(payload, "world_model_discovery", default={}),
            "original_failure_type": raw_failure_type,
            "dreamaudit_schema": "rich" if "simulator_validation" in payload else "compact",
        },
    )


def adapt_dreamaudit_certificates(root: Path | str, limit: int | None = None) -> list[FailureCertificate]:
    """Adapt all certificate JSON files under a DreamAudit artifact directory."""

    if limit is not None and limit <= 0:
        return []
    root_path = Path(root)
    paths = sorted(path for path in root_path.rglob("*.json") if path.is_file())
    certs: list[FailureCertificate] = []
    for path in paths:
        try:
            payload = load_dreamaudit_certificate(path)
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict) or "certificate_id" not in payload:
            continue
        if not any(key in payload for key in ("perturbed_validation", "simulator_validation", "world_model_discovery")):
            continue
        certs.append(adapt_dreamaudit_certificate(payload, source_path=path))
        if limit is not None and len(certs) >= limit:
            break
    return certs


def summarize_adapted_certificates(certificates: list[FailureCertificate]) -> JsonDict:
    """Return a compact underwriting summary for adapted DreamAudit evidence."""

    failure_families = sorted({cert.failure_type for cert in certificates})
    high_severity = sum(1 for cert in certificates if cert.severity == "high")
    mean_failure_rate = sum(cert.failure_rate_neighborhood for cert in certificates) / len(certificates) if certificates else 0.0
    return {
        "certificates": len(certificates),
        "failure_families": failure_families,
        "high_severity": high_severity,
        "mean_failure_rate_neighborhood": round(mean_failure_rate, 3),
        "sources": sorted({cert.source for cert in certificates})[:5],
    }
