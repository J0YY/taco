"""Stable JSON dataclasses for the TACO MVP."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEMO_CREATED_AT = "2026-06-04T00:00:00+00:00"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def dataclass_to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {key: dataclass_to_dict(value) for key, value in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(key): dataclass_to_dict(value) for key, value in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [dataclass_to_dict(value) for value in obj]
    if hasattr(obj, "item"):
        return obj.item()
    return obj


def write_json(obj: Any, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dataclass_to_dict(obj), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass
class InsuranceApplication:
    application_id: str
    company_name: str
    robot_type: str
    policy_id: str
    deployment_units: int
    coverage_requested_usd: int
    deployment_stage: str
    telemetry_available: bool
    created_at: str
    metadata: dict[str, Any]


@dataclass
class FailureCertificate:
    certificate_id: str
    policy_id: str
    task_id: str
    failure_type: str
    severity: str
    perturbation: dict[str, Any]
    minimal_failure_cost: float
    failure_rate_neighborhood: float
    failure_timestep: int
    replay_command: str
    patch_recipe: dict[str, Any]
    source: str
    metadata: dict[str, Any]


@dataclass
class ReplayArtifacts:
    certificate_id: str
    success_video_path: str | None
    failure_video_path: str | None
    mitigated_video_path: str | None
    success_trace_path: str | None
    failure_trace_path: str | None
    mitigated_trace_path: str | None
    artifact_source: str
    metadata: dict[str, Any]


@dataclass
class InternalRiskMetrics:
    certificate_id: str
    concept_coverage_score: float
    feature_stability_score: float
    unsafe_dominance_score: float
    early_warning_margin_seconds: float
    causal_mitigability_score: float
    internal_risk_score: float
    dominant_risk_signature: str
    monitor_possible: bool
    metrics_source: str
    details: dict[str, Any]


@dataclass
class QuoteBreakdown:
    quote_id: str
    application_id: str
    status: str
    coverage_type: str
    coverage_limit_usd: int
    base_monthly_premium_usd: int
    deployment_multiplier: float
    behavioral_fragility_multiplier: float
    internal_risk_multiplier: float
    mitigation_discount_multiplier: float
    final_monthly_premium_usd: int
    required_controls: list[str]
    exclusions: list[str]
    quote_explanation: list[str]
    metadata: dict[str, Any]


@dataclass
class PolicyBinder:
    binder_id: str
    application: InsuranceApplication
    quote: QuoteBreakdown
    certificates: list[FailureCertificate]
    internal_metrics: list[InternalRiskMetrics]
    created_at: str
    disclaimer: str


def default_application() -> InsuranceApplication:
    return InsuranceApplication(
        application_id="APP-APEX-001",
        company_name="Apex Robotics",
        robot_type="warehouse manipulation arm",
        policy_id="openvla_warehouse_v3",
        deployment_units=200,
        coverage_requested_usd=10_000_000,
        deployment_stage="pre-deployment",
        telemetry_available=False,
        created_at=DEMO_CREATED_AT,
        metadata={"source": "demo_generated_placeholder_data"},
    )
