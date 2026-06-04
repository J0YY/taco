"""Deterministic insurance quote engine for the TACO demo."""

from __future__ import annotations

from statistics import mean

from .schemas import InsuranceApplication, InternalRiskMetrics, NormalizedDreamAuditCertificate, QuoteBreakdown


def traditional_underwriting_status(application: InsuranceApplication) -> dict:
    if not application.telemetry_available:
        return {
            "status": "blocked_no_telemetry",
            "explanation": "Traditional underwriting blocked because no deployment telemetry or historical loss data is available. TACO can proceed using internal underwriting.",
        }
    return {"status": "priceable_with_telemetry", "explanation": "Fleet telemetry is available for conventional actuarial review."}


def behavioral_fragility_multiplier(minimal_failure_cost: float, failure_rate_neighborhood: float) -> float:
    cost_factor = 1.0 + max(0.0, 0.6 - minimal_failure_cost)
    rate_factor = 1.0 + 0.75 * failure_rate_neighborhood
    return cost_factor * rate_factor


def internal_risk_multiplier(internal_risk_score: float) -> float:
    return 1.0 + 1.25 * internal_risk_score


def mitigation_discount(causal_mitigability_score: float, monitor_enabled: bool) -> float:
    if not monitor_enabled:
        return 1.0
    return 1.0 - min(0.45, 0.45 * causal_mitigability_score)


def required_control_for_failure(failure_type: str) -> str | None:
    if "occlusion" in failure_type:
        return "occlusion_risk_monitor_enabled"
    if "language" in failure_type or "instruction" in failure_type:
        return "language_override_sanitizer_enabled"
    if "distractor" in failure_type or "confusion" in failure_type:
        return "target_identity_confirmation_enabled"
    return None


def _round_100(value: float) -> int:
    return int(round(value / 100.0) * 100)


def generate_quote(
    application: InsuranceApplication,
    certificates: list[NormalizedDreamAuditCertificate],
    metrics_by_cert: dict[str, InternalRiskMetrics],
    monitor_enabled: bool,
    controls_enabled: dict[str, bool] | None = None,
) -> QuoteBreakdown:
    base = int(application.coverage_requested_usd * 0.0008 + application.deployment_units * 35)
    if not certificates:
        status = traditional_underwriting_status(application)["status"]
        return QuoteBreakdown(
            quote_id=f"QUOTE-{application.application_id}",
            application_id=application.application_id,
            status=status,
            coverage_type="Learned-Policy Liability",
            coverage_limit_usd=application.coverage_requested_usd,
            base_monthly_premium_usd=base,
            deployment_multiplier=1.0,
            behavioral_fragility_multiplier=1.0,
            internal_risk_multiplier=1.0,
            mitigation_discount_multiplier=1.0,
            final_monthly_premium_usd=0,
            required_controls=[],
            exclusions=[],
            quote_explanation=[traditional_underwriting_status(application)["explanation"]],
            metadata={"audit_present": False},
        )

    controls_enabled = controls_enabled or {}
    behavioral_mults = [behavioral_fragility_multiplier(c.minimal_failure_cost, c.failure_rate_neighborhood) for c in certificates]
    behavioral = 0.65 * max(behavioral_mults) + 0.35 * mean(behavioral_mults)
    risk_scores = [m.internal_risk_score for m in metrics_by_cert.values()] or [0.0]
    aggregate_risk = 0.7 * max(risk_scores) + 0.3 * mean(risk_scores)
    internal = internal_risk_multiplier(aggregate_risk)
    mitigability_scores = [m.causal_mitigability_score for m in metrics_by_cert.values()] or [0.0]
    aggregate_mitigability = mean(mitigability_scores)

    controls = ["reaudit_required_after_model_update"]
    for cert in certificates:
        control = required_control_for_failure(cert.failure_type)
        if control and control not in controls:
            controls.append(control)

    all_specific_controls_enabled = all(controls_enabled.get(c, monitor_enabled) for c in controls if c != "reaudit_required_after_model_update")
    effective_monitor_enabled = monitor_enabled and all_specific_controls_enabled
    discount = mitigation_discount(aggregate_mitigability, effective_monitor_enabled)
    deployment = 1.0 + min(1.5, application.deployment_units / 500)
    final = _round_100(base * deployment * behavioral * internal * discount)

    exclusions: list[str] = []
    if not effective_monitor_enabled:
        exclusions.append("Known DreamAudit certificate families are excluded until required internal-risk controls are enabled.")
    for cert in certificates:
        control = required_control_for_failure(cert.failure_type)
        if control and not controls_enabled.get(control, monitor_enabled):
            exclusions.append(f"{cert.certificate_id} {cert.failure_type.replace('_', '-')} excluded if {control.replace('_', '-')} is disabled.")

    lowest_cost = min(c.minimal_failure_cost for c in certificates)
    saved_pct = int(round((1.0 - discount) * 100))
    explanation = [
        "Traditional underwriting had no telemetry to price this robot fleet.",
        f"DreamAudit found {len(certificates)} replayable failure families.",
        f"The lowest minimal failure cost was {lowest_cost:.2f}, indicating fragile failure boundaries.",
        "Internal risk signatures appeared before physical failure, so runtime monitors can reduce expected loss.",
        f"Required controls reduce premium by {saved_pct}%.",
    ]
    return QuoteBreakdown(
        quote_id=f"QUOTE-{application.application_id}",
        application_id=application.application_id,
        status="conditionally_approved" if effective_monitor_enabled else "approved_with_exclusions",
        coverage_type="Learned-Policy Liability",
        coverage_limit_usd=application.coverage_requested_usd,
        base_monthly_premium_usd=base,
        deployment_multiplier=round(deployment, 4),
        behavioral_fragility_multiplier=round(behavioral, 4),
        internal_risk_multiplier=round(internal, 4),
        mitigation_discount_multiplier=round(discount, 4),
        final_monthly_premium_usd=final,
        required_controls=controls,
        exclusions=exclusions,
        quote_explanation=explanation,
        metadata={"aggregate_internal_risk_score": aggregate_risk, "aggregate_causal_mitigability_score": aggregate_mitigability},
    )

