from taco_demo.diligence_memo import build_diligence_memo
from taco_demo.insurance_scenarios import INSURANCE_SCENARIOS, scenario_summary
from taco_demo.maniskill_suite import build_maniskill_suite_cases
from taco_demo.quote_engine import generate_quote
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application


def test_insurance_scenarios_cover_10_end_to_end_workflows():
    assert len(INSURANCE_SCENARIOS) == 10
    assert scenario_summary()["scenarios"] == 10
    assert scenario_summary()["controls"] >= 8
    for scenario in INSURANCE_SCENARIOS:
        assert scenario["failure"]
        assert scenario["evidence_identified"]
        assert scenario["exclusion_if_missing"]
        assert len(scenario["workflow"]) >= 5
        assert scenario["pricing"]["without_controls_monthly_usd"] > scenario["pricing"]["with_controls_monthly_usd"]


def test_diligence_memo_includes_scenarios_and_suite_breadth():
    app = default_application()
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "test", {})
        for cert in DEMO_CERTIFICATES
    ]
    controls = {
        "reaudit_required_after_model_update": True,
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
    }
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, controls)
    memo = build_diligence_memo(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_size": 40, "cases": build_maniskill_suite_cases()},
    )
    assert "VC Readiness Gates" in memo
    assert "Readiness score:" in memo
    assert "VC Data Room Checklist" in memo
    assert "Ten Insurance Workflow Examples" in memo
    assert "IW-001" in memo
    assert "IW-010" in memo
    assert "Supplemental suite size: 40 replay videos" in memo
