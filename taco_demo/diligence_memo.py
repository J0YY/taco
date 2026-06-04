"""Investor and underwriting diligence memo generation."""

from __future__ import annotations

from collections import Counter
from typing import Any

from .data_room import build_data_room_checklist, build_data_room_manifest, data_room_rows
from .design_partner_plan import build_design_partner_plan
from .fundraise_readiness import build_fundraise_readiness, fundraise_readiness_rows
from .investor_case import FUNDRAISE_MILESTONES, MOAT_HYPOTHESES, RESEARCH_FOUNDATIONS
from .insurance_scenarios import INSURANCE_SCENARIOS
from .methodology_evidence import build_methodology_evidence_map
from .pricing_diligence import build_pricing_diligence
from .renewal_loop import INCIDENT_LOG, RUNTIME_EVENTS, renewal_summary
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown
from .seed_financing_plan import build_seed_financing_plan


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
    data_room = build_data_room_checklist(application, certificates, metrics, quote, suite_manifest, dreamaudit_intake)
    data_room_manifest = build_data_room_manifest(application, certificates, metrics, quote, suite_manifest, dreamaudit_intake)
    design_partner_plan = build_design_partner_plan(application, quote)
    seed_financing_plan = build_seed_financing_plan(application, quote, fundraise_readiness, design_partner_plan)
    methodology_map = build_methodology_evidence_map(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        dreamaudit_intake,
    )
    pricing_diligence = build_pricing_diligence(application, certificates, metrics, quote)

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
            "## Methodology Evidence Map",
            "",
            f"* Methodology score: {methodology_map['score']}/100",
            f"* Posture: {methodology_map['status']}",
            f"* Boundary: {methodology_map['boundary']}",
            "",
            "| Claim | Status | Current evidence | Boundary |",
            "| --- | --- | --- | --- |",
        ]
    )
    for claim in methodology_map["claims"]:
        lines.append(
            f"| {claim['claim_id']} | {claim['status']} | {claim['current_evidence']} | {claim['boundary']} |"
        )

    lines.extend(
        [
            "",
            "## Pricing Diligence Sensitivity",
            "",
            f"* Status: {pricing_diligence['status']}",
            f"* Boundary: {pricing_diligence['boundary']}",
            f"* All-controls monthly premium: ${pricing_diligence['all_controls_monthly_premium_usd']:,.0f}",
            f"* No-controls monthly premium: ${pricing_diligence['no_controls_monthly_premium_usd']:,.0f}",
            f"* Aggregate control delta: ${pricing_diligence['aggregate_control_delta_usd']:,.0f}",
            "",
            "| Factor | Value | Diligence meaning |",
            "| --- | ---: | --- |",
        ]
    )
    for factor in pricing_diligence["factor_stack"]:
        lines.append(f"| {factor['factor']} | {factor['value']} | {factor['diligence_meaning']} |")
    lines.extend(["", "| Control | Disabled premium | Delta | Disabled status |", "| --- | ---: | ---: | --- |"])
    for control in pricing_diligence["control_sensitivities"]:
        lines.append(
            f"| {control['control']} | ${control['premium_with_control_disabled_usd']:,.0f} | "
            f"${control['monthly_delta_usd']:,.0f} | {control['status_with_control_disabled']} |"
        )

    lines.extend(
        [
            "",
            "## VC Data Room Checklist",
            "",
            f"* Data room manifest: {data_room_manifest['manifest_id']}",
            f"* Internal packet score: {data_room['internal_packet_score']}/100",
            f"* Internal ready items: {data_room['internal_ready_items']}/{data_room['internal_total_items']}",
            f"* External pending items: {data_room['external_pending_items']}",
            "",
            "| Artifact | Status | Evidence | Next action |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in data_room_rows(data_room):
        lines.append(f"| {row['Artifact']} | {row['Status']} | {row['Evidence']} | {row['Next Action']} |")

    lines.extend(
        [
            "",
            "## Design-Partner Diligence Plan",
            "",
            f"* Plan status: {design_partner_plan['status']}",
            f"* Boundary: {design_partner_plan['boundary']}",
            f"* Pilot tracks: {len(design_partner_plan['tracks'])}",
            "",
            "| Track | Partner profile | Buyer question | Commercial signal |",
            "| --- | --- | --- | --- |",
        ]
    )
    for track in design_partner_plan["tracks"]:
        lines.append(
            f"| {track['track_id']} | {track['partner_profile']} | {track['buyer_question']} | {track['commercial_signal']} |"
        )
    lines.extend(["", "| Window | Goal | Evidence to collect |", "| --- | --- | --- |"])
    for milestone in design_partner_plan["thirty_sixty_ninety_day_plan"]:
        lines.append(f"| {milestone['window']} | {milestone['goal']} | {milestone['evidence_to_collect']} |")

    lines.extend(
        [
            "",
            "## Seed Financing Plan",
            "",
            f"* Plan status: {seed_financing_plan['status']}",
            f"* Boundary: {seed_financing_plan['boundary']}",
            f"* Target raise: ${seed_financing_plan['target_raise_usd']:,.0f}",
            f"* Estimated runway: {seed_financing_plan['estimated_runway_months']} months",
            "",
            "| Use of funds | Amount | Diligence evidence |",
            "| --- | ---: | --- |",
        ]
    )
    for item in seed_financing_plan["use_of_funds"]:
        lines.append(f"| {item['category']} | ${item['amount_usd']:,.0f} | {item['diligence_evidence']} |")
    lines.extend(["", "| Gate | Milestone | Success metric |", "| --- | --- | --- |"])
    for gate in seed_financing_plan["milestone_gates"]:
        lines.append(f"| {gate['gate']} | {gate['milestone']} | {gate['success_metric']} |")

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
            "* Current bundled trace arrays are local evidence fixtures; recorded VLA activations can now be exported through an explicit layer-to-signal map into the same metric path.",
            "* The quote formula is transparent demo logic, not filed actuarial pricing.",
            "* This is not an insurance offer or insurance policy.",
            "",
        ]
    )
    return "\n".join(lines)
