"""Competitive positioning artifact for investor diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_competitive_positioning(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    methodology_map: dict[str, Any],
    commercial_model: dict[str, Any],
    investor_proof_pipeline: dict[str, Any],
    methodology_validation_protocol: dict[str, Any],
) -> dict[str, Any]:
    """Return bounded competitive positioning for the TACO seed narrative."""

    safe_claims = [claim for claim in methodology_map.get("claims", []) if claim.get("status") != "needs_work"]
    return {
        "positioning_id": f"COMP-{application.application_id}",
        "status": "category_positioning_ready_needs_market_validation",
        "boundary": (
            "This is a strategic positioning artifact, not a market study, customer survey, win-rate analysis, "
            "procurement proof, competitor benchmark, signed demand, or evidence that buyers have accepted the category."
        ),
        "category_definition": {
            "category_name": "autonomy-risk evidence layer",
            "wedge": "pre-deployment learned-policy liability evidence for robotics insurance",
            "buyer": commercial_model.get("initial_buyer", "robotics OEM risk team, enterprise insurance buyer, broker, MGA, or carrier"),
            "job_to_be_done": (
                "Turn simulator failures, internal risk traces, controls, exclusions, and packet fingerprints into a "
                "reviewable insurance and diligence workflow before fleet telemetry exists."
            ),
            "current_proof_base": f"{len(safe_claims)} bounded methodology claims; target raise ${investor_proof_pipeline.get('target_raise_usd', 0):,.0f}.",
        },
        "why_now": _why_now(application, quote),
        "alternative_categories": _alternative_categories(),
        "wedge_strategy": _wedge_strategy(commercial_model, investor_proof_pipeline),
        "defensibility_hypotheses": _defensibility_hypotheses(methodology_validation_protocol),
        "do_not_claim": [
            "Do not claim TACO has displaced incumbents until buyer-reviewed competitive evidence exists.",
            "Do not claim insurers have accepted TACO as a required standard until signed carrier or broker artifacts exist.",
            "Do not claim a market category exists because the local demo has a complete packet.",
            "Do not claim pricing power, win rates, or buyer demand from modeled ARR or reviewer workflows alone.",
        ],
        "next_validation_actions": [
            "Ask each external reviewer which existing workflow TACO would replace, augment, or fail to fit.",
            "Attach two packet-fingerprinted reviewer memos that name the alternative they would otherwise use.",
            "Collect buyer-language evidence for whether TACO is sold as insurance evidence, robot QA, compliance, or model-risk infrastructure.",
            "Update the commercial model only after a reviewer or buyer names budget owner, current spend, and decision trigger.",
        ],
    }


def competitive_alternative_rows(positioning: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for alternative category comparison."""

    return [
        {
            "Alternative": item["alternative"],
            "Buyer Default": item["buyer_default"],
            "Where TACO Differs": item["where_taco_differs"],
            "Proof Needed": item["proof_needed"],
        }
        for item in positioning["alternative_categories"]
    ]


