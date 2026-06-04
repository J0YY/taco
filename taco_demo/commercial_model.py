"""Commercial scale model for TACO seed diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


MARKET_SOURCES: list[dict[str, str]] = [
    {
        "source_id": "ifr_world_robotics_2025",
        "title": "International Federation of Robotics - World Robotics 2025 Industrial Robots",
        "url": "https://ifr.org/news/global-robot-demand-in-factories-doubles-over-10-years/1st-quarterly-newsletter-2015",
        "fact_used": "IFR reported 542,000 industrial robot installations in 2024, 4.664 million industrial robots in operational use, and a forecast above 700,000 annual installations by 2028.",
    },
    {
        "source_id": "naic_pc_2024_results",
        "title": "NAIC - U.S. Property & Casualty and Title Insurance Industries 2024 Full Year Results",
        "url": "https://content.naic.org/sites/default/files/2024-annual-property-casualty-and-title-insurance-industries-analysis-report.pdf",
        "fact_used": "NAIC reported U.S. P&C direct premiums written of about $1.1T in 2024, with commercial liability-related lines such as other liability occurrence, commercial auto liability, and commercial multi-peril liability each measured in tens of billions of dollars.",
    },
]


def build_commercial_scale_model(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    readiness: dict[str, Any],
    seed_financing_plan: dict[str, Any],
    pilot_walkthrough: dict[str, Any],
) -> dict[str, Any]:
    """Return a bounded market and go-to-market model for investor diligence."""

    required_controls = list(quote.required_controls)
    seed_target = int(seed_financing_plan.get("target_raise_usd", 0) or 0)
    base_platform_fee = 150_000
    base_packet_fee = 20_000
    base_accounts = 20
    base_packets = 40
    scenarios = [
        _scenario(
            "conservative_design_partner_services",
            8,
            75_000,
            0,
            0,
            "Design-partner and evidence-integration revenue only; useful if insurance capacity path takes longer.",
        ),
        _scenario(
            "base_evidence_platform",
            base_accounts,
            base_platform_fee,
            base_packets,
            base_packet_fee,
            "Broker/OEM/carrier evidence workbench with packet fees for transferred underwriting reviews.",
        ),
        _scenario(
            "breakout_underwriting_network",
            50,
            250_000,
            150,
            35_000,
            "Multiple buyer categories reuse TACO packet formats across robotics policy families.",
        ),
    ]
    base_arr = next(item["modeled_arr_usd"] for item in scenarios if item["scenario_id"] == "base_evidence_platform")
    return {
        "model_id": f"COMM-{application.application_id}",
        "status": "scenario_model_not_revenue_forecast",
        "boundary": "This is a directional commercial scenario model, not a market-size audit, committed revenue, signed pipeline, insurance capacity, or an actuarial filing.",
        "target_raise_usd": seed_target,
        "target_customer_context": {
            "company_name": application.company_name,
            "robot_type": application.robot_type,
            "deployment_units": application.deployment_units,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "required_controls": required_controls,
        },
        "market_context": [
            {
                "context": "robot_deployment_scale",
                "source_id": "ifr_world_robotics_2025",
                "evidence": "Industrial robot deployment is large and still expanding, with IFR reporting 542,000 installations in 2024 and 4.664M units in operational use.",
                "taco_implication": "Even a narrow autonomy-risk evidence wedge can start with robotics teams that need pre-deployment risk review before field telemetry exists.",
            },
            {
                "context": "insurance_premium_context",
                "source_id": "naic_pc_2024_results",
                "evidence": "U.S. P&C premium volume and commercial liability lines are large enough that specialized evidence workflows can matter before TACO ever carries risk.",
                "taco_implication": "The first commercial product can sell evidence infrastructure to brokers, MGAs, carriers, OEMs, and enterprise risk teams rather than immediately underwriting on balance sheet.",
            },
        ],
        "buyer_segments": [
            _segment(
                "robotics_oem_risk_team",
                "Robotics OEM shipping learned policies into enterprise environments.",
                "Needs a defensible risk packet before procurement, legal, or insurance review.",
                "Evidence workbench plus DreamAudit/activation integration.",
                "Annual platform fee plus per-policy evidence packet fee.",
                "Pilot walkthrough produces partner-specific certificates, activation traces, and accepted/missing claim list.",
            ),
            _segment(
                "broker_mga_program_team",
                "Specialty broker, MGA, or program administrator receiving robotics submissions.",
                "Needs a repeatable triage artifact for risks that lack claims history.",
                "Submission intake, packet verifier, quote worksheet, and control/exclusion map.",
                "Seat/platform fee, packet fee, or referral workflow before licensed commission economics.",
                "Reviewer memo states whether TACO artifacts improve bind/no-bind triage.",
            ),
            _segment(
                "carrier_reinsurer_model_risk",
                "Carrier, reinsurer, or capacity reviewer assessing autonomy exposure.",
                "Needs boundaries around simulation evidence, internals, pricing, and policy wording.",
                "Methodology map, pricing diligence, objection register, and evidence-depth ladder.",
                "Enterprise review fee or paid pilot tied to model-risk and capacity-gate work.",
                "Named evidence gates for actuarial, compliance, and source-data review.",
            ),
            _segment(
                "enterprise_procurement_risk",
                "Enterprise buyer deciding whether to deploy autonomous robotics vendors.",
                "Needs deployment risk evidence before operational loss history exists.",
                "Vendor risk packet, required controls, renewal monitor plan, and incident workflow.",
                "Per-vendor review fee or enterprise risk platform subscription.",
                "Procurement/risk team says which TACO artifacts change deployment approval.",
            ),
        ],
        "revenue_scenarios": scenarios,
        "base_case": {
            "modeled_arr_usd": base_arr,
            "seed_raise_multiple": round(base_arr / seed_target, 2) if seed_target else None,
            "accounts": base_accounts,
            "platform_fee_usd": base_platform_fee,
            "packet_fees": base_packets,
            "packet_fee_usd": base_packet_fee,
        },
        "seed_round_commercial_gates": [
            {
                "gate": "first_two_external_walkthroughs",
                "proof_required": "Two reviewers verify packet/index.json and complete the pilot walkthrough evidence capture form.",
                "linked_artifact": pilot_walkthrough.get("playbook_id", "pilot_walkthrough_playbook"),
            },
            {
                "gate": "first_paid_design_partner",
                "proof_required": "A broker, OEM, carrier, reinsurer, or enterprise risk team signs a paid pilot or scoped evidence-integration agreement.",
                "linked_artifact": seed_financing_plan.get("plan_id", "seed_financing_plan"),
            },
            {
                "gate": "repeatable_policy_family",
                "proof_required": "At least one robot policy family has partner-specific certificates, activation traces, pricing sensitivity, and accepted/missing claims from reviewer feedback.",
                "linked_artifact": "manifest.json",
            },
            {
                "gate": "capacity_or_referral_path",
                "proof_required": "A carrier, MGA, broker, reinsurer, or referral partner names the compliance and capacity path required before live insurance launch.",
                "linked_artifact": "commercial/pilot_walkthrough_playbook.json",
            },
        ],
        "source_material": MARKET_SOURCES,
        "assumptions_to_validate": [
            "Evidence-platform fees are collectible before TACO becomes a licensed insurance producer, MGA, or carrier partner.",
            "Robotics OEMs and enterprise risk teams will pay for pre-deployment evidence even when insurance capacity is still pending.",
            "Brokers, MGAs, carriers, or reinsurers will accept packet verification and source paths as a useful intake standard.",
            "Per-policy packet fees scale only if DreamAudit and activation capture reduce marginal evidence-production labor.",
            "Insurance commissions, underwriting profit, or risk-bearing economics are excluded until licensing and capacity structure are resolved.",
        ],
        "why_five_million_can_be_rational": [
            f"The proposed ${seed_target:,.0f} round funds the highest-risk proof gates: live internals, broader evidence generation, external pilots, actuarial/compliance work, and secure data-room operations.",
            "The base scenario does not require TACO to carry insurance risk; it models evidence-platform revenue from the workflows already represented in the data room.",
            "The commercial upside is tied to repeatable artifact format and buyer workflow reuse, not just one Apex Robotics quote.",
        ],
    }


def commercial_market_rows(model: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly market-context rows."""

    return [
        {
            "Context": item["context"],
            "Source": item["source_id"],
            "Evidence": item["evidence"],
            "TACO Implication": item["taco_implication"],
        }
        for item in model["market_context"]
    ]


