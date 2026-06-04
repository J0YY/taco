"""Evidence provenance audit for VC and carrier diligence."""

from __future__ import annotations

from typing import Any

from .activation_evidence_contract import REAL_ACTIVATION_SOURCES
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


def build_evidence_provenance_audit(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return source classification and claim boundaries for packet evidence."""

    suite_cases = list(suite_manifest.get("cases", []))
    certificate_rows = [_certificate_row(cert) for cert in certificates]
    metric_rows = [_metric_row(metric) for metric in metrics]
    video_rows = [_video_row(case) for case in suite_cases]
    live_dreamaudit_sources = sum(1 for row in certificate_rows if row["evidence_class"] == "adapted_dreamaudit_certificate")
    recorded_activation_metrics = sum(1 for row in metric_rows if row["evidence_class"] == "recorded_activation_trace")
    generated_video_count = sum(1 for row in video_rows if row["evidence_class"] == "generated_maniskill_rma_replay")
    fixture_certificate_count = sum(1 for row in certificate_rows if row["evidence_class"] == "local_fixture_certificate")
    complete_primary_coverage = bool(certificates) and {metric.certificate_id for metric in metrics} >= {
        cert.certificate_id for cert in certificates
    }
    status = _status(
        certificate_count=len(certificates),
        complete_primary_coverage=complete_primary_coverage,
        recorded_activation_metrics=recorded_activation_metrics,
        suite_size=len(video_rows),
    )
    return {
        "audit_id": f"PROV-{application.application_id}",
        "status": status,
        "boundary": (
            "This audit classifies evidence provenance for diligence; it is not external validation, not a claim that "
            "generated videos are real-world losses, not proof of customer deployment, and not proof that activation "
            "features are causal explanations."
        ),
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "robot_type": application.robot_type,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
        },
        "current_counts": {
            "certificates": len(certificate_rows),
            "metrics": len(metric_rows),
            "suite_videos": len(video_rows),
            "adapted_dreamaudit_certificates": live_dreamaudit_sources,
            "local_fixture_certificates": fixture_certificate_count,
            "recorded_activation_metrics": recorded_activation_metrics,
            "generated_suite_videos": generated_video_count,
            "dreamaudit_intake_attached": bool(dreamaudit_intake and dreamaudit_intake.get("root_exists")),
            "complete_primary_metric_coverage": complete_primary_coverage,
        },
        "certificate_sources": certificate_rows,
        "metric_sources": metric_rows,
        "suite_video_sources": video_rows,
        "claim_upgrade_rules": _claim_upgrade_rules(),
        "reviewer_questions": _reviewer_questions(),
        "packet_use_policy": [
            "Use local fixture certificates to demonstrate schema and quote mechanics, not customer deployment evidence.",
            "Use adapted DreamAudit certificates only with preserved source paths, replay commands, and minimality metadata.",
            "Use recorded activation metrics only when NPZ traces, layer-to-signal maps, and shared calibration are attached.",
            "Use generated ManiSkill/RMA videos as replay illustrations until simulator source commands and reviewer reproduction notes are attached.",
        ],
    }


def provenance_certificate_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly certificate provenance rows."""

    return [
        {
            "Certificate": item["certificate_id"],
            "Evidence Class": item["evidence_class"],
            "Source": item["source"],
            "Can Claim": item["can_claim"],
            "Upgrade Gate": item["upgrade_gate"],
        }
        for item in audit["certificate_sources"]
    ]


def provenance_metric_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly metric provenance rows."""

    return [
        {
            "Certificate": item["certificate_id"],
            "Evidence Class": item["evidence_class"],
            "Metric Source": item["metrics_source"],
            "Recorded Signals": item["recorded_required_signal_count"],
            "Can Claim": item["can_claim"],
        }
        for item in audit["metric_sources"]
    ]


def provenance_video_rows(audit: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly video provenance rows."""

    return [
        {
            "Video": item["video_id"],
            "Evidence Class": item["evidence_class"],
            "Failure Family": item["failure_family"],
            "Source Path": item["source_path"],
            "Can Claim": item["can_claim"],
        }
        for item in audit["suite_video_sources"]
    ]


def provenance_upgrade_rows(audit: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly claim upgrade rows."""

    return [
        {
            "Claim": item["claim"],
            "Current Safe Level": item["current_safe_level"],
            "Upgrade Requires": item["upgrade_requires"],
            "Do Not Count": item["do_not_count"],
        }
        for item in audit["claim_upgrade_rules"]
    ]


def _certificate_row(cert: FailureCertificate) -> dict[str, Any]:
    source = str(cert.source)
    is_dreamaudit = source.startswith("dreamaudit:")
    evidence_class = "adapted_dreamaudit_certificate" if is_dreamaudit else "local_fixture_certificate"
    return {
        "certificate_id": cert.certificate_id,
        "failure_type": cert.failure_type,
        "severity": cert.severity,
        "source": source,
        "source_path": cert.metadata.get("original_path"),
        "replay_command": cert.replay_command,
        "minimal_failure_cost": cert.minimal_failure_cost,
        "failure_rate_neighborhood": cert.failure_rate_neighborhood,
        "evidence_class": evidence_class,
        "can_claim": (
            "DreamAudit-style failure certificate adapted into TACO schema with preserved source and replay fields."
            if is_dreamaudit
            else "Local fixture certificate exercises the quote and binder workflow offline."
        ),
        "cannot_claim": (
            "Cannot claim external reviewer acceptance, customer deployment, or carrier approval from certificate presence alone."
        ),
        "upgrade_gate": (
            "External reviewer reproduces the DreamAudit source path and accepts the certificate family."
            if is_dreamaudit
            else "Replace fixture with partner-specific DreamAudit certificate or simulator run artifact."
        ),
    }


def _metric_row(metric: InternalRiskMetrics) -> dict[str, Any]:
    recorded_signals = int(metric.details.get("recorded_required_signal_count", 0) or 0)
    evidence_class = (
        "recorded_activation_trace" if metric.metrics_source in REAL_ACTIVATION_SOURCES else "generated_or_demo_trace_metric"
    )
    return {
        "certificate_id": metric.certificate_id,
        "metrics_source": metric.metrics_source,
        "evidence_class": evidence_class,
        "recorded_required_signal_count": recorded_signals,
        "dominant_risk_signature": metric.dominant_risk_signature,
        "internal_risk_score": metric.internal_risk_score,
        "monitor_possible": metric.monitor_possible,
        "can_claim": (
            "Metric comes from activation-recorder-compatible trace output and can support an internals-based demo claim."
            if evidence_class == "recorded_activation_trace"
            else "Metric supports local scoring mechanics but should not be described as recorded model internals."
        ),
        "cannot_claim": "Cannot claim causal explanation, validated layer map, or actuarial rate credibility from this metric alone.",
        "upgrade_gate": "Attach success/failure/mitigated NPZ traces, layer map, shared calibration, and reviewer reproduction notes.",
    }


def _video_row(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "video_id": str(case.get("video_id", "unknown")),
        "failure_family": str(case.get("failure_family", "unknown")),
        "source_path": str(case.get("video_path", "")),
        "evidence_class": "generated_maniskill_rma_replay",
        "can_claim": "Replay illustration of a failure family and required control in the local evidence suite.",
        "cannot_claim": "Cannot claim observed real-world loss, production incident, or external simulator acceptance.",
        "upgrade_gate": "Attach simulator command, seed, environment metadata, and reviewer reproduction result for the replay.",
    }


def _status(
    *,
    certificate_count: int,
    complete_primary_coverage: bool,
    recorded_activation_metrics: int,
    suite_size: int,
) -> str:
    if certificate_count and complete_primary_coverage and recorded_activation_metrics >= certificate_count and suite_size >= 40:
        return "provenance_audit_ready_external_acceptance_pending"
    if certificate_count and complete_primary_coverage and suite_size >= 40:
        return "provenance_audit_ready_recorded_activations_pending"
    return "provenance_audit_needs_primary_evidence_coverage"


def _claim_upgrade_rules() -> list[dict[str, str]]:
    return [
        _rule(
            "internals_based_underwriting",
            "May say the demo includes activation-recorder-compatible internal metrics.",
            "Recorded success/failure/mitigated NPZ traces, layer-to-signal map, shared calibration, and reviewer reproduction note.",
            "Hand-authored metric JSON or screenshots of activations.",
        ),
        _rule(
            "dreamaudit_failure_evidence",
            "May say TACO adapts DreamAudit-style certificates and can scan a local DreamAudit corpus.",
            "Source DreamAudit paths, replay commands, minimality metadata, and external reviewer reproduction.",
            "Certificate count without source paths or replayability.",
        ),
        _rule(
            "video_suite_evidence",
            "May say the packet includes a generated 40-video failure-family suite.",
            "Simulator seed, command, environment metadata, and independent replay result.",
            "GIF presence alone or marketing cuts of failures.",
        ),
        _rule(
            "pricing_or_control_credit",
            "May say pricing changes conditionally under the local quote model.",
            "Actuarial review, control effectiveness replication, and carrier or broker written feedback.",
            "Local premium delta as filed pricing or guaranteed savings.",
        ),
    ]


def _rule(claim: str, current_safe_level: str, upgrade_requires: str, do_not_count: str) -> dict[str, str]:
    return {
        "claim": claim,
        "current_safe_level": current_safe_level,
        "upgrade_requires": upgrade_requires,
        "do_not_count": do_not_count,
    }


def _reviewer_questions() -> list[str]:
    return [
        "Can a reviewer trace each metric back to a certificate and trace source without relying on slides?",
        "Which evidence is fixture/generated versus adapted from DreamAudit or recorded from hooks?",
        "Which claims must stay at local-demo level until an external reviewer reproduces the artifact?",
        "What source path, command, seed, or calibration note is missing before upgrading the claim?",
    ]
