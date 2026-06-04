"""Buyer ROI diligence model for TACO commercial review."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_buyer_roi_model(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    renewal: dict[str, Any],
    commercial_model: dict[str, Any],
    external_validation_kit: dict[str, Any],
) -> dict[str, Any]:
    """Return modeled buyer economics without claiming guaranteed savings."""

    annual_taco_subscription_usd = 120_000
    implementation_services_usd = 45_000
    first_year_cost_usd = annual_taco_subscription_usd + implementation_services_usd
    monthly_premium = int(quote.final_monthly_premium_usd or 0)
    premium_delta_proxy = max(0, int(quote.metadata.get("no_controls_monthly_premium_usd", 0) or 0) - monthly_premium)
    if premium_delta_proxy == 0:
        premium_delta_proxy = max(0, monthly_premium // 2)
    prevented_loss = int(renewal.get("prevented_loss_usd", 0) or 0)
    incurred_loss = int(renewal.get("incurred_loss_usd", 0) or 0)
    risk_review_delay_days = 45
    launch_delay_cost_per_day_usd = 8_000
    evidence_ops_hours_saved = 160
    evidence_ops_hourly_cost_usd = 175
    review_cycle_reduction_value_usd = risk_review_delay_days * launch_delay_cost_per_day_usd
    evidence_ops_value_usd = evidence_ops_hours_saved * evidence_ops_hourly_cost_usd
    control_credit_value_usd = premium_delta_proxy * 12
    base_modeled_value_usd = review_cycle_reduction_value_usd + evidence_ops_value_usd + control_credit_value_usd + prevented_loss
    downside_value_usd = max(0, evidence_ops_value_usd + control_credit_value_usd // 2 - incurred_loss)
    upside_value_usd = base_modeled_value_usd + 2 * prevented_loss + review_cycle_reduction_value_usd
    return {
        "roi_id": f"ROI-{application.application_id}",
        "status": "modeled_buyer_economics_not_validated_savings",
        "boundary": "This is a buyer ROI diligence model, not guaranteed savings, signed customer demand, a procurement commitment, an insurance offer, or evidence that TACO reduced real losses.",
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "robot_type": application.robot_type,
            "deployment_units": application.deployment_units,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": monthly_premium,
        },
        "assumption_set": {
            "annual_taco_subscription_usd": annual_taco_subscription_usd,
            "implementation_services_usd": implementation_services_usd,
            "first_year_cost_usd": first_year_cost_usd,
            "risk_review_delay_days": risk_review_delay_days,
            "launch_delay_cost_per_day_usd": launch_delay_cost_per_day_usd,
            "evidence_ops_hours_saved": evidence_ops_hours_saved,
            "evidence_ops_hourly_cost_usd": evidence_ops_hourly_cost_usd,
            "control_credit_monthly_proxy_usd": premium_delta_proxy,
            "prevented_loss_evidence_usd": prevented_loss,
            "incurred_loss_evidence_usd": incurred_loss,
        },
        "buyer_value_drivers": [
            _driver(
                "robotics_oem_or_enterprise_risk",
                "Reduce pre-deployment risk-review delay by giving enterprise buyers replayable failures, controls, and renewal evidence.",
                review_cycle_reduction_value_usd,
                "Validate with procurement/risk reviewer cycle-time before and after a transferred-packet pilot.",
            ),
            _driver(
                "broker_or_mga_submission_desk",
                "Reduce underwriting-evidence assembly time and make control/exclusion conversations legible.",
                evidence_ops_value_usd,
                "Validate with broker/MGA time study and reviewer scorecard completion rate.",
            ),
            _driver(
                "carrier_or_reinsurer_model_risk",
                "Improve control-credit and exclusion discipline before capacity or actuarial review.",
                control_credit_value_usd,
                "Validate with carrier/reinsurer review of control effectiveness and actuarial readiness gates.",
            ),
            _driver(
                "claims_and_renewal_team",
                "Turn monitor events and incident logs into renewal and claims-loop evidence.",
                prevented_loss,
                "Validate with real staged-deployment prevented-loss and incurred-loss records.",
            ),
        ],
        "roi_scenarios": [
            _scenario("downside", downside_value_usd, first_year_cost_usd),
            _scenario("base", base_modeled_value_usd, first_year_cost_usd),
            _scenario("upside", upside_value_usd, first_year_cost_usd),
        ],
        "procurement_readiness": {
            "required_external_validation_status": external_validation_kit.get("status"),
            "commercial_model_id": commercial_model.get("model_id"),
            "base_modeled_arr_context_usd": commercial_model.get("base_case", {}).get("modeled_arr_usd"),
            "documents_to_collect": [
                "buyer ROI assumption confirmation",
                "review-cycle baseline and post-pilot cycle time",
                "evidence-assembly time study",
                "control-effectiveness acceptance memo",
                "permission-to-quote feedback status",
                "signed pilot scope, LOI, or procurement review memo",
            ],
        },
        "sensitivity_cases": [
            {
                "case": "no_launch_delay_value",
                "modeled_value_usd": evidence_ops_value_usd + control_credit_value_usd + prevented_loss,
                "interpretation": "TACO still needs evidence-ops or insurance-workflow value if buyers do not credit faster launch review.",
            },
            {
                "case": "no_control_credit_value",
                "modeled_value_usd": review_cycle_reduction_value_usd + evidence_ops_value_usd + prevented_loss,
                "interpretation": "Buyer ROI can remain positive if evidence-review workflow matters before actuarial control credits are approved.",
            },
            {
                "case": "loss_evidence_only",
                "modeled_value_usd": max(0, prevented_loss - incurred_loss),
                "interpretation": "Loss evidence alone is not enough for a procurement case until real prevented-loss records exist.",
            },
        ],
        "proof_gates": [
            {
                "gate": "buyer_confirms_delay_cost",
                "proof_required": "Named buyer confirms launch-review delay and daily cost range.",
            },
            {
                "gate": "reviewer_confirms_artifact_usefulness",
                "proof_required": "External validation capture scorecard passes artifact_usefulness and decision_authority gates.",
            },
            {
                "gate": "evidence_ops_time_study",
                "proof_required": "Broker, MGA, carrier, or OEM compares evidence assembly time with and without TACO packet.",
            },
            {
                "gate": "control_credit_validated",
                "proof_required": "Actuarial/carrier review accepts which controls can affect pricing, exclusions, or underwriting conditions.",
            },
            {
                "gate": "commercial_document_signed",
                "proof_required": "Pilot scope, LOI, data-access agreement, broker memo, or procurement review memo is signed.",
            },
        ],
        "open_roi_risks": [
            "Modeled launch-delay and evidence-ops values are unvalidated until a buyer supplies baseline workflow data.",
            "Control-credit value is a proxy from demo pricing sensitivity, not approved carrier pricing.",
            "Prevented-loss evidence comes from local runtime examples until staged-deployment logs are attached.",
            "Positive modeled ROI does not prove willingness to pay, budget authority, or procurement approval.",
        ],
    }


def buyer_value_driver_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly rows for buyer value drivers."""

    return [
        {
            "Buyer": item["buyer"],
            "Value Driver": item["value_driver"],
            "Modeled Value": item["modeled_value_usd"],
            "Validation Needed": item["validation_needed"],
        }
        for item in model["buyer_value_drivers"]
    ]


