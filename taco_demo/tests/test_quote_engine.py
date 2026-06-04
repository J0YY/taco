from taco_demo.quote_engine import (
    behavioral_fragility_multiplier,
    generate_quote,
    traditional_underwriting_status,
)
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application


def metric(cert_id: str, risk: float = 0.5, mitigability: float = 0.7):
    return InternalRiskMetrics(cert_id, 1.0, 0.5, 0.8, 0.8, mitigability, risk, "sig", True, "test", {})


def test_no_telemetry_blocks_traditional_underwriting():
    app = default_application()
    assert traditional_underwriting_status(app)["status"] == "blocked_no_telemetry"
    quote = generate_quote(app, [], {}, monitor_enabled=False)
    assert quote.status == "blocked_no_telemetry"


def test_monitor_discount_lowers_premium():
    app = default_application()
    metrics = {c.certificate_id: metric(c.certificate_id, mitigability=0.8) for c in DEMO_CERTIFICATES}
    controls = {"occlusion_risk_monitor_enabled": True, "language_override_sanitizer_enabled": True, "target_identity_confirmation_enabled": True}
    enabled = generate_quote(app, DEMO_CERTIFICATES, metrics, True, controls)
    disabled = generate_quote(app, DEMO_CERTIFICATES, metrics, False, {k: False for k in controls})
    assert enabled.final_monthly_premium_usd < disabled.final_monthly_premium_usd


def test_lower_minimal_cost_increases_behavioral_multiplier():
    assert behavioral_fragility_multiplier(0.2, 0.5) > behavioral_fragility_multiplier(0.5, 0.5)


def test_higher_internal_risk_increases_quote():
    app = default_application()
    low = {c.certificate_id: metric(c.certificate_id, risk=0.2) for c in DEMO_CERTIFICATES}
    high = {c.certificate_id: metric(c.certificate_id, risk=0.8) for c in DEMO_CERTIFICATES}
    controls = {"occlusion_risk_monitor_enabled": True, "language_override_sanitizer_enabled": True, "target_identity_confirmation_enabled": True}
    assert generate_quote(app, DEMO_CERTIFICATES, high, True, controls).final_monthly_premium_usd > generate_quote(app, DEMO_CERTIFICATES, low, True, controls).final_monthly_premium_usd


def test_required_controls_generated_from_failure_types():
    metrics = {c.certificate_id: metric(c.certificate_id) for c in DEMO_CERTIFICATES}
    quote = generate_quote(default_application(), DEMO_CERTIFICATES, metrics, True)
    assert "occlusion_risk_monitor_enabled" in quote.required_controls
    assert "language_override_sanitizer_enabled" in quote.required_controls
    assert "target_identity_confirmation_enabled" in quote.required_controls

