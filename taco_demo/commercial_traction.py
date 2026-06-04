"""Commercial traction operating plan for TACO seed diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_commercial_traction_plan(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    commercial_model: dict[str, Any],
    buyer_roi_model: dict[str, Any],
    investor_proof_pipeline: dict[str, Any],
    external_validation_kit: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
    research_validation_plan: dict[str, Any],
    design_partner_plan: dict[str, Any],
    seed_financing_plan: dict[str, Any],
) -> dict[str, Any]:
    """Return a bounded GTM plan for converting proof artifacts into countable traction."""

    target_raise = int(seed_financing_plan.get("target_raise_usd", 0) or 0)
    modeled_arr = int(commercial_model.get("base_case", {}).get("modeled_arr_usd", 0) or 0)
    target_prospects = 34
    package_rows = _packages()
    return {
        "plan_id": f"TRACT-{application.application_id}",
        "status": "traction_operating_plan_ready_not_revenue_claim",
        "boundary": "This is a commercial traction operating plan, not evidence of signed customers, committed revenue, paid pilots, procurement approval, insurance capacity, investment interest, filed pricing, or loss reduction.",
        "target_raise_usd": target_raise,
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "robot_type": application.robot_type,
            "deployment_units": application.deployment_units,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "required_controls": list(quote.required_controls),
        },
        "traction_thesis": {
            "safe_claim": "TACO can run a repeatable evidence-sales motion where each buyer conversation ends in a packet-fingerprinted artifact, missing-evidence memo, data-access path, or scoped pilot document.",
            "blocked_claim": "Do not claim revenue traction, market pull, buyer ROI, carrier capacity, or research validation until the countable artifacts below are signed, paid, or written by named external reviewers.",
            "seed_round_argument": f"The proposed ${target_raise:,.0f} round funds enough evidence production, security, and reviewer workflow to test whether a ${modeled_arr:,.0f} base evidence-platform scenario is reachable.",
        },
        "icp_segments": _segments(design_partner_plan, external_validation_kit),
        "commercial_packages": package_rows,
        "weekly_metrics": _weekly_metrics(),
        "counting_rules": _counting_rules(),
        "investor_reporting": {
            "weekly_rollup": [
                "new packet SHA-256 and artifact changes since prior investor update",
                "prospects contacted by ICP segment and role",
                "countable external artifacts collected",
                "claims upgraded, claims downgraded, and overclaims blocked",
                "pilot, data-access, or paid-scope documents created with permission status",
            ],
            "do_not_blend": [
                "Do not blend friendly meetings into pipeline dollars.",
                "Do not blend modeled ARR with signed ARR.",
                "Do not blend reviewer curiosity with carrier capacity.",
                "Do not blend demo replay success with validated control loss reduction.",
            ],
        },
        "proof_gate_links": _proof_gate_links(
            investor_proof_pipeline,
            buyer_roi_model,
            claim_validation_ledger,
            research_validation_plan,
        ),
        "minimum_countable_seed_package": [
            "at least two paid or written pilot scopes tied to named ICP segments",
            "at least two packet-fingerprinted external reviewer memos with accepted/rejected claims",
            "at least one source-data or activation-trace access path for partner-specific evidence",
            "at least one broker, MGA, carrier, reinsurer, or capacity-review next-document request",
            "a permission-to-quote register separating attributable quotes from anonymous diligence notes",
        ],
        "open_risks": [
            "Prospects may value the packet but require services-heavy customization before recurring software revenue is credible.",
            "Broker, carrier, and reinsurer reviewers may request regulatory or actuarial work before they support customer-facing insurance language.",
            "Robot OEMs may be blocked from sharing model internals, which could slow the internals-based evidence claim even when the adapter works.",
            "Modeled buyer ROI may fail procurement validation if deployment delay costs or insurance-control credits are lower than assumed.",
        ],
    }


def commercial_traction_segment_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly ICP segment rows."""

    return [
        {
            "Segment": item["segment_id"],
            "Buyer": item["buyer"],
            "Target Prospects": item["target_prospects"],
            "First Offer": item["first_offer"],
            "Conversion Artifact": item["conversion_artifact"],
            "Do Not Count": item["do_not_count"],
        }
        for item in plan["icp_segments"]
    ]


def commercial_traction_package_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly commercial package rows."""

    return [
        {
            "Package": item["package_id"],
            "Price": item["price_usd"],
            "Term": item["term"],
            "Buyer": item["buyer"],
            "Output": item["deliverable"],
            "Upgrade Gate": item["upgrade_gate"],
        }
        for item in plan["commercial_packages"]
    ]


def commercial_traction_metric_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly weekly metric rows."""

    return [
        {
            "Metric": item["metric"],
            "Target": item["weekly_target"],
            "Count Only If": item["count_only_if"],
            "Owner": item["owner"],
        }
        for item in plan["weekly_metrics"]
    ]


