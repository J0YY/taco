"""Design-partner diligence plan for TACO seed fundraising."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


DESIGN_PARTNER_TRACKS: list[dict[str, Any]] = [
    {
        "track_id": "robotics_oem_predeployment",
        "partner_profile": "Robotics OEM deploying learned manipulation policies before fleet telemetry exists.",
        "buyer_question": "Can TACO turn replay failures and internal traces into evidence that de-risks enterprise deployment?",
        "pilot_artifacts": [
            "3-5 replayable failure certificates from the OEM policy",
            "activation or internal trace bundle for each primary certificate",
            "conditional quote worksheet with required controls and exclusions",
            "runtime monitor checklist for renewal evidence",
        ],
        "acceptance_criteria": [
            "OEM engineering lead can reproduce at least one failure certificate",
            "required controls map to deployable monitor or policy-gating changes",
            "risk team agrees the packet answers pre-deployment evidence gaps",
        ],
        "commercial_signal": "Signed design-partner memo or LOI to use TACO evidence in enterprise procurement or carrier review.",
    },
    {
        "track_id": "broker_mga_underwriting_desk",
        "partner_profile": "Broker, MGA, or specialty program team exploring robotics liability submissions.",
        "buyer_question": "Can TACO make learned-policy risk legible enough to triage submissions before loss history exists?",
        "pilot_artifacts": [
            "submission intake checklist",
            "data-room packet with packet/index.json checksum verification",
            "control-linked pricing deltas and exclusions",
            "claims and renewal loop example",
        ],
        "acceptance_criteria": [
            "broker or MGA can explain the quote conditions to an insured",
            "underwriter identifies which evidence would be required for bind/no-bind review",
            "packet format is acceptable for diligence-room handoff",
        ],
        "commercial_signal": "Broker/MGA letter naming TACO as an evidence intake layer for robotics submissions.",
    },
    {
        "track_id": "carrier_reinsurer_model_risk",
        "partner_profile": "Carrier, reinsurer, or risk-capital reviewer assessing autonomy underwriting methodology.",
        "buyer_question": "Can replay certificates plus internal-risk metrics support an auditable risk-control framework?",
        "pilot_artifacts": [
            "methodology memo with research anchors",
            "carrier-readiness DreamAudit evidence ladder",
            "packet verifier output and SHA-256 fingerprint",
            "exception list for controls disabled or evidence missing",
        ],
        "acceptance_criteria": [
            "reviewer can separate simulator evidence from live deployment assumptions",
            "reviewer can identify required actuarial/compliance work before real product launch",
            "reviewer agrees the evidence package is useful even before pricing filing",
        ],
        "commercial_signal": "Carrier or reinsurer feedback memo defining evidence gates for a paid pilot or fronting discussion.",
    },
]


def build_design_partner_plan(application: InsuranceApplication, quote: QuoteBreakdown) -> dict[str, Any]:
    """Return a structured plan for turning the demo into external diligence proof."""

    return {
        "plan_id": f"DP-{application.application_id}",
        "status": "external_validation_pending",
        "boundary": "This is a diligence plan, not evidence of signed design partners or insurance capacity.",
        "target_customer": application.company_name,
        "target_policy_id": application.policy_id,
        "coverage_context": {
            "coverage_requested_usd": application.coverage_requested_usd,
            "deployment_units": application.deployment_units,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "required_controls": list(quote.required_controls),
        },
        "tracks": DESIGN_PARTNER_TRACKS,
        "thirty_sixty_ninety_day_plan": [
            {
                "window": "30_days",
                "goal": "Secure three diligence conversations and run one transferred-packet walkthrough.",
                "evidence_to_collect": "Meeting notes, reviewer questions, packet-verifier screenshots, and missing-evidence list.",
            },
            {
                "window": "60_days",
                "goal": "Convert one robotics OEM or broker/MGA into a structured design-partner pilot.",
                "evidence_to_collect": "Pilot scope, named policy/task family, target controls, and data-access requirements.",
            },
            {
                "window": "90_days",
                "goal": "Produce one external memo or LOI that states which TACO artifacts changed underwriting or deployment review.",
                "evidence_to_collect": "Signed feedback memo, LOI, or redlined evidence checklist from the reviewer.",
            },
        ],
        "diligence_questions": [
            "Which evidence would make a learned-policy robotics submission bindable or procurement-ready?",
            "Which replay or internal-risk artifacts are confusing, missing, or overclaimed?",
            "Which controls need runtime proof before premium discounts are credible?",
            "What external compliance, actuarial, or capacity work is required before launch?",
        ],
    }


def design_partner_plan_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for the design-partner tracks."""

    return [
        {
            "Track": track["track_id"],
            "Partner Profile": track["partner_profile"],
            "Buyer Question": track["buyer_question"],
            "Commercial Signal": track["commercial_signal"],
        }
        for track in plan["tracks"]
    ]
