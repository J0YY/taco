"""Insurance capacity and compliance roadmap for TACO diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


REGULATORY_SOURCES: list[dict[str, str]] = [
    {
        "source_id": "naic_industry_rate_form_licensing",
        "title": "NAIC Industry resources - SERFF, UCAA, NIPR, rate and form filing",
        "url": "https://content.naic.org/industry",
        "fact_used": "NAIC identifies SERFF as a web-based rate/form filing system and describes UCAA and NIPR pathways for carrier and producer licensing workflows.",
    },
    {
        "source_id": "naic_state_licensing_handbook",
        "title": "NAIC State Licensing Handbook",
        "url": "https://content.naic.org/sites/default/files/inline-files/State%20Licensing%20Handbook%20-%20Complete%20and%20Final.pdf",
        "fact_used": "NAIC describes U.S. insurance regulation as state-based and frames producer licensing around state standards, reciprocity, and uniformity work.",
    },
    {
        "source_id": "naic_mga_model_225",
        "title": "NAIC Managing General Agents Act, Model 225",
        "url": "https://content.naic.org/sites/default/files/model-law-225.pdf",
        "fact_used": "The NAIC model act frames MGA status around managing insurer business, underwriting authority, required contracts, insurer duties, and examination authority.",
    },
    {
        "source_id": "washington_pc_rate_form_example",
        "title": "Washington Office of the Insurance Commissioner - Property and casualty rate and form filing instructions",
        "url": "https://www.insurance.wa.gov/insurers-regulated-entities/rate-and-form-filing/property-and-casualty-rate-and-form-filing-instructions",
        "fact_used": "Washington publishes P&C rate and form filing instructions and lists examples of policy forms, rates, rules, and filing exceptions, illustrating that requirements are state and line specific.",
    },
]


def build_capacity_roadmap(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    pricing_diligence: dict[str, Any],
    commercial_model: dict[str, Any],
    pilot_walkthrough: dict[str, Any],
) -> dict[str, Any]:
    """Return a non-legal insurance-capacity roadmap for investor diligence."""

    controls = list(quote.required_controls)
    return {
        "roadmap_id": f"CAP-{application.application_id}",
        "status": "capacity_path_defined_not_committed",
        "boundary": "This is a diligence roadmap, not legal advice, regulatory approval, admitted or surplus-lines authority, carrier capacity, reinsurance capacity, an insurance offer, or a filed product.",
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "quote_status": quote.status,
            "required_controls": controls,
        },
        "recommended_sequence": [
            {
                "phase": "phase_0_evidence_vendor",
                "posture": "Sell evidence workflow and data-room verification without soliciting, binding, or adjusting insurance.",
                "allowed_outputs_to_validate": [
                    "DreamAudit and activation evidence intake",
                    "packet verification and diligence memo",
                    "control/exclusion worksheet marked non-binding",
                    "reviewer evidence capture forms",
                ],
                "blocked_outputs_until_approved": [
                    "policy sale or solicitation",
                    "binder issuance for real insureds",
                    "claims adjustment",
                    "use of demo quote as filed rate",
                ],
                "proof_to_collect": "Counsel memo confirming evidence-only scope and customer-facing disclaimers.",
            },
            {
                "phase": "phase_1_referral_or_producer_path",
                "posture": "Partner with a licensed broker, producer, or referral partner for customer conversations involving insurance placement.",
                "allowed_outputs_to_validate": [
                    "producer/broker workflow handoff",
                    "submission packet standard",
                    "referral economics and compliance controls",
                ],
                "blocked_outputs_until_approved": [
                    "commission receipt without licensing review",
                    "state-specific solicitation without licensed partner",
                ],
                "proof_to_collect": "Producer licensing or referral memo, state-by-state operating rules, and appointed partner agreement.",
            },
            {
                "phase": "phase_2_mga_or_fronting_path",
                "posture": "Define whether TACO becomes an MGA/MGU-style underwriting evidence layer for a licensed carrier or fronting partner.",
                "allowed_outputs_to_validate": [
                    "underwriting authority term sheet",
                    "MGA agreement checklist",
                    "claims-handling boundary",
                    "premium trust and fiduciary-control design",
                ],
                "blocked_outputs_until_approved": [
                    "binding authority",
                    "claims payment or reinsurance negotiation",
                    "carrier paper usage",
                ],
                "proof_to_collect": "Carrier/fronting partner term sheet, MGA counsel checklist, authority matrix, and controls evidence.",
            },
            {
                "phase": "phase_3_rate_form_capacity_launch",
                "posture": "Prepare state, line, admitted/surplus-lines, rate/form, actuarial, claims, and reinsurance launch materials.",
                "allowed_outputs_to_validate": [
                    "policy-form and endorsement drafts",
                    "actuarial support memo",
                    "SERFF or state filing plan when applicable",
                    "claims and renewal operations",
                    "capacity or reinsurance evidence gate",
                ],
                "blocked_outputs_until_approved": [
                    "live insurance offer",
                    "filed rate claims",
                    "coverage representation outside approved authority",
                ],
                "proof_to_collect": "Capacity commitment, filing counsel plan, actuarial memo, claims operations plan, and approved customer-facing wording.",
            },
        ],
        "capacity_paths": [
            _capacity_path(
                "evidence_vendor",
                "Fastest near-term revenue path; avoids claiming insurance authority.",
                "No risk-bearing economics; must keep non-binding boundaries visible.",
                "Counsel-approved evidence-only workflow and customer disclaimers.",
            ),
            _capacity_path(
                "licensed_broker_or_referral_partner",
                "Lets TACO enter real insurance conversations through licensed channels.",
                "Economics and control of customer workflow depend on partner structure and state rules.",
                "NIPR/producer licensing or referral-partner compliance memo.",
            ),
            _capacity_path(
                "mga_mgu_fronting",
                "Turns TACO evidence into delegated underwriting workflow if a carrier/fronting partner grants authority.",
                "Requires carrier oversight, written authority, fiduciary controls, claims boundaries, and compliance review.",
                "Carrier term sheet, MGA agreement checklist, authority matrix, and controls audit.",
            ),
            _capacity_path(
                "carrier_reinsurer_product_path",
                "Largest long-term upside if TACO becomes an underwriting standard or product layer.",
                "Slowest path; requires capacity, filings, actuarial support, policy wording, and operational maturity.",
                "Capacity commitment, actuarial memo, state filing plan, and claims/renewal playbook.",
            ),
        ],
        "regulatory_workstreams": [
            {
                "workstream": "licensing_and_customer_communications",
                "source_ids": ["naic_state_licensing_handbook", "naic_industry_rate_form_licensing"],
                "diligence_question": "Which customer conversations are evidence-only, referral, producer, MGA, or carrier activities?",
                "required_artifacts": [
                    "customer-facing disclaimer set",
                    "licensed-partner map",
                    "state-by-state workflow memo",
                ],
            },
            {
                "workstream": "mga_authority_and_controls",
                "source_ids": ["naic_mga_model_225"],
                "diligence_question": "Does TACO manage insurer business, accept/reject risk, handle claims, or negotiate reinsurance?",
                "required_artifacts": [
                    "underwriting authority matrix",
                    "written agreement checklist",
                    "fiduciary/premium handling controls",
                    "claims-handling boundary",
                ],
            },
            {
                "workstream": "rate_form_and_policy_wording",
                "source_ids": ["naic_industry_rate_form_licensing", "washington_pc_rate_form_example"],
                "diligence_question": "Which state, line, admitted/surplus-lines, rate/rule, and policy-form requirements apply?",
                "required_artifacts": [
                    "line-of-business classification memo",
                    "policy form and endorsement drafts",
                    "SERFF/state filing plan when applicable",
                    "actuarial support memo",
                ],
            },
            {
                "workstream": "claims_renewal_and_data_governance",
                "source_ids": ["naic_industry_rate_form_licensing"],
                "diligence_question": "Who owns claims operations, renewal evidence, customer data, and regulator-facing records?",
                "required_artifacts": [
                    "claims intake and escalation SOP",
                    "renewal evidence retention policy",
                    "security and data-access control map",
                    "audit trail for packet verification and source evidence",
                ],
            },
        ],
        "readiness_gates": [
            {
                "gate": "evidence_only_counsel_memo",
                "status": "needed_before_paid_customer_rollout",
                "proof_required": "Counsel confirms TACO can sell evidence workflow without insurance solicitation, binding, or claims activity.",
            },
            {
                "gate": "licensed_partner_path",
                "status": "needed_before_insurance_conversations",
                "proof_required": "Broker, producer, MGA, carrier, or referral partner operating rules are documented.",
            },
            {
                "gate": "mga_or_capacity_term_sheet",
                "status": "needed_before_binding_authority",
                "proof_required": "Carrier/fronting/reinsurance partner names delegated authority, controls, claims boundaries, and capacity limits.",
            },
            {
                "gate": "actuarial_and_filing_plan",
                "status": "needed_before_live_insurance_offer",
                "proof_required": "Line, state, rate/form, policy wording, actuarial support, and filing path are documented.",
            },
        ],
        "links_to_existing_artifacts": {
            "pricing_boundary": pricing_diligence.get("pricing_id", "commercial/pricing_diligence.json"),
            "commercial_model": commercial_model.get("model_id", "commercial/commercial_scale_model.json"),
            "pilot_walkthrough": pilot_walkthrough.get("playbook_id", "commercial/pilot_walkthrough_playbook.json"),
        },
        "source_material": REGULATORY_SOURCES,
        "open_risks": [
            "Insurance-law requirements vary by state, line of business, admitted/surplus-lines path, role, and customer communication.",
            "Evidence-platform revenue may still need legal review if customer communications imply coverage advice or placement.",
            "MGA or fronting economics require carrier oversight and written authority before any binding workflow.",
            "Demo quote logic cannot become live pricing without actuarial, filing, compliance, and capacity review.",
            "Claims, renewal, data retention, and regulator-facing audit trails need operating owners before launch.",
        ],
    }


def capacity_phase_rows(roadmap: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly launch phase rows."""

    return [
        {
            "Phase": phase["phase"],
            "Posture": phase["posture"],
            "Allowed Outputs": "; ".join(phase["allowed_outputs_to_validate"]),
            "Blocked Outputs": "; ".join(phase["blocked_outputs_until_approved"]),
            "Proof To Collect": phase["proof_to_collect"],
        }
        for phase in roadmap["recommended_sequence"]
    ]


def capacity_path_rows(roadmap: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly capacity path rows."""

    return [
        {
            "Path": path["path"],
            "Why It Matters": path["why_it_matters"],
            "Diligence Risk": path["diligence_risk"],
            "Proof Required": path["proof_required"],
        }
        for path in roadmap["capacity_paths"]
    ]


def regulatory_workstream_rows(roadmap: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly regulatory workstream rows."""

    return [
        {
            "Workstream": item["workstream"],
            "Source IDs": "; ".join(item["source_ids"]),
            "Diligence Question": item["diligence_question"],
            "Required Artifacts": "; ".join(item["required_artifacts"]),
        }
        for item in roadmap["regulatory_workstreams"]
    ]


def capacity_gate_rows(roadmap: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly readiness gates."""

    return [
        {
            "Gate": gate["gate"],
            "Status": gate["status"],
            "Proof Required": gate["proof_required"],
        }
        for gate in roadmap["readiness_gates"]
    ]


def _capacity_path(path: str, why_it_matters: str, diligence_risk: str, proof_required: str) -> dict[str, str]:
    return {
        "path": path,
        "why_it_matters": why_it_matters,
        "diligence_risk": diligence_risk,
        "proof_required": proof_required,
    }
