from taco_demo.fundraise_readiness import build_fundraise_readiness, fundraise_readiness_rows
from taco_demo.investor_case import RESEARCH_FOUNDATIONS, UNDERWRITING_WORKFLOW, investor_summary
from taco_demo.maniskill_suite import build_maniskill_suite_cases
from taco_demo.quote_engine import generate_quote
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application


def _carrier_ready_dreamaudit_intake() -> dict[str, object]:
    return {
        "root": "/tmp/dreamaudit",
        "root_exists": True,
        "summary": {"certificates": 250},
        "readiness": {"readiness_score": 85, "status": "needs_more_evidence", "gaps": ["Less than half of certificates include minimality reports."]},
        "evidence_depth_ladder": [
            {"scan_limit": 250, "status": "needs_more_evidence"},
            {"scan_limit": 5000, "status": "carrier_review_ready"},
        ],
        "recommended_scan_limit": 5000,
    }


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


def test_fundraise_readiness_scores_artifact_backed_seed_package():
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
    readiness = build_fundraise_readiness(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_size": 40, "cases": build_maniskill_suite_cases()},
        _carrier_ready_dreamaudit_intake(),
    )

    assert readiness["score"] == 100
    assert readiness["posture"] == "seed_diligence_ready_with_live_evidence_caveats"
    assert readiness["gates_passed"] == readiness["gates_total"]
    assert readiness["caveats"] == ["Secure 2-3 design-partner reviews with robotics OEMs, brokers, MGAs, or carriers."]
    assert fundraise_readiness_rows(readiness)[0]["Status"] == "Pass"


def test_fundraise_readiness_requires_live_dreamaudit_scan_for_full_score():
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
    readiness = build_fundraise_readiness(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_size": 40, "cases": build_maniskill_suite_cases()},
    )

    assert readiness["score"] == 85
    assert readiness["posture"] == "credible_seed_demo_needs_live_dreamaudit_scan"
    assert "Run the DreamAudit Intake scan" in readiness["gaps"][0]


def test_fundraise_readiness_surfaces_gaps_for_empty_package():
    app = default_application()
    quote = generate_quote(app, [], {}, {})
    readiness = build_fundraise_readiness(app, [], [], quote, {"suite_size": 0, "cases": []}, scenarios=[], research_foundations=[])

    assert readiness["score"] < 50
    assert readiness["posture"] == "early_seed_story_needs_more_evidence"
    assert readiness["gaps"]
