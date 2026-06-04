from taco_demo.binder import issue_binder
from taco_demo.quote_engine import generate_quote
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import DEMO_CREATED_AT, InternalRiskMetrics, default_application, read_json, write_json
from taco_demo.scripts import bootstrap_demo_data


def test_dataclass_json_roundtrip_works(tmp_path):
    app = default_application()
    path = tmp_path / "application.json"
    write_json(app, path)
    assert read_json(path)["application_id"] == "APP-APEX-001"
    assert read_json(path)["created_at"] == DEMO_CREATED_AT


def test_bootstrap_force_is_application_deterministic(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap_demo_data, "create_all_demo_videos", lambda root: [])
    monkeypatch.setattr(
        bootstrap_demo_data,
        "write_maniskill_suite",
        lambda root, force=False: root / "maniskill_suite" / "manifest.json",
    )
    bootstrap_demo_data.bootstrap(tmp_path, force=True)
    first = read_json(tmp_path / "applications" / "APP-APEX-001.json")
    bootstrap_demo_data.bootstrap(tmp_path, force=True)
    second = read_json(tmp_path / "applications" / "APP-APEX-001.json")
    assert first == second


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
