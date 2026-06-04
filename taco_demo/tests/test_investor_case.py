import io
import hashlib
import json
import struct
import zipfile
from dataclasses import replace

from taco_demo.data_room import (
    MAX_ZIP_MEMBERS,
    MAX_ZIP_MEMBER_BYTES,
    PACKET_FORMAT_V1,
    PACKET_FORMAT_V2,
    PACKET_FORMAT_V3,
    PACKET_FORMAT_V4,
    PACKET_FORMAT_V5,
    PACKET_FORMAT_V6,
    PACKET_INDEX_PATH,
    REQUIRED_BUNDLE_FILES_V5,
    REQUIRED_BUNDLE_FILES_V4,
    REQUIRED_BUNDLE_FILES_V3,
    REQUIRED_BUNDLE_FILES_V2,
    REQUIRED_BUNDLE_FILES_V1,
    build_data_room_bundle,
    build_data_room_checklist,
    build_data_room_manifest,
    data_room_bundle_summary,
    data_room_rows,
    verify_data_room_bundle,
)
from taco_demo.design_partner_plan import build_design_partner_plan, design_partner_plan_rows
from taco_demo.diligence_memo import build_diligence_memo
from taco_demo.fundraise_readiness import build_fundraise_readiness, fundraise_readiness_rows
from taco_demo.investor_case import RESEARCH_FOUNDATIONS, UNDERWRITING_WORKFLOW, investor_summary
from taco_demo.investor_objections import build_investor_objection_register, investor_objection_rows
from taco_demo.maniskill_suite import build_maniskill_suite_cases
from taco_demo.methodology_evidence import build_methodology_evidence_map, methodology_evidence_rows
from taco_demo.pricing_diligence import build_pricing_diligence, pricing_control_rows, pricing_factor_rows
from taco_demo.quote_engine import generate_quote
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application
from taco_demo.seed_financing_plan import (
    TARGET_SEED_RAISE_USD,
    build_seed_financing_plan,
    seed_financing_milestone_rows,
    seed_financing_use_of_funds_rows,
)


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


def _mark_zip_member_encrypted(bundle: bytes, member_name: str) -> bytes:
    data = bytearray(bundle)
    target = member_name.encode("utf-8")
    position = 0
    while True:
        central_offset = data.find(b"PK\x01\x02", position)
        if central_offset == -1:
            raise AssertionError(f"ZIP member not found: {member_name}")
        name_length = struct.unpack("<H", data[central_offset + 28 : central_offset + 30])[0]
        extra_length = struct.unpack("<H", data[central_offset + 30 : central_offset + 32])[0]
        comment_length = struct.unpack("<H", data[central_offset + 32 : central_offset + 34])[0]
        name = data[central_offset + 46 : central_offset + 46 + name_length]
        if name == target:
            local_offset = struct.unpack("<I", data[central_offset + 42 : central_offset + 46])[0]
            local_flags = struct.unpack("<H", data[local_offset + 6 : local_offset + 8])[0]
            central_flags = struct.unpack("<H", data[central_offset + 8 : central_offset + 10])[0]
            data[local_offset + 6 : local_offset + 8] = struct.pack("<H", local_flags | 1)
            data[central_offset + 8 : central_offset + 10] = struct.pack("<H", central_flags | 1)
            return bytes(data)
        position = central_offset + 46 + name_length + extra_length + comment_length