def commercial_traction_rule_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly count/do-not-count rows."""

    return [
        {
            "Rule": item["rule"],
            "Count": item["count"],
            "Do Not Count": item["do_not_count"],
            "Evidence Field": item["evidence_field"],
        }
        for item in plan["counting_rules"]
    ]


def _segments(
    design_partner_plan: dict[str, Any],
    external_validation_kit: dict[str, Any],
) -> list[dict[str, Any]]:
    tracks = {str(track.get("track_id", "")): track for track in design_partner_plan.get("tracks", []) if isinstance(track, dict)}
    capture = {
        str(track.get("track_id", "")): track
        for track in external_validation_kit.get("reviewer_tracks", [])
        if isinstance(track, dict)
    }
    return [
        _segment(
            "robotics_oem_predeployment",
            "Robotics OEM or autonomy platform team shipping learned policies before field claims history exists.",
            12,
            "Policy Evidence Sprint",
            "Paid pilot scope, data-access agreement, or named missing-evidence memo tied to a policy family.",
            "A technical demo meeting without source data access, packet SHA, or next-document owner.",
            tracks.get("robotics_oem_predeployment", {}).get("buyer_question", ""),
            capture.get("robotics_oem_predeployment", {}).get("minimum_success", ""),
        ),
        _segment(
            "broker_mga_submission_desk",
            "Specialty broker, MGA, or program administrator triaging robotics submissions.",
            8,
            "Autonomy Submission Triage",
            "Broker/MGA submission memo marking how the packet changes bind, decline, exclusion, or referral workflow.",
            "A broker intro that does not name an underwriting decision or missing-evidence request.",
            tracks.get("broker_mga_underwriting_desk", {}).get("buyer_question", ""),
            capture.get("broker_mga_underwriting_desk", {}).get("minimum_success", ""),
        ),
        _segment(
            "carrier_reinsurer_model_risk",
            "Carrier, reinsurer, or capacity reviewer assessing autonomy model risk and evidence limits.",
            6,
            "Capacity Diligence Packet",
            "Capacity, actuarial, model-risk, or counsel memo naming requirements for the next review.",
            "General interest in robotics insurance without capacity, compliance, data-quality, or actuarial next steps.",
            tracks.get("carrier_reinsurer_model_risk", {}).get("buyer_question", ""),
            capture.get("carrier_reinsurer_model_risk", {}).get("minimum_success", ""),
        ),
        _segment(
            "enterprise_risk_procurement",
            "Enterprise risk, procurement, or safety team approving autonomous robot vendors.",
            8,
            "Deployment Evidence Review",
            "Procurement/risk review note saying which controls, exclusions, or evidence change deployment approval.",
            "A procurement conversation that does not connect TACO artifacts to vendor approval or insurance terms.",
            tracks.get("enterprise_procurement_risk", {}).get("buyer_question", ""),
            capture.get("enterprise_procurement_risk", {}).get("minimum_success", ""),
        ),
    ]


def _segment(
    segment_id: str,
    buyer: str,
    target_prospects: int,
    first_offer: str,
    conversion_artifact: str,
    do_not_count: str,
    buyer_question: object,
    minimum_success: object,
) -> dict[str, Any]:
    return {
        "segment_id": segment_id,
        "buyer": buyer,
        "target_prospects": target_prospects,
        "first_offer": first_offer,
        "conversion_artifact": conversion_artifact,
        "do_not_count": do_not_count,
        "buyer_question": str(buyer_question or "Can TACO evidence reduce review uncertainty before claims history exists?"),
        "minimum_success": str(minimum_success or "Written artifact with role, packet SHA-256, accepted/rejected claims, and next proof gate."),
    }


def _packages() -> list[dict[str, Any]]:
    return [
        _package(
            "evidence_packet_walkthrough",
            15_000,
            "2 weeks",
            "Any reviewer track",
            "Verified packet walkthrough, claim ledger review, missing-evidence memo, and permission status.",
            "Reviewer verifies packet/index.json and names at least one accepted or rejected claim.",
        ),
        _package(
            "policy_evidence_sprint",
            45_000,
            "4 to 6 weeks",
            "Robotics OEM or enterprise risk team",
            "DreamAudit certificates, activation trace plan, control/exclusion worksheet, and buyer ROI assumption check.",
            "Buyer signs paid scope or data-access agreement for a named policy or task family.",
        ),
        _package(
            "autonomy_submission_triage",
            75_000,
            "annual retainer or 3-month pilot",
            "Broker, MGA, or program administrator",
            "Repeatable submission intake workflow with packet verifier, quote worksheet, and referral/exclusion memo.",
            "Submission desk uses TACO packet on at least two prospective insureds and records decision impact.",
        ),
        _package(
            "capacity_diligence_packet",
            60_000,
            "4 weeks",
            "Carrier, reinsurer, or capacity reviewer",
            "Methodology, actuarial limits, capacity-roadmap, security, and model-risk review packet.",
            "Reviewer issues a written capacity, actuarial, compliance, or data-quality next-step memo.",
        ),
    ]


def _package(
    package_id: str,
    price_usd: int,
    term: str,
    buyer: str,
    deliverable: str,
    upgrade_gate: str,
) -> dict[str, Any]:
    return {
        "package_id": package_id,
        "price_usd": price_usd,
        "term": term,
        "buyer": buyer,
        "deliverable": deliverable,
        "upgrade_gate": upgrade_gate,
    }


def _weekly_metrics() -> list[dict[str, Any]]:
    return [
        _metric("verified_packet_walkthroughs", 3, "packet SHA-256, reviewer role, and verifier result are recorded", "founder_or_gm"),
        _metric("named_missing_evidence_memos", 2, "memo names rejected claims, missing artifact, owner, and next action", "evidence_operator"),
        _metric("source_data_access_paths", 1, "DreamAudit, activation, replay, or policy-family source path is attached with permission", "robotics_engineering"),
        _metric("paid_pilot_scopes_or_lois", 1, "document has counterparty, scope, price or non-price terms, and signature/status", "gtm_or_partnerships"),
        _metric("buyer_roi_confirmations", 1, "buyer confirms one delay-cost, review-time, control-credit, or procurement assumption", "founder_or_gm"),
        _metric("permission_to_quote_decisions", 2, "permission metadata is recorded as public, anonymized, private, or rejected", "founder_and_counsel"),
    ]


def _metric(metric: str, weekly_target: int, count_only_if: str, owner: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "weekly_target": weekly_target,
        "count_only_if": count_only_if,
        "owner": owner,
    }


def _counting_rules() -> list[dict[str, str]]:
    return [
        _rule(
            "signed_or_paid_commercial_artifact",
            "Signed pilot scope, paid invoice, LOI, data-access agreement, or written review scope.",
            "Friendly meeting, investor intro, unsigned notes, or pricing discussed verbally.",
            "document_status",
        ),
        _rule(
            "packet_fingerprinted_review",
            "Reviewer memo references packet SHA-256, accepted/rejected claims, and missing-evidence request.",
            "Screenshot demo, slide feedback, or anonymous comment without packet version.",
            "packet_sha256",
        ),
        _rule(
            "buyer_roi_validation",
            "Named buyer confirms a specific assumption used by the ROI model.",
            "Founder-modeled savings, generic procurement pain, or unverified insurance discount.",
            "confirmed_assumption",
        ),
        _rule(
            "capacity_or_underwriting_progress",
            "Carrier, reinsurer, MGA, broker, actuary, or counsel names a next-document or compliance gate.",
            "Curiosity about robotics risk without underwriting, capacity, actuarial, or legal next step.",
            "reviewer_next_gate",
        ),
        _rule(
            "research_or_internals_progress",
            "Source data, activation trace, or reviewer validation artifact closes a specific hypothesis workstream.",
            "Generated videos alone or local fixture metrics presented as partner validation.",
            "validated_hypothesis_id",
        ),
    ]


def _rule(rule: str, count: str, do_not_count: str, evidence_field: str) -> dict[str, str]:
    return {
        "rule": rule,
        "count": count,
        "do_not_count": do_not_count,
        "evidence_field": evidence_field,
    }


def _proof_gate_links(
    investor_proof_pipeline: dict[str, Any],
    buyer_roi_model: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
    research_validation_plan: dict[str, Any],
) -> list[dict[str, str]]:
    proof_gates = ", ".join(item.get("gate", "") for item in investor_proof_pipeline.get("proof_gates", [])[:3])
    roi_gates = ", ".join(item.get("gate", "") for item in buyer_roi_model.get("proof_gates", [])[:3])
    claim_gates = ", ".join(item.get("claim_id", "") for item in claim_validation_ledger.get("claims", [])[:4])
    research_gates = ", ".join(item.get("workstream", "") for item in research_validation_plan.get("validation_workstreams", [])[:3])
    return [
        {
            "source_artifact": investor_proof_pipeline.get("pipeline_id", "investor_proof_pipeline"),
            "traction_use": "Defines the external proof workflow and prevents meeting-only upgrades.",
            "linked_gates": proof_gates,
        },
        {
            "source_artifact": buyer_roi_model.get("roi_id", "buyer_roi_model"),
            "traction_use": "Turns buyer economics into assumptions that must be confirmed before value claims.",
            "linked_gates": roi_gates,
        },
        {
            "source_artifact": claim_validation_ledger.get("ledger_id", "claim_validation_ledger"),
            "traction_use": "Separates investor-safe claims from blocked overclaims during sales calls.",
            "linked_gates": claim_gates,
        },
        {
            "source_artifact": research_validation_plan.get("plan_id", "research_validation_plan"),
            "traction_use": "Maps technical diligence requests to falsifiable research workstreams.",
            "linked_gates": research_gates,
        },
    ]
