from taco_demo.investor_case import RESEARCH_FOUNDATIONS, UNDERWRITING_WORKFLOW, investor_summary
from taco_demo.quote_engine import generate_quote
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application


def test_research_foundations_have_sources_and_translations():
    assert len(RESEARCH_FOUNDATIONS) >= 4
    for foundation in RESEARCH_FOUNDATIONS:
        assert foundation["claim"]
        assert foundation["url"].startswith("https://")
        assert "TACO" in foundation["taco_translation"]


def test_underwriting_workflow_spans_application_to_binder():
    artifacts = [item["artifact"] for item in UNDERWRITING_WORKFLOW]
    assert artifacts[0] == "InsuranceApplication JSON"
    assert "PolicyBinder JSON/Markdown" in artifacts[-1]


def test_investor_summary_contains_fundraise_proof_points():
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
    summary = investor_summary(app, DEMO_CERTIFICATES, metrics, quote)
    assert "evidence layer" in summary["fundraise_thesis"]
    assert len(summary["proof_points"]) >= 4
    assert summary["aggregate_internal_risk"] > 0
