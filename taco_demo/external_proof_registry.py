"""External proof registry for reviewer artifacts and permissions."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_external_proof_registry(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    external_validation_kit: dict[str, Any],
    investor_proof_pipeline: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
    seed_round_close_plan: dict[str, Any],
) -> dict[str, Any]:
    """Return a registry for external proof artifacts before they are collected."""

    packet_context = external_validation_kit.get("packet_context", {})
    manifest_id = str(packet_context.get("manifest_id", f"DR-{application.application_id}"))
    proof_slots = _proof_slots(
        application,
        quote,
        external_validation_kit,
        investor_proof_pipeline,
        claim_validation_ledger,
        seed_round_close_plan,
    )
    countable_slots = [slot for slot in proof_slots if slot["countable_now"]]
    permissioned_slots = [slot for slot in proof_slots if slot["permission_to_quote"] in {"anonymous", "named"}]
    public_slots = [slot for slot in proof_slots if slot["redaction_status"] == "public_ready"]
    return {
        "registry_id": f"EPROOF-{application.application_id}",
        "status": "registry_ready_no_external_artifacts_collected",
        "boundary": (
            "This registry defines external proof slots, permission metadata, redaction gates, and claim-upgrade rules; "
            "it is not evidence that reviewer memos, pilots, LOIs, paid scopes, investor interest, customer demand, "
            "carrier capacity, or permission-to-quote artifacts have been collected."
        ),
        "packet_context": {
            "manifest_id": manifest_id,
            "packet_sha256_required": True,
            "packet_format_expected": "taco_data_room_zip_v21",
            "minimum_packet_files_reviewed": int(packet_context.get("minimum_external_packet_artifact_count", 0) or 0),
        },
        "current_counts": {
            "proof_slots": len(proof_slots),
            "countable_external_artifacts": len(countable_slots),
            "permissioned_quote_artifacts": len(permissioned_slots),
            "public_ready_artifacts": len(public_slots),
            "claims_with_external_upgrade_path": len(_claim_ids(claim_validation_ledger)),
        },
        "proof_slots": proof_slots,
        "permission_policy": _permission_policy(),
        "redaction_gates": _redaction_gates(),
        "claim_upgrade_rules": _claim_upgrade_rules(claim_validation_ledger),
        "investor_update_rules": _investor_update_rules(),
        "next_collection_actions": [
            "Collect one completed reviewer feedback form with packet SHA-256 and accepted/rejected claim IDs.",
            "Attach permission-to-quote state before any reviewer sentence enters an investor update.",
            "Attach redaction status before any source path, activation trace, memo, LOI, or pilot scope enters the exported data room.",
            "Promote only countable artifacts that satisfy packet fingerprint, author role, artifact body, permission, and redaction gates.",
        ],
    }


def external_proof_slot_rows(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly rows for proof slots."""

    return [
        {
            "Slot": item["slot_id"],
            "Track": item["reviewer_track"],
            "Status": item["evidence_status"],
            "Countable Now": item["countable_now"],
            "Permission": item["permission_to_quote"],
            "Redaction": item["redaction_status"],
            "Required Artifact": item["required_artifact"],
        }
        for item in registry["proof_slots"]
    ]


