"""Actuarial readiness plan for turning TACO evidence into filed pricing work."""

from __future__ import annotations

from typing import Any

from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


ACTUARIAL_SOURCE_MATERIAL: list[dict[str, str]] = [
    {
        "source_id": "asop_53_pc_future_costs",
        "title": "ASOP No. 53 - Estimating Future Costs for Prospective Property/Casualty Risk Transfer and Risk Retention",
        "url": "https://www.actuarialstandardsboard.org/asops/estimating-future-costs-prospective-propertycasualty-risk-transfer-risk-retention/",
        "fact_used": "Future-cost estimates for P/C risk transfer consider loss and loss-adjustment expenses, operational expenses, reinsurance, cost of capital, methods, assumptions, exposure base, credibility, and disclosures.",
    },
    {
        "source_id": "asop_23_data_quality",
        "title": "ASOP No. 23 - Data Quality",
        "url": "https://www.actuarialstandardsboard.org/asops/data-quality/",
        "fact_used": "Actuarial work needs data selection, review, use, reliance, confidentiality, and disclosure controls; non-traditional and derived data still require quality review.",
    },
    {
        "source_id": "asop_56_modeling",
        "title": "ASOP No. 56 - Modeling",
        "url": "https://www.actuarialstandardsboard.org/wp-content/uploads/2020/01/asop056_195.pdf",
        "fact_used": "Models used for actuarial services need intended purpose, data and assumptions, governance and controls, validation, and communication of limitations.",
    },
    {
        "source_id": "asop_41_communications",
        "title": "ASOP No. 41 - Actuarial Communications",
        "url": "https://www.actuarialstandardsboard.org/asops/actuarial-communications/",
        "fact_used": "Actuarial communications should identify intended users, scope, assumptions, limitations, and appropriate disclosures.",
    },
]


