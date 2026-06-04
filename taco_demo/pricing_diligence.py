"""Pricing sensitivity and actuarial-boundary diligence helpers."""

from __future__ import annotations

from typing import Any

from .quote_engine import generate_quote
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


def build_pricing_diligence(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
) -> dict[str, Any]:
    """Return a pricing diligence artifact derived from quote-engine outputs."""

    metrics_by_cert = {metric.certificate_id: metric for metric in metrics}
    enabled_controls = {control: True for control in quote.required_controls}
    all_controls_quote = generate_quote(application, certificates, metrics_by_cert, enabled_controls)
    no_controls_quote = generate_quote(
        application,
        certificates,
        metrics_by_cert,
        {control: False for control in quote.required_controls},
    )
    control_sensitivities = []
    for control in quote.required_controls:
        toggled = dict(enabled_controls)
        toggled[control] = False
        toggled_quote = generate_quote(application, certificates, metrics_by_cert, toggled)
        control_sensitivities.append(
            {
                "control": control,
                "premium_with_all_controls_usd": all_controls_quote.final_monthly_premium_usd,
                "premium_with_control_disabled_usd": toggled_quote.final_monthly_premium_usd,
                "monthly_delta_usd": toggled_quote.final_monthly_premium_usd - all_controls_quote.final_monthly_premium_usd,
                "status_with_control_disabled": toggled_quote.status,
                "exclusions_with_control_disabled": list(toggled_quote.exclusions),
            }
        )
    factor_rows = [
        _factor(
            "base_monthly_premium_usd",
            all_controls_quote.base_monthly_premium_usd,
            "Coverage limit and deployed units before learned-policy risk multipliers.",
        ),
        _factor(
            "deployment_multiplier",
            all_controls_quote.deployment_multiplier,
            "Fleet-size exposure multiplier capped inside the quote engine.",
        ),
        _factor(
            "behavioral_fragility_multiplier",
            all_controls_quote.behavioral_fragility_multiplier,
            "Failure-boundary multiplier from minimal failure cost and neighborhood failure rate.",
        ),
        _factor(
            "internal_risk_multiplier",
            all_controls_quote.internal_risk_multiplier,
            "Internal-risk multiplier from aggregate trace scores.",
        ),
        _factor(
            "mitigation_discount_multiplier",
            all_controls_quote.mitigation_discount_multiplier,
            "Discount multiplier applied only when all required controls are enabled.",
        ),
    ]
    return {
        "pricing_id": f"PRICE-{application.application_id}",
        "status": "demo_pricing_diligence_not_actuarial_filing",
        "boundary": "This artifact explains quote-engine sensitivity for diligence; it is not filed actuarial pricing, an insurance offer, or a rate adequacy opinion.",
        "coverage_context": {
            "application_id": application.application_id,
            "coverage_requested_usd": application.coverage_requested_usd,
            "deployment_units": application.deployment_units,
            "quote_id": quote.quote_id,
        },
        "factor_stack": factor_rows,
        "control_sensitivities": control_sensitivities,
        "all_controls_monthly_premium_usd": all_controls_quote.final_monthly_premium_usd,
        "no_controls_monthly_premium_usd": no_controls_quote.final_monthly_premium_usd,
        "aggregate_control_delta_usd": no_controls_quote.final_monthly_premium_usd - all_controls_quote.final_monthly_premium_usd,
        "diligence_questions": [
            "Which premium change comes from exposure, behavioral fragility, internal risk, or mitigation controls?",
            "Which disabled controls create exclusions rather than silent price-only changes?",
            "Which assumptions need actuarial, compliance, carrier, or reinsurer review before launch?",
            "Can a reviewer recompute the premium deltas by rerunning the quote engine with controls toggled?",
        ],
        "open_pricing_risks": [
            "The quote formula is transparent demo logic, not carrier-filed pricing.",
            "Loss frequency and severity assumptions need external actuarial review.",
            "Control discounts require real-world effectiveness evidence before live deployment.",
            "Capacity, compliance, and policy wording must be reviewed before any insurance offer.",
        ],
    }


def pricing_factor_rows(pricing: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly quote factor rows."""

    return [
        {
            "Factor": item["factor"],
            "Value": item["value"],
            "Diligence Meaning": item["diligence_meaning"],
        }
        for item in pricing["factor_stack"]
    ]


def pricing_control_rows(pricing: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly control sensitivity rows."""

    return [
        {
            "Control": item["control"],
            "All Controls": item["premium_with_all_controls_usd"],
            "Disabled": item["premium_with_control_disabled_usd"],
            "Delta": item["monthly_delta_usd"],
            "Disabled Status": item["status_with_control_disabled"],
            "Exclusions": "; ".join(item["exclusions_with_control_disabled"]),
        }
        for item in pricing["control_sensitivities"]
    ]


def _factor(factor: str, value: int | float, diligence_meaning: str) -> dict[str, Any]:
    return {
        "factor": factor,
        "value": value,
        "diligence_meaning": diligence_meaning,
    }
