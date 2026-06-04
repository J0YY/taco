from taco_demo.binder import issue_binder
from taco_demo.quote_engine import generate_quote
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application, read_json, write_json


def test_dataclass_json_roundtrip_works(tmp_path):
    app = default_application()
    path = tmp_path / "application.json"
    write_json(app, path)
    assert read_json(path)["application_id"] == "APP-APEX-001"


def test_binder_contains_application_quote_certificates_and_metrics(tmp_path):
    app = default_application()
    metrics = [InternalRiskMetrics(cert.certificate_id, 1.0, 0.5, 0.7, 0.8, 0.75, 0.45, "signature", True, "test", {}) for cert in DEMO_CERTIFICATES]
    quote = generate_quote(
        app,
        DEMO_CERTIFICATES,
        {metric.certificate_id: metric for metric in metrics},
        {
            "reaudit_required_after_model_update": True,
            "occlusion_risk_monitor_enabled": True,
            "language_override_sanitizer_enabled": True,
            "target_identity_confirmation_enabled": True,
        },
    )
    path = issue_binder(app, DEMO_CERTIFICATES, metrics, quote, tmp_path)
    binder = read_json(path)
    assert binder["application"]["application_id"] == app.application_id
    assert binder["quote"]["quote_id"] == quote.quote_id
    assert len(binder["certificates"]) == 3
    assert len(binder["internal_metrics"]) == 3
