"""Fundraise-readiness gates for investor diligence."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .insurance_scenarios import INSURANCE_SCENARIOS
from .investor_case import RESEARCH_FOUNDATIONS
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


def build_fundraise_readiness(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
    *,
    scenarios: list[dict[str, Any]] = INSURANCE_SCENARIOS,
    research_foundations: list[dict[str, str]] = RESEARCH_FOUNDATIONS,
) -> dict[str, Any]:
    """Score whether the current evidence package can withstand seed diligence."""

    suite_cases = list(suite_manifest.get("cases", []))
    suite_size = int(suite_manifest.get("suite_size", len(suite_cases)) or 0)
    suite_families = {str(case.get("failure_family", "unknown")) for case in suite_cases}
    scenario_controls = {str(scenario.get("required_control", "")) for scenario in scenarios if scenario.get("required_control")}
    pricing_deltas = [
        scenario["pricing"]["without_controls_monthly_usd"] - scenario["pricing"]["with_controls_monthly_usd"]
        for scenario in scenarios
        if "pricing" in scenario
        and "without_controls_monthly_usd" in scenario["pricing"]
        and "with_controls_monthly_usd" in scenario["pricing"]
    ]
    metrics_by_cert = {metric.certificate_id: metric for metric in metrics}
    covered_metrics = sum(1 for cert in certificates if cert.certificate_id in metrics_by_cert)
    mean_internal_risk = sum(metric.internal_risk_score for metric in metrics) / len(metrics) if metrics else 0.0
    mean_mitigability = sum(metric.causal_mitigability_score for metric in metrics) / len(metrics) if metrics else 0.0
    family_counts = Counter(cert.failure_type for cert in certificates)

    gates = [
        _gate(
            "Replayable Evidence Breadth",
            15,
            suite_size >= 40 and len(suite_families) >= 8 and len(certificates) >= 3,
            f"{suite_size} suite videos, {len(suite_families)} suite failure families, {len(certificates)} primary certificates.",
            "Keep at least 40 replay examples and 3+ primary certificates attached to the demo package.",
        ),
        _gate(
            "Insurance Workflow And Pricing Depth",
            15,
            len(scenarios) >= 10 and len(scenario_controls) >= 8 and len(pricing_deltas) == len(scenarios) and all(delta > 0 for delta in pricing_deltas),
            f"{len(scenarios)} end-to-end workflows, {len(scenario_controls)} controls, ${sum(pricing_deltas):,.0f}/mo aggregate control delta.",
            "Add more priced workflows or control-linked premium deltas before investor diligence.",
        ),
        _dreamaudit_gate(dreamaudit_intake),
        _gate(
            "Internals-Based Risk Path",
            20,
            bool(certificates) and covered_metrics == len(certificates) and mean_internal_risk > 0 and mean_mitigability > 0,
            f"{covered_metrics}/{len(certificates)} certificates have internal metrics; mean risk {mean_internal_risk:.2f}; mean mitigability {mean_mitigability:.2f}.",
            "Record real VLA activations for the same certificates and keep metric coverage complete.",
        ),
        _gate(
            "Commercial Underwriting Package",
            15,
            application.coverage_requested_usd > 0
            and quote.final_monthly_premium_usd > 0
            and bool(quote.required_controls)
            and len(family_counts) >= 3,
            f"${application.coverage_requested_usd:,.0f} requested coverage, ${quote.final_monthly_premium_usd:,.0f}/mo quoted, {len(quote.required_controls)} required controls.",
            "Connect the quote to named controls, exclusions, and at least three failure families.",
        ),
        _gate(
            "Research-Backed Methodology",
            10,
            len(research_foundations) >= 4 and all(item.get("url", "").startswith("https://") for item in research_foundations),
            f"{len(research_foundations)} research anchors linked to simulation, perturbation, interpretability, and monitoring.",
            "Add primary-source research anchors for any methodology claim that investors will diligence.",
        ),
        _gate(
            "Design-Partner Diligence Path",
            10,
            suite_size >= 40 and len(scenarios) >= 10 and bool(quote.required_controls),
            "Evidence package can support broker/carrier/OEM walkthroughs, but signed design-partner review is still external.",
            "Secure 2-3 design-partner reviews with robotics OEMs, brokers, MGAs, or carriers.",
            caveat=True,
        ),
    ]
    score = sum(gate["weight"] for gate in gates if gate["passed"])
    gaps = [gate["next_action"] for gate in gates if not gate["passed"]]
    caveats = [gate["next_action"] for gate in gates if gate.get("caveat")]
    failed_gate_names = {gate["name"] for gate in gates if not gate["passed"]}
    if score >= 85 and not gaps:
        posture = "seed_diligence_ready_with_live_evidence_caveats"
    elif score >= 85 and "Live DreamAudit Corpus" in failed_gate_names:
        posture = "credible_seed_demo_needs_live_dreamaudit_scan"
    elif score >= 85:
        posture = "seed_diligence_ready_with_targeted_evidence_gaps"
    elif score >= 70:
        posture = "credible_seed_demo_needs_design_partner_validation"
    else:
        posture = "early_seed_story_needs_more_evidence"
    return {
        "score": score,
        "posture": posture,
        "gates_passed": sum(1 for gate in gates if gate["passed"]),
        "gates_total": len(gates),
        "gates": gates,
        "gaps": gaps,
        "caveats": caveats,
    }


def fundraise_readiness_rows(readiness: dict[str, Any]) -> list[dict[str, Any]]:
    """Return table rows for Streamlit and Markdown rendering."""

    rows = []
    for gate in readiness["gates"]:
        rows.append(
            {
                "Gate": gate["name"],
                "Weight": gate["weight"],
                "Status": "Pass" if gate["passed"] else "Needs Work",
                "Evidence": gate["evidence"],
                "Next Action": gate["next_action"],
            }
        )
    return rows


def _dreamaudit_gate(dreamaudit_intake: dict[str, Any] | None) -> dict[str, Any]:
    if not dreamaudit_intake:
        return _gate(
            "Live DreamAudit Corpus",
            15,
            False,
            "No live DreamAudit intake summary is attached to this investor package.",
            "Run the DreamAudit Intake scan and attach the carrier-readiness ladder before investor diligence.",
        )
    if not dreamaudit_intake.get("root_exists"):
        return _gate(
            "Live DreamAudit Corpus",
            15,
            False,
            f"DreamAudit artifact path was not found: {dreamaudit_intake.get('root', 'unknown')}.",
            "Point DreamAudit Intake at an existing artifact directory before investor diligence.",
        )
    readiness = dreamaudit_intake.get("readiness", {})
    summary = dreamaudit_intake.get("summary", {})
    ladder = list(dreamaudit_intake.get("evidence_depth_ladder", []))
    recommended_limit = dreamaudit_intake.get("recommended_scan_limit")
    carrier_ready_rung = next((row for row in ladder if row.get("status") == "carrier_review_ready"), None)
    selected_status = str(readiness.get("status", "unknown"))
    selected_score = int(readiness.get("readiness_score", 0) or 0)
    certificates = int(summary.get("certificates", 0) or 0)
    passed = selected_status == "carrier_review_ready" or carrier_ready_rung is not None
    if passed:
        ready_depth = recommended_limit or (carrier_ready_rung or {}).get("scan_limit") or "selected scan"
        evidence = (
            f"{certificates} selected DreamAudit certificates; selected readiness {selected_score}/100 ({selected_status}); "
            f"carrier-ready ladder depth {ready_depth}."
        )
        next_action = "Use the carrier-ready DreamAudit ladder in investor and carrier walkthroughs."
    else:
        gaps = "; ".join(readiness.get("gaps", [])) or "No carrier-ready ladder depth found."
        evidence = f"{certificates} selected DreamAudit certificates; selected readiness {selected_score}/100 ({selected_status}); gaps: {gaps}"
        next_action = "Expand or improve the DreamAudit scan until a ladder rung reaches carrier_review_ready."
    return _gate("Live DreamAudit Corpus", 15, passed, evidence, next_action)


def _gate(name: str, weight: int, passed: bool, evidence: str, next_action: str, *, caveat: bool = False) -> dict[str, Any]:
    return {
        "name": name,
        "weight": weight,
        "passed": passed,
        "evidence": evidence,
        "next_action": next_action,
        "caveat": caveat,
    }