def commercial_segment_rows(model: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly buyer segment rows."""

    return [
        {
            "Segment": item["segment_id"],
            "Buyer": item["buyer"],
            "Pain": item["pain"],
            "First Product": item["first_product"],
            "Commercial Motion": item["commercial_motion"],
            "Proof Gate": item["proof_gate"],
        }
        for item in model["buyer_segments"]
    ]


def commercial_scenario_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly revenue scenario rows."""

    return [
        {
            "Scenario": item["scenario_id"],
            "Accounts": item["accounts"],
            "Platform Fee": item["platform_fee_usd"],
            "Packet Fees": item["packet_fees"],
            "Packet Fee": item["packet_fee_usd"],
            "Modeled ARR": item["modeled_arr_usd"],
            "Boundary": item["boundary"],
        }
        for item in model["revenue_scenarios"]
    ]


def commercial_gate_rows(model: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly commercial proof gates."""

    return [
        {
            "Gate": item["gate"],
            "Proof Required": item["proof_required"],
            "Linked Artifact": item["linked_artifact"],
        }
        for item in model["seed_round_commercial_gates"]
    ]


def _scenario(
    scenario_id: str,
    accounts: int,
    platform_fee_usd: int,
    packet_fees: int,
    packet_fee_usd: int,
    boundary: str,
) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "accounts": accounts,
        "platform_fee_usd": platform_fee_usd,
        "packet_fees": packet_fees,
        "packet_fee_usd": packet_fee_usd,
        "modeled_arr_usd": accounts * platform_fee_usd + packet_fees * packet_fee_usd,
        "boundary": boundary,
    }


def _segment(
    segment_id: str,
    buyer: str,
    pain: str,
    first_product: str,
    commercial_motion: str,
    proof_gate: str,
) -> dict[str, str]:
    return {
        "segment_id": segment_id,
        "buyer": buyer,
        "pain": pain,
        "first_product": first_product,
        "commercial_motion": commercial_motion,
        "proof_gate": proof_gate,
    }
