"""External validation capture kit for design-partner evidence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_external_validation_capture_kit(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    design_partner_plan: dict[str, Any],
    pilot_walkthrough: dict[str, Any],
    data_room_manifest: dict[str, Any],
) -> dict[str, Any]:
    """Return a machine-readable kit for collecting external diligence proof."""

    manifest_id = str(data_room_manifest.get("manifest_id", f"DR-{application.application_id}"))
    packet_files = set(data_room_manifest.get("packet_files", []))
    required_review_artifacts = [
        "packet/index.json",
        "manifest.json",
        "diligence_memo.md",
        "research/methodology_evidence_map.json",
        "commercial/pricing_diligence.json",
        "commercial/pilot_walkthrough_playbook.json",
        "technical/technical_diligence_runbook.json",
    ]
    packet_artifacts_attached = [name for name in required_review_artifacts if name in packet_files]
    return {
        "kit_id": f"EXTVAL-{application.application_id}",
        "status": "capture_ready_external_evidence_not_collected",
        "boundary": "This kit is a workflow for collecting external validation; it is not evidence of signed customers, completed pilots, committed revenue, insurance capacity, or permission to quote reviewer feedback.",
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "deployment_units": application.deployment_units,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "required_controls": list(quote.required_controls),
        },
        "packet_context": {
            "manifest_id": manifest_id,
            "required_review_artifacts": required_review_artifacts,
            "attached_required_review_artifacts": packet_artifacts_attached,
            "packet_verification_required": True,
            "minimum_external_packet_artifact_count": len(required_review_artifacts),
        },
        "reviewer_tracks": [_capture_track(track, pilot_walkthrough) for track in design_partner_plan.get("tracks", [])],
        "scorecard": [
            _score_item(
                "decision_authority",
                20,
                "Reviewer has authority over underwriting, procurement, model-risk, product partnership, or capacity review.",
                "Meeting only reaches a curious observer without decision influence.",
            ),
            _score_item(
                "artifact_usefulness",
                20,
                "Reviewer names at least one TACO artifact that changes an existing review workflow.",
                "Reviewer cannot identify a useful artifact or workflow insertion point.",
            ),
            _score_item(
                "missing_evidence_specificity",
                15,
                "Reviewer gives concrete missing evidence items, owners, and acceptable proof format.",
                "Feedback is generic and cannot drive the next build or diligence step.",
            ),
            _score_item(
                "source_data_path",
                15,
                "Reviewer can grant or help source DreamAudit certificates, simulator replays, activation traces, or staged-deployment logs.",
                "No path to live evidence or partner data is identified.",
            ),
            _score_item(
                "commercial_document_path",
                20,
                "Reviewer commits to a feedback memo, pilot scope, data-access agreement, LOI, broker memo, or carrier review scope.",
                "No written follow-up artifact is available.",
            ),
            _score_item(
                "boundary_acceptance",
                10,
                "Reviewer accepts that TACO is not claiming actuarial filing, insurance capacity, signed customers, or live deployment proof.",
                "Reviewer objects that the walkthrough overstated current evidence or authority.",
            ),
        ],
        "capture_forms": _capture_forms(application, manifest_id),
        "loi_or_pilot_scope_template": {
            "document_status": "template_only_not_signed",
            "counterparty": "reviewer_organization_name",
            "decision_context": "procurement_underwriting_model_risk_capacity_or_product_partnership",
            "proposed_scope": [
                "policy_family_or_robot_task_family",
                "evidence_inputs_to_review",
                "DreamAudit_or_activation_trace_access_path",
                "packet_verification_and_feedback_workflow",
                "success_criteria_for_paid_pilot_or_next_review",
            ],
            "commercial_terms_to_fill": [
                "pilot_fee_or_no_fee",
                "data_access_rights",
                "confidentiality_and_redaction",
                "permission_to_quote_feedback",
                "target_decision_date",
            ],
            "non_claim_language": [
                "This template is not a signed LOI.",
                "This template is not an insurance offer or carrier capacity commitment.",
                "This template does not authorize public use of reviewer feedback until permission is recorded.",
            ],
        },
        "evidence_status_ladder": [
            {
                "status": "private_notes_only",
                "investor_weight": "weak",
                "proof_required": "Internal notes with no reviewer attribution or permission to quote.",
            },
            {
                "status": "anonymous_feedback_memo",
                "investor_weight": "moderate",
                "proof_required": "Written external memo with role/org type, accepted claims, rejected claims, and missing evidence.",
            },
            {
                "status": "named_feedback_memo",
                "investor_weight": "strong",
                "proof_required": "Named reviewer memo with permission-to-quote scope and packet SHA-256.",
            },
            {
                "status": "pilot_scope_or_data_access",
                "investor_weight": "very_strong",
                "proof_required": "Signed pilot scope, data-access agreement, or source-evidence transfer path.",
            },
            {
                "status": "loi_or_paid_pilot",
                "investor_weight": "round_anchor",
                "proof_required": "Signed LOI, paid pilot, broker/MGA memo, carrier review scope, or OEM procurement pilot.",
            },
        ],
        "red_flags": [
            "Feedback is summarized without reviewer permission or packet fingerprint.",
            "A meeting is counted as customer demand without written follow-up or named decision context.",
            "The team treats a broker, carrier, or OEM conversation as insurance capacity or signed revenue.",
            "Reviewer asks for source evidence and TACO cannot provide a DreamAudit or activation trace access path.",
            "The proposed LOI omits data rights, confidentiality, or permission-to-quote boundaries.",
        ],
        "next_actions": [
            "Run one capture form per external reviewer and attach packet SHA-256.",
            "Score each reviewer conversation using the six scorecard gates before updating fundraise posture.",
            "Move only written artifacts with permission-to-quote metadata into the data room.",
            "Convert the strongest reviewer track into a signed pilot scope, data-access agreement, or LOI.",
        ],
    }


def external_validation_track_rows(kit: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for reviewer capture tracks."""

    return [
        {
            "Track": item["track_id"],
            "Reviewer": item["reviewer_profile"],
            "Decision To Test": item["decision_to_test"],
            "Evidence To Capture": "; ".join(item["evidence_to_capture"]),
            "Conversion Document": item["conversion_document"],
        }
        for item in kit["reviewer_tracks"]
    ]