def _corrupt_zip_member_payload(bundle: bytes, member_name: str) -> bytes:
    data = bytearray(bundle)
    target = member_name.encode("utf-8")
    position = 0
    while True:
        central_offset = data.find(b"PK\x01\x02", position)
        if central_offset == -1:
            raise AssertionError(f"ZIP member not found: {member_name}")
        name_length = struct.unpack("<H", data[central_offset + 28 : central_offset + 30])[0]
        extra_length = struct.unpack("<H", data[central_offset + 30 : central_offset + 32])[0]
        comment_length = struct.unpack("<H", data[central_offset + 32 : central_offset + 34])[0]
        name = data[central_offset + 46 : central_offset + 46 + name_length]
        if name == target:
            compressed_size = struct.unpack("<I", data[central_offset + 20 : central_offset + 24])[0]
            local_offset = struct.unpack("<I", data[central_offset + 42 : central_offset + 46])[0]
            local_name_length = struct.unpack("<H", data[local_offset + 26 : local_offset + 28])[0]
            local_extra_length = struct.unpack("<H", data[local_offset + 28 : local_offset + 30])[0]
            payload_start = local_offset + 30 + local_name_length + local_extra_length
            if compressed_size == 0:
                raise AssertionError(f"ZIP member has no compressed payload: {member_name}")
            data[payload_start + compressed_size // 2] ^= 0xFF
            return bytes(data)
        position = central_offset + 46 + name_length + extra_length + comment_length


def test_research_foundations_have_sources_and_translations():
    assert len(RESEARCH_FOUNDATIONS) >= 4
    for foundation in RESEARCH_FOUNDATIONS:
        assert foundation["claim"]
        assert foundation["url"].startswith("https://")
        assert "TACO" in foundation["taco_translation"]


def test_methodology_evidence_map_separates_backed_claims_from_open_risks():
    app = default_application()
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "demo_trace_fixture", {})
        for cert in DEMO_CERTIFICATES
    ]
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, {})
    evidence_map = build_methodology_evidence_map(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        _carrier_ready_dreamaudit_intake(),
    )
    rows = methodology_evidence_rows(evidence_map)

    assert evidence_map["map_id"] == "METHOD-APP-APEX-001"
    assert evidence_map["score"] >= 85
    assert "does not claim actuarial validation" in evidence_map["boundary"]
    assert len(evidence_map["claims"]) >= 6
    assert len(evidence_map["open_methodology_risks"]) >= 4
    assert any(claim["claim_id"] == "internal_activation_risk_path" for claim in evidence_map["claims"])
    assert all(row["Current Evidence"] for row in rows)
    assert all(claim["boundary"] for claim in evidence_map["claims"])
    claims_by_id = {claim["claim_id"]: claim for claim in evidence_map["claims"]}
    assert claims_by_id["live_corpus_transfer"]["status"] == "research_and_artifact_backed"


def test_methodology_evidence_map_does_not_treat_carrier_ready_dreamaudit_as_activation_evidence():
    app = default_application()
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "demo_trace_fixture", {})
        for cert in DEMO_CERTIFICATES
    ]
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, {})
    carrier_ready_intake = _carrier_ready_dreamaudit_intake()
    carrier_ready_intake["readiness"] = {"readiness_score": 100, "status": "carrier_review_ready", "gaps": []}
    evidence_map = build_methodology_evidence_map(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        carrier_ready_intake,
    )
    claims_by_id = {claim["claim_id"]: claim for claim in evidence_map["claims"]}

    assert claims_by_id["live_corpus_transfer"]["status"] == "research_and_artifact_backed"
    assert claims_by_id["internal_activation_risk_path"]["status"] == "demo_backed_needs_live_evidence"


def test_methodology_evidence_map_requires_real_activation_sources_for_every_primary_metric():
    app = default_application()
    metrics = [
        InternalRiskMetrics(
            cert.certificate_id,
            1.0,
            0.6,
            0.4,
            0.8,
            0.9,
            0.2,
            "signature",
            True,
            "recorded_activation_forward_hooks" if index == 0 else "demo_trace_fixture",
            {},
        )
        for index, cert in enumerate(DEMO_CERTIFICATES)
    ]
    metrics.append(
        InternalRiskMetrics("FR-EXTRA", 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "recorded_activation_forward_hooks", {})
    )
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, {})
    evidence_map = build_methodology_evidence_map(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        _carrier_ready_dreamaudit_intake(),
    )
    claims_by_id = {claim["claim_id"]: claim for claim in evidence_map["claims"]}

    assert claims_by_id["internal_activation_risk_path"]["status"] == "demo_backed_needs_live_evidence"


