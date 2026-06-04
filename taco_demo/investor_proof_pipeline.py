"""Investor proof pipeline for converting TACO diligence into external evidence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown
from .seed_financing_plan import TARGET_SEED_RAISE_USD


def build_investor_proof_pipeline(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    fundraise_readiness: dict[str, Any],
    design_partner_plan: dict[str, Any],
    pilot_walkthrough: dict[str, Any],
    external_validation_kit: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
    buyer_roi_model: dict[str, Any],
) -> dict[str, Any]:
    """Return a VC-facing operating workflow for upgrading local proof into external proof."""

    readiness_score = int(fundraise_readiness.get("score", 0) or 0)
    claim_score = int(claim_validation_ledger.get("evidence_score", 0) or 0)
    external_gate_count = int(claim_validation_ledger.get("external_validation_needed", 0) or 0)
    reviewer_tracks = _reviewer_targets(design_partner_plan, external_validation_kit)
    stage_count = 5
    current_artifact_score = round((0.45 * readiness_score) + (0.35 * claim_score) + 20)
    required_external_artifacts = [
        "two named external reviewer memos with packet SHA-256",
        "one source-data path for DreamAudit certificates or activation traces",
        "one buyer ROI assumption confirmation or paid pilot scope",
        "one broker, MGA, carrier, reinsurer, or OEM next-review document",
        "one permission-to-quote decision per public claim",
    ]
    return {
        "pipeline_id": f"PROOF-{application.application_id}",
        "status": _status(current_artifact_score, external_gate_count),
        "boundary": "This is an investor proof operating workflow, not evidence of signed customers, completed pilots, committed revenue, committed financing, insurance capacity, carrier approval, or guaranteed savings.",
        "target_raise_usd": TARGET_SEED_RAISE_USD,
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "robot_type": application.robot_type,
            "deployment_units": application.deployment_units,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "required_controls": list(quote.required_controls),
        },
        "current_scores": {
            "fundraise_readiness_score": readiness_score,
            "claim_validation_score": claim_score,
            "current_artifact_score": min(100, current_artifact_score),
            "external_validation_gates_remaining": external_gate_count,
        },
        "round_thesis": {
            "safe_claim": "TACO is a working evidence layer for learned-policy robotics underwriting, with local replay, internals, pricing, packet, and diligence workflows ready for external validation.",
            "blocked_claim": "TACO should not present itself as having signed customers, actuarially filed pricing, bound insurance capacity, guaranteed savings, or validated market demand until the proof pipeline collects written external artifacts.",
            "seed_round_argument": f"The proposed ${TARGET_SEED_RAISE_USD:,.0f} seed funds the conversion from local evidence product to partner-specific DreamAudit, activation, broker/carrier, and buyer proof.",
        },
        "workflow_stages": _workflow_stages(required_external_artifacts),
        "reviewer_targets": reviewer_tracks,
        "proof_gates": _proof_gates(required_external_artifacts, buyer_roi_model, pilot_walkthrough),
        "weekly_operating_cadence": [
            {
                "cadence": "monday_packet_update",
                "owner": "evidence_operator",
                "output": "latest packet SHA-256, changed artifact list, and claims whose evidence level changed",
            },
            {
                "cadence": "tuesday_reviewer_walkthroughs",
                "owner": "founder_or_gm",
                "output": "one completed reviewer form with accepted claims, rejected claims, missing evidence, and follow-up document status",
            },
            {
                "cadence": "wednesday_live_evidence_build",
                "owner": "robotics_engineering",
                "output": "DreamAudit certificates, activation NPZ traces, replay paths, or calibrated signal map attached to the data room",
            },
            {
                "cadence": "thursday_commercial_conversion",
                "owner": "gtm_or_partnerships",
                "output": "pilot scope, data-access agreement, buyer ROI confirmation, LOI draft, broker memo, or carrier review scope",
            },
            {
                "cadence": "friday_investor_claim_review",
                "owner": "founder_and_counsel",
                "output": "claim ledger update, overclaim audit, permission-to-quote status, and next investor proof request",
            },
        ],
        "data_room_upgrade_rules": [
            {
                "rule": "do_not_upgrade_from_meeting_alone",
                "required_evidence": "Written reviewer artifact with role, org type, packet SHA-256, accepted/rejected claims, and permission metadata.",
            },
            {
                "rule": "internals_claim_requires_trace",
                "required_evidence": "Recorded activation NPZ, layer-to-signal map, calibration note, and metric output for the same certificate family.",
            },
            {
                "rule": "roi_claim_requires_buyer_confirmation",
                "required_evidence": "Named buyer confirmation of delay cost, evidence-ops time, control-credit interpretation, or pilot economics.",
            },
            {
                "rule": "capacity_claim_requires_capacity_reviewer",
                "required_evidence": "Carrier, reinsurer, MGA, fronting, broker, actuary, or counsel memo marking what is sufficient for next review.",
            },
        ],
        "minimum_fundraise_package": required_external_artifacts,
        "open_risks": [
            "External reviewers may agree the packet is useful but still reject current pricing, capacity, or ROI assumptions.",
            "Partner-specific activations may require access approvals, redaction, and calibration before they can be shown in a data room.",
            "Insurance capacity and regulatory work can lag evidence-product traction, so the seed story should keep evidence revenue separate from risk-bearing launch.",
        ],
    }


def investor_proof_stage_rows(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly rows for the proof pipeline stages."""

    return [
        {
            "Stage": item["stage"],
            "Window": item["window"],
            "Objective": item["objective"],
            "Artifacts To Produce": "; ".join(item["artifacts_to_produce"]),
            "Exit Gate": item["exit_gate"],
        }
        for item in pipeline["workflow_stages"]
    ]


