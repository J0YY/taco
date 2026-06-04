"""Investor and underwriting diligence memo generation."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .fundraise_readiness import build_fundraise_readiness, fundraise_readiness_rows
from .investor_case import FUNDRAISE_MILESTONES, MOAT_HYPOTHESES, RESEARCH_FOUNDATIONS
from .insurance_scenarios import INSURANCE_SCENARIOS
from .renewal_loop import INCIDENT_LOG, RUNTIME_EVENTS, renewal_summary
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


def build_diligence_memo(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> str:
    """Build a single Markdown artifact for investors, brokers, and underwriters."""

    metrics_by_id = {metric.certificate_id: metric for metric in metrics}
    suite_cases = list(suite_manifest.get("cases", []))
    family_counts = Counter(str(case.get("failure_family", "unknown")) for case in suite_cases)
    env_count = len({str(case.get("env_id", "unknown")) for case in suite_cases})
    earliest_warning = max((metric.early_warning_margin_seconds for metric in metrics), default=0.0)
    mean_risk = sum(metric.internal_risk_score for metric in metrics) / len(metrics) if metrics else 0.0
    mean_mitigability = sum(metric.causal_mitigability_score for metric in metrics) / len(metrics) if metrics else 0.0
    renewal = renewal_summary(quote)
    fundraise_readiness = build_fundraise_readiness(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        dreamaudit_intake,
    )

    lines = [
        "# TACO Investor Diligence Memo",
        "",
        "## One-Line Thesis",
        "",
        "TACO is the evidence layer that makes learned robot policies insurable before claims history exists.",
        "",
        "## VC Readiness Gates",
        "",
        f"* Readiness score: {fundraise_readiness['score']}/100",
        f"* Posture: {str(fundraise_readiness['posture']).replace('_', ' ')}",
        f"* Gates passed: {fundraise_readiness['gates_passed']}/{fundraise_readiness['gates_total']}",
        "",
        "| Gate | Weight | Status | Evidence | Next action |",
        "| --- | ---: | --- | --- | --- |",
    ]
    for row in fundraise_readiness_rows(fundraise_readiness):
        lines.append(
            f"| {row['Gate']} | {row['Weight']} | {row['Status']} | {row['Evidence']} | {row['Next Action']} |"
        )

    lines.extend(
        [
            "",
            "## Customer And Coverage Wedge",
            "",
            f"* Named insured: {application.company_name}",
            f"* Robot type: {application.robot_type}",
            f"* Policy ID: {application.policy_id}",
            f"* Deployment units: {application.deployment_units:,}",
            f"* Coverage requested: ${application.coverage_requested_usd:,.0f}",
            f"* Deployment stage: {application.deployment_stage}",
            f"* Fleet telemetry available: {application.telemetry_available}",
            "",
            "## Underwriting Result",
            "",
            f"* Quote status: {quote.status}",
            f"* Monthly premium: ${quote.final_monthly_premium_usd:,.0f}",
            f"* Required controls: {', '.join(quote.required_controls)}",
            f"* Exclusions: {', '.join(quote.exclusions) if quote.exclusions else 'None while controls remain enabled'}",
            f"* Earliest internal warning margin: {earliest_warning:.2f}s",
            f"* Mean internal risk score: {mean_risk:.2f}",
            f"* Mean causal mitigability score: {mean_mitigability:.2f}",
            "",
            "## Replayable Failure Evidence",
            "",
            "| Certificate | Failure family | Minimal cost | Neighborhood rate | Internal signal | Required control |",
            "| --- | --- | ---: | ---: | --- | --- |",
        ]
    )

    for cert in certificates:
        metric = metrics_by_id.get(cert.certificate_id)
        signal = metric.dominant_risk_signature if metric else "not_computed"
        control = cert.patch_recipe.get("recommended_control", "not_specified")
        lines.append(
            f"| {cert.certificate_id} | {cert.failure_type} | {cert.minimal_failure_cost:.2f} | "
            f"{cert.failure_rate_neighborhood:.2f} | {signal} | {control} |"
        )

    lines.extend(
        [
            "",
            "## ManiSkill/RMA Evidence Breadth",
            "",
            f"* Supplemental suite size: {suite_manifest.get('suite_size', len(suite_cases))} replay videos",
            f"* Distinct ManiSkill-style environments: {env_count}",
            f"* Distinct failure families: {len(family_counts)}",
            "",
            "| Failure family | Video count |",
            "| --- | ---: |",
        ]
    )
    for family, count in sorted(family_counts.items()):
        lines.append(f"| {family} | {count} |")

    lines.extend(
        [
            "",
            "## Ten Insurance Workflow Examples",
            "",
            "| Scenario | Coverage | Failure | With Controls | Without Controls | Required Control |",
            "| --- | --- | --- | ---: | ---: | --- |",
        ]
    )
    for scenario in INSURANCE_SCENARIOS:
        pricing = scenario["pricing"]
        lines.append(
            f"| {scenario['scenario_id']} | {scenario['coverage']} | {scenario['failure']} | "
            f"${pricing['with_controls_monthly_usd']:,.0f}/mo | ${pricing['without_controls_monthly_usd']:,.0f}/mo | "
            f"{scenario['required_control']} |"
        )

    lines.extend(
        [
            "",
            "## Runtime Compliance And Renewal Loop",
            "",
            f"* Runtime monitor events: {renewal['runtime_events']}",
            f"* Compliance score: {renewal['compliance_score']:.2f}",
            f"* Prevented loss evidence: ${renewal['prevented_loss_usd']:,.0f}",
            f"* Incurred loss evidence: ${renewal['incurred_loss_usd']:,.0f}",
            f"* Renewal monthly premium: ${renewal['renewal_monthly_premium_usd']:,.0f}",
            f"* Renewal delta: ${renewal['renewal_delta_usd']:,.0f}",
            f"* Re-audit required: {renewal['re_audit_required']}",
            "",
            "| Event | Control | Status | Evidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for event in RUNTIME_EVENTS:
        lines.append(f"| {event['event_id']} | {event['control']} | {event['status']} | {event['evidence']} |")
    lines.extend(["", "| Incident | Severity | Loss | Coverage response |", "| --- | --- | ---: | --- |"])
    for incident in INCIDENT_LOG:
        lines.append(
            f"| {incident['incident_id']} | {incident['severity']} | ${incident['estimated_loss_usd']:,.0f} | "
            f"{incident['coverage_response']} |"
        )

    lines.extend(
        [
            "",
            "## Why This Is Fundable If De-Risked",
            "",
            "* The wedge starts before claims history exists, where conventional underwriting is blocked.",
            "* Replay certificates, internal traces, mitigations, exclusions, and claims outcomes can compound into proprietary evidence.",
            "* Controls are not merely safety suggestions; they become coverage conditions and premium deltas.",
            "* The same evidence package can serve robot OEMs, enterprise risk teams, brokers, MGAs, carriers, reinsurers, and certification partners.",
            "",
            "## Moat Hypotheses",
            "",
        ]
    )
    lines.extend(f"* {item}" for item in MOAT_HYPOTHESES)
    lines.extend(["", "## Next De-Risking Milestones", ""])
    lines.extend(f"* {item}" for item in FUNDRAISE_MILESTONES)
    lines.extend(["", "## Research Anchors", ""])
    lines.extend(f"* {item['source']}: {item['taco_translation']} ({item['url']})" for item in RESEARCH_FOUNDATIONS)
    lines.extend(
        [
            "",
            "## Assumptions And Current Limits",
            "",
            "* Current bundled videos are local replay renderings; DreamAudit/simulator videos can be ingested through the same certificate workflow.",
            "* Current bundled trace arrays are local evidence fixtures; recorded VLA activations can be captured with the activation recorder.",
            "* The quote formula is transparent demo logic, not filed actuarial pricing.",
            "* This is not an insurance offer or insurance policy.",
            "",
        ]
    )
    return "\n".join(lines)