def external_validation_scorecard_rows(kit: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly rows for validation scorecard gates."""

    return [
        {
            "Gate": item["gate"],
            "Weight": item["weight"],
            "Pass Condition": item["pass_condition"],
            "Fail Condition": item["fail_condition"],
        }
        for item in kit["scorecard"]
    ]


def external_validation_ladder_rows(kit: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for the external evidence ladder."""

    return [
        {
            "Status": item["status"],
            "Investor Weight": item["investor_weight"],
            "Proof Required": item["proof_required"],
        }
        for item in kit["evidence_status_ladder"]
    ]


def _capture_track(track: dict[str, Any], pilot_walkthrough: dict[str, Any]) -> dict[str, Any]:
    track_id = str(track.get("track_id", "external_reviewer"))
    role_tracks = {
        str(item.get("track_id", "")): item
        for item in pilot_walkthrough.get("role_tracks", [])
        if isinstance(item, dict)
    }
    role_track = role_tracks.get(track_id, {})
    return {
        "track_id": track_id,
        "reviewer_profile": str(track.get("partner_profile", "External reviewer with decision authority.")),
        "decision_to_test": str(track.get("buyer_question", "Does TACO evidence change an external decision workflow?")),
        "prework_packet": [
            "verified_data_room_zip",
            "packet_sha256",
            "diligence_memo",
            "pricing_diligence",
            "technical_diligence_runbook",
        ],
        "evidence_to_capture": [
            "reviewer role and decision authority",
            "accepted claim IDs",
            "rejected or overclaimed claim IDs",
            "missing evidence list with owner and deadline",
            "permission-to-quote status",
            "next commercial document status",
        ],
        "questions_to_ask": list(role_track.get("questions_to_ask", [])) or [
            "Which artifact changes your current decision workflow?",
            "Which missing proof blocks a pilot, LOI, or next review?",
        ],
        "conversion_document": str(track.get("commercial_signal", "Written feedback memo defining the next evidence gate.")),
        "minimum_success": "Named decision context, one useful artifact, one missing-evidence request, and one written follow-up path.",
    }


def _score_item(gate: str, weight: int, pass_condition: str, fail_condition: str) -> dict[str, Any]:
    return {
        "gate": gate,
        "weight": weight,
        "pass_condition": pass_condition,
        "fail_condition": fail_condition,
    }


def _capture_forms(application: InsuranceApplication, manifest_id: str) -> dict[str, Any]:
    return {
        "reviewer_feedback_form": {
            "application_id": application.application_id,
            "manifest_id": manifest_id,
            "reviewer_org": "organization_name",
            "reviewer_role": "title_and_decision_authority",
            "reviewer_track": "robotics_oem_predeployment_broker_mga_underwriting_desk_carrier_reinsurer_model_risk",
            "review_date": "YYYY-MM-DD",
            "packet_sha256": "sha256_from_packet_verifier",
            "decision_context": "procurement_underwriting_model_risk_capacity_product_partnership_or_other",
            "artifacts_reviewed": [],
            "claims_accepted": [],
            "claims_rejected": [],
            "missing_evidence": [],
            "follow_up_commitment": "none_feedback_memo_pilot_scope_data_access_loi_broker_memo_carrier_review_scope",
            "permission_to_quote": "none_anonymous_named_private_only",
            "next_owner": "taco_or_reviewer",
            "next_deadline": "YYYY-MM-DD",
        },
        "missing_evidence_item": {
            "artifact_gap": "specific_missing_artifact",
            "why_it_matters": "decision_blocked_without_this",
            "acceptable_proof": "certificate_trace_video_security_review_actuarial_memo_or_other",
            "owner": "taco_partner_or_joint",
            "deadline": "YYYY-MM-DD",
        },
    }