def investor_proof_reviewer_rows(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly rows for target reviewer tracks."""

    return [
        {
            "Track": item["track_id"],
            "Target Count": item["target_count"],
            "Reviewer Profile": item["reviewer_profile"],
            "Decision To Test": item["decision_to_test"],
            "Conversion Document": item["conversion_document"],
        }
        for item in pipeline["reviewer_targets"]
    ]


def investor_proof_gate_rows(pipeline: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly rows for proof gates."""

    return [
        {
            "Gate": item["gate"],
            "Why It Matters": item["why_it_matters"],
            "Pass Condition": item["pass_condition"],
            "Do Not Count": item["do_not_count"],
        }
        for item in pipeline["proof_gates"]
    ]


def _workflow_stages(required_external_artifacts: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "stage": "0_packet_reproducibility",
            "window": "week_0",
            "objective": "Make the local packet independently testable before any investor or reviewer meeting.",
            "artifacts_to_produce": [
                "green pytest output",
                "app import or Streamlit run",
                "packet SHA-256 verifier output",
                "current claim validation ledger",
            ],
            "exit_gate": "Reviewer can reproduce the packet and identify which claims are local, live, modeled, or external-pending.",
        },
        {
            "stage": "1_reviewer_discovery",
            "window": "weeks_1_to_2",
            "objective": "Run role-specific walkthroughs with decision-capable robotics, broker, carrier, or enterprise reviewers.",
            "artifacts_to_produce": [
                "completed reviewer capture form",
                "accepted and rejected claim IDs",
                "missing-evidence list with owner and deadline",
            ],
            "exit_gate": "At least two reviewers name a useful artifact and a concrete missing-evidence request.",
        },
        {
            "stage": "2_live_evidence_attachment",
            "window": "weeks_2_to_4",
            "objective": "Replace the highest-risk fixture assumptions with partner-specific DreamAudit certificates or activation traces.",
            "artifacts_to_produce": [
                "DreamAudit source paths or adapted certificates",
                "activation NPZ traces and layer-to-signal map",
                "updated methodology and claim ledgers",
            ],
            "exit_gate": "Internals and replay claims point to source artifacts for the same policy or task family under review.",
        },
        {
            "stage": "3_commercial_document_conversion",
            "window": "weeks_4_to_8",
            "objective": "Turn useful-reviewer feedback into signed or written commercial artifacts.",
            "artifacts_to_produce": required_external_artifacts[:4],
            "exit_gate": "A reviewer document states how TACO evidence changes a procurement, underwriting, model-risk, or capacity workflow.",
        },
        {
            "stage": "4_seed_round_readiness",
            "window": "weeks_8_to_12",
            "objective": "Assemble the investor packet around written proof, not demo-only inference.",
            "artifacts_to_produce": [
                "updated data-room ZIP",
                "permission-to-quote register",
                "proof-gate status summary",
                "seed use-of-funds tied to live-evidence and partner-conversion milestones",
            ],
            "exit_gate": "Fundraise narrative can cite written external artifacts without implying bound insurance, filed rates, or committed revenue.",
        },
    ]


def _reviewer_targets(
    design_partner_plan: dict[str, Any],
    external_validation_kit: dict[str, Any],
) -> list[dict[str, Any]]:
    capture_tracks = {
        str(item.get("track_id", "")): item
        for item in external_validation_kit.get("reviewer_tracks", [])
        if isinstance(item, dict)
    }
    rows = []
    for track in design_partner_plan.get("tracks", []):
        track_id = str(track.get("track_id", "external_reviewer"))
        capture = capture_tracks.get(track_id, {})
        target_count = 2 if "broker" in track_id or "carrier" in track_id else 1
        rows.append(
            {
                "track_id": track_id,
                "target_count": target_count,
                "reviewer_profile": str(capture.get("reviewer_profile") or track.get("partner_profile", "")),
                "decision_to_test": str(capture.get("decision_to_test") or track.get("buyer_question", "")),
                "conversion_document": str(capture.get("conversion_document") or track.get("commercial_signal", "")),
                "minimum_success": str(capture.get("minimum_success", "Written feedback with next proof gate.")),
            }
        )
    return rows


def _proof_gates(
    required_external_artifacts: list[str],
    buyer_roi_model: dict[str, Any],
    pilot_walkthrough: dict[str, Any],
) -> list[dict[str, str]]:
    buyer_docs = "; ".join(buyer_roi_model.get("procurement_readiness", {}).get("documents_to_collect", [])[:3])
    conversion_gates = "; ".join(item.get("gate", "") for item in pilot_walkthrough.get("conversion_gates", [])[:3])
    return [
        _gate(
            "packet_reproduced_by_external_reviewer",
            "Shows TACO can transfer a verifiable evidence packet instead of a one-off founder demo.",
            "External reviewer verifies packet/index.json, packet SHA-256, and at least three artifact paths.",
            "A live meeting where only screenshots are shown.",
        ),
        _gate(
            "claim_ledger_external_feedback",
            "Lets investors see which claims survived scrutiny and which were downgraded.",
            "Reviewer marks accepted, rejected, missing, and overclaimed items in writing.",
            "Private founder notes without reviewer role, packet fingerprint, or permission metadata.",
        ),
        _gate(
            "live_internals_or_dreamaudit_artifact",
            "Closes the highest technical gap around whether TACO is internals-based and transferable.",
            "DreamAudit certificates or activation traces attach source paths, layer maps, calibrations, and metric outputs.",
            "Fixture traces or videos presented as partner-specific evidence.",
        ),
        _gate(
            "buyer_roi_confirmed",
            "Moves the buyer case from modeled economics to customer-confirmed procurement evidence.",
            f"Buyer validates at least one ROI input or document path: {buyer_docs or required_external_artifacts[2]}.",
            "A model spreadsheet with no named buyer confirmation.",
        ),
        _gate(
            "commercial_conversion_document",
            "Turns technical interest into a fundraise-grade external artifact.",
            f"One signed or written document reaches a conversion gate: {conversion_gates or required_external_artifacts[3]}.",
            "A friendly call counted as customer demand or committed revenue.",
        ),
    ]


def _gate(gate: str, why_it_matters: str, pass_condition: str, do_not_count: str) -> dict[str, str]:
    return {
        "gate": gate,
        "why_it_matters": why_it_matters,
        "pass_condition": pass_condition,
        "do_not_count": do_not_count,
    }


def _status(current_artifact_score: int, external_gate_count: int) -> str:
    if current_artifact_score >= 85 and external_gate_count <= 2:
        return "seed_round_proof_pipeline_ready_needs_final_written_artifacts"
    if current_artifact_score >= 70:
        return "credible_seed_story_needs_external_proof_execution"
    return "proof_pipeline_defined_needs_stronger_local_artifacts"
