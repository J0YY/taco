from taco_demo.diligence_memo import build_diligence_memo
from taco_demo.maniskill_suite import build_maniskill_suite_cases
from taco_demo.quote_engine import generate_quote
from taco_demo.renewal_loop import INCIDENT_LOG, RUNTIME_EVENTS, renewal_summary
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application


def _metrics():
    return [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "test", {})
        for cert in DEMO_CERTIFICATES
    ]


def _quote():
    controls = {
        "reaudit_required_after_model_update": True,
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
    }
    metrics = _metrics()
    return generate_quote(default_application(), DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, controls)


def test_renewal_summary_links_runtime_compliance_to_pricing():
    summary = renewal_summary(_quote())
    assert summary["runtime_events"] == len(RUNTIME_EVENTS)
    assert summary["prevented_loss_usd"] > summary["incurred_loss_usd"]
    assert summary["re_audit_required"] is True
    assert summary["renewal_monthly_premium_usd"] > 0


def test_high_compliance_without_losses_reduces_renewal_premium():
    clean_events = [replace_event_status(event, "passed") for event in RUNTIME_EVENTS]
    quote = _quote()
    summary = renewal_summary(quote, runtime_events=clean_events, incidents=[])
    assert summary["compliance_score"] == 1.0
    assert summary["renewal_monthly_premium_usd"] < quote.final_monthly_premium_usd


def test_diligence_memo_includes_renewal_loop():
    app = default_application()
    metrics = _metrics()
    quote = _quote()
    memo = build_diligence_memo(app, DEMO_CERTIFICATES, metrics, quote, {"suite_size": 40, "cases": build_maniskill_suite_cases()})
    assert "Runtime Compliance And Renewal Loop" in memo
    assert "Runtime monitor events" in memo
    assert INCIDENT_LOG[0]["incident_id"] in memo


def replace_event_status(event, status):
    updated = dict(event)
    updated["status"] = status
    return updated