def competitive_wedge_rows(positioning: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for wedge strategy."""

    return [
        {
            "Step": item["step"],
            "Motion": item["motion"],
            "Buyer Proof": item["buyer_proof"],
            "Investor Readout": item["investor_readout"],
        }
        for item in positioning["wedge_strategy"]
    ]


def competitive_defensibility_rows(positioning: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for defensibility hypotheses."""

    return [
        {
            "Hypothesis": item["hypothesis"],
            "Mechanism": item["mechanism"],
            "Validation Gate": item["validation_gate"],
            "Failure Signal": item["failure_signal"],
        }
        for item in positioning["defensibility_hypotheses"]
    ]


def _why_now(application: InsuranceApplication, quote: QuoteBreakdown) -> list[dict[str, str]]:
    return [
        {
            "driver": "pre_deployment_robotics_gap",
            "evidence_in_packet": f"{application.company_name} is {application.deployment_stage} with telemetry_available={application.telemetry_available}.",
            "positioning_use": "Start where loss-history underwriting cannot answer the buyer's first question.",
        },
        {
            "driver": "simulator_and_dreamaudit_artifacts_are_packetizable",
            "evidence_in_packet": "Replay certificates, 40-video suite, DreamAudit adapter, and data-room verifier are attached.",
            "positioning_use": "Make robot failure evidence inspectable by non-simulator specialists.",
        },
        {
            "driver": "internals_can_become_underwriting_signals",
            "evidence_in_packet": "Activation recorder path and internal-risk metrics feed the quote and claim ledger.",
            "positioning_use": "Differentiate from output-only robot QA by pricing why the policy failed.",
        },
        {
            "driver": "controls_change_terms",
            "evidence_in_packet": f"Conditional quote ${quote.final_monthly_premium_usd:,.0f}/month with required controls and exclusions.",
            "positioning_use": "Turn safety evidence into insurance terms rather than standalone dashboards.",
        },
    ]


def _alternative_categories() -> list[dict[str, str]]:
    return [
        {
            "alternative": "traditional_insurance_underwriting",
            "buyer_default": "Wait for fleet telemetry, claims history, site surveys, and carrier underwriting appetite.",
            "where_taco_differs": "Creates pre-deployment evidence objects and control-linked terms before claims history exists.",
            "why_not_enough": "Loss-history workflows can block frontier policies when the robot is not deployed yet.",
            "proof_needed": "Broker/carrier memo that TACO shortens or improves an actual submission workflow.",
        },
        {
            "alternative": "robotics_simulation_or_qa_tools",
            "buyer_default": "Use simulator failures for engineering debug, model selection, or safety signoff.",
            "where_taco_differs": "Packages failures as underwriting certificates with controls, exclusions, quote deltas, and packet hashes.",
            "why_not_enough": "Engineering QA rarely maps directly to insurance terms, premium conditions, or binder exclusions.",
            "proof_needed": "Engineering reviewer confirms the evidence maps to risk transfer or procurement decisions.",
        },
        {
            "alternative": "ml_observability_or_model_monitoring",
            "buyer_default": "Monitor model behavior after deployment and alert on drift or incidents.",
            "where_taco_differs": "Links pre-deployment activations and mitigations to insurability before runtime telemetry exists.",
            "why_not_enough": "Post-deployment observability does not solve the first-policy underwriting gap alone.",
            "proof_needed": "Activation-incrementality endpoint beats output-only baselines in the validation protocol.",
        },
        {
            "alternative": "certification_or_safety_case_tooling",
            "buyer_default": "Prepare compliance, safety case, or certification evidence for auditors and regulators.",
            "where_taco_differs": "Focuses on underwriting artifacts, conditional coverage terms, and broker/carrier review workflows.",
            "why_not_enough": "Certification artifacts may not include premium deltas, exclusions, or carrier data-quality boundaries.",
            "proof_needed": "Reviewer memo classifies which safety-case artifacts are allowed, limited, or disallowed for underwriting.",
        },
        {
            "alternative": "broker_or_mga_submission_workflow",
            "buyer_default": "Package application, exposure, controls, loss runs, and narrative documents for markets.",
            "where_taco_differs": "Adds replayable learned-policy evidence and internals-based risk signatures to the submission file.",
            "why_not_enough": "Submission tooling does not create robot-policy evidence or validate simulator/control artifacts.",
            "proof_needed": "Broker or MGA names the packet fields they would include in a real market submission.",
        },
    ]


def _wedge_strategy(commercial_model: dict[str, Any], investor_proof_pipeline: dict[str, Any]) -> list[dict[str, str]]:
    base_arr = int(commercial_model.get("base_case", {}).get("modeled_arr_usd", 0) or 0)
    proof_gates = len(investor_proof_pipeline.get("proof_gates", []))
    return [
        {
            "step": "1_evidence_sprint",
            "motion": "Sell a bounded paid evidence sprint around one robot policy family.",
            "buyer_proof": "Packet walkthrough, replay certificates, quote sensitivity, and missing-evidence memo.",
            "investor_readout": "Proof of workflow urgency, not ARR or insurance capacity.",
        },
        {
            "step": "2_submission_packet",
            "motion": "Convert sprint outputs into broker, MGA, carrier, or enterprise risk submission artifacts.",
            "buyer_proof": f"{proof_gates} proof gates and packet SHA-256 review trail.",
            "investor_readout": "Proof that TACO can enter an existing insurance workflow.",
        },
        {
            "step": "3_repeatable_platform",
            "motion": "Standardize failure-family taxonomy, activation maps, controls, and reviewer requests across policies.",
            "buyer_proof": "Repeated source paths, accepted failure families, and claim ledger upgrades.",
            "investor_readout": f"Path to modeled base ARR ${base_arr:,.0f}, still not booked revenue.",
        },
        {
            "step": "4_capacity_or_certification_channel",
            "motion": "Partner with licensed insurance or certification channels after artifact acceptance.",
            "buyer_proof": "Carrier/reinsurer review scope, actuarial data-quality memo, or certification handoff.",
            "investor_readout": "Strategic leverage only after external artifacts are collected.",
        },
    ]


def _defensibility_hypotheses(methodology_validation_protocol: dict[str, Any]) -> list[dict[str, str]]:
    protocol_id = methodology_validation_protocol.get("protocol_id", "methodology_validation_protocol")
    return [
        {
            "hypothesis": "evidence_graph_compounds",
            "mechanism": "Certificates, traces, controls, exclusions, reviewer decisions, and claim downgrades accumulate around a shared schema.",
            "validation_gate": f"{protocol_id}: packet_review_utility and claim-ledger diff must pass.",
            "failure_signal": "Reviewers treat each packet as one-off consulting with no reusable schema value.",
        },
        {
            "hypothesis": "internals_create_non_obvious_signal",
            "mechanism": "Activation-derived warning and mitigation ranking add information beyond output labels.",
            "validation_gate": f"{protocol_id}: activation_incrementality_over_outputs must beat output-only baseline.",
            "failure_signal": "Output-only replay labels perform as well as activation features.",
        },
        {
            "hypothesis": "insurance_terms_are_the_distribution_channel",
            "mechanism": "Controls, exclusions, and re-audit triggers make safety work financially legible to buyers and carriers.",
            "validation_gate": f"{protocol_id}: control_effect_directionality plus reviewer feasibility must pass.",
            "failure_signal": "Buyers like the analysis but cannot connect it to procurement, risk transfer, or coverage terms.",
        },
        {
            "hypothesis": "packet_standard_becomes_workflow_lock_in",
            "mechanism": "Broker, carrier, OEM, and risk reviewers ask for the same packet fields across policies.",
            "validation_gate": "External proof registry must collect two role-distinct reviewer artifacts with packet SHA-256.",
            "failure_signal": "Each reviewer requests incompatible artifacts or only accepts their existing proprietary format.",
        },
    ]
