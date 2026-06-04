"""DreamAudit corpus reconciliation for carrier and VC diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication


def build_dreamaudit_corpus_reconciliation(
    application: InsuranceApplication,
    dreamaudit_intake: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return a claim-bounded reconciliation of live DreamAudit intake evidence."""

    if not dreamaudit_intake:
        return _not_scanned(application, "No DreamAudit intake summary is attached to this packet.")
    if not dreamaudit_intake.get("root_exists"):
        return _not_scanned(application, f"DreamAudit path not found: {dreamaudit_intake.get('root', 'unknown')}.")

    summary = dict(dreamaudit_intake.get("summary", {}) or {})
    readiness = dict(dreamaudit_intake.get("readiness", {}) or {})
    failure_counts = dict(dreamaudit_intake.get("failure_counts", {}) or {})
    schema_counts = dict(dreamaudit_intake.get("schema_counts", {}) or {})
    backend_counts = dict(dreamaudit_intake.get("backend_counts", {}) or {})
    ladder = list(dreamaudit_intake.get("evidence_depth_ladder", []) or [])
    selected_count = int(summary.get("certificates", 0) or 0)
    family_count = len(failure_counts or summary.get("failure_families", []))
    minimality_reports = int(readiness.get("minimality_reports", 0) or 0)
    replay_commands = int(readiness.get("replay_commands", 0) or 0)
    source_directories = int(readiness.get("source_directories", 0) or 0)
    unmapped = list(readiness.get("unmapped_failure_families", []) or [])
    gaps = list(readiness.get("gaps", []) or [])
    recommended_scan_limit = dreamaudit_intake.get("recommended_scan_limit")
    carrier_ready = readiness.get("status") == "carrier_review_ready" or any(
        row.get("status") == "carrier_review_ready" for row in ladder
    )
    gate_inputs = {
        "selected_count": selected_count,
        "family_count": family_count,
        "minimality_reports": minimality_reports,
        "replay_commands": replay_commands,
        "source_directories": source_directories,
        "unmapped": unmapped,
        "recommended_scan_limit": recommended_scan_limit,
        "carrier_ready": carrier_ready,
    }
    gates = _evidence_gates(gate_inputs)
    return {
        "reconciliation_id": f"DA-CORPUS-{application.application_id}",
        "status": _status(selected_count, family_count, gaps, carrier_ready),
        "boundary": (
            "This reconciliation proves that DreamAudit artifacts were normalized into TACO evidence contracts and "
            "that remaining carrier-review gaps are explicit; it is not proof of external acceptance, sim-to-real "
            "transfer, actuarial credibility, customer deployment, or permission to expose source paths publicly."
        ),
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "deployment_stage": application.deployment_stage,
        },
        "current_evidence": {
            "root": dreamaudit_intake.get("root"),
            "selected_certificates": selected_count,
            "failure_family_count": family_count,
            "readiness_score": int(readiness.get("readiness_score", 0) or 0),
            "readiness_status": readiness.get("status", "unknown"),
            "minimality_reports": minimality_reports,
            "replay_commands": replay_commands,
            "source_directories": source_directories,
            "recommended_scan_limit": recommended_scan_limit,
        },
        "evidence_counts": {
            "failure_counts": failure_counts,
            "schema_counts": schema_counts,
            "backend_counts": backend_counts,
        },
        "evidence_gates": gates,
        "carrier_gap_register": _gap_register(gaps),
        "claim_upgrade_paths": _claim_upgrade_paths(carrier_ready),
        "source_path_policy": _source_path_policy(),
        "do_not_claim": [
            "Do not say the DreamAudit corpus is carrier-accepted until written reviewer artifacts are attached.",
            "Do not treat replayable simulator failures as live loss-frequency evidence.",
            "Do not expose source paths outside private diligence without redaction and permission state.",
            "Do not claim minimality depth is sufficient when the minimality coverage gate fails.",
        ],
    }


