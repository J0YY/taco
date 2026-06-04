"""Seed round close plan for TACO fundraising diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_seed_round_close_plan(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    fundraise_readiness: dict[str, Any],
    seed_financing_plan: dict[str, Any],
    investor_proof_pipeline: dict[str, Any],
    commercial_traction_plan: dict[str, Any],
    commercial_unit_economics: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
) -> dict[str, Any]:
    """Return an operating plan for closing the proposed seed round."""

    target_raise = int(seed_financing_plan.get("target_raise_usd", 5_000_000) or 5_000_000)
    readiness_score = int(fundraise_readiness.get("score", 0) or 0)
    proof_score = int(investor_proof_pipeline.get("current_scores", {}).get("current_artifact_score", 0) or 0)
    evidence_score = int(claim_validation_ledger.get("evidence_score", 0) or 0)
    base_margin = _base_margin(commercial_unit_economics)
    safe_claims = [
        claim
        for claim in claim_validation_ledger.get("claims", [])
        if str(claim.get("evidence_level", "")).startswith(("artifact", "research", "local_demo"))
    ]
    status = (
        "seed_close_plan_ready_external_proof_pending"
        if readiness_score >= 80 and proof_score >= 70 and base_margin >= 60
        else "seed_close_plan_needs_more_evidence"
    )
    return {
        "close_plan_id": f"CLOSE-{application.application_id}",
        "status": status,
        "boundary": (
            "This is a fundraise operating plan, not committed financing, investor interest, signed customer demand, "
            "carrier capacity, actuarial approval, or a securities offering document."
        ),
        "target_raise_usd": target_raise,
        "target_runway_months": int(seed_financing_plan.get("estimated_runway_months", 18) or 18),
        "current_signal_stack": {
            "readiness_score": readiness_score,
            "proof_artifact_score": proof_score,
            "claim_evidence_score": evidence_score,
            "base_gross_margin_pct": base_margin,
            "monthly_conditional_premium_usd": quote.final_monthly_premium_usd,
            "target_pipeline_prospects": sum(int(item.get("target_prospects", 0) or 0) for item in commercial_traction_plan.get("icp_segments", [])),
            "safe_claim_count": len(safe_claims),
        },
        "minimum_close_package": _minimum_close_package(target_raise),
        "investor_segments": _investor_segments(),
        "weekly_close_motion": _weekly_close_motion(target_raise),
        "partner_meeting_prompts": _partner_meeting_prompts(application),
        "closing_gates": _closing_gates(base_margin),
        "no_count_rules": _no_count_rules(),
        "upgrade_path": [
            "Replace local fixture claims with live DreamAudit packet source paths for the lead investor data-room check.",
            "Attach at least two packet-fingerprinted written reviewer artifacts from different buyer categories.",
            "Show one paid evidence sprint or signed pilot scope that names the TACO packet artifacts used.",
            "Attach delivery-cost logs and sales-source attribution before upgrading modeled margin or CAC/payback claims.",
        ],
    }


def seed_round_investor_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return investor-segment rows for UI and memo rendering."""

    return [
        {
            "Segment": item["segment"],
            "Target Partners": item["target_partners"],
            "Lead Question": item["lead_question"],
            "Evidence To Lead With": item["evidence_to_lead_with"],
            "Disqualifier": item["disqualifier"],
        }
        for item in plan["investor_segments"]
    ]


def seed_round_week_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return weekly close-motion rows for UI and memo rendering."""

    return [
        {
            "Week": item["week"],
            "Objective": item["objective"],
            "Output": item["output"],
            "Decision Gate": item["decision_gate"],
        }
        for item in plan["weekly_close_motion"]
    ]


def seed_round_gate_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return close-gate rows for UI and memo rendering."""

    return [
        {
            "Gate": item["gate"],
            "Pass Condition": item["pass_condition"],
            "Evidence Source": item["evidence_source"],
            "Do Not Count": item["do_not_count"],
        }
        for item in plan["closing_gates"]
    ]


