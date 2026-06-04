"""Commercial unit-economics model for TACO seed diligence."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_commercial_unit_economics(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    commercial_model: dict[str, Any],
    commercial_traction_plan: dict[str, Any],
    seed_financing_plan: dict[str, Any],
    buyer_roi_model: dict[str, Any],
) -> dict[str, Any]:
    """Return a bounded unit-economics artifact for investor diligence."""

    target_raise = int(seed_financing_plan.get("target_raise_usd", 0) or 0)
    runway_months = int(seed_financing_plan.get("estimated_runway_months", 0) or 0)
    base_case = commercial_model.get("base_case", {})
    platform_accounts = int(base_case.get("accounts", 0) or 0)
    platform_fee = int(base_case.get("platform_fee_usd", 0) or 0)
    packet_count = int(base_case.get("packet_fees", 0) or 0)
    packet_fee = int(base_case.get("packet_fee_usd", 0) or 0)
    base_revenue_rows = _base_revenue_rows(
        commercial_traction_plan,
        platform_accounts,
        platform_fee,
        packet_count,
        packet_fee,
    )
    return {
        "unit_id": f"UNIT-{application.application_id}",
        "status": "unit_economics_model_ready_not_financial_forecast",
        "boundary": "This is a modeled unit-economics diligence artifact, not audited financials, booked revenue, signed ARR, committed pipeline, CAC proof, gross-margin proof, insurance commission revenue, underwriting profit, or carrier capacity.",
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
        "assumption_set": {
            "seed_runway_months": runway_months,
            "base_modeled_arr_usd": int(base_case.get("modeled_arr_usd", 0) or 0),
            "base_platform_accounts": platform_accounts,
            "base_platform_fee_usd": platform_fee,
            "base_packet_count": packet_count,
            "base_packet_fee_usd": packet_fee,
            "revenue_recognition_boundary": "Count only signed or paid evidence workflow revenue; exclude insurance premium, commissions, float, underwriting profit, and risk-bearing economics until licensed capacity exists.",
        },
        "base_revenue_mix": base_revenue_rows,
        "margin_scenarios": _margin_scenarios(commercial_model, base_revenue_rows),
        "cac_payback_model": _cac_payback_model(commercial_traction_plan),
        "seed_milestone_gates": _seed_milestone_gates(target_raise, runway_months),
        "risk_bearing_exclusions": [
            "No insurance premium is counted as TACO revenue in this unit-economics model.",
            "No carrier commission, MGA fee, loss-ratio upside, float, reserve release, or underwriting profit is included.",
            "No CAC payback is considered proven until paid documents identify source, channel, sales effort, and permission status.",
            "No gross margin is considered proven until evidence-production labor, cloud/GPU cost, support time, and reviewer operations are logged per paid scope.",
        ],
        "proof_needed_to_upgrade": [
            "paid invoice or signed pilot scope for each package type",
            "time-and-cost log per evidence packet, policy sprint, and submission triage workflow",
            "source-data access path that reduces repeated evidence-production labor",
            "sales-source attribution for each counted prospect and commercial document",
            "finance review separating software, services, pass-through infrastructure, and insurance-risk economics",
        ],
        "linked_buyer_value": {
            "roi_id": buyer_roi_model.get("roi_id", "buyer_roi_model"),
            "proof_gate_count": len(buyer_roi_model.get("proof_gates", [])),
            "reason_to_pay_boundary": "Buyer ROI remains modeled until buyers confirm delay cost, review-time savings, control-credit interpretation, or paid pilot economics.",
        },
    }


def unit_economics_revenue_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly revenue-mix rows."""

    return [
        {
            "Line": item["line_id"],
            "Unit Price": item["unit_price_usd"],
            "Units": item["modeled_units"],
            "Revenue": item["modeled_revenue_usd"],
            "Delivery Cost": item["delivery_cost_usd"],
            "Gross Margin": item["gross_margin_pct"],
            "Boundary": item["boundary"],
        }
        for item in model["base_revenue_mix"]
    ]