def test_methodology_evidence_map_flags_missing_live_and_internal_evidence():
    app = default_application()
    quote = generate_quote(app, DEMO_CERTIFICATES, {}, {})
    evidence_map = build_methodology_evidence_map(
        app,
        DEMO_CERTIFICATES,
        [],
        quote,
        {"suite_name": "empty", "suite_size": 0, "cases": []},
    )
    claims_by_id = {claim["claim_id"]: claim for claim in evidence_map["claims"]}

    assert evidence_map["score"] < 85
    assert claims_by_id["internal_activation_risk_path"]["status"] == "needs_work"
    assert claims_by_id["live_corpus_transfer"]["status"] == "needs_work"


def test_pricing_diligence_explains_quote_factors_and_control_deltas_without_actuarial_claim():
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
    pricing = build_pricing_diligence(app, DEMO_CERTIFICATES, metrics, quote)
    factor_rows = pricing_factor_rows(pricing)
    control_rows = pricing_control_rows(pricing)

    assert pricing["pricing_id"] == "PRICE-APP-APEX-001"
    assert pricing["all_controls_monthly_premium_usd"] == quote.final_monthly_premium_usd
    assert pricing["no_controls_monthly_premium_usd"] > pricing["all_controls_monthly_premium_usd"]
    assert pricing["aggregate_control_delta_usd"] > 0
    assert "not filed actuarial pricing" in pricing["boundary"]
    assert {row["Factor"] for row in factor_rows} == {
        "base_monthly_premium_usd",
        "deployment_multiplier",
        "behavioral_fragility_multiplier",
        "internal_risk_multiplier",
        "mitigation_discount_multiplier",
    }
    assert len(control_rows) == len(quote.required_controls)
    assert any(row["Delta"] > 0 for row in control_rows)
    assert all(row["Disabled Status"] == "approved_with_exclusions" for row in control_rows)


def test_investor_objection_register_links_pushback_to_evidence_and_gaps():
    app = default_application()
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "demo_trace_fixture", {})
        for cert in DEMO_CERTIFICATES
    ]
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, {})
    suite_manifest = {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()}
    readiness = build_fundraise_readiness(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, _carrier_ready_dreamaudit_intake())
    methodology_map = build_methodology_evidence_map(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, _carrier_ready_dreamaudit_intake())
    pricing = build_pricing_diligence(app, DEMO_CERTIFICATES, metrics, quote)
    design_partner_plan = build_design_partner_plan(app, quote)
    seed_financing_plan = build_seed_financing_plan(app, quote, readiness, design_partner_plan)
    register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    rows = investor_objection_rows(register)

    assert register["register_id"] == "OBJ-TACO-SEED-DILIGENCE"
    assert "not proof of signed customers" in register["boundary"]
    assert len(register["objections"]) >= 6
    assert {item["objection_id"] for item in register["objections"]} >= {
        "is_this_real_or_demo_theater",
        "where_is_the_buyer_pull",
        "is_pricing_actuarially_valid",
        "is_the_internals_path_real",
    }
    assert all(item["current_evidence"] for item in register["objections"])
    assert all(item["next_proof_to_collect"] for item in register["objections"])
    assert any(item["answer_strength"] == "demo_backed_needs_live_evidence" for item in register["objections"])
    assert all(row["Boundary"] for row in rows)


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
    design_partner_item = next(item for item in checklist["items"] if item["artifact"] == "Design-Partner References")
    assert "Structured broker/carrier/OEM pilot plan is attached" in design_partner_item["evidence"]


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
    assert manifest["design_partner_plan"]["status"] == "external_validation_pending"
    assert len(manifest["design_partner_plan"]["tracks"]) >= 3
    assert manifest["seed_financing_plan"]["target_raise_usd"] == TARGET_SEED_RAISE_USD
    assert "not committed financing" in manifest["seed_financing_plan"]["boundary"]
    assert manifest["methodology_evidence_map"]["score"] >= 85
    assert "does not claim actuarial validation" in manifest["methodology_evidence_map"]["boundary"]
    assert manifest["pricing_diligence"]["aggregate_control_delta_usd"] > 0
    assert "not filed actuarial pricing" in manifest["pricing_diligence"]["boundary"]
    assert manifest["investor_objection_register"]["register_id"] == "OBJ-TACO-SEED-DILIGENCE"
    assert len(manifest["investor_objection_register"]["objections"]) >= 6
    assert len(manifest["suite_summary"]["video_paths"]) == 40


def test_design_partner_plan_is_structured_without_claiming_signed_partners():
    app = default_application()
    quote = generate_quote(app, DEMO_CERTIFICATES, {}, {})
    plan = build_design_partner_plan(app, quote)
    rows = design_partner_plan_rows(plan)

    assert plan["plan_id"] == "DP-APP-APEX-001"
    assert plan["status"] == "external_validation_pending"
    assert "not evidence of signed design partners" in plan["boundary"]
    assert len(plan["tracks"]) == 3
    assert {track["track_id"] for track in plan["tracks"]} == {
        "robotics_oem_predeployment",
        "broker_mga_underwriting_desk",
        "carrier_reinsurer_model_risk",
    }
    assert len(plan["thirty_sixty_ninety_day_plan"]) == 3
    assert all(row["Commercial Signal"] for row in rows)


def test_seed_financing_plan_ties_five_million_round_to_milestones_without_claiming_commitments():
    app = default_application()
    quote = generate_quote(app, DEMO_CERTIFICATES, {}, {})
    plan = build_seed_financing_plan(app, quote, {"score": 85}, {"status": "external_validation_pending"})
    use_rows = seed_financing_use_of_funds_rows(plan)
    milestone_rows = seed_financing_milestone_rows(plan)

    assert plan["plan_id"] == "SEED-APP-APEX-001"
    assert plan["target_raise_usd"] == 5_000_000
    assert sum(item["amount_usd"] for item in plan["use_of_funds"]) == plan["target_raise_usd"]
    assert plan["estimated_runway_months"] == 18
    assert "not committed financing" in plan["boundary"]
    assert plan["current_diligence_posture"]["readiness_score"] == 85
    assert plan["current_diligence_posture"]["external_validation_required"] is True
    assert len(use_rows) >= 5
    assert len(milestone_rows) >= 4
    assert all(row["Diligence Evidence"] for row in use_rows)


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
    assert summary["packet_sha256"] == hashlib.sha256(bundle).hexdigest()
    assert "packet/index.json" in summary["files"]
    assert "commercial/design_partner_plan.json" in summary["files"]
    assert "commercial/seed_financing_plan.json" in summary["files"]
    assert "commercial/pricing_diligence.json" in summary["files"]
    assert "commercial/investor_objection_register.json" in summary["files"]
    assert "research/methodology_evidence_map.json" in summary["files"]
    assert "insurance/workflow_examples.json" in summary["files"]
    assert "research/sources.json" in summary["files"]
    assert f"certificates/{DEMO_CERTIFICATES[0].certificate_id}.json" in summary["files"]
    assert f"metrics/{metrics[0].certificate_id}.json" in summary["files"]

    with zipfile.ZipFile(io.BytesIO(bundle), mode="r") as archive:
        manifest = json.loads(archive.read("manifest.json"))
        index = json.loads(archive.read("packet/index.json"))
        readme = archive.read("README.md").decode("utf-8")
        metric = json.loads(archive.read(f"metrics/{metrics[0].certificate_id}.json"))
        design_partner_plan = json.loads(archive.read("commercial/design_partner_plan.json"))
        seed_financing_plan = json.loads(archive.read("commercial/seed_financing_plan.json"))
        pricing_diligence = json.loads(archive.read("commercial/pricing_diligence.json"))
        objection_register = json.loads(archive.read("commercial/investor_objection_register.json"))
        methodology_map = json.loads(archive.read("research/methodology_evidence_map.json"))

    assert manifest["manifest_id"] == "DR-APP-APEX-001"
    assert index["packet_format"] == PACKET_FORMAT_V6
    assert index["checksum_algorithm"] == "sha256"
    assert index["manifest_id"] == manifest["manifest_id"]
    assert manifest["dreamaudit"]["recommended_scan_limit"] == 5000
    assert design_partner_plan["plan_id"] == "DP-APP-APEX-001"
    assert design_partner_plan["status"] == "external_validation_pending"
    assert seed_financing_plan["plan_id"] == "SEED-APP-APEX-001"
    assert seed_financing_plan["target_raise_usd"] == 5_000_000
    assert pricing_diligence["pricing_id"] == "PRICE-APP-APEX-001"
    assert pricing_diligence["aggregate_control_delta_usd"] > 0
    assert objection_register["register_id"] == "OBJ-TACO-SEED-DILIGENCE"
    assert len(objection_register["objections"]) >= 6
    assert methodology_map["map_id"] == "METHOD-APP-APEX-001"
    assert methodology_map["score"] >= 85
    assert metric["metrics_source"] == "recorded_activation_forward_hooks"
    assert "not an insurance offer" in readme
    assert "not an insurance offer, filed actuarial product, rate adequacy opinion" in readme
    verification = verify_data_room_bundle(bundle)
    assert verification["valid"] is True
    assert verification["packet_sha256"] == hashlib.sha256(bundle).hexdigest()


