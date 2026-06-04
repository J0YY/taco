"""Runtime compliance and renewal pricing evidence for TACO."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .schemas import QuoteBreakdown


RUNTIME_EVENTS = [
    {
        "event_id": "RT-001",
        "timestamp": "2026-06-04T09:00:00+00:00",
        "deployment_phase": "staged_shadow",
        "control": "occlusion_risk_monitor_enabled",
        "status": "passed",
        "failure_family": "occlusion_induced_wrong_grasp",
        "evidence": "Monitor requested second view before target feature collapse reached action threshold.",
        "claim_prevented_usd": 18000,
    },
    {
        "event_id": "RT-002",
        "timestamp": "2026-06-04T09:08:00+00:00",
        "deployment_phase": "staged_shadow",
        "control": "language_override_sanitizer_enabled",
        "status": "passed",
        "failure_family": "language_override_instruction_conflict",
        "evidence": "Conflicting suffix blocked before action planner accepted instruction.",
        "claim_prevented_usd": 12500,
    },
    {
        "event_id": "RT-003",
        "timestamp": "2026-06-04T09:17:00+00:00",
        "deployment_phase": "staged_shadow",
        "control": "target_identity_confirmation_enabled",
        "status": "passed",
        "failure_family": "distractor_object_confusion",
        "evidence": "Target identity confirmation stopped action under high distractor similarity.",
        "claim_prevented_usd": 9200,
    },
    {
        "event_id": "RT-004",
        "timestamp": "2026-06-04T10:03:00+00:00",
        "deployment_phase": "pilot_shift",
        "control": "workspace_geofence",
        "status": "passed",
        "failure_family": "workspace_boundary_overreach",
        "evidence": "Geofence slowed action as joint-limit risk exceeded deployment threshold.",
        "claim_prevented_usd": 21600,
    },
    {
        "event_id": "RT-005",
        "timestamp": "2026-06-04T10:22:00+00:00",
        "deployment_phase": "pilot_shift",
        "control": "force_governor",
        "status": "warning",
        "failure_family": "contact_force_overshoot",
        "evidence": "Force governor detected overshoot but required one human reset.",
        "claim_prevented_usd": 7600,
    },
    {
        "event_id": "RT-006",
        "timestamp": "2026-06-04T11:41:00+00:00",
        "deployment_phase": "pilot_shift",
        "control": "pose_uncertainty_gate",
        "status": "failed",
        "failure_family": "camera_glare_pose_drift",
        "evidence": "Pose uncertainty gate was disabled for a lighting change; re-audit trigger fired.",
        "claim_prevented_usd": 0,
    },
    {
        "event_id": "RT-007",
        "timestamp": "2026-06-04T12:15:00+00:00",
        "deployment_phase": "pilot_shift",
        "control": "reaudit_required_after_model_update",
        "status": "passed",
        "failure_family": "model_update_regression",
        "evidence": "Model update blocked from covered deployment until replay certificates were regenerated.",
        "claim_prevented_usd": 24800,
    },
    {
        "event_id": "RT-008",
        "timestamp": "2026-06-04T13:02:00+00:00",
        "deployment_phase": "pilot_shift",
        "control": "deformable_recovery_monitor",
        "status": "warning",
        "failure_family": "rope_entanglement_memory_bias",
        "evidence": "Recovery monitor escalated after memorized trajectory dominated deformable state.",
        "claim_prevented_usd": 5400,
    },
]

INCIDENT_LOG = [
    {
        "incident_id": "CL-001",
        "severity": "near_miss",
        "failure_family": "contact_force_overshoot",
        "estimated_loss_usd": 0,
        "coverage_response": "No claim; retained as monitor-warning evidence for renewal.",
    },
    {
        "incident_id": "CL-002",
        "severity": "coverage_condition_breach",
        "failure_family": "camera_glare_pose_drift",
        "estimated_loss_usd": 3400,
        "coverage_response": "Excluded pending lighting validation because pose uncertainty gate was disabled.",
    },
    {
        "incident_id": "CL-003",
        "severity": "near_miss",
        "failure_family": "model_update_regression",
        "estimated_loss_usd": 0,
        "coverage_response": "No claim; re-audit trigger prevented covered deployment drift.",
    },
]


def renewal_summary(quote: QuoteBreakdown, runtime_events: list[dict[str, Any]] | None = None, incidents: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    events = runtime_events or RUNTIME_EVENTS
    claims = incidents or INCIDENT_LOG
    status_counts = Counter(str(event["status"]) for event in events)
    total_events = len(events)
    passed = status_counts.get("passed", 0)
    warnings = status_counts.get("warning", 0)
    failed = status_counts.get("failed", 0)
    compliance_score = round((passed + 0.5 * warnings) / total_events, 3) if total_events else 0.0
    prevented_loss = sum(int(event.get("claim_prevented_usd", 0)) for event in events)
    incurred_loss = sum(int(claim.get("estimated_loss_usd", 0)) for claim in claims)
    renewal_multiplier = 1.0
    if compliance_score >= 0.9 and incurred_loss == 0:
        renewal_multiplier = 0.92
    elif compliance_score >= 0.8:
        renewal_multiplier = 0.97
    elif compliance_score < 0.65:
        renewal_multiplier = 1.18
    elif failed:
        renewal_multiplier = 1.08
    renewal_premium = int(round((quote.final_monthly_premium_usd * renewal_multiplier) / 100.0) * 100)
    return {
        "runtime_events": total_events,
        "status_counts": dict(status_counts),
        "compliance_score": compliance_score,
        "prevented_loss_usd": prevented_loss,
        "incurred_loss_usd": incurred_loss,
        "renewal_multiplier": renewal_multiplier,
        "renewal_monthly_premium_usd": renewal_premium,
        "renewal_delta_usd": renewal_premium - quote.final_monthly_premium_usd,
        "re_audit_required": bool(failed),
    }