def build_actuarial_readiness_plan(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    pricing_diligence: dict[str, Any],
    capacity_roadmap: dict[str, Any],
) -> dict[str, Any]:
    """Return a non-opinion actuarial readiness plan for carrier diligence."""

    failure_families = sorted({certificate.failure_type for certificate in certificates})
    metric_sources = sorted({metric.metrics_source for metric in metrics})
    mean_failure_rate = (
        sum(certificate.failure_rate_neighborhood for certificate in certificates) / len(certificates)
        if certificates
        else 0.0
    )
    mean_internal_risk = sum(metric.internal_risk_score for metric in metrics) / len(metrics) if metrics else 0.0
    return {
        "plan_id": f"ACT-{application.application_id}",
        "status": "actuarial_readiness_defined_not_opinion",
        "boundary": "This is an actuarial readiness plan, not an actuarial opinion, rate adequacy opinion, filed rate, insurance offer, loss reserve estimate, or carrier-approved pricing indication.",
        "coverage_context": {
            "application_id": application.application_id,
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "coverage_requested_usd": application.coverage_requested_usd,
            "deployment_units": application.deployment_units,
            "quote_id": quote.quote_id,
            "demo_monthly_premium_usd": quote.final_monthly_premium_usd,
            "quote_status": quote.status,
        },
        "current_evidence_summary": {
            "failure_certificate_count": len(certificates),
            "failure_families": failure_families,
            "internal_metric_count": len(metrics),
            "metric_sources": metric_sources,
            "mean_failure_rate_neighborhood": round(mean_failure_rate, 3),
            "mean_internal_risk_score": round(mean_internal_risk, 3),
            "pricing_artifact": pricing_diligence.get("pricing_id"),
            "capacity_artifact": capacity_roadmap.get("roadmap_id"),
        },
        "future_cost_elements": [
            _future_cost_element(
                "expected_loss_and_loss_adjustment_expense",
                "Claim frequency and severity by failure family, deployment unit, task family, and required control state.",
                "DreamAudit/live simulator certificates, staged-deployment incident logs, claims/near-miss logs, and control effectiveness evidence.",
                "Current demo has replay failures and incident examples, but no credible live loss history or carrier claim payments.",
            ),
            _future_cost_element(
                "underwriting_and_evidence_expense",
                "Cost to ingest evidence, verify packet chain-of-custody, review activations, and renew controls.",
                "Operator time study, packet-review workflow logs, broker/carrier review notes, and security-control cost model.",
                "Current packet shows workflow, not operating cost experience.",
            ),
            _future_cost_element(
                "risk_margin_and_cost_of_capital",
                "Capital load for thin data, model uncertainty, concentration, severity tail, and coverage wording uncertainty.",
                "Carrier/reinsurer capital model assumptions, capacity term sheet, and sensitivity study.",
                "Current demo has no capacity commitment or reinsurer capital view.",
            ),
            _future_cost_element(
                "reinsurance_or_capacity_cost",
                "Fronting, reinsurance, MGA/MGU, or carrier capacity cost once a launch path is selected.",
                "Capacity roadmap outputs, broker/carrier term sheet, reinsurance indications, and counsel-approved role structure.",
                "Current roadmap defines paths but no committed capacity.",
            ),
            _future_cost_element(
                "profit_and_contingency",
                "Provision for profit, contingencies, and operational uncertainty consistent with selected risk-transfer structure.",
                "Carrier pricing policy, target margin, expense model, and adverse deviation study.",
                "Current quote has transparent demo multipliers, not carrier profit provisions.",
            ),
        ],
        "data_readiness_gates": [
            _gate(
                "exposure_base_defined",
                "Select exposure bases that strongly relate to risk cost: robot-hours, task attempts, deployed units, task-family mix, and control-enabled runtime.",
                "No exposure denominator, or exposure is only deployment unit count.",
                "asop_53_pc_future_costs",
            ),
            _gate(
                "data_quality_reviewed",
                "Document source, completeness, reconciliation, confidentiality, derived-data logic, and limitations for certificates, traces, videos, incidents, and claims.",
                "Simulator certificates and activation traces are accepted without data-quality review.",
                "asop_23_data_quality",
            ),
            _gate(
                "model_purpose_and_limits_documented",
                "State which models estimate frequency, severity, control effectiveness, and uncertainty, with intended users and limitations.",
                "The quote engine is presented as an actuarial model without purpose, assumptions, validation, or limitations.",
                "asop_56_modeling",
            ),
            _gate(
                "credibility_and_complement_defined",
                "Define when DreamAudit/staged-deployment data become credible and what external complement of credibility is used until then.",
                "Thin simulator evidence is treated as fully credible loss experience.",
                "asop_53_pc_future_costs",
            ),
            _gate(
                "actuarial_communications_ready",
                "Prepare intended-user, scope, reliance, assumptions, limitations, and deviation/disclosure language before an actuary reviews outputs.",
                "Investor memo language is reused as an actuarial communication without disclosures.",
                "asop_41_communications",
            ),
        ],
        "credibility_ramp": [
            {
                "phase": "demo_fixture_only",
                "evidence": "Local replay certificates, local traces, generated videos, and transparent quote formula.",
                "actuarial_use": "Product discovery and reviewer education only.",
                "blocked_claims": ["rate adequacy", "loss estimate", "control discount validation", "carrier filing"],
            },
            {
                "phase": "live_dreamaudit_corpus",
                "evidence": "Carrier-ready DreamAudit scan with source paths, minimality, replay commands, and failure-family distribution.",
                "actuarial_use": "Candidate exposure segmentation and failure taxonomy validation.",
                "blocked_claims": ["claims severity calibration", "rate filing", "loss reserve estimate"],
            },
            {
                "phase": "activation_and_control_study",
                "evidence": "Recorded activation traces, control-on/control-off replay pairs, and staged monitor event logs.",
                "actuarial_use": "Control-effectiveness prior and underwriting condition validation.",
                "blocked_claims": ["premium discount without real-world effectiveness evidence"],
            },
            {
                "phase": "staged_deployment_experience",
                "evidence": "Robot-hours, task attempts, incidents, near misses, claims, prevented losses, and control compliance by customer.",
                "actuarial_use": "Frequency/severity estimation, credibility weighting, and model validation.",
                "blocked_claims": ["filed pricing until counsel/carrier/actuary approve assumptions and communications"],
            },
            {
                "phase": "carrier_filing_or_program_review",
                "evidence": "Actuarial memo, rate/form support, policy wording, claims process, capacity/reinsurance economics, and approved communications.",
                "actuarial_use": "Carrier/program launch diligence subject to jurisdiction, line, role, and partner structure.",
                "blocked_claims": ["none cleared by local repo alone"],
            },
        ],
        "model_validation_workstreams": [
            {
                "workstream": "frequency_model",
                "current_input": "failure_rate_neighborhood and failure-family counts from certificates.",
                "validation_needed": "Compare simulated failure rates with staged deployment incidents per exposure base.",
                "owner": "actuary_plus_robotics_risk",
            },
            {
                "workstream": "severity_model",
                "current_input": "minimal failure cost, scenario loss examples, and incident estimated losses.",
                "validation_needed": "Map failure families to claim severities, loss adjustment expenses, and coverage wording.",
                "owner": "actuary_plus_claims",
            },
            {
                "workstream": "control_effectiveness_model",
                "current_input": "quote-engine control toggles and mitigated replay traces.",
                "validation_needed": "Estimate real-world effectiveness and confidence intervals from control-on/control-off evidence.",
                "owner": "actuary_plus_safety_engineering",
            },
            {
                "workstream": "uncertainty_and_tail_model",
                "current_input": "open methodology risks, infrequent-event flags, and no-controls premium sensitivity.",
                "validation_needed": "Stress test rare severe losses, correlated fleet failures, and model-update drift.",
                "owner": "actuary_plus_reinsurer",
            },
        ],
        "filing_and_claims_handoff": [
            {
                "handoff": "actuarial_support_memo",
                "required_contents": [
                    "scope and intended users",
                    "future cost elements",
                    "data-quality review",
                    "model assumptions and limitations",
                    "credibility approach",
                    "rate/form and jurisdiction boundaries",
                ],
            },
            {
                "handoff": "claims_operations_feedback_loop",
                "required_contents": [
                    "claim cause taxonomy",
                    "coverage condition status at loss time",
                    "activation/control evidence retention",
                    "loss adjustment expense capture",
                    "renewal re-audit trigger",
                ],
            },
            {
                "handoff": "regulatory_or_program_packet",
                "required_contents": [
                    "approved customer-facing wording",
                    "capacity or fronting path",
                    "policy forms and exclusions",
                    "actuarial communication disclosures",
                    "security and privacy controls",
                ],
            },
        ],
        "source_material": ACTUARIAL_SOURCE_MATERIAL,
        "open_actuarial_risks": [
            "No actuary has reviewed or signed the demo quote as a future-cost estimate.",
            "No live loss, claims, exposure, or loss-adjustment-expense history is represented in the local repo.",
            "Control discounts are demo sensitivity outputs until real-world effectiveness and compliance evidence exist.",
            "Rate/form filing, unfair-discrimination review, capacity economics, and policy wording depend on jurisdiction and partner structure.",
        ],
    }


