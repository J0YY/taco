import io
import json
import zipfile
from dataclasses import replace

from taco_demo.data_room import (
    build_data_room_bundle,
    build_data_room_checklist,
    build_data_room_manifest,
    data_room_bundle_summary,
    data_room_rows,
    verify_data_room_bundle,
)
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


def test_fundraise_readiness_does_not_blame_dreamaudit_for_other_high_score_gaps():
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
        research_foundations=[],
    )

    assert readiness["score"] == 90
    assert readiness["posture"] == "seed_diligence_ready_with_targeted_evidence_gaps"
    assert readiness["gaps"] == ["Add primary-source research anchors for any methodology claim that investors will diligence."]


def test_fundraise_readiness_surfaces_gaps_for_empty_package():
    app = default_application()
    quote = generate_quote(app, [], {}, {})
    readiness = build_fundraise_readiness(app, [], [], quote, {"suite_size": 0, "cases": []}, scenarios=[], research_foundations=[])

    assert readiness["score"] < 50
    assert readiness["posture"] == "early_seed_story_needs_more_evidence"
    assert readiness["gaps"]


def test_data_room_checklist_tracks_internal_packet_and_external_gap():
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
    checklist = build_data_room_checklist(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_size": 40, "cases": build_maniskill_suite_cases()},
        _carrier_ready_dreamaudit_intake(),
    )

    assert checklist["internal_packet_score"] == 100
    assert checklist["internal_ready_items"] == checklist["internal_total_items"]
    assert checklist["external_pending_items"] == 1
    assert data_room_rows(checklist)[-1]["Status"] == "External Pending"


def test_data_room_checklist_marks_live_dreamaudit_missing_without_scan():
    app = default_application()
    quote = generate_quote(app, [], {}, {})
    checklist = build_data_room_checklist(app, [], [], quote, {"suite_size": 0, "cases": []})

    dreamaudit_item = next(item for item in checklist["items"] if item["artifact"] == "Live DreamAudit Corpus")
    assert dreamaudit_item["status"] == "needs_live_scan"
    assert checklist["internal_packet_score"] < 100


def test_data_room_manifest_exports_machine_readable_packet():
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
    manifest = build_data_room_manifest(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        _carrier_ready_dreamaudit_intake(),
    )

    assert manifest["manifest_id"] == "DR-APP-APEX-001"
    assert manifest["checklist"]["internal_packet_score"] == 100
    assert len(manifest["primary_certificates"]) == len(DEMO_CERTIFICATES)
    assert len(manifest["internal_metrics"]) == len(metrics)
    assert manifest["dreamaudit"]["recommended_scan_limit"] == 5000
    assert len(manifest["suite_summary"]["video_paths"]) == 40


def test_data_room_bundle_exports_auditable_zip_packet():
    app = default_application()
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "recorded_activation_forward_hooks", {})
        for cert in DEMO_CERTIFICATES
    ]
    controls = {
        "reaudit_required_after_model_update": True,
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
    }
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, controls)
    bundle = build_data_room_bundle(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        "# diligence memo\n",
        _carrier_ready_dreamaudit_intake(),
    )
    summary = data_room_bundle_summary(bundle)

    assert summary["contains_manifest"] is True
    assert summary["contains_memo"] is True
    assert summary["contains_video_index"] is True
    assert summary["contains_packet_index"] is True
    assert "packet/index.json" in summary["files"]
    assert "insurance/workflow_examples.json" in summary["files"]
    assert "research/sources.json" in summary["files"]
    assert f"certificates/{DEMO_CERTIFICATES[0].certificate_id}.json" in summary["files"]
    assert f"metrics/{metrics[0].certificate_id}.json" in summary["files"]

    with zipfile.ZipFile(io.BytesIO(bundle), mode="r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        index = json.loads(archive.read("packet/index.json"))
        readme = archive.read("README.md").decode("utf-8")
        metric = json.loads(archive.read(f"metrics/{metrics[0].certificate_id}.json"))

    assert manifest["manifest_id"] == "DR-APP-APEX-001"
    assert index["checksum_algorithm"] == "sha256"
    assert index["manifest_id"] == manifest["manifest_id"]
    assert manifest["dreamaudit"]["recommended_scan_limit"] == 5000
    assert metric["metrics_source"] == "recorded_activation_forward_hooks"
    assert "not an insurance offer" in readme
    assert verify_data_room_bundle(bundle)["valid"] is True


def test_data_room_bundle_verifier_detects_tampering():
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
    bundle = build_data_room_bundle(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        "# diligence memo\n",
    )

    tampered = io.BytesIO()
    with zipfile.ZipFile(io.BytesIO(bundle), mode="r") as original:
        with zipfile.ZipFile(tampered, mode="w", compression=zipfile.ZIP_DEFLATED) as modified:
            for name in original.namelist():
                payload = b'{"quote_id":"tampered"}' if name == "quote.json" else original.read(name)
                modified.writestr(name, payload)

    verification = verify_data_room_bundle(tampered.getvalue())

    assert verification["valid"] is False
    assert "Checksum mismatch: quote.json" in verification["issues"]


def test_data_room_bundle_verifier_fails_closed_on_malformed_zip():
    verification = verify_data_room_bundle(b"not a zip")

    assert verification["valid"] is False
    assert verification["file_count"] == 0
    assert verification["issues"][0].startswith("Invalid data-room packet:")


def test_data_room_bundle_verifier_rejects_empty_packet_index():
    required_files = [
        "README.md",
        "manifest.json",
        "application.json",
        "quote.json",
        "checklist.json",
        "diligence_memo.md",
        "insurance/workflow_examples.json",
        "research/sources.json",
        "suite/video_index.json",
        "dreamaudit/summary.json",
    ]
    for index_payload, expected_issue in [
        ("[]", "Invalid packet index: expected JSON object"),
        ("{}", "Invalid packet index: files must be a non-empty list"),
        ('{"files":[]}', "Invalid packet index: files must be a non-empty list"),
    ]:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in required_files:
                archive.writestr(name, b"")
            archive.writestr("packet/index.json", index_payload)

        verification = verify_data_room_bundle(buffer.getvalue())

        assert verification["valid"] is False
        assert expected_issue in verification["issues"]


def test_data_room_bundle_sanitizes_external_certificate_ids_in_zip_paths():
    app = default_application()
    certs = [
        replace(DEMO_CERTIFICATES[0], certificate_id="../../outside/FR-001"),
        replace(DEMO_CERTIFICATES[1], certificate_id="..//outside/FR-001"),
    ]
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "test", {})
        for cert in certs
    ]
    controls = {
        "reaudit_required_after_model_update": True,
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
    }
    quote = generate_quote(app, certs, {metric.certificate_id: metric for metric in metrics}, controls)

    bundle = build_data_room_bundle(
        app,
        certs,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        "# diligence memo\n",
    )
    files = data_room_bundle_summary(bundle)["files"]

    assert "certificates/outside_FR-001.json" in files
    assert "certificates/outside_FR-001__2.json" in files
    assert "metrics/outside_FR-001.json" in files
    assert "metrics/outside_FR-001__2.json" in files
    assert not any(name.startswith("../") or "/../" in name for name in files)