def seed_round_rule_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return no-count rule rows for UI and memo rendering."""

    return [
        {
            "Rule": item["rule"],
            "Do Not Count": item["do_not_count"],
            "Upgrade Evidence": item["upgrade_evidence"],
        }
        for item in plan["no_count_rules"]
    ]


def _base_margin(commercial_unit_economics: dict[str, Any]) -> int:
    for item in commercial_unit_economics.get("margin_scenarios", []):
        if item.get("scenario_id") == "base_packet_platform":
            return int(item.get("gross_margin_pct", 0) or 0)
    return 0


def _minimum_close_package(target_raise: int) -> list[dict[str, Any]]:
    return [
        {
            "package_item": "lead_partner_packet",
            "minimum": "One verified v20 data-room packet with checksum index, memo, live-evidence boundary, and no-overclaim ledger.",
            "why_it_matters": "Lets a lead partner diligence the evidence path without relying on a live narrated demo.",
        },
        {
            "package_item": "external_reviewer_proof",
            "minimum": "Two written, packet-fingerprinted reviewer artifacts across broker/MGA, carrier/reinsurer, OEM, or enterprise risk tracks.",
            "why_it_matters": "Converts product interest into third-party workflow evidence without pretending it is revenue.",
        },
        {
            "package_item": "commercial_conversion_proof",
            "minimum": "One paid evidence sprint, signed pilot scope, LOI, or permission-to-quote artifact naming TACO evidence objects.",
            "why_it_matters": "Shows the buyer does not just like the story; they can place the artifact in a real workflow.",
        },
        {
            "package_item": "technical_depth_proof",
            "minimum": "DreamAudit certificate intake plus recorded activation trace export path exercised with explicit layer-to-signal mapping.",
            "why_it_matters": "Closes the main technical objection that TACO is output-only scoring or a hardcoded insurance dashboard.",
        },
        {
            "package_item": "seed_use_of_funds_match",
            "minimum": f"${target_raise:,.0f} plan tied to 18-month milestones, hiring areas, and evidence upgrades.",
            "why_it_matters": "Makes the round size legible as a milestone plan rather than an arbitrary capital ask.",
        },
    ]


def _investor_segments() -> list[dict[str, Any]]:
    return [
        {
            "segment": "robotics_frontier_seed_leads",
            "target_partners": 12,
            "lead_question": "Can this become the default evidence layer for deploying learned robot policies?",
            "evidence_to_lead_with": "DreamAudit adapter, 40 replay examples, activation recorder, and packet verification.",
            "disqualifier": "Partner only wants generic robotics tooling and will not underwrite insurance or risk workflow wedge.",
        },
        {
            "segment": "insurtech_fintech_seed_leads",
            "target_partners": 10,
            "lead_question": "Can synthetic evidence create a new underwriting category before claims history exists?",
            "evidence_to_lead_with": "Conditional quote, pricing diligence, actuarial roadmap, capacity roadmap, and no-overclaim ledger.",
            "disqualifier": "Partner requires filed rates, live carrier capacity, or booked premium before seed.",
        },
        {
            "segment": "automation_enterprise_workflow_investors",
            "target_partners": 8,
            "lead_question": "Does the evidence packet unblock procurement, compliance, and risk reviews for autonomy buyers?",
            "evidence_to_lead_with": "Buyer ROI model, enterprise security plan, pilot walkthrough, and external validation capture kit.",
            "disqualifier": "Partner cannot connect the packet to procurement, safety, certification, or insurance workflows.",
        },
        {
            "segment": "strategic_insurance_and_robotics_angels",
            "target_partners": 15,
            "lead_question": "Will experienced operators introduce carrier, MGA, broker, reinsurer, or OEM reviewers?",
            "evidence_to_lead_with": "Investor proof pipeline, commercial traction plan, reviewer tracks, and seed milestone gates.",
            "disqualifier": "Conversation produces advice only, with no written review, intro, pilot scope, or permission-to-quote path.",
        },
    ]


def _weekly_close_motion(target_raise: int) -> list[dict[str, Any]]:
    return [
        {
            "week": "week_0_packet_freeze",
            "objective": "Freeze the packet, run tests, verify ZIP checksums, and produce a concise lead-partner memo.",
            "output": "Versioned data-room packet, diligence memo, and claim ledger with current boundaries.",
            "decision_gate": "No partner calls until the packet verifies locally and the no-overclaim ledger is current.",
        },
        {
            "week": "week_1_technical_and_buyer_validation",
            "objective": "Run reviewer walkthroughs with one robotics technical reviewer and one insurance workflow reviewer.",
            "output": "Two packet-fingerprinted written reviewer artifacts or explicit gap notes.",
            "decision_gate": "Advance only if reviewers can explain where TACO fits in their current deployment or underwriting workflow.",
        },
        {
            "week": "week_2_lead_partner_outreach",
            "objective": "Contact focused seed leads with the one-line thesis, packet link, and current external-proof status.",
            "output": "Partner meetings segmented by robotics, insurtech, enterprise workflow, and strategic operator fit.",
            "decision_gate": "Count only meetings where the partner engages with the packet, not generic pitch feedback.",
        },
        {
            "week": "week_3_partner_diligence",
            "objective": "Run live demo, DreamAudit/activation path walkthrough, and commercial milestone review with serious leads.",
            "output": "Lead-partner diligence checklist completion and open-risk list.",
            "decision_gate": "A credible lead must accept the current boundary between demo evidence and external validation gaps.",
        },
        {
            "week": "week_4_term_sheet_path",
            "objective": "Turn lead interest into a term-sheet path or explicit missing-proof request.",
            "output": "Term-sheet process, partner memo, or prioritized missing-proof request.",
            "decision_gate": f"Do not claim the ${target_raise:,.0f} round is in motion without a lead process or written IC path.",
        },
    ]


def _partner_meeting_prompts(application: InsuranceApplication) -> list[dict[str, str]]:
    return [
        {
            "prompt": "wedge",
            "question": f"If {application.company_name} had this packet before deployment, which approval, underwriting, or procurement step would it change?",
            "good_answer": "Reviewer names a specific bind/no-bind, safety, procurement, compliance, capacity, or deployment gate.",
        },
        {
            "prompt": "technical_depth",
            "question": "Which evidence object would you inspect first to decide whether this is real and not a dashboard?",
            "good_answer": "Reviewer asks for packet checksums, DreamAudit source paths, activation traces, replay commands, or control deltas.",
        },
        {
            "prompt": "commercial_pull",
            "question": "Would you pay for a packet walkthrough, evidence sprint, or platform subscription before TACO carries insurance risk?",
            "good_answer": "Reviewer identifies a budget owner, buying trigger, and written artifact they would need.",
        },
        {
            "prompt": "round_risk",
            "question": "What proof would make this a seed-lead conversation instead of an interesting robotics risk demo?",
            "good_answer": "Reviewer gives a concrete written-proof, customer-proof, capacity-proof, or technical-proof threshold.",
        },
    ]


def _closing_gates(base_margin: int) -> list[dict[str, str]]:
    return [
        {
            "gate": "packet_reproducibility",
            "pass_condition": "Fresh checkout can install requirements, bootstrap data, run pytest, import Streamlit, and verify the v20 ZIP packet.",
            "evidence_source": "technical_diligence_runbook and packet/index.json",
            "do_not_count": "Screenshots, slides, or an unverified exported ZIP.",
        },
        {
            "gate": "internals_based_path",
            "pass_condition": "Activation recorder can export calibrated traces for success/failure/mitigated rollouts into compute_internal_metrics.",
            "evidence_source": "activation_recorder tests and live trace export artifacts",
            "do_not_count": "Output-only scores or hand-labeled risk tables without recorded activation source metadata.",
        },
        {
            "gate": "external_workflow_pull",
            "pass_condition": "At least two external reviewers write that the packet would affect an underwriting, procurement, or deployment review.",
            "evidence_source": "external_validation_capture_kit and investor_proof_pipeline",
            "do_not_count": "Friendly calls, verbal interest, or intros without written artifact feedback.",
        },
        {
            "gate": "commercial_conversion",
            "pass_condition": "At least one paid scope, signed pilot/LOI, or permission-to-quote artifact names TACO evidence objects.",
            "evidence_source": "commercial_traction_plan",
            "do_not_count": "Pipeline, unsigned ARR, capacity interest, or modeled buyer ROI.",
        },
        {
            "gate": "unit_economics_believability",
            "pass_condition": f"Base packet-platform gross margin stays at or above 60% after delivery-cost logging; current modeled margin is {base_margin}%.",
            "evidence_source": "commercial_unit_economics",
            "do_not_count": "Risk-bearing insurance economics, underwriting profit, commissions, float, or unlicensed premium revenue.",
        },
    ]


def _no_count_rules() -> list[dict[str, str]]:
    return [
        {
            "rule": "investor_interest",
            "do_not_count": "Partner meeting, warm intro, or positive email.",
            "upgrade_evidence": "Lead process, written IC memo request, partner diligence checklist, or signed financing document.",
        },
        {
            "rule": "customer_demand",
            "do_not_count": "Verbal buyer excitement or generic robotics insurance need.",
            "upgrade_evidence": "Paid sprint, signed pilot scope, LOI, or permission-to-quote artifact naming TACO packet objects.",
        },
        {
            "rule": "technical_validation",
            "do_not_count": "Local fixture success or deterministic replay alone.",
            "upgrade_evidence": "Live DreamAudit source paths, recorded activations, packet checksum verification, and reviewer-run command outputs.",
        },
        {
            "rule": "insurance_capacity",
            "do_not_count": "Carrier curiosity, broker intro, or modeled premium.",
            "upgrade_evidence": "Licensed partner path, capacity term sheet, actuarial review, filing plan, or referral agreement.",
        },
    ]
