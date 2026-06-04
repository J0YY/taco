"""VC data-room checklist generation for TACO diligence."""

from __future__ import annotations

from typing import Any

from .insurance_scenarios import INSURANCE_SCENARIOS
from .investor_case import RESEARCH_FOUNDATIONS
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown, dataclass_to_dict


def build_data_room_checklist(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return diligence packet items investors and carriers will ask to inspect."""

    suite_cases = list(suite_manifest.get("cases", []))
    suite_size = int(suite_manifest.get("suite_size", len(suite_cases)) or 0)
    suite_families = {str(case.get("failure_family", "unknown")) for case in suite_cases}
    metric_ids = {metric.certificate_id for metric in metrics}
    covered_metrics = sum(1 for cert in certificates if cert.certificate_id in metric_ids)
    metric_sources = sorted({metric.metrics_source for metric in metrics})
    metric_source_text = ", ".join(metric_sources) if metric_sources else "none"
    dreamaudit = _dreamaudit_status(dreamaudit_intake)
    items = [
        _item(
            "Application And Coverage File",
            "ready" if application.application_id and quote.quote_id else "needs_work",
            f"{application.application_id}; ${application.coverage_requested_usd:,.0f} requested coverage; quote {quote.quote_id}.",
            "Keep the application JSON, quote breakdown, and coverage request in the diligence packet.",
        ),
        _item(
            "Replay Failure Certificates",
            "ready" if len(certificates) >= 3 else "needs_work",
            f"{len(certificates)} primary replayable failure certificates attached.",
            "Attach at least three primary certificates with replay commands and required controls.",
        ),
        _item(
            "Internal Risk Trace Coverage",
            "ready" if certificates and covered_metrics == len(certificates) else "needs_work",
            f"{covered_metrics}/{len(certificates)} certificates have internal risk metrics; sources: {metric_source_text}.",
            "Attach activation/trace NPZ evidence for every primary certificate.",
        ),
        _item(
            "ManiSkill/RMA Video Suite",
            "ready" if suite_size >= 40 and len(suite_families) >= 8 else "needs_work",
            f"{suite_size} videos across {len(suite_families)} failure families.",
            "Keep the 40-video replay suite and manifest in the data room.",
        ),
        _item(
            "Insurance Workflow And Pricing Examples",
            "ready" if len(INSURANCE_SCENARIOS) >= 10 else "needs_work",
            f"{len(INSURANCE_SCENARIOS)} priced end-to-end insurance workflows.",
            "Include 10+ workflows with controls, exclusions, and premium deltas.",
        ),
        _item(
            "Live DreamAudit Corpus",
            dreamaudit["status"],
            dreamaudit["evidence"],
            dreamaudit["next_action"],
        ),
        _item(
            "Research And Methodology Sources",
            "ready" if len(RESEARCH_FOUNDATIONS) >= 4 else "needs_work",
            f"{len(RESEARCH_FOUNDATIONS)} linked research anchors.",
            "Attach primary-source references for simulation, perturbation, interpretability, and monitoring claims.",
        ),
        _item(
            "Design-Partner References",
            "external_pending",
            "Signed broker/carrier/OEM design-partner reviews are not represented in local demo artifacts.",
            "Secure 2-3 design-partner reviews and add written feedback or LOIs to the data room.",
        ),
    ]
    ready_items = sum(1 for item in items if item["status"] == "ready")
    internal_items = [item for item in items if item["status"] != "external_pending"]
    internal_ready = sum(1 for item in internal_items if item["status"] == "ready")
    return {
        "ready_items": ready_items,
        "total_items": len(items),
        "internal_ready_items": internal_ready,
        "internal_total_items": len(internal_items),
        "internal_packet_score": round(100 * internal_ready / len(internal_items)) if internal_items else 0,
        "external_pending_items": sum(1 for item in items if item["status"] == "external_pending"),
        "items": items,
    }


def data_room_rows(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    """Return table rows for the Streamlit UI and Markdown memo."""

    return [
        {
            "Artifact": item["artifact"],
            "Status": item["status"].replace("_", " ").title(),
            "Evidence": item["evidence"],
            "Next Action": item["next_action"],
        }
        for item in checklist["items"]
    ]


def build_data_room_manifest(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a machine-readable diligence manifest for export."""

    checklist = build_data_room_checklist(application, certificates, metrics, quote, suite_manifest, dreamaudit_intake)
    suite_cases = list(suite_manifest.get("cases", []))
    dreamaudit_summary = _dreamaudit_manifest_summary(dreamaudit_intake)
    return {
        "manifest_id": f"DR-{application.application_id}",
        "purpose": "VC/carrier diligence packet for learned-policy liability underwriting evidence.",
        "application": dataclass_to_dict(application),
        "quote": dataclass_to_dict(quote),
        "checklist": checklist,
        "primary_certificates": [dataclass_to_dict(cert) for cert in certificates],
        "internal_metrics": [dataclass_to_dict(metric) for metric in metrics],
        "suite_summary": {
            "suite_name": suite_manifest.get("suite_name", "unknown"),
            "suite_size": int(suite_manifest.get("suite_size", len(suite_cases)) or 0),
            "failure_families": sorted({str(case.get("failure_family", "unknown")) for case in suite_cases}),
            "video_paths": [str(case.get("video_path", "")) for case in suite_cases if case.get("video_path")],
        },
        "dreamaudit": dreamaudit_summary,
    }


def _dreamaudit_status(dreamaudit_intake: dict[str, Any] | None) -> dict[str, str]:
    if not dreamaudit_intake:
        return {
            "status": "needs_live_scan",
            "evidence": "No DreamAudit intake scan is attached.",
            "next_action": "Run DreamAudit Intake and attach the carrier-readiness ladder.",
        }
    if not dreamaudit_intake.get("root_exists"):
        return {
            "status": "needs_live_scan",
            "evidence": f"DreamAudit path not found: {dreamaudit_intake.get('root', 'unknown')}.",
            "next_action": "Point DreamAudit Intake at an existing artifact directory.",
        }
    readiness = dreamaudit_intake.get("readiness", {})
    ladder = list(dreamaudit_intake.get("evidence_depth_ladder", []))
    recommended = dreamaudit_intake.get("recommended_scan_limit")
    carrier_ready = readiness.get("status") == "carrier_review_ready" or any(
        row.get("status") == "carrier_review_ready" for row in ladder
    )
    selected_count = int(dreamaudit_intake.get("summary", {}).get("certificates", 0) or 0)
    selected_score = int(readiness.get("readiness_score", 0) or 0)
    status = "ready" if carrier_ready else "needs_live_scan"
    evidence = (
        f"{selected_count} selected DreamAudit certificates; selected readiness {selected_score}/100; "
        f"recommended carrier-ready depth {recommended or 'not found'}."
    )
    next_action = (
        "Attach the carrier-ready ladder and representative source paths to the data room."
        if carrier_ready
        else "Expand the DreamAudit scan until a carrier-ready ladder depth is available."
    )
    return {"status": status, "evidence": evidence, "next_action": next_action}


def _dreamaudit_manifest_summary(dreamaudit_intake: dict[str, Any] | None) -> dict[str, Any]:
    if not dreamaudit_intake:
        return {"attached": False, "status": "not_scanned"}
    readiness = dreamaudit_intake.get("readiness", {})
    return {
        "attached": True,
        "root": dreamaudit_intake.get("root"),
        "root_exists": bool(dreamaudit_intake.get("root_exists")),
        "selected_certificates": int(dreamaudit_intake.get("summary", {}).get("certificates", 0) or 0),
        "readiness_score": int(readiness.get("readiness_score", 0) or 0),
        "readiness_status": readiness.get("status", "unknown"),
        "recommended_scan_limit": dreamaudit_intake.get("recommended_scan_limit"),
        "evidence_depth_ladder": dreamaudit_intake.get("evidence_depth_ladder", []),
        "gaps": readiness.get("gaps", []),
    }


def _item(artifact: str, status: str, evidence: str, next_action: str) -> dict[str, str]:
    return {
        "artifact": artifact,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }
