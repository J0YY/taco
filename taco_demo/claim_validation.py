"""Investor claim validation ledger for TACO diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


EVIDENCE_LEVEL_WEIGHT = {
    "artifact_verified": 1.0,
    "local_demo_backed": 0.75,
    "research_backed_needs_external_validation": 0.55,
    "modeled_economics_needs_buyer_confirmation": 0.45,
    "explicitly_not_claimed": 0.0,
}


def build_claim_validation_ledger(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    readiness: dict[str, Any],
    methodology_map: dict[str, Any],
    pricing_diligence: dict[str, Any],
    commercial_model: dict[str, Any],
    buyer_roi_model: dict[str, Any],
    actuarial_plan: dict[str, Any],
    external_validation_kit: dict[str, Any],
    technical_runbook: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a diligence ledger that separates safe claims from overclaims."""

    dreamaudit_ready = _dreamaudit_ready(dreamaudit_intake)
    external_status = str(external_validation_kit.get("status", "unknown"))
    claims = [
        _claim(
            "predeployment_underwriting_gap",
            "TACO addresses a real workflow gap when robot policies lack deployment telemetry or claims history.",
            "artifact_verified" if not application.telemetry_available else "research_backed_needs_external_validation",
            [
                "application.json",
                "quote.json",
                "research/sources.json",
                "commercial/pilot_walkthrough_playbook.json",
            ],
            f"{application.company_name} is {application.deployment_stage}; telemetry_available={application.telemetry_available}.",
            "Signed buyer, broker, or carrier memo confirming the gap in their own submission workflow.",
            "Do not claim market-wide urgency, budget ownership, or adoption from the demo application alone.",
        ),
        _claim(
            "replayable_failure_evidence",
            "Replayable simulator failures can be packaged as underwriting evidence objects.",
            "artifact_verified",
            [
                "certificates/*.json",
                "suite/video_index.json",
                "taco_demo/maniskill_suite.py",
                "dreamaudit/summary.json",
            ],
            f"{methodology_map.get('score', 0)}/100 methodology score with replay, suite, and DreamAudit transfer claims mapped.",
            "Reviewer reproduces selected certificates or accepts the transferred packet format in a walkthrough.",
            "Do not claim live-field frequency, loss relativity, or policy performance from simulator replays.",
        ),
        _claim(
            "internals_based_risk_signal",
            "Internal activation traces can expose risk signatures that output-only pass/fail labels miss.",
            _internals_evidence_level(methodology_map),
            [
                "metrics/*.json",
                "taco_demo/activation_recorder.py",
                "taco_demo/dreamaudit_adapter.py",
                "technical/technical_diligence_runbook.json",
            ],
            _methodology_evidence(methodology_map, "internal_activation_risk_path"),
            "Attach policy-specific recorded activations and reviewer-confirmed calibration checks.",
            "Do not claim general mechanistic interpretability, causal proof, or production monitoring readiness.",
        ),
        _claim(
            "control_linked_pricing_sensitivity",
            "TACO can show how required controls, exclusions, and quote sensitivity connect to evidence.",
            "local_demo_backed" if pricing_diligence.get("aggregate_control_delta_usd", 0) > 0 else "research_backed_needs_external_validation",
            [
                "quote.json",
                "commercial/pricing_diligence.json",
                "insurance/workflow_examples.json",
                "commercial/actuarial_readiness_plan.json",
            ],
            f"${int(pricing_diligence.get('aggregate_control_delta_usd', 0) or 0):,.0f}/mo modeled aggregate control delta; {len(quote.required_controls)} required controls.",
            "Carrier, actuary, or reinsurer review of control effectiveness, rating treatment, exclusions, and filing path.",
            "Do not claim filed rates, actuarial adequacy, coverage availability, or a binding insurance offer.",
        ),
        _claim(
            "buyer_roi_economic_case",
            "A buyer-facing ROI case can be modeled from review-cycle value, evidence operations, control deltas, and renewal evidence.",
            "modeled_economics_needs_buyer_confirmation",
            [
                "commercial/buyer_roi_model.json",
                "commercial/pricing_diligence.json",
                "commercial/external_validation_capture_kit.json",
            ],
            f"{len(buyer_roi_model.get('roi_scenarios', []))} scenarios; status {buyer_roi_model.get('status', 'unknown')}.",
            "Named buyer confirms delay cost, evidence-ops time saved, control-credit interpretation, and willingness to pay.",
            "Do not claim guaranteed savings, customer demand, procurement approval, or live loss reduction.",
        ),
        _claim(
            "seed_scale_story",
            "A $5M seed round can be framed around evidence-platform milestones before TACO carries insurance risk.",
            "research_backed_needs_external_validation",
            [
                "commercial/commercial_scale_model.json",
                "commercial/seed_financing_plan.json",
                "commercial/investor_objection_register.json",
                "commercial/pilot_walkthrough_playbook.json",
            ],
            f"Readiness posture {readiness.get('posture', 'unknown')}; commercial model status {commercial_model.get('status', 'unknown')}.",
            "Paid pilot, LOI, reviewer memo, or procurement review showing the artifact format changes a real decision.",
            "Do not claim committed revenue, signed pipeline, audited TAM, or investor commitment.",
        ),
        _claim(
            "actuarial_and_capacity_path",
            "The packet identifies the actuarial, carrier, reinsurer, licensing, filing, and claims gates needed before launch.",
            "local_demo_backed",
            [
                "commercial/actuarial_readiness_plan.json",
                "commercial/capacity_roadmap.json",
                "commercial/pricing_diligence.json",
            ],
            f"Actuarial status {actuarial_plan.get('status', 'unknown')}; {len(actuarial_plan.get('data_readiness_gates', []))} data/model gates.",
            "Carrier, actuary, compliance counsel, or fronting/MGA partner marks which gates are sufficient for the first live program.",
            "Do not claim regulatory approval, carrier capacity, rate adequacy, legal advice, or reserve support.",
        ),
        _claim(
            "external_validation_status",
            "TACO is ready to capture external validation, but signed proof is still pending until reviewers complete the workflow.",
            "research_backed_needs_external_validation" if external_status == "capture_ready_external_evidence_not_collected" else "local_demo_backed",
            [
                "commercial/external_validation_capture_kit.json",
                "commercial/design_partner_plan.json",
                "commercial/pilot_walkthrough_playbook.json",
            ],
            f"External validation kit status {external_status}; {len(external_validation_kit.get('scorecard', []))} scorecard gates.",
            "At least two completed reviewer scorecards plus permission-to-quote status and signed commercial-document path.",
            "Do not imply completed pilots, signed customers, LOIs, or quote permission before the capture kit contains them.",
        ),
        _claim(
            "transferable_data_room",
            "The diligence packet is transferable and tamper-checkable as a local SHA-256 indexed ZIP.",
            "artifact_verified",
            [
                "packet/index.json",
                "manifest.json",
                "technical/technical_diligence_runbook.json",
            ],
            f"Runbook status {technical_runbook.get('status', 'unknown')}; packet verifier is part of the local app.",
            "External reviewer independently verifies the transferred ZIP and records the packet fingerprint in a review memo.",
            "Packet integrity proves chain of custody, not production security certification or buyer acceptance.",
        ),
        _claim(
            "live_dreamaudit_corpus",
            "DreamAudit can expand the demo from local fixtures toward a larger failure corpus.",
            "local_demo_backed" if dreamaudit_ready else "research_backed_needs_external_validation",
            [
                "dreamaudit/summary.json",
                "taco_demo/dreamaudit_intake.py",
                "taco_demo/dreamaudit_adapter.py",
            ],
            _dreamaudit_evidence(dreamaudit_intake),
            "Carrier-ready DreamAudit ladder plus source-path review for minimality, reproducibility, and control mapping.",
            "Do not claim carrier-ready corpus quality when only local fixtures or partial scans are attached.",
        ),
    ]
    blocked = [claim for claim in claims if claim["evidence_level"] == "explicitly_not_claimed"]
    needs_external = [
        claim
        for claim in claims
        if claim["evidence_level"] in {"research_backed_needs_external_validation", "modeled_economics_needs_buyer_confirmation"}
    ]
    evidence_score = round(
        100 * sum(EVIDENCE_LEVEL_WEIGHT[claim["evidence_level"]] for claim in claims) / len(claims)
    )
    return {
        "ledger_id": f"CLAIM-{application.application_id}",
        "status": _status(evidence_score, needs_external),
        "evidence_score": evidence_score,
        "boundary": "This ledger controls investor-facing claims. It strengthens diligence by naming evidence, upgrade gates, and disallowed overclaims; it is not proof of external adoption, actuarial approval, regulatory approval, or financing.",
        "claim_count": len(claims),
        "external_validation_needed": len(needs_external),
        "blocked_claims": len(blocked),
        "claims": claims,
        "pitch_usage": {
            "safe_wording": "TACO is a local, auditable proof-of-concept for robotics insurance evidence workflows.",
            "unsafe_wording": [
                "TACO has proven loss reduction.",
                "TACO has filed or carrier-approved pricing.",
                "TACO has signed customers or committed revenue.",
                "TACO has production security certification.",
            ],
            "next_two_proofs": [
                "Two completed external reviewer scorecards tied to packet fingerprints.",
                "One signed paid pilot, LOI, broker memo, or procurement review memo that confirms workflow value.",
            ],
        },
    }