def dreamaudit_gate_rows(reconciliation: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for corpus evidence gates."""

    return [
        {
            "Gate": item["gate"],
            "Status": item["status"].replace("_", " ").title(),
            "Evidence": item["evidence"],
            "Failure Action": item["failure_action"],
        }
        for item in reconciliation["evidence_gates"]
    ]


def dreamaudit_gap_rows(reconciliation: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for corpus gaps."""

    return [
        {
            "Gap": item["gap"],
            "Blocks": item["blocks"],
            "Next Action": item["next_action"],
        }
        for item in reconciliation["carrier_gap_register"]
    ]


def dreamaudit_claim_rows(reconciliation: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for DreamAudit claim-upgrade paths."""

    return [
        {
            "Claim": item["claim"],
            "Current Level": item["current_level"],
            "Upgrade Evidence": item["upgrade_evidence"],
            "Blocked Until": item["blocked_until"],
        }
        for item in reconciliation["claim_upgrade_paths"]
    ]


def _not_scanned(application: InsuranceApplication, reason: str) -> dict[str, Any]:
    return {
        "reconciliation_id": f"DA-CORPUS-{application.application_id}",
        "status": "not_scanned",
        "boundary": (
            "This reconciliation is empty until DreamAudit intake runs; it is not proof of live evidence, "
            "external acceptance, sim-to-real transfer, actuarial credibility, or customer deployment."
        ),
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "deployment_stage": application.deployment_stage,
        },
        "current_evidence": {
            "root": None,
            "selected_certificates": 0,
            "failure_family_count": 0,
            "readiness_score": 0,
            "readiness_status": "not_scanned",
            "minimality_reports": 0,
            "replay_commands": 0,
            "source_directories": 0,
            "recommended_scan_limit": None,
        },
        "evidence_counts": {"failure_counts": {}, "schema_counts": {}, "backend_counts": {}},
        "evidence_gates": [
            _gate("intake_scan_attached", "fail", reason, "Run DreamAudit Intake against a real artifact directory."),
        ],
        "carrier_gap_register": [_gap(reason, "live_dreamaudit_corpus", "Attach DreamAudit intake summary.")],
        "claim_upgrade_paths": _claim_upgrade_paths(False),
        "source_path_policy": _source_path_policy(),
        "do_not_claim": [
            "Do not say live DreamAudit evidence is attached until the scan summary is present.",
            "Do not infer carrier readiness from local fixture certificates.",
        ],
    }


def _status(selected_count: int, family_count: int, gaps: list[Any], carrier_ready: bool) -> str:
    if carrier_ready and selected_count >= 30 and family_count >= 3:
        return "carrier_review_ready_pending_external_acceptance"
    if selected_count >= 30 and family_count >= 3:
        return "live_corpus_imported_needs_evidence_upgrades" if gaps else "live_corpus_imported_no_selected_gaps"
    if selected_count:
        return "early_live_corpus_needs_broader_scan"
    return "not_scanned"


def _evidence_gates(inputs: dict[str, Any]) -> list[dict[str, str]]:
    selected_count = int(inputs["selected_count"])
    family_count = int(inputs["family_count"])
    minimality_reports = int(inputs["minimality_reports"])
    replay_commands = int(inputs["replay_commands"])
    source_directories = int(inputs["source_directories"])
    unmapped = list(inputs["unmapped"])
    recommended_scan_limit = inputs["recommended_scan_limit"]
    carrier_ready = bool(inputs["carrier_ready"])
    minimality_rate = minimality_reports / selected_count if selected_count else 0.0
    replay_rate = replay_commands / selected_count if selected_count else 0.0
    return [
        _gate(
            "source_path_presence",
            "pass" if selected_count > 0 and source_directories > 0 else "fail",
            f"{selected_count} selected certificates across {source_directories} source directories.",
            "Attach source paths or adapted certificate set before counting live DreamAudit evidence.",
        ),
        _gate(
            "failure_family_control_mapping",
            "pass" if family_count >= 3 and not unmapped else "fail",
            f"{family_count} mapped failure families; unmapped families: {', '.join(unmapped) if unmapped else 'none'}.",
            "Map each imported family to required controls before using it for underwriting terms.",
        ),
        _gate(
            "minimality_coverage",
            "pass" if selected_count and minimality_rate >= 0.5 else "fail",
            f"{minimality_reports}/{selected_count} selected certificates include completed minimality evidence.",
            "Run or attach minimality reports for at least half of selected certificates.",
        ),
        _gate(
            "replay_command_coverage",
            "pass" if selected_count and replay_rate >= 0.8 else "fail",
            f"{replay_commands}/{selected_count} selected certificates expose replay or inspection commands.",
            "Attach replay commands before presenting the corpus as reproducible.",
        ),
        _gate(
            "source_diversity",
            "pass" if source_directories >= 2 else "fail",
            f"{source_directories} DreamAudit artifact directories represented.",
            "Add another suite, seed, or perturbation run before carrier review.",
        ),
        _gate(
            "carrier_depth_ladder",
            "pass" if carrier_ready and recommended_scan_limit else "fail",
            f"Recommended carrier-ready depth: {recommended_scan_limit or 'not found'}.",
            "Expand scan depth or close listed gaps until the ladder has a carrier-ready rung.",
        ),
    ]


def _gap_register(gaps: list[Any]) -> list[dict[str, str]]:
    if not gaps:
        return [_gap("No selected DreamAudit readiness gaps reported.", "none", "Collect external reviewer acceptance artifacts.")]
    return [_gap(str(gap), _gap_blocks(str(gap)), _gap_action(str(gap))) for gap in gaps]


def _gap(gap: str, blocks: str, next_action: str) -> dict[str, str]:
    return {"gap": gap, "blocks": blocks, "next_action": next_action}


def _gap_blocks(gap: str) -> str:
    lowered = gap.lower()
    if "minimality" in lowered:
        return "minimal_failure_boundary_claim"
    if "family" in lowered:
        return "failure_family_breadth_claim"
    if "replay" in lowered:
        return "reproducible_evidence_claim"
    if "source" in lowered:
        return "source_diversity_claim"
    return "carrier_review_ready_claim"


def _gap_action(gap: str) -> str:
    lowered = gap.lower()
    if "minimality" in lowered:
        return "Run minimality sweeps or attach completed minimality reports for representative families."
    if "family" in lowered:
        return "Scan additional suites or perturbation types until at least three mapped families are represented."
    if "replay" in lowered:
        return "Attach replay commands or certificate-inspection commands for imported artifacts."
    if "source" in lowered:
        return "Add another DreamAudit artifact directory, suite, seed, or perturbation generator."
    return "Attach the missing DreamAudit artifact and reviewer evidence before upgrading the claim."


def _claim_upgrade_paths(carrier_ready: bool) -> list[dict[str, str]]:
    current_level = "live_adapter_evidence" if carrier_ready else "live_adapter_evidence_needs_gap_closure"
    return [
        {
            "claim": "replayable_failure_evidence",
            "current_level": current_level,
            "upgrade_evidence": "Carrier or robotics reviewer accepts packet-fingerprinted source paths and replay commands.",
            "blocked_until": "Written reviewer artifact with permission state is attached.",
        },
        {
            "claim": "minimal_failure_boundary",
            "current_level": current_level,
            "upgrade_evidence": "Representative minimality sweeps pass coverage gate and match source certificates.",
            "blocked_until": "Minimality coverage gate passes for selected corpus.",
        },
        {
            "claim": "underwriting_control_mapping",
            "current_level": current_level,
            "upgrade_evidence": "Reviewer agrees imported failure families map to required controls, exclusions, or missing evidence.",
            "blocked_until": "Unmapped family list is empty and reviewer memo is attached.",
        },
    ]


def _source_path_policy() -> list[dict[str, str]]:
    return [
        {
            "policy": "private_diligence_by_default",
            "rule": "DreamAudit source paths may be shown in private review packets but should not appear in public fundraising materials.",
        },
        {
            "policy": "redaction_before_export",
            "rule": "Customer, cluster, credential, and proprietary model paths require redaction or private-only marking.",
        },
        {
            "policy": "packet_hash_required",
            "rule": "Any external reviewer artifact must name the packet SHA-256 before it upgrades claims.",
        },
    ]


def _gate(gate: str, status: str, evidence: str, failure_action: str) -> dict[str, str]:
    return {
        "gate": gate,
        "status": status,
        "evidence": evidence,
        "failure_action": failure_action,
    }
