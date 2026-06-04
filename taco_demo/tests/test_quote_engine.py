from dataclasses import replace

from taco_demo.quote_engine import behavioral_fragility_multiplier, generate_quote, required_control_for_failure, traditional_underwriting_status
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application


def metric(certificate_id: str, risk: float = 0.45, mitigability: float = 0.75) -> InternalRiskMetrics:
    return InternalRiskMetrics(certificate_id, 1.0, 0.5, 0.7, 0.8, mitigability, risk, "signature", True, "test", {})


def enabled_controls():
    return {
        "reaudit_required_after_model_update": True,
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
        "action_noise_envelope_monitor_enabled": True,
        "vision_shift_monitor_enabled": True,
    }


def test_no_telemetry_blocks_traditional_underwriting():
    assert traditional_underwriting_status(default_application())["status"] == "blocked_no_telemetry"
    quote = generate_quote(default_application(), [], {}, {})
    assert quote.status == "blocked_no_telemetry"


def test_lower_minimal_failure_cost_increases_behavioral_multiplier():
    cert = DEMO_CERTIFICATES[0]
    fragile = replace(cert, minimal_failure_cost=0.2)
    stable = replace(cert, minimal_failure_cost=0.5)
    assert behavioral_fragility_multiplier(fragile) > behavioral_fragility_multiplier(stable)


def test_higher_internal_risk_increases_quote():
    app = default_application()
    low = {cert.certificate_id: metric(cert.certificate_id, risk=0.2) for cert in DEMO_CERTIFICATES}
    high = {cert.certificate_id: metric(cert.certificate_id, risk=0.8) for cert in DEMO_CERTIFICATES}
    assert generate_quote(app, DEMO_CERTIFICATES, high, enabled_controls()).final_monthly_premium_usd > generate_quote(app, DEMO_CERTIFICATES, low, enabled_controls()).final_monthly_premium_usd


def test_enabling_required_monitors_lowers_premium():
    app = default_application()
    metrics = {cert.certificate_id: metric(cert.certificate_id, mitigability=0.8) for cert in DEMO_CERTIFICATES}
    disabled = enabled_controls()
    disabled["occlusion_risk_monitor_enabled"] = False
    assert generate_quote(app, DEMO_CERTIFICATES, metrics, enabled_controls()).final_monthly_premium_usd < generate_quote(app, DEMO_CERTIFICATES, metrics, disabled).final_monthly_premium_usd


def test_disabling_specific_controls_creates_exclusions():
    metrics = {cert.certificate_id: metric(cert.certificate_id) for cert in DEMO_CERTIFICATES}
    controls = enabled_controls()
    controls["occlusion_risk_monitor_enabled"] = False
    quote = generate_quote(default_application(), DEMO_CERTIFICATES, metrics, controls)
    assert any("FR-001" in exclusion for exclusion in quote.exclusions)


def test_dreamaudit_action_and_vision_failures_map_to_named_controls():
    assert required_control_for_failure("action_noise_counterfactual_failure") == "action_noise_envelope_monitor_enabled"
    assert required_control_for_failure("vision_perturbation_counterfactual_failure") == "vision_shift_monitor_enabled"


def test_action_and_vision_controls_create_specific_exclusions():
    action_cert = replace(DEMO_CERTIFICATES[0], certificate_id="DA-ACTION-001", failure_type="action_noise_counterfactual_failure")
    vision_cert = replace(DEMO_CERTIFICATES[0], certificate_id="DA-VISION-001", failure_type="vision_perturbation_counterfactual_failure")
    certs = [action_cert, vision_cert]
    metrics = {cert.certificate_id: metric(cert.certificate_id) for cert in certs}
    controls = enabled_controls()
    controls["action_noise_envelope_monitor_enabled"] = False
    controls["vision_shift_monitor_enabled"] = False

    quote = generate_quote(default_application(), certs, metrics, controls)

    assert "action_noise_envelope_monitor_enabled" in quote.required_controls
    assert "vision_shift_monitor_enabled" in quote.required_controls
    assert any("action-noise sensitivity" in exclusion for exclusion in quote.exclusions)
    assert any("vision-shift sensitivity" in exclusion for exclusion in quote.exclusions)