def test_diligence_memo_includes_design_partner_and_seed_plan_boundaries():
    app = default_application()
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "test", {})
        for cert in DEMO_CERTIFICATES
    ]
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, {})
    memo = build_diligence_memo(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()},
        _carrier_ready_dreamaudit_intake(),
    )

    assert "## Design-Partner Diligence Plan" in memo
    assert "external_validation_pending" in memo
    assert "not evidence of signed design partners" in memo
    assert "robotics_oem_predeployment" in memo
    assert "## Seed Financing Plan" in memo
    assert "not committed financing" in memo
    assert "$5,000,000" in memo
    assert "## Methodology Evidence Map" in memo
    assert "does not claim actuarial validation" in memo
    assert "internal_activation_risk_path" in memo
    assert "## Pricing Diligence Sensitivity" in memo
    assert "not filed actuarial pricing" in memo
    assert "## Investor Objection Register" in memo
    assert "is_this_real_or_demo_theater" in memo


def test_data_room_bundle_verifier_rejects_tampered_packet_index_metadata():
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
    cases = [
        (
            "packet_format",
            "evil_format",
            "Invalid packet index: packet_format must be taco_data_room_zip_v1, taco_data_room_zip_v2, taco_data_room_zip_v3, taco_data_room_zip_v4, taco_data_room_zip_v5, or taco_data_room_zip_v6",
        ),
        ("checksum_algorithm", "md5", "Invalid packet index: checksum_algorithm must be sha256"),
        ("required_files", [], "Invalid packet index: required_files does not match packet requirements"),
        ("manifest_id", "DR-EVIL", "Invalid packet index: manifest_id does not match manifest.json"),
        ("indexed_file_count", 0, "Invalid packet index: indexed_file_count does not match files"),
        ("indexed_file_count", "16", "Invalid packet index: indexed_file_count must be an integer"),
    ]
    for key, value, expected_issue in cases:
        tampered = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(bundle), mode="r") as original:
            with zipfile.ZipFile(tampered, mode="w", compression=zipfile.ZIP_DEFLATED) as modified:
                for name in original.namelist():
                    payload = original.read(name)
                    if name == "packet/index.json":
                        index = json.loads(payload)
                        index[key] = value
                        payload = json.dumps(index).encode("utf-8")
                    modified.writestr(name, payload)

        verification = verify_data_room_bundle(tampered.getvalue())

        assert verification["valid"] is False
        assert expected_issue in verification["issues"]


def test_data_room_bundle_verifier_accepts_legacy_v1_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V1}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V1,
        "manifest_id": "DR-LEGACY",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V1 | {PACKET_INDEX_PATH}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in sorted(payloads.items())
        ],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
        archive.writestr(PACKET_INDEX_PATH, json.dumps(packet_index))

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is True
    assert verification["indexed_file_count"] == len(payloads)


