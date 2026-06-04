"""Deterministic quote logic for learned-policy liability coverage."""

from __future__ import annotations

from statistics import mean

from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


def traditional_underwriting_status(application: InsuranceApplication) -> dict[str, str]:
    if not application.telemetry_available:
        return {
            "status": "blocked_no_telemetry",
            "explanation": "Traditional underwriting blocked because no deployment telemetry or historical loss data is available. TACO can proceed using internal underwriting.",
        }
    return {"status": "telemetry_available", "explanation": "Deployment telemetry is available for traditional underwriting."}


def behavioral_fragility_multiplier(certificate: FailureCertificate) -> float:
    cost_factor = 1.0 + max(0.0, 0.6 - certificate.minimal_failure_cost)
    rate_factor = 1.0 + 0.75 * certificate.failure_rate_neighborhood
    return cost_factor * rate_factor


def required_control_for_failure(failure_type: str) -> str | None:
    if "occlusion" in failure_type:
        return "occlusion_risk_monitor_enabled"
    if "language" in failure_type or "instruction" in failure_type:
        return "language_override_sanitizer_enabled"
    if "distractor" in failure_type or "confusion" in failure_type:
        return "target_identity_confirmation_enabled"
    if "action_noise" in failure_type or ("action" in failure_type and "noise" in failure_type):
        return "action_noise_envelope_monitor_enabled"
    if "vision" in failure_type or "observation" in failure_type:
        return "vision_shift_monitor_enabled"
    return None


def _controls_enabled(required_controls: list[str], controls_enabled: dict[str, bool]) -> bool:
    return all(controls_enabled.get(control, False) for control in required_controls)


def _round_100(value: float) -> int:
    return int(round(value / 100.0) * 100)


def generate_quote(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics_by_cert: dict[str, InternalRiskMetrics],
    controls_enabled: dict[str, bool],
) -> QuoteBreakdown:
    base = int(application.coverage_requested_usd * 0.0008 + application.deployment_units * 35)
    if not certificates:
        status = traditional_underwriting_status(application)
        return QuoteBreakdown(
            quote_id=f"QUOTE-{application.application_id}",
            application_id=application.application_id,
            status=status["status"],
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
            quote_explanation=[status["explanation"]],
            metadata={"audit_present": False},
        )

    deployment_multiplier = 1.0 + min(1.5, application.deployment_units / 500)
    cert_behavior = [behavioral_fragility_multiplier(cert) for cert in certificates]
    behavioral_multiplier = 0.65 * max(cert_behavior) + 0.35 * mean(cert_behavior)

    risk_scores = [metrics_by_cert[cert.certificate_id].internal_risk_score for cert in certificates if cert.certificate_id in metrics_by_cert]
    mitigability_scores = [metrics_by_cert[cert.certificate_id].causal_mitigability_score for cert in certificates if cert.certificate_id in metrics_by_cert]
    aggregate_internal_risk = 0.7 * max(risk_scores) + 0.3 * mean(risk_scores) if risk_scores else 0.0
    aggregate_mitigability = mean(mitigability_scores) if mitigability_scores else 0.0
    internal_multiplier = 1.0 + 1.25 * aggregate_internal_risk

    required_controls = ["reaudit_required_after_model_update"]
    for cert in certificates:
        control = required_control_for_failure(cert.failure_type)
        if control and control not in required_controls:
            required_controls.append(control)

    enabled = _controls_enabled(required_controls, controls_enabled)
    mitigation_discount_multiplier = 1.0 - min(0.45, 0.45 * aggregate_mitigability) if enabled else 1.0
    final = _round_100(base * deployment_multiplier * behavioral_multiplier * internal_multiplier * mitigation_discount_multiplier)

    exclusions: list[str] = []
    for cert in certificates:
        control = required_control_for_failure(cert.failure_type)
        if not control or controls_enabled.get(control, False):
            continue
        if cert.certificate_id == "FR-001":
            exclusions.append("FR-001 occlusion-induced target collapse excluded until occlusion-risk monitor is enabled.")
        elif cert.certificate_id == "FR-002":
            exclusions.append("FR-002 language override failures excluded until instruction sanitizer is enabled.")
        elif cert.certificate_id == "FR-003":
            exclusions.append("FR-003 semantic distractor confusion excluded until target identity confirmation is enabled.")
        elif control == "action_noise_envelope_monitor_enabled":
            exclusions.append(f"{cert.certificate_id} action-noise sensitivity excluded until action-envelope monitoring is enabled.")
        elif control == "vision_shift_monitor_enabled":
            exclusions.append(f"{cert.certificate_id} vision-shift sensitivity excluded until vision-shift monitoring and re-audit triggers are enabled.")
        else:
            exclusions.append(f"{cert.certificate_id} known failure family excluded until required internal-risk control is enabled.")

    if not controls_enabled.get("reaudit_required_after_model_update", False):
        exclusions.append("Coverage excludes post-update learned-policy behavior until re-audit is completed.")

    lowest_cost = min(cert.minimal_failure_cost for cert in certificates)
    quote_explanation = [
        "Traditional underwriting had no telemetry.",
        f"TACO found {len(certificates)} replayable failure families.",
        f"The lowest minimal failure cost was {lowest_cost:.2f}.",
        "Internal risk signatures appeared before physical failure.",
        "Required controls reduce expected loss and premium.",
    ]
    return QuoteBreakdown(
        quote_id=f"QUOTE-{application.application_id}",
        application_id=application.application_id,
        status="conditionally_approved" if enabled else "approved_with_exclusions",
        coverage_type="Learned-Policy Liability",
        coverage_limit_usd=application.coverage_requested_usd,
        base_monthly_premium_usd=base,
        deployment_multiplier=round(deployment_multiplier, 4),
        behavioral_fragility_multiplier=round(behavioral_multiplier, 4),
        internal_risk_multiplier=round(internal_multiplier, 4),
        mitigation_discount_multiplier=round(mitigation_discount_multiplier, 4),
        final_monthly_premium_usd=final,
        required_controls=required_controls,
        exclusions=exclusions,
        quote_explanation=quote_explanation,
        metadata={
            "aggregate_internal_risk_score": round(aggregate_internal_risk, 4),
            "aggregate_causal_mitigability_score": round(aggregate_mitigability, 4),
        },
    )
