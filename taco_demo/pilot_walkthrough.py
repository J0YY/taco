"""External reviewer walkthrough playbook for TACO diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_pilot_walkthrough_playbook(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    design_partner_plan: dict[str, Any],
    objection_register: dict[str, Any],
    methodology_map: dict[str, Any],
    pricing_diligence: dict[str, Any],
) -> dict[str, Any]:
    """Return a meeting workflow that converts reviewer walkthroughs into evidence."""

    return {
        "playbook_id": f"WALK-{application.application_id}",
        "status": "external_walkthrough_ready_not_completed",
        "boundary": "This is a reviewer walkthrough plan, not evidence of completed pilots, signed customers, or insurance capacity.",
        "target_customer": application.company_name,
        "policy_context": {
            "policy_id": application.policy_id,
            "robot_type": application.robot_type,
            "deployment_units": application.deployment_units,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "quote_status": quote.status,
        },
        "prework": [
            "Send the verified data-room ZIP and packet SHA-256 before the meeting.",
            "Ask the reviewer to name their decision context: procurement, bind/no-bind, model-risk, compliance, or product partnership.",
            "Collect permission to record non-confidential objections, missing-evidence requests, and follow-up commitments.",
        ],
        "meeting_agenda": [
            _agenda_step(
                1,
                "Packet transfer and checksum verification",
                "Reviewer verifies packet/index.json and manifest SHA-256 before inspecting claims.",
                "packet/index.json verification result and packet SHA-256.",
            ),
            _agenda_step(
                2,
                "Blocked underwriting context",
                "Show why the application is blocked by conventional telemetry-first underwriting.",
                "Named reviewer agrees or rejects the pre-deployment underwriting gap.",
            ),
            _agenda_step(
                3,
                "Replay certificate inspection",
                "Walk through primary failure certificates, minimal costs, neighborhood rates, and required controls.",
                "List of accepted, disputed, or missing replay evidence.",
            ),
            _agenda_step(
                4,
                "Internals and methodology evidence map",
                "Separate live DreamAudit or activation evidence from demo fixtures and open methodology risks.",
                "Reviewer marks which claims are credible, confusing, or overclaimed.",
            ),
            _agenda_step(
                5,
                "Pricing sensitivity and exclusions",
                "Inspect factor stack, control deltas, and disabled-control exclusions.",
                "Reviewer names the actuarial, compliance, or carrier-capacity work needed before binding.",
            ),
            _agenda_step(
                6,
                "Objection register review",
                "Use the objection register to capture unresolved VC, broker, carrier, or OEM diligence questions.",
                "Updated objection list with next proof owner and deadline.",
            ),
            _agenda_step(
                7,
                "Evidence capture and conversion gate",
                "Decide whether the reviewer will provide a feedback memo, pilot scope, LOI, or data-access path.",
                "Completed evidence capture form and next commercial document status.",
            ),
        ],
        "role_tracks": [_role_track(track, objection_register, methodology_map, pricing_diligence) for track in design_partner_plan.get("tracks", [])],
        "evidence_capture_form": {
            "reviewer_org_type": "broker_mga_carrier_reinsurer_oem_enterprise_or_other",
            "reviewer_role": "name_role_and_decision_authority",
            "review_date": "YYYY-MM-DD",
            "packet_sha256": "sha256_from_packet_verifier",
            "artifacts_reviewed": [
                "packet/index.json",
                "manifest.json",
                "diligence_memo.md",
                "commercial/pilot_walkthrough_playbook.json",
                "research/methodology_evidence_map.json",
                "commercial/pricing_diligence.json",
                "commercial/investor_objection_register.json",
            ],
            "claims_accepted": [],
            "claims_rejected": [],
            "missing_evidence": [],
            "follow_up_commitment": "none_feedback_memo_pilot_scope_data_access_loi_or_other",
            "loi_or_pilot_scope_status": "not_requested_drafting_requested_received_or_rejected",
            "permission_to_quote_feedback": "not_requested_private_anonymous_or_named",
            "next_owner": "taco_or_reviewer",
            "next_deadline": "YYYY-MM-DD",
        },
        "conversion_gates": [
            {
                "gate": "feedback_memo_collected",
                "success_condition": "Reviewer provides written comments on evidence usefulness and missing artifacts.",
            },
            {
                "gate": "pilot_scope_defined",
                "success_condition": "Reviewer names the robot task family, policy family, evidence inputs, and expected decision output.",
            },
            {
                "gate": "policy_family_named",
                "success_condition": "A concrete coverage, procurement, model-risk, or compliance review workflow is named.",
            },
            {
                "gate": "source_data_access_granted",
                "success_condition": "Partner authorizes access to DreamAudit certificates, simulator rollouts, activation traces, or staged-deployment logs.",
            },
            {
                "gate": "commercial_document_signed",
                "success_condition": "LOI, paid pilot, data-access agreement, broker memo, or carrier review scope is signed.",
            },
        ],
        "red_flags": [
            "Reviewer is asked to accept actuarial pricing or rate adequacy from demo quote logic.",
            "Packet cannot point to source certificate, trace, replay, or activation paths for a claim under review.",
            "The walkthrough treats local videos as live deployment evidence.",
            "No named reviewer has authority over underwriting, procurement, model-risk, or partnership decisions.",
            "The team upgrades evidence status without written reviewer feedback or source-data access.",
        ],
    }


def pilot_walkthrough_rows(playbook: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for role-specific walkthrough tracks."""

    rows = []
    for track in playbook.get("role_tracks", []):
        rows.append(
            {
                "Track": str(track["track_id"]),
                "Reviewer Role": str(track["reviewer_role"]),
                "Meeting Objective": str(track["meeting_objective"]),
                "Artifacts To Show": "; ".join(track["artifacts_to_show"]),
                "Evidence To Collect": "; ".join(track["evidence_to_collect"]),
                "Pass/Fail Criteria": "; ".join(track["pass_fail_criteria"]),
            }
        )
    return rows


