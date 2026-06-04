"""Seed financing plan for TACO investor diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


TARGET_SEED_RAISE_USD = 5_000_000
RUNWAY_MONTHS = 18


USE_OF_FUNDS: list[dict[str, Any]] = [
    {
        "category": "engineering_internals_integration",
        "amount_usd": 1_450_000,
        "purpose": "Ship production DreamAudit ingestion, activation capture, trace scoring, packet verification, and reviewer APIs.",
        "diligence_evidence": "Real certificate corpus, activation NPZ traces, packet checksums, and passing verifier tests.",
    },
    {
        "category": "robotics_evidence_generation",
        "amount_usd": 900_000,
        "purpose": "Expand simulator and policy-evaluation coverage across robot families, task families, and failure modes.",
        "diligence_evidence": "40+ replay videos now, then partner-specific suites with source paths and reproducible commands.",
    },
    {
        "category": "carrier_broker_design_partners",
        "amount_usd": 950_000,
        "purpose": "Run structured broker, MGA, carrier, reinsurer, OEM, and enterprise risk-team pilots.",
        "diligence_evidence": "Signed pilot scopes, reviewer memos, LOIs, and bind/no-bind evidence checklists.",
    },
    {
        "category": "insurance_compliance_actuarial",
        "amount_usd": 1_050_000,
        "purpose": "Prepare filings, capacity partnerships, actuarial assumptions, compliance review, and claims/renewal operations.",
        "diligence_evidence": "Coverage-form review, actuarial memo, fronting or MGA path, and renewal evidence workflow.",
    },
    {
        "category": "gtm_operations_security",
        "amount_usd": 650_000,
        "purpose": "Build the secure data-room workflow, enterprise procurement motion, support operations, and security controls.",
        "diligence_evidence": "SOC2-style control backlog, enterprise buyer packet workflow, and customer security review responses.",
    },
]


MILESTONE_GATES: list[dict[str, Any]] = [
    {
        "gate": "0_to_90_days",
        "milestone": "Convert the current demo into two transferred-packet diligence pilots.",
        "success_metric": "Two external reviewers verify packet/index.json and provide written artifact-gap feedback.",
        "capital_dependency": "Design-partner and engineering integration budget.",
    },
    {
        "gate": "90_to_180_days",
        "milestone": "Attach live DreamAudit and activation traces to at least one partner policy family.",
        "success_metric": "Partner-specific certificates, real activation NPZ files, and control-linked quote worksheet.",
        "capital_dependency": "Engineering internals integration and robotics evidence generation budget.",
    },
    {
        "gate": "180_to_270_days",
        "milestone": "Turn reviewer feedback into a paid pilot or signed LOI with a broker, MGA, carrier, or OEM.",
        "success_metric": "Signed commercial document naming TACO artifacts used in underwriting or deployment review.",
        "capital_dependency": "Carrier/broker design-partner budget and GTM operations.",
    },
    {
        "gate": "270_to_365_days",
        "milestone": "Define the launch path for coverage capacity, compliance, and claims/renewal operations.",
        "success_metric": "Actuarial/compliance memo plus fronting, MGA, carrier, reinsurer, or referral-partner path.",
        "capital_dependency": "Insurance compliance and actuarial budget.",
    },
]


def build_seed_financing_plan(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    readiness: dict[str, Any] | None = None,
    design_partner_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable seed financing and milestone plan."""

    readiness_score = int(readiness.get("score", 0) or 0) if readiness else None
    design_partner_status = design_partner_plan.get("status") if design_partner_plan else "not_attached"
    return {
        "plan_id": f"SEED-{application.application_id}",
        "status": "proposed_financing_plan",
        "boundary": "This is a proposed use-of-funds and milestone plan, not committed financing, revenue, insurance capacity, or signed customer demand.",
        "target_raise_usd": TARGET_SEED_RAISE_USD,
        "estimated_runway_months": RUNWAY_MONTHS,
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "required_controls": list(quote.required_controls),
        },
        "current_diligence_posture": {
            "readiness_score": readiness_score,
            "design_partner_status": design_partner_status,
            "external_validation_required": True,
        },
        "use_of_funds": USE_OF_FUNDS,
        "milestone_gates": MILESTONE_GATES,
        "fundraise_questions": [
            "Can a reviewer verify that evidence came from DreamAudit certificates or recorded activations rather than a hardcoded demo path?",
            "Which design-partner memo would make the wedge credible to a carrier, broker, MGA, or robotics OEM?",
            "What insurance-capacity path is required before TACO can move from evidence workflow to live product?",
            "Which milestone should unlock the next tranche of hiring or infrastructure spend?",
        ],
        "investor_diligence_asks": [
            "Review the data-room packet and checksum index.",
            "Inspect live DreamAudit intake results and source paths.",
            "Inspect activation-recorder traces or partner-specific trace exports.",
            "Review design-partner plan status, external feedback, and signed commercial documents when available.",
            "Review compliance, actuarial, and capacity assumptions before treating quotes as launch-ready pricing.",
        ],
        "risk_register": [
            {
                "risk": "External validation is still pending.",
                "mitigation": "Use the 30/60/90 design-partner plan to collect signed reviewer memos or LOIs.",
            },
            {
                "risk": "Research-backed evidence is not the same as filed actuarial pricing.",
                "mitigation": "Fund actuarial/compliance work and keep demo quote boundaries explicit in every packet.",
            },
            {
                "risk": "Simulator and activation evidence may not transfer across every robot policy family.",
                "mitigation": "Require partner-specific certificates, source paths, and calibrated trace bundles before underwriting claims.",
            },
        ],
    }


def seed_financing_use_of_funds_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly use-of-funds rows."""

    return [
        {
            "Category": item["category"],
            "Amount": item["amount_usd"],
            "Purpose": item["purpose"],
            "Diligence Evidence": item["diligence_evidence"],
        }
        for item in plan["use_of_funds"]
    ]


def seed_financing_milestone_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly milestone rows."""

    return [
        {
            "Gate": item["gate"],
            "Milestone": item["milestone"],
            "Success Metric": item["success_metric"],
            "Capital Dependency": item["capital_dependency"],
        }
        for item in plan["milestone_gates"]
    ]
