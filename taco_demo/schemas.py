"""Dataclasses and JSON helpers for TACO contracts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def dataclass_to_dict(obj: Any) -> Any:
    if is_dataclass(obj):
        return {k: dataclass_to_dict(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): dataclass_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [dataclass_to_dict(v) for v in obj]
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
class NormalizedDreamAuditCertificate:
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
    source_path: str | None
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
class InternalUnderwritingCertificate:
    certificate_id: str
    source_dreamaudit_certificate_id: str
    application: InsuranceApplication
    robot_policy: dict[str, Any]
    behavioral_evidence: dict[str, Any]
    internal_evidence: InternalRiskMetrics
    mitigation_evidence: dict[str, Any]
    insurance_decision: QuoteBreakdown
    created_at: str
    disclaimer: str


def default_application() -> InsuranceApplication:
    return InsuranceApplication(
        application_id="APP-APEX-001",
        company_name="Apex Robotics",
        robot_type="warehouse_manipulation_arm",
        policy_id="openvla_warehouse_v3",
        deployment_units=200,
        coverage_requested_usd=10_000_000,
        deployment_stage="pre_deployment",
        telemetry_available=False,
        created_at=now_iso(),
        metadata={"source": "demo_generated_placeholder_data"},
    )