def buyer_roi_scenario_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly rows for ROI scenarios."""

    return [
        {
            "Scenario": item["scenario"],
            "Modeled Value": item["modeled_value_usd"],
            "First-Year Cost": item["first_year_cost_usd"],
            "Net Value": item["net_value_usd"],
            "Payback Months": item["payback_months"],
        }
        for item in model["roi_scenarios"]
    ]


def buyer_roi_proof_rows(model: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for ROI proof gates."""

    return [
        {
            "Gate": item["gate"],
            "Proof Required": item["proof_required"],
        }
        for item in model["proof_gates"]
    ]


def _driver(buyer: str, value_driver: str, modeled_value_usd: int, validation_needed: str) -> dict[str, Any]:
    return {
        "buyer": buyer,
        "value_driver": value_driver,
        "modeled_value_usd": modeled_value_usd,
        "validation_needed": validation_needed,
    }


def _scenario(scenario: str, modeled_value_usd: int, first_year_cost_usd: int) -> dict[str, Any]:
    net_value = modeled_value_usd - first_year_cost_usd
    monthly_value = modeled_value_usd / 12 if modeled_value_usd > 0 else 0
    payback_months = round(first_year_cost_usd / monthly_value, 1) if monthly_value else None
    return {
        "scenario": scenario,
        "modeled_value_usd": modeled_value_usd,
        "first_year_cost_usd": first_year_cost_usd,
        "net_value_usd": net_value,
        "payback_months": payback_months,
    }