def claim_validation_rows(ledger: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for the claim ledger."""

    return [
        {
            "Claim": claim["claim_id"],
            "Evidence Level": claim["evidence_level"].replace("_", " ").title(),
            "Current Evidence": claim["current_evidence"],
            "Upgrade Gate": claim["upgrade_gate"],
            "Disallowed Overclaim": claim["disallowed_overclaim"],
        }
        for claim in ledger["claims"]
    ]


def claim_validation_summary_rows(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    """Return summary rows for claim evidence levels."""

    counts: dict[str, int] = {}
    for claim in ledger["claims"]:
        counts[claim["evidence_level"]] = counts.get(claim["evidence_level"], 0) + 1
    return [
        {
            "Evidence Level": level.replace("_", " ").title(),
            "Claims": count,
            "Weight": EVIDENCE_LEVEL_WEIGHT[level],
        }
        for level, count in sorted(counts.items())
    ]


def _claim(
    claim_id: str,
    investor_safe_claim: str,
    evidence_level: str,
    artifacts: list[str],
    current_evidence: str,
    upgrade_gate: str,
    disallowed_overclaim: str,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "investor_safe_claim": investor_safe_claim,
        "evidence_level": evidence_level,
        "artifacts": artifacts,
        "current_evidence": current_evidence,
        "upgrade_gate": upgrade_gate,
        "disallowed_overclaim": disallowed_overclaim,
    }


def _status(evidence_score: int, needs_external: list[dict[str, Any]]) -> str:
    if evidence_score >= 70 and needs_external:
        return "claims_bounded_and_investor_ready_pending_external_validation"
    if evidence_score >= 80:
        return "claims_artifact_verified"
    if evidence_score >= 60:
        return "claims_need_targeted_validation"
    return "claims_need_more_evidence"


def _methodology_evidence(methodology_map: dict[str, Any], claim_id: str) -> str:
    claim = next((item for item in methodology_map.get("claims", []) if item.get("claim_id") == claim_id), None)
    if not claim:
        return "Methodology evidence claim is not present in the map."
    return str(claim.get("current_evidence", "No current evidence recorded."))


def _internals_evidence_level(methodology_map: dict[str, Any]) -> str:
    claim = next(
        (item for item in methodology_map.get("claims", []) if item.get("claim_id") == "internal_activation_risk_path"),
        None,
    )
    if not claim:
        return "research_backed_needs_external_validation"
    status = str(claim.get("status", ""))
    if status == "research_and_artifact_backed":
        return "artifact_verified"
    if status == "demo_backed_needs_live_evidence":
        return "local_demo_backed"
    return "research_backed_needs_external_validation"


def _dreamaudit_ready(dreamaudit_intake: dict[str, Any] | None) -> bool:
    if not dreamaudit_intake or not dreamaudit_intake.get("root_exists"):
        return False
    readiness = dreamaudit_intake.get("readiness", {})
    ladder = list(dreamaudit_intake.get("evidence_depth_ladder", []))
    return str(readiness.get("status", "")) == "carrier_review_ready" or any(
        row.get("status") == "carrier_review_ready" for row in ladder
    )


def _dreamaudit_evidence(dreamaudit_intake: dict[str, Any] | None) -> str:
    if not dreamaudit_intake:
        return "No DreamAudit intake is attached."
    summary = dreamaudit_intake.get("summary", {})
    readiness = dreamaudit_intake.get("readiness", {})
    return (
        f"{int(summary.get('certificates', 0) or 0)} DreamAudit certificates; "
        f"readiness status {readiness.get('status', 'unknown')}."
    )