def actuarial_cost_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for future cost elements."""

    return [
        {
            "Element": item["element"],
            "Meaning": item["meaning"],
            "Evidence Needed": item["evidence_needed"],
            "Current Gap": item["current_gap"],
        }
        for item in plan["future_cost_elements"]
    ]


def actuarial_gate_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for actuarial data/model gates."""

    return [
        {
            "Gate": item["gate"],
            "Pass Condition": item["pass_condition"],
            "Fail Condition": item["fail_condition"],
            "Source Anchor": item["source_anchor"],
        }
        for item in plan["data_readiness_gates"]
    ]


def actuarial_credibility_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for credibility ramp phases."""

    return [
        {
            "Phase": item["phase"],
            "Evidence": item["evidence"],
            "Actuarial Use": item["actuarial_use"],
            "Blocked Claims": "; ".join(item["blocked_claims"]),
        }
        for item in plan["credibility_ramp"]
    ]


def actuarial_validation_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for model validation workstreams."""

    return [
        {
            "Workstream": item["workstream"],
            "Current Input": item["current_input"],
            "Validation Needed": item["validation_needed"],
            "Owner": item["owner"],
        }
        for item in plan["model_validation_workstreams"]
    ]


def _future_cost_element(element: str, meaning: str, evidence_needed: str, current_gap: str) -> dict[str, str]:
    return {
        "element": element,
        "meaning": meaning,
        "evidence_needed": evidence_needed,
        "current_gap": current_gap,
    }


def _gate(gate: str, pass_condition: str, fail_condition: str, source_anchor: str) -> dict[str, str]:
    return {
        "gate": gate,
        "pass_condition": pass_condition,
        "fail_condition": fail_condition,
        "source_anchor": source_anchor,
    }