def external_proof_rule_rows(registry: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for claim-upgrade rules."""

    return [
        {
            "Claim": item["claim_id"],
            "Current Level": item["current_evidence_level"],
            "External Proof Required": item["external_proof_required"],
            "Do Not Upgrade From": item["do_not_upgrade_from"],
        }
        for item in registry["claim_upgrade_rules"]
    ]


def external_proof_redaction_rows(registry: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for redaction gates."""

    return [
        {
            "Gate": item["gate"],
            "Pass Condition": item["pass_condition"],
            "Blocked Until": item["blocked_until"],
        }
        for item in registry["redaction_gates"]
    ]


def _proof_slots(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    external_validation_kit: dict[str, Any],
    investor_proof_pipeline: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
    seed_round_close_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    reviewer_tracks = list(external_validation_kit.get("reviewer_tracks", []))
    first_track = str((reviewer_tracks[0] if reviewer_tracks else {}).get("track_id", "external_reviewer"))
    proof_gates = [str(gate.get("gate", "")) for gate in investor_proof_pipeline.get("proof_gates", [])]
    close_gates = [str(gate.get("gate", "")) for gate in seed_round_close_plan.get("closing_gates", [])]
    company_context = f"{application.company_name}; quote {quote.quote_id}; monthly premium ${quote.final_monthly_premium_usd:,.0f}"
    return [
        _slot(
            "reviewer_feedback_memo_primary",
            first_track,
            "not_collected",
            "Written reviewer memo with packet SHA-256, role, org type, accepted/rejected claims, and missing-evidence list.",
            ["external_validation_status", "transferable_data_room", "predeployment_underwriting_gap"],
            "packet_reproduced_by_external_reviewer" if "packet_reproduced_by_external_reviewer" in proof_gates else "external_workflow_pull",
            "private_only",
            "not_redacted",
            company_context,
        ),
        _slot(
            "reviewer_feedback_memo_second_track",
            "broker_mga_or_carrier_reviewer",
            "not_collected",
            "Second written reviewer artifact from a different buyer category with claim feedback and workflow fit.",
            ["external_validation_status", "control_linked_pricing_sensitivity"],
            "claim_ledger_external_feedback" if "claim_ledger_external_feedback" in proof_gates else "external_workflow_pull",
            "private_only",
            "not_redacted",
            company_context,
        ),
        _slot(
            "live_dreamaudit_source_path",
            "robotics_technical_reviewer",
            "not_collected",
            "Partner-specific DreamAudit certificate source path or adapted certificate set tied to the reviewed policy family.",
            ["replayable_failure_evidence", "live_dreamaudit_corpus"],
            "live_internals_or_dreamaudit_artifact" if "live_internals_or_dreamaudit_artifact" in proof_gates else "internals_based_path",
            "none",
            "source_path_private",
            company_context,
        ),
        _slot(
            "recorded_activation_trace_bundle",
            "robotics_technical_reviewer",
            "not_collected",
            "Recorded activation NPZ bundle with layer-to-signal map, calibration note, and metric output for matching certificates.",
            ["internals_based_risk_signal"],
            "internals_based_path" if "internals_based_path" in close_gates else "live_internals_or_dreamaudit_artifact",
            "none",
            "source_path_private",
            company_context,
        ),
        _slot(
            "commercial_conversion_document",
            "buyer_or_broker_decision_owner",
            "not_collected",
            "Paid evidence sprint, signed pilot scope, LOI, data-access agreement, broker memo, or carrier review scope.",
            ["buyer_roi_economic_case", "seed_scale_story"],
            "commercial_conversion",
            "none",
            "not_redacted",
            company_context,
        ),
        _slot(
            "permission_to_quote_register",
            "founder_and_counsel",
            "not_collected",
            "Permission register mapping each reviewer artifact to none, anonymous, named, or private-only quote rights.",
            _claim_ids(claim_validation_ledger),
            "permission_to_quote_decision",
            "none",
            "not_redacted",
            company_context,
        ),
    ]


def _slot(
    slot_id: str,
    reviewer_track: str,
    evidence_status: str,
    required_artifact: str,
    claim_ids: list[str],
    proof_gate: str,
    permission_to_quote: str,
    redaction_status: str,
    context: str,
) -> dict[str, Any]:
    return {
        "slot_id": slot_id,
        "reviewer_track": reviewer_track,
        "evidence_status": evidence_status,
        "countable_now": False,
        "required_artifact": required_artifact,
        "linked_claim_ids": claim_ids,
        "proof_gate": proof_gate,
        "permission_to_quote": permission_to_quote,
        "redaction_status": redaction_status,
        "packet_sha256": "required_before_counting",
        "context": context,
        "do_not_count": "Do not count until the artifact body, reviewer role, packet SHA-256, permission state, and redaction gate are attached.",
    }


def _permission_policy() -> list[dict[str, str]]:
    return [
        {
            "permission": "none",
            "investor_use": "Do not quote or attribute; use only as internal operating context.",
            "upgrade_required": "Written permission state from reviewer or counterparty.",
        },
        {
            "permission": "private_only",
            "investor_use": "Show privately to approved diligence reviewers only if confidentiality terms allow it.",
            "upgrade_required": "Anonymous or named quote permission before using in broad fundraise materials.",
        },
        {
            "permission": "anonymous",
            "investor_use": "Quote role and organization category without name or identifying details.",
            "upgrade_required": "Redaction review and packet fingerprint in the artifact record.",
        },
        {
            "permission": "named",
            "investor_use": "Quote reviewer or counterparty name only within the recorded scope.",
            "upgrade_required": "Named permission, redaction approval, and counsel/founder review.",
        },
    ]


def _redaction_gates() -> list[dict[str, str]]:
    return [
        {
            "gate": "source_path_redaction",
            "pass_condition": "Source paths, customer names, cluster paths, and credentials are removed or scoped before export.",
            "blocked_until": "technical owner marks source artifacts public-ready or private-diligence-only.",
        },
        {
            "gate": "activation_trace_redaction",
            "pass_condition": "Activation traces are stripped of proprietary model inputs, raw customer data, and uncontrolled identifiers.",
            "blocked_until": "model owner approves trace export scope and calibration description.",
        },
        {
            "gate": "reviewer_quote_redaction",
            "pass_condition": "Reviewer wording, attribution, and organization category match recorded permission.",
            "blocked_until": "permission-to-quote register is complete.",
        },
        {
            "gate": "commercial_document_redaction",
            "pass_condition": "Pricing, party names, data rights, and confidentiality clauses are redacted according to counterparty permission.",
            "blocked_until": "founder and counsel review the commercial artifact.",
        },
    ]


def _claim_upgrade_rules(claim_validation_ledger: dict[str, Any]) -> list[dict[str, str]]:
    rules = []
    for claim in claim_validation_ledger.get("claims", []):
        claim_id = str(claim.get("claim_id", "unknown_claim"))
        rules.append(
            {
                "claim_id": claim_id,
                "current_evidence_level": str(claim.get("evidence_level", "unknown")),
                "external_proof_required": str(claim.get("upgrade_gate", "Written external artifact with packet SHA-256.")),
                "do_not_upgrade_from": str(claim.get("disallowed_overclaim", "Meeting notes, screenshots, or unpermissioned comments.")),
            }
        )
    return rules


def _investor_update_rules() -> list[dict[str, str]]:
    return [
        {
            "rule": "weekly_artifact_delta",
            "allowed_update": "Report new proof slots filled, packet SHA-256, permission state, and claim evidence changes.",
            "blocked_update": "Do not report a meeting as demand, revenue, capacity, or lead interest.",
        },
        {
            "rule": "quote_permission",
            "allowed_update": "Quote only artifacts with anonymous or named permission and matching redaction status.",
            "blocked_update": "Do not paraphrase private-only feedback in investor materials.",
        },
        {
            "rule": "claim_upgrade",
            "allowed_update": "Upgrade claim evidence only when the proof slot satisfies its linked gate.",
            "blocked_update": "Do not upgrade from local fixture evidence, screenshots, or unaudited source paths.",
        },
    ]


def _claim_ids(claim_validation_ledger: dict[str, Any]) -> list[str]:
    return [str(claim.get("claim_id", "unknown_claim")) for claim in claim_validation_ledger.get("claims", [])]