def unit_economics_scenario_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly margin scenario rows."""

    return [
        {
            "Scenario": item["scenario_id"],
            "Revenue": item["modeled_revenue_usd"],
            "Delivery Cost": item["delivery_cost_usd"],
            "Gross Profit": item["gross_profit_usd"],
            "Gross Margin": item["gross_margin_pct"],
            "What Must Be True": item["what_must_be_true"],
        }
        for item in model["margin_scenarios"]
    ]


def unit_economics_payback_rows(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Return Streamlit-friendly CAC/payback rows."""

    return [
        {
            "Motion": item["motion"],
            "Modeled CAC": item["modeled_cac_usd"],
            "Modeled ACV": item["modeled_acv_usd"],
            "Gross Margin": item["gross_margin_pct"],
            "Payback Months": item["payback_months"],
            "Upgrade Gate": item["upgrade_gate"],
        }
        for item in model["cac_payback_model"]
    ]


def unit_economics_gate_rows(model: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly milestone gate rows."""

    return [
        {
            "Gate": item["gate"],
            "Metric": item["metric"],
            "Pass Condition": item["pass_condition"],
            "Do Not Count": item["do_not_count"],
        }
        for item in model["seed_milestone_gates"]
    ]


def _base_revenue_rows(
    commercial_traction_plan: dict[str, Any],
    platform_accounts: int,
    platform_fee: int,
    packet_count: int,
    packet_fee: int,
) -> list[dict[str, Any]]:
    package_by_id = {
        str(item.get("package_id", "")): item
        for item in commercial_traction_plan.get("commercial_packages", [])
        if isinstance(item, dict)
    }
    return [
        _line(
            "walkthrough_services",
            int(package_by_id.get("evidence_packet_walkthrough", {}).get("price_usd", 15_000) or 15_000),
            12,
            6_000,
            "Low-friction paid diligence package; still services-heavy until packet verification becomes self-serve.",
        ),
        _line(
            "policy_evidence_sprints",
            int(package_by_id.get("policy_evidence_sprint", {}).get("price_usd", 45_000) or 45_000),
            8,
            22_000,
            "Integration-heavy partner work; proves willingness to pay but not yet software-like margin.",
        ),
        _line(
            "submission_triage_retainer",
            int(package_by_id.get("autonomy_submission_triage", {}).get("price_usd", 75_000) or 75_000),
            6,
            24_000,
            "Repeatable broker/MGA workflow; margin improves only if submission intake and verifier reuse reduce analyst labor.",
        ),
        _line(
            "evidence_platform_subscription",
            platform_fee or 150_000,
            platform_accounts or 20,
            45_000,
            "Modeled platform line from the commercial scale model; not signed ARR.",
        ),
        _line(
            "packet_fee_reuse",
            packet_fee or 20_000,
            packet_count or 40,
            7_000,
            "Per-policy packet revenue; depends on DreamAudit/activation capture reducing marginal evidence-production cost.",
        ),
    ]


def _line(line_id: str, unit_price: int, modeled_units: int, unit_delivery_cost: int, boundary: str) -> dict[str, Any]:
    revenue = unit_price * modeled_units
    delivery_cost = unit_delivery_cost * modeled_units
    gross_profit = revenue - delivery_cost
    return {
        "line_id": line_id,
        "unit_price_usd": unit_price,
        "modeled_units": modeled_units,
        "unit_delivery_cost_usd": unit_delivery_cost,
        "modeled_revenue_usd": revenue,
        "delivery_cost_usd": delivery_cost,
        "gross_profit_usd": gross_profit,
        "gross_margin_pct": round(100 * gross_profit / revenue) if revenue else 0,
        "boundary": boundary,
    }


def _margin_scenarios(commercial_model: dict[str, Any], base_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    revenue_by_scenario = {
        str(item.get("scenario_id", "")): int(item.get("modeled_arr_usd", 0) or 0)
        for item in commercial_model.get("revenue_scenarios", [])
        if isinstance(item, dict)
    }
    base_revenue = sum(item["modeled_revenue_usd"] for item in base_rows)
    base_delivery_cost = sum(item["delivery_cost_usd"] for item in base_rows)
    return [
        _scenario(
            "services_heavy_launch",
            revenue_by_scenario.get("conservative_design_partner_services", 600_000),
            330_000,
            "Paid pilots are mostly founder/engineering services; acceptable for proof, not sufficient for venture-scale margin.",
        ),
        _scenario(
            "base_packet_platform",
            base_revenue or revenue_by_scenario.get("base_evidence_platform", 3_800_000),
            base_delivery_cost,
            "Packet reuse, verifier workflow, and activation/DreamAudit source paths reduce marginal delivery work.",
        ),
        _scenario(
            "underwriting_network_reuse",
            revenue_by_scenario.get("breakout_underwriting_network", 17_750_000),
            4_080_000,
            "Multiple buyer categories reuse the same evidence contracts; this requires external validation and repeatable implementation playbooks.",
        ),
    ]


def _scenario(scenario_id: str, revenue: int, delivery_cost: int, what_must_be_true: str) -> dict[str, Any]:
    gross_profit = revenue - delivery_cost
    return {
        "scenario_id": scenario_id,
        "modeled_revenue_usd": revenue,
        "delivery_cost_usd": delivery_cost,
        "gross_profit_usd": gross_profit,
        "gross_margin_pct": round(100 * gross_profit / revenue) if revenue else 0,
        "what_must_be_true": what_must_be_true,
    }


def _cac_payback_model(commercial_traction_plan: dict[str, Any]) -> list[dict[str, Any]]:
    package_prices = {
        str(item.get("package_id", "")): int(item.get("price_usd", 0) or 0)
        for item in commercial_traction_plan.get("commercial_packages", [])
        if isinstance(item, dict)
    }
    return [
        _payback(
            "founder_led_packet_walkthrough",
            10_000,
            package_prices.get("evidence_packet_walkthrough", 15_000),
            60,
            "Packet walkthrough counted only with invoice, packet SHA-256, and reviewer artifact.",
        ),
        _payback(
            "paid_policy_evidence_sprint",
            35_000,
            package_prices.get("policy_evidence_sprint", 45_000),
            51,
            "Policy sprint counted only with signed scope, source-data path, and delivery cost log.",
        ),
        _payback(
            "broker_mga_platform_motion",
            75_000,
            package_prices.get("autonomy_submission_triage", 75_000),
            68,
            "Broker/MGA motion counted only when repeated submissions use the same verifier workflow.",
        ),
        _payback(
            "carrier_capacity_diligence",
            60_000,
            package_prices.get("capacity_diligence_packet", 60_000),
            55,
            "Carrier/reinsurer diligence counted only as evidence revenue, not insurance capacity or commission revenue.",
        ),
    ]


def _payback(
    motion: str,
    modeled_cac_usd: int,
    modeled_acv_usd: int,
    gross_margin_pct: int,
    upgrade_gate: str,
) -> dict[str, Any]:
    gross_profit_per_year = modeled_acv_usd * gross_margin_pct / 100
    monthly_gross_profit = gross_profit_per_year / 12 if gross_profit_per_year else 0
    return {
        "motion": motion,
        "modeled_cac_usd": modeled_cac_usd,
        "modeled_acv_usd": modeled_acv_usd,
        "gross_margin_pct": gross_margin_pct,
        "payback_months": round(modeled_cac_usd / monthly_gross_profit, 1) if monthly_gross_profit else None,
        "upgrade_gate": upgrade_gate,
    }


def _seed_milestone_gates(target_raise: int, runway_months: int) -> list[dict[str, str]]:
    return [
        {
            "gate": "services_margin_known",
            "metric": "delivery cost per paid walkthrough and evidence sprint",
            "pass_condition": "At least five paid or written scopes include source, labor, compute, reviewer-ops, and support cost logs.",
            "do_not_count": "Founder estimates or unpaid demos without delivery-cost tracking.",
        },
        {
            "gate": "repeatable_platform_margin",
            "metric": "gross margin on repeat packet workflow",
            "pass_condition": "At least two buyer categories reuse packet verification and evidence capture with gross margin above 65%.",
            "do_not_count": "One-off integration projects that require bespoke evidence production each time.",
        },
        {
            "gate": "cac_payback_evidence",
            "metric": "sales-source and payback record by channel",
            "pass_condition": "Each counted deal has source, sales effort, ACV, gross margin, and payback-month estimate tied to a signed artifact.",
            "do_not_count": "Prospect meetings, investor intros, or pipeline value without signed documents.",
        },
        {
            "gate": "seed_burn_to_milestone",
            "metric": f"${target_raise:,.0f} over {runway_months} months",
            "pass_condition": "Use-of-funds can be tied to live evidence, paid pilots, compliance path, security posture, and repeatable margin data.",
            "do_not_count": "Hiring or infrastructure spend that does not close a named proof, margin, or capacity gate.",
        },
    ]