def test_data_room_bundle_verifier_accepts_legacy_v2_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V2}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V2"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V2,
        "manifest_id": "DR-LEGACY-V2",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V2 | {PACKET_INDEX_PATH}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in sorted(payloads.items())
        ],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
        archive.writestr(PACKET_INDEX_PATH, json.dumps(packet_index))

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is True
    assert verification["indexed_file_count"] == len(payloads)


def test_data_room_bundle_verifier_accepts_legacy_v3_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V3}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V3"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V3,
        "manifest_id": "DR-LEGACY-V3",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V3 | {PACKET_INDEX_PATH}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in sorted(payloads.items())
        ],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
        archive.writestr(PACKET_INDEX_PATH, json.dumps(packet_index))

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is True
    assert verification["indexed_file_count"] == len(payloads)


def test_data_room_bundle_verifier_accepts_legacy_v4_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V4}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V4"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V4,
        "manifest_id": "DR-LEGACY-V4",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V4 | {PACKET_INDEX_PATH}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in sorted(payloads.items())
        ],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
        archive.writestr(PACKET_INDEX_PATH, json.dumps(packet_index))

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is True
    assert verification["indexed_file_count"] == len(payloads)


def test_data_room_bundle_verifier_accepts_legacy_v5_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V5}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V5"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V5,
        "manifest_id": "DR-LEGACY-V5",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V5 | {PACKET_INDEX_PATH}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in sorted(payloads.items())
        ],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
        archive.writestr(PACKET_INDEX_PATH, json.dumps(packet_index))

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is True
    assert verification["indexed_file_count"] == len(payloads)


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
    assert verification["packet_sha256"] == hashlib.sha256(b"not a zip").hexdigest()
    assert verification["issues"][0].startswith("Invalid data-room packet:")


def test_data_room_bundle_verifier_fails_closed_on_read_time_zip_errors():
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
    packet_index = {
        "files": [
            {
                "path": name,
                "bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
            }
            for name in required_files
        ]
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in required_files:
            archive.writestr(name, b"")
        archive.writestr("packet/index.json", json.dumps(packet_index))

    verification = verify_data_room_bundle(_mark_zip_member_encrypted(buffer.getvalue(), "packet/index.json"))

    assert verification["valid"] is False
    assert any(issue.startswith("Invalid data-room packet:") for issue in verification["issues"])


def test_data_room_bundle_verifier_fails_closed_on_corrupt_deflate_payloads():
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
    packet_index = {
        "files": [
            {
                "path": name,
                "bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
            }
            for name in required_files
        ]
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in required_files:
            archive.writestr(name, b"")
        archive.writestr("packet/index.json", json.dumps(packet_index))

    verification = verify_data_room_bundle(_corrupt_zip_member_payload(buffer.getvalue(), "packet/index.json"))

    assert verification["valid"] is False
    assert any(issue.startswith("Invalid data-room packet:") for issue in verification["issues"])


def test_data_room_bundle_verifier_rejects_oversized_members_before_reading():
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
    payloads = {name: b"" for name in required_files}
    payloads["manifest.json"] = b'{"manifest_id":"DR-TEST"}'
    payloads["huge.bin"] = b"x" * (MAX_ZIP_MEMBER_BYTES + 1)
    packet_index = {
        "packet_format": "taco_data_room_zip_v1",
        "manifest_id": "DR-TEST",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(required_files + ["packet/index.json"]),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in payloads.items()
        ],
    }
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in payloads.items():
            archive.writestr(name, payload)
        archive.writestr("packet/index.json", json.dumps(packet_index))

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is False
    assert verification["indexed_file_count"] == 0
    assert "ZIP member too large: huge.bin" in verification["issues"]
    assert "Packet index not read because ZIP size limits failed" in verification["issues"]


def test_data_room_bundle_verifier_stops_on_member_count_limit():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for index in range(MAX_ZIP_MEMBERS + 1):
            archive.writestr(f"extra-{index}.txt", b"")

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is False
    assert verification["file_count"] == MAX_ZIP_MEMBERS + 1
    assert verification["indexed_file_count"] == 0
    assert f"ZIP member count exceeds limit: {MAX_ZIP_MEMBERS + 1} > {MAX_ZIP_MEMBERS}" in verification["issues"]
    assert all("Missing required file" not in issue for issue in verification["issues"])


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
        ('{"files":null}', "Invalid packet index: files must be a non-empty list"),
        ('{"files":[]}', "Invalid packet index: files must be a non-empty list"),
    ]:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in required_files:
                payload = b'{"manifest_id":"DR-TEST"}' if name == "manifest.json" else b""
                archive.writestr(name, payload)
            archive.writestr("packet/index.json", index_payload)

        verification = verify_data_room_bundle(buffer.getvalue())

        assert verification["valid"] is False
        assert expected_issue in verification["issues"]