def _agenda_step(order: int, step: str, purpose: str, evidence_output: str) -> dict[str, Any]:
    return {
        "order": order,
        "step": step,
        "purpose": purpose,
        "evidence_output": evidence_output,
    }


def _role_track(
    track: dict[str, Any],
    objection_register: dict[str, Any],
    methodology_map: dict[str, Any],
    pricing_diligence: dict[str, Any],
) -> dict[str, Any]:
    track_id = str(track.get("track_id", "external_reviewer"))
    reviewer_role = _reviewer_role(track_id)
    primary_objections = [item["objection_id"] for item in objection_register.get("objections", [])[:3]]
    open_claims = [
        claim["claim_id"]
        for claim in methodology_map.get("claims", [])
        if str(claim.get("status", "")).endswith("needs_live_evidence") or claim.get("status") == "needs_work"
    ][:3]
    pricing_questions = [str(item) for item in pricing_diligence.get("diligence_questions", [])[:2]]
    return {
        "track_id": track_id,
        "reviewer_role": reviewer_role,
        "meeting_objective": track.get("buyer_question", "Evaluate whether TACO evidence changes an external decision workflow."),
        "artifacts_to_show": [
            *list(track.get("pilot_artifacts", [])),
            "methodology evidence map",
            "pricing diligence sensitivity",
            "investor objection register",
        ],
        "questions_to_ask": [
            "Which artifact changes your current decision workflow, if any?",
            "Which claim is credible only after live partner evidence is attached?",
            "Which control, exclusion, or pricing delta is commercially legible?",
            *pricing_questions,
        ],
        "evidence_to_collect": [
            "written feedback memo or reviewer-notes excerpt",
            "accepted and rejected claim IDs",
            "missing evidence list",
            "decision workflow where TACO could be inserted",
            "next proof owner and deadline",
        ],
        "pass_fail_criteria": [
            *list(track.get("acceptance_criteria", [])),
            "reviewer can identify at least one usable TACO artifact and one missing evidence item",
            "reviewer does not object that the meeting overclaimed pricing, customers, capacity, or completed pilots",
        ],
        "objections_to_test": primary_objections,
        "open_methodology_claims_to_test": open_claims,
        "commercial_signal": track.get("commercial_signal", "Written feedback defining next evidence gate."),
    }


def _reviewer_role(track_id: str) -> str:
    if "oem" in track_id:
        return "robotics_oem_engineering_or_enterprise_risk_lead"
    if "broker" in track_id or "mga" in track_id:
        return "broker_mga_underwriting_or_program_lead"
    if "carrier" in track_id or "reinsurer" in track_id:
        return "carrier_reinsurer_model_risk_or_capacity_reviewer"
    return "external_reviewer_with_decision_authority"