def test_data_room_bundle_verifier_rejects_unsafe_member_paths():
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
    for unsafe_name in ["", ".", "./evil.txt", "foo/.", "foo//bar", "..", "safe/..", "C:/evil.txt", "C:evil.txt"]:
        entries = {name: b"" for name in required_files}
        entries[unsafe_name] = b"indexed hostile member"
        packet_index = {
            "files": [
                {
                    "path": name,
                    "bytes": len(payload),
                    "sha256": hashlib.sha256(payload).hexdigest(),
                }
                for name, payload in entries.items()
            ]
        }
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, payload in entries.items():
                archive.writestr(name, payload)
            archive.writestr("packet/index.json", json.dumps(packet_index))

        verification = verify_data_room_bundle(buffer.getvalue())

        assert verification["valid"] is False
        assert f"Unsafe ZIP member path: {unsafe_name}" in verification["issues"]


def test_data_room_bundle_verifier_rejects_non_integer_byte_counts():
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
    for malformed_byte_count in [0.9, "0", False]:
        packet_index = {
            "packet_format": "taco_data_room_zip_v1",
            "manifest_id": "DR-TEST",
            "checksum_algorithm": "sha256",
            "indexed_file_count": len(required_files),
            "required_files": sorted(required_files + ["packet/index.json"]),
            "files": [
                {
                    "path": name,
                    "bytes": malformed_byte_count,
                    "sha256": hashlib.sha256(b"").hexdigest(),
                }
                for name in required_files
            ]
        }
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name in required_files:
                payload = b'{"manifest_id":"DR-TEST"}' if name == "manifest.json" else b""
                archive.writestr(name, payload)
            archive.writestr("packet/index.json", json.dumps(packet_index))

        verification = verify_data_room_bundle(buffer.getvalue())

        assert verification["valid"] is False
        assert f"Invalid packet index: file bytes must be an integer for {required_files[0]}" in verification["issues"]


def test_data_room_bundle_verifier_rejects_duplicate_packet_index_paths():
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
    files = []
    for name in required_files:
        files.append(
            {
                "path": name,
                "bytes": 0,
                "sha256": hashlib.sha256(b"tampered").hexdigest(),
            }
        )
        files.append(
            {
                "path": name,
                "bytes": 0,
                "sha256": hashlib.sha256(b"").hexdigest(),
            }
        )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in required_files:
            payload = b'{"manifest_id":"DR-TEST"}' if name == "manifest.json" else b""
            archive.writestr(name, payload)
        archive.writestr(
            "packet/index.json",
            json.dumps(
                {
                    "packet_format": "taco_data_room_zip_v1",
                    "manifest_id": "DR-TEST",
                    "checksum_algorithm": "sha256",
                    "indexed_file_count": len(files),
                    "required_files": sorted(required_files + ["packet/index.json"]),
                    "files": files,
                }
            ),
        )

    verification = verify_data_room_bundle(buffer.getvalue())

    assert verification["valid"] is False
    assert f"Duplicate packet index path: {required_files[0]}" in verification["issues"]
    assert f"Checksum mismatch: {required_files[0]}" in verification["issues"]


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
