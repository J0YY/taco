import io
import hashlib
import json
import struct
import zipfile
from dataclasses import replace

from taco_demo.actuarial_readiness import (
    actuarial_cost_rows,
    actuarial_credibility_rows,
    actuarial_gate_rows,
    actuarial_validation_rows,
    build_actuarial_readiness_plan,
)
from taco_demo.buyer_roi import (
    build_buyer_roi_model,
    buyer_roi_proof_rows,
    buyer_roi_scenario_rows,
    buyer_value_driver_rows,
)
from taco_demo.capacity_roadmap import (
    build_capacity_roadmap,
    capacity_gate_rows,
    capacity_path_rows,
    capacity_phase_rows,
    regulatory_workstream_rows,
)
from taco_demo.claim_validation import (
    build_claim_validation_ledger,
    claim_validation_rows,
    claim_validation_summary_rows,
)
from taco_demo.commercial_model import (
    build_commercial_scale_model,
    commercial_gate_rows,
    commercial_market_rows,
    commercial_scenario_rows,
    commercial_segment_rows,
)
from taco_demo.commercial_traction import (
    build_commercial_traction_plan,
    commercial_traction_metric_rows,
    commercial_traction_package_rows,
    commercial_traction_rule_rows,
    commercial_traction_segment_rows,
)
from taco_demo.data_room import (
    MAX_ZIP_MEMBERS,
    MAX_ZIP_MEMBER_BYTES,
    PACKET_FORMAT_V1,
    PACKET_FORMAT_V2,
    PACKET_FORMAT_V3,
    PACKET_FORMAT_V4,
    PACKET_FORMAT_V5,
    PACKET_FORMAT_V6,
    PACKET_FORMAT_V7,
    PACKET_FORMAT_V8,
    PACKET_FORMAT_V9,
    PACKET_FORMAT_V10,
    PACKET_FORMAT_V11,
    PACKET_FORMAT_V12,
    PACKET_FORMAT_V13,
    PACKET_FORMAT_V14,
    PACKET_FORMAT_V15,
    PACKET_FORMAT_V16,
    PACKET_FORMAT_V17,
    PACKET_FORMAT_V18,
    PACKET_INDEX_PATH,
    REQUIRED_BUNDLE_FILES_V17,
    REQUIRED_BUNDLE_FILES_V16,
    REQUIRED_BUNDLE_FILES_V15,
    REQUIRED_BUNDLE_FILES_V14,
    REQUIRED_BUNDLE_FILES_V13,
    REQUIRED_BUNDLE_FILES_V12,
    REQUIRED_BUNDLE_FILES_V11,
    REQUIRED_BUNDLE_FILES_V10,
    REQUIRED_BUNDLE_FILES_V9,
    REQUIRED_BUNDLE_FILES_V8,
    REQUIRED_BUNDLE_FILES_V7,
    REQUIRED_BUNDLE_FILES_V6,
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
from taco_demo.external_validation import (
    build_external_validation_capture_kit,
    external_validation_ladder_rows,
    external_validation_scorecard_rows,
    external_validation_track_rows,
)
from taco_demo.fundraise_readiness import build_fundraise_readiness, fundraise_readiness_rows
from taco_demo.investor_case import RESEARCH_FOUNDATIONS, UNDERWRITING_WORKFLOW, investor_summary
from taco_demo.investor_objections import build_investor_objection_register, investor_objection_rows
from taco_demo.investor_proof_pipeline import (
    build_investor_proof_pipeline,
    investor_proof_gate_rows,
    investor_proof_reviewer_rows,
    investor_proof_stage_rows,
)
from taco_demo.maniskill_suite import build_maniskill_suite_cases
from taco_demo.methodology_evidence import build_methodology_evidence_map, methodology_evidence_rows
from taco_demo.pilot_walkthrough import build_pilot_walkthrough_playbook, pilot_walkthrough_rows
from taco_demo.pricing_diligence import build_pricing_diligence, pricing_control_rows, pricing_factor_rows
from taco_demo.quote_engine import generate_quote
from taco_demo.research_validation import (
    build_research_validation_plan,
    research_validation_hypothesis_rows,
    research_validation_rule_rows,
    research_validation_workstream_rows,
)
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.schemas import InternalRiskMetrics, default_application
from taco_demo.seed_financing_plan import (
    TARGET_SEED_RAISE_USD,
    build_seed_financing_plan,
    seed_financing_milestone_rows,
    seed_financing_use_of_funds_rows,
)
from taco_demo.security_plan import (
    build_enterprise_security_plan,
    security_control_rows,
    security_data_class_rows,
    security_gate_rows,
    security_question_rows,
    security_workflow_rows,
)
from taco_demo.technical_runbook import build_technical_diligence_runbook, technical_gate_rows, technical_step_rows


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


def test_actuarial_readiness_plan_maps_pricing_to_future_cost_and_data_quality_gates():
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
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    capacity_roadmap = build_capacity_roadmap(app, quote, pricing, commercial_model, pilot_walkthrough)
    plan = build_actuarial_readiness_plan(app, DEMO_CERTIFICATES, metrics, quote, pricing, capacity_roadmap)

    assert plan["plan_id"] == "ACT-APP-APEX-001"
    assert plan["status"] == "actuarial_readiness_defined_not_opinion"
    assert "not an actuarial opinion" in plan["boundary"]
    assert "rate adequacy opinion" in plan["boundary"]
    assert plan["current_evidence_summary"]["failure_certificate_count"] == len(DEMO_CERTIFICATES)
    assert plan["current_evidence_summary"]["pricing_artifact"] == "PRICE-APP-APEX-001"
    assert plan["current_evidence_summary"]["capacity_artifact"] == "CAP-APP-APEX-001"
    assert len(plan["future_cost_elements"]) >= 5
    assert len(plan["data_readiness_gates"]) >= 5
    assert {gate["source_anchor"] for gate in plan["data_readiness_gates"]} >= {
        "asop_53_pc_future_costs",
        "asop_23_data_quality",
        "asop_56_modeling",
        "asop_41_communications",
    }
    assert plan["credibility_ramp"][0]["phase"] == "demo_fixture_only"
    assert plan["credibility_ramp"][-1]["phase"] == "carrier_filing_or_program_review"
    assert any(source["source_id"] == "asop_53_pc_future_costs" for source in plan["source_material"])
    assert any(risk.startswith("No actuary") for risk in plan["open_actuarial_risks"])
    assert actuarial_cost_rows(plan)
    assert actuarial_gate_rows(plan)
    assert actuarial_credibility_rows(plan)[0]["Phase"] == "demo_fixture_only"
    assert actuarial_validation_rows(plan)


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


def test_pilot_walkthrough_playbook_turns_plan_into_capture_workflow_without_claiming_completed_pilots():
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
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    playbook = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    rows = pilot_walkthrough_rows(playbook)

    assert playbook["playbook_id"] == "WALK-APP-APEX-001"
    assert playbook["status"] == "external_walkthrough_ready_not_completed"
    assert "not evidence of completed pilots" in playbook["boundary"]
    assert len(playbook["meeting_agenda"]) == 7
    assert len(playbook["role_tracks"]) == len(design_partner_plan["tracks"])
    assert len(playbook["conversion_gates"]) >= 5
    assert "packet_sha256" in playbook["evidence_capture_form"]
    assert "claims_accepted" in playbook["evidence_capture_form"]
    assert any("actuarial pricing" in flag for flag in playbook["red_flags"])
    assert all(row["Evidence To Collect"] for row in rows)
    assert all(row["Reviewer Role"] for row in rows)


def test_external_validation_capture_kit_scores_reviewer_feedback_without_claiming_customers():
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
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    kit = build_external_validation_capture_kit(
        app,
        quote,
        design_partner_plan,
        pilot_walkthrough,
        {
            "manifest_id": "DR-APP-APEX-001",
            "packet_files": {
                "packet/index.json",
                "manifest.json",
                "diligence_memo.md",
                "research/methodology_evidence_map.json",
                "commercial/pricing_diligence.json",
                "commercial/pilot_walkthrough_playbook.json",
                "technical/technical_diligence_runbook.json",
            },
        },
    )

    assert kit["kit_id"] == "EXTVAL-APP-APEX-001"
    assert kit["status"] == "capture_ready_external_evidence_not_collected"
    assert "not evidence of signed customers" in kit["boundary"]
    assert kit["packet_context"]["packet_verification_required"] is True
    assert len(kit["packet_context"]["attached_required_review_artifacts"]) == kit["packet_context"]["minimum_external_packet_artifact_count"]
    assert len(kit["reviewer_tracks"]) == len(design_partner_plan["tracks"])
    assert sum(item["weight"] for item in kit["scorecard"]) == 100
    assert {item["gate"] for item in kit["scorecard"]} >= {
        "decision_authority",
        "artifact_usefulness",
        "commercial_document_path",
        "boundary_acceptance",
    }
    assert kit["loi_or_pilot_scope_template"]["document_status"] == "template_only_not_signed"
    assert "permission_to_quote_feedback" in kit["loi_or_pilot_scope_template"]["commercial_terms_to_fill"]
    assert kit["evidence_status_ladder"][-1]["status"] == "loi_or_paid_pilot"
    assert external_validation_track_rows(kit)
    assert external_validation_scorecard_rows(kit)[0]["Weight"] == 20
    assert external_validation_ladder_rows(kit)[-1]["Investor Weight"] == "round_anchor"


def test_commercial_scale_model_ties_market_context_to_revenue_scenarios_without_claiming_revenue():
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
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)

    assert model["model_id"] == "COMM-APP-APEX-001"
    assert model["status"] == "scenario_model_not_revenue_forecast"
    assert "not a market-size audit" in model["boundary"]
    assert "signed pipeline" in model["boundary"]
    assert model["base_case"]["modeled_arr_usd"] == 3_800_000
    assert model["target_raise_usd"] == 5_000_000
    assert len(model["market_context"]) >= 2
    assert len(model["buyer_segments"]) >= 4
    assert len(model["revenue_scenarios"]) == 3
    assert all(source["url"].startswith("https://") for source in model["source_material"])
    assert any("Insurance commissions" in assumption for assumption in model["assumptions_to_validate"])
    assert commercial_market_rows(model)
    assert commercial_segment_rows(model)
    assert commercial_scenario_rows(model)[1]["Modeled ARR"] == 3_800_000
    assert len(commercial_gate_rows(model)) >= 4


def test_buyer_roi_model_links_stakeholder_value_to_proof_gates_without_claiming_savings():
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
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    external_validation_kit = build_external_validation_capture_kit(
        app,
        quote,
        design_partner_plan,
        pilot_walkthrough,
        {"manifest_id": "DR-APP-APEX-001", "packet_files": []},
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    model = build_buyer_roi_model(
        app,
        quote,
        {"prevented_loss_usd": 74_000, "incurred_loss_usd": 12_000},
        commercial_model,
        external_validation_kit,
        pricing,
    )

    assert model["roi_id"] == "ROI-APP-APEX-001"
    assert model["status"] == "modeled_buyer_economics_not_validated_savings"
    assert "not guaranteed savings" in model["boundary"]
    assert model["assumption_set"]["first_year_cost_usd"] == 165_000
    assert model["assumption_set"]["control_credit_source"] == "pricing_diligence_no_controls_delta"
    assert model["assumption_set"]["control_credit_monthly_proxy_usd"] == pricing["aggregate_control_delta_usd"]
    assert model["assumption_set"]["control_credit_monthly_proxy_usd"] > 0
    assert len(model["buyer_value_drivers"]) == 4
    assert len(model["roi_scenarios"]) == 3
    assert next(item for item in model["roi_scenarios"] if item["scenario"] == "base")["net_value_usd"] > 0
    assert {gate["gate"] for gate in model["proof_gates"]} >= {
        "buyer_confirms_delay_cost",
        "evidence_ops_time_study",
        "control_credit_validated",
        "commercial_document_signed",
    }
    assert model["procurement_readiness"]["required_external_validation_status"] == "capture_ready_external_evidence_not_collected"
    assert "buyer ROI assumption confirmation" in model["procurement_readiness"]["documents_to_collect"]
    assert any(case["case"] == "loss_evidence_only" for case in model["sensitivity_cases"])
    assert buyer_value_driver_rows(model)
    assert buyer_roi_scenario_rows(model)[1]["Net Value"] > 0
    assert buyer_roi_proof_rows(model)


def test_claim_validation_ledger_bounds_investor_claims_and_overclaims():
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
    suite_manifest = {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()}
    dreamaudit_intake = _carrier_ready_dreamaudit_intake()
    readiness = build_fundraise_readiness(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    methodology_map = build_methodology_evidence_map(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    pricing = build_pricing_diligence(app, DEMO_CERTIFICATES, metrics, quote)
    design_partner_plan = build_design_partner_plan(app, quote)
    seed_financing_plan = build_seed_financing_plan(app, quote, readiness, design_partner_plan)
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    external_validation_kit = build_external_validation_capture_kit(
        app,
        quote,
        design_partner_plan,
        pilot_walkthrough,
        {"manifest_id": "DR-APP-APEX-001", "packet_files": []},
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    capacity_roadmap = build_capacity_roadmap(app, quote, pricing, commercial_model, pilot_walkthrough)
    actuarial_plan = build_actuarial_readiness_plan(app, DEMO_CERTIFICATES, metrics, quote, pricing, capacity_roadmap)
    buyer_roi_model = build_buyer_roi_model(app, quote, {"prevented_loss_usd": 74_000}, commercial_model, external_validation_kit, pricing)
    technical_runbook = build_technical_diligence_runbook(
        app,
        quote,
        suite_manifest,
        {"attached": True, "status": "carrier_review_ready"},
        {"plan_id": "SEC-APP-APEX-001"},
    )

    ledger = build_claim_validation_ledger(
        app,
        quote,
        readiness,
        methodology_map,
        pricing,
        commercial_model,
        buyer_roi_model,
        actuarial_plan,
        external_validation_kit,
        technical_runbook,
        dreamaudit_intake,
    )

    assert ledger["ledger_id"] == "CLAIM-APP-APEX-001"
    assert ledger["status"] == "claims_bounded_and_investor_ready_pending_external_validation"
    assert ledger["evidence_score"] >= 70
    assert "not proof of external adoption" in ledger["boundary"]
    assert ledger["claim_count"] == 10
    assert ledger["external_validation_needed"] >= 3
    assert any(claim["claim_id"] == "internals_based_risk_signal" for claim in ledger["claims"])
    assert any("Do not claim filed rates" in claim["disallowed_overclaim"] for claim in ledger["claims"])
    assert "TACO has signed customers or committed revenue." in ledger["pitch_usage"]["unsafe_wording"]
    assert claim_validation_rows(ledger)
    assert claim_validation_summary_rows(ledger)


def test_investor_proof_pipeline_turns_demo_artifacts_into_external_proof_workflow():
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
    suite_manifest = {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()}
    dreamaudit_intake = _carrier_ready_dreamaudit_intake()
    readiness = build_fundraise_readiness(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    methodology_map = build_methodology_evidence_map(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    pricing = build_pricing_diligence(app, DEMO_CERTIFICATES, metrics, quote)
    design_partner_plan = build_design_partner_plan(app, quote)
    seed_financing_plan = build_seed_financing_plan(app, quote, readiness, design_partner_plan)
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    external_validation_kit = build_external_validation_capture_kit(
        app,
        quote,
        design_partner_plan,
        pilot_walkthrough,
        {"manifest_id": "DR-APP-APEX-001", "packet_files": []},
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    capacity_roadmap = build_capacity_roadmap(app, quote, pricing, commercial_model, pilot_walkthrough)
    actuarial_plan = build_actuarial_readiness_plan(app, DEMO_CERTIFICATES, metrics, quote, pricing, capacity_roadmap)
    buyer_roi_model = build_buyer_roi_model(app, quote, {"prevented_loss_usd": 74_000}, commercial_model, external_validation_kit, pricing)
    technical_runbook = build_technical_diligence_runbook(
        app,
        quote,
        suite_manifest,
        {"attached": True, "status": "carrier_review_ready"},
        {"plan_id": "SEC-APP-APEX-001"},
    )
    claim_ledger = build_claim_validation_ledger(
        app,
        quote,
        readiness,
        methodology_map,
        pricing,
        commercial_model,
        buyer_roi_model,
        actuarial_plan,
        external_validation_kit,
        technical_runbook,
        dreamaudit_intake,
    )

    pipeline = build_investor_proof_pipeline(
        app,
        quote,
        readiness,
        design_partner_plan,
        pilot_walkthrough,
        external_validation_kit,
        claim_ledger,
        buyer_roi_model,
    )

    assert pipeline["pipeline_id"] == "PROOF-APP-APEX-001"
    assert pipeline["target_raise_usd"] == TARGET_SEED_RAISE_USD
    assert pipeline["status"] == "credible_seed_story_needs_external_proof_execution"
    assert "not evidence of signed customers" in pipeline["boundary"]
    assert pipeline["current_scores"]["current_artifact_score"] >= 70
    assert pipeline["current_scores"]["external_validation_gates_remaining"] >= 3
    assert len(pipeline["workflow_stages"]) == 5
    assert any(stage["stage"] == "2_live_evidence_attachment" for stage in pipeline["workflow_stages"])
    assert {target["track_id"] for target in pipeline["reviewer_targets"]} == {
        "robotics_oem_predeployment",
        "broker_mga_underwriting_desk",
        "carrier_reinsurer_model_risk",
    }
    assert any(gate["gate"] == "live_internals_or_dreamaudit_artifact" for gate in pipeline["proof_gates"])
    assert "two named external reviewer memos with packet SHA-256" in pipeline["minimum_fundraise_package"]
    assert any(rule["rule"] == "do_not_upgrade_from_meeting_alone" for rule in pipeline["data_room_upgrade_rules"])
    assert investor_proof_stage_rows(pipeline)
    assert investor_proof_reviewer_rows(pipeline)[0]["Target Count"] >= 1
    assert investor_proof_gate_rows(pipeline)


def test_research_validation_plan_makes_methodology_falsifiable_without_overclaiming():
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
    suite_manifest = {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()}
    dreamaudit_intake = _carrier_ready_dreamaudit_intake()
    readiness = build_fundraise_readiness(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    methodology_map = build_methodology_evidence_map(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    pricing = build_pricing_diligence(app, DEMO_CERTIFICATES, metrics, quote)
    design_partner_plan = build_design_partner_plan(app, quote)
    seed_financing_plan = build_seed_financing_plan(app, quote, readiness, design_partner_plan)
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    external_validation_kit = build_external_validation_capture_kit(
        app,
        quote,
        design_partner_plan,
        pilot_walkthrough,
        {"manifest_id": "DR-APP-APEX-001", "packet_files": []},
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    capacity_roadmap = build_capacity_roadmap(app, quote, pricing, commercial_model, pilot_walkthrough)
    actuarial_plan = build_actuarial_readiness_plan(app, DEMO_CERTIFICATES, metrics, quote, pricing, capacity_roadmap)
    buyer_roi_model = build_buyer_roi_model(app, quote, {"prevented_loss_usd": 74_000}, commercial_model, external_validation_kit, pricing)
    technical_runbook = build_technical_diligence_runbook(
        app,
        quote,
        suite_manifest,
        {"attached": True, "status": "carrier_review_ready"},
        {"plan_id": "SEC-APP-APEX-001"},
    )
    claim_ledger = build_claim_validation_ledger(
        app,
        quote,
        readiness,
        methodology_map,
        pricing,
        commercial_model,
        buyer_roi_model,
        actuarial_plan,
        external_validation_kit,
        technical_runbook,
        dreamaudit_intake,
    )
    pipeline = build_investor_proof_pipeline(
        app,
        quote,
        readiness,
        design_partner_plan,
        pilot_walkthrough,
        external_validation_kit,
        claim_ledger,
        buyer_roi_model,
    )

    plan = build_research_validation_plan(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        suite_manifest,
        methodology_map,
        claim_ledger,
        pipeline,
        dreamaudit_intake,
    )

    assert plan["plan_id"] == "RVAL-APP-APEX-001"
    assert plan["status"] == "research_validation_plan_ready_for_external_execution"
    assert "not proof of sim-to-real transfer" in plan["boundary"]
    assert plan["current_evidence_summary"]["research_validation_score"] >= 85
    assert plan["current_evidence_summary"]["real_activation_metric_count"] == len(metrics)
    assert len(plan["research_sources"]) == len(RESEARCH_FOUNDATIONS)
    assert {item["hypothesis_id"] for item in plan["hypotheses"]} >= {
        "simulation_replay_is_useful_predeployment_evidence",
        "internal_activations_add_signal",
        "packetized_evidence_changes_reviewer_workflow",
    }
    assert any(item["workstream"] == "activation_incrementality" for item in plan["validation_workstreams"])
    assert any(rule["rule"] == "internals_not_incremental" for rule in plan["downgrade_rules"])
    assert "TACO has proven sim-to-real transfer for learned-policy insurance." in plan["blocked_claims_until_validated"]
    assert research_validation_hypothesis_rows(plan)
    assert research_validation_workstream_rows(plan)
    assert research_validation_rule_rows(plan)


def test_commercial_traction_plan_converts_proof_workflows_into_countable_seed_traction():
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
    suite_manifest = {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()}
    dreamaudit_intake = _carrier_ready_dreamaudit_intake()
    readiness = build_fundraise_readiness(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    methodology_map = build_methodology_evidence_map(app, DEMO_CERTIFICATES, metrics, quote, suite_manifest, dreamaudit_intake)
    pricing = build_pricing_diligence(app, DEMO_CERTIFICATES, metrics, quote)
    design_partner_plan = build_design_partner_plan(app, quote)
    seed_financing_plan = build_seed_financing_plan(app, quote, readiness, design_partner_plan)
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    external_validation_kit = build_external_validation_capture_kit(
        app,
        quote,
        design_partner_plan,
        pilot_walkthrough,
        {"manifest_id": "DR-APP-APEX-001", "packet_files": []},
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    capacity_roadmap = build_capacity_roadmap(app, quote, pricing, commercial_model, pilot_walkthrough)
    actuarial_plan = build_actuarial_readiness_plan(app, DEMO_CERTIFICATES, metrics, quote, pricing, capacity_roadmap)
    buyer_roi_model = build_buyer_roi_model(app, quote, {"prevented_loss_usd": 74_000}, commercial_model, external_validation_kit, pricing)
    technical_runbook = build_technical_diligence_runbook(
        app,
        quote,
        suite_manifest,
        {"attached": True, "status": "carrier_review_ready"},
        {"plan_id": "SEC-APP-APEX-001"},
    )
    claim_ledger = build_claim_validation_ledger(
        app,
        quote,
        readiness,
        methodology_map,
        pricing,
        commercial_model,
        buyer_roi_model,
        actuarial_plan,
        external_validation_kit,
        technical_runbook,
        dreamaudit_intake,
    )
    pipeline = build_investor_proof_pipeline(
        app,
        quote,
        readiness,
        design_partner_plan,
        pilot_walkthrough,
        external_validation_kit,
        claim_ledger,
        buyer_roi_model,
    )
    research_plan = build_research_validation_plan(
        app,
        DEMO_CERTIFICATES,
        metrics,
        quote,
        suite_manifest,
        methodology_map,
        claim_ledger,
        pipeline,
        dreamaudit_intake,
    )

    traction_plan = build_commercial_traction_plan(
        app,
        quote,
        commercial_model,
        buyer_roi_model,
        pipeline,
        external_validation_kit,
        claim_ledger,
        research_plan,
        design_partner_plan,
        seed_financing_plan,
    )

    assert traction_plan["plan_id"] == "TRACT-APP-APEX-001"
    assert traction_plan["status"] == "traction_operating_plan_ready_not_revenue_claim"
    assert "not evidence of signed customers" in traction_plan["boundary"]
    assert traction_plan["target_raise_usd"] == TARGET_SEED_RAISE_USD
    assert sum(segment["target_prospects"] for segment in traction_plan["icp_segments"]) == 34
    assert {segment["segment_id"] for segment in traction_plan["icp_segments"]} >= {
        "robotics_oem_predeployment",
        "broker_mga_submission_desk",
        "carrier_reinsurer_model_risk",
        "enterprise_risk_procurement",
    }
    assert any(package["package_id"] == "policy_evidence_sprint" and package["price_usd"] == 45_000 for package in traction_plan["commercial_packages"])
    assert any(metric["metric"] == "paid_pilot_scopes_or_lois" for metric in traction_plan["weekly_metrics"])
    assert any(rule["rule"] == "packet_fingerprinted_review" for rule in traction_plan["counting_rules"])
    assert "at least two paid or written pilot scopes tied to named ICP segments" in traction_plan["minimum_countable_seed_package"]
    assert any(link["source_artifact"] == "PROOF-APP-APEX-001" for link in traction_plan["proof_gate_links"])
    assert commercial_traction_segment_rows(traction_plan)
    assert commercial_traction_package_rows(traction_plan)
    assert commercial_traction_metric_rows(traction_plan)
    assert commercial_traction_rule_rows(traction_plan)


def test_capacity_roadmap_separates_evidence_revenue_from_insurance_authority():
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
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    roadmap = build_capacity_roadmap(app, quote, pricing, commercial_model, pilot_walkthrough)

    assert roadmap["roadmap_id"] == "CAP-APP-APEX-001"
    assert roadmap["status"] == "capacity_path_defined_not_committed"
    assert "not legal advice" in roadmap["boundary"]
    assert "carrier capacity" in roadmap["boundary"]
    assert len(roadmap["recommended_sequence"]) == 4
    assert roadmap["recommended_sequence"][0]["phase"] == "phase_0_evidence_vendor"
    assert "binder issuance for real insureds" in roadmap["recommended_sequence"][0]["blocked_outputs_until_approved"]
    assert {path["path"] for path in roadmap["capacity_paths"]} >= {
        "evidence_vendor",
        "licensed_broker_or_referral_partner",
        "mga_mgu_fronting",
        "carrier_reinsurer_product_path",
    }
    assert any("SERFF" in source["fact_used"] for source in roadmap["source_material"])
    assert all(source["url"].startswith("https://") for source in roadmap["source_material"])
    assert len(roadmap["regulatory_workstreams"]) >= 4
    assert len(roadmap["readiness_gates"]) >= 4
    assert roadmap["links_to_existing_artifacts"]["pricing_boundary"] == "PRICE-APP-APEX-001"
    assert capacity_phase_rows(roadmap)
    assert capacity_path_rows(roadmap)
    assert regulatory_workstream_rows(roadmap)
    assert capacity_gate_rows(roadmap)


def test_enterprise_security_plan_maps_sensitive_evidence_to_control_backlog_without_claiming_soc2():
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
    objection_register = build_investor_objection_register(
        readiness,
        methodology_map,
        pricing,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough = build_pilot_walkthrough_playbook(
        app,
        quote,
        design_partner_plan,
        objection_register,
        methodology_map,
        pricing,
    )
    commercial_model = build_commercial_scale_model(app, quote, readiness, seed_financing_plan, pilot_walkthrough)
    capacity_roadmap = build_capacity_roadmap(app, quote, pricing, commercial_model, pilot_walkthrough)
    plan = build_enterprise_security_plan(
        app,
        quote,
        {"manifest_id": "DR-APP-APEX-001", "primary_certificates": DEMO_CERTIFICATES, "internal_metrics": metrics},
        {"attached": True, "status": "carrier_review_ready"},
        capacity_roadmap,
    )

    assert plan["plan_id"] == "SEC-APP-APEX-001"
    assert plan["status"] == "security_plan_defined_not_audited"
    assert "not SOC 2 certification" in plan["boundary"]
    assert "production control attestation" in plan["boundary"]
    assert set(plan["trust_posture"]["nist_csf_functions"]) == {"govern", "identify", "protect", "detect", "respond", "recover"}
    assert set(plan["trust_posture"]["soc2_categories"]) == {
        "security",
        "availability",
        "processing_integrity",
        "confidentiality",
        "privacy",
    }
    assert len(plan["sensitive_data_classes"]) >= 4
    assert len(plan["control_backlog"]) >= 7
    assert any(control["control_id"] == "packet_chain_of_custody" for control in plan["control_backlog"])
    assert any(item["data_class"] == "model_activation_traces" for item in plan["sensitive_data_classes"])
    assert all(source["url"].startswith("https://") for source in plan["source_material"])
    assert any("role-scoped" in gate["proof_required"] for gate in plan["seed_round_security_gates"])
    assert security_data_class_rows(plan)
    assert security_control_rows(plan)
    assert security_workflow_rows(plan)
    assert security_question_rows(plan)
    assert security_gate_rows(plan)


def test_technical_diligence_runbook_defines_local_and_live_reproduction_gates():
    app = default_application()
    metrics = [
        InternalRiskMetrics(cert.certificate_id, 1.0, 0.6, 0.4, 0.8, 0.9, 0.2, "signature", True, "demo_trace_fixture", {})
        for cert in DEMO_CERTIFICATES
    ]
    quote = generate_quote(app, DEMO_CERTIFICATES, {metric.certificate_id: metric for metric in metrics}, {})
    suite_manifest = {"suite_name": "suite", "suite_size": 40, "cases": build_maniskill_suite_cases()}
    security_plan = {
        "plan_id": "SEC-APP-APEX-001",
        "control_backlog": [{"control_id": "packet_chain_of_custody"} for _ in range(7)],
    }
    runbook = build_technical_diligence_runbook(
        app,
        quote,
        suite_manifest,
        {"attached": True, "status": "carrier_review_ready"},
        security_plan,
    )
    rows = technical_step_rows(runbook)
    gates = technical_gate_rows(runbook)

    assert runbook["runbook_id"] == "TECH-APP-APEX-001"
    assert runbook["status"] == "local_reproducibility_defined_live_evidence_optional"
    assert "not proof of live customer deployment" in runbook["boundary"]
    assert len(runbook["local_repro_steps"]) >= 7
    assert len(runbook["live_evidence_steps"]) >= 3
    assert any(step["step_id"] == "run_full_test_suite" for step in runbook["local_repro_steps"])
    assert any(step["step_id"] == "activation_recorder_trace_export" for step in runbook["live_evidence_steps"])
    assert runbook["expected_current_counts"]["maniskill_suite_size"] == 40
    assert runbook["expected_current_counts"]["dreamaudit_attached"] is True
    assert runbook["expected_current_counts"]["security_control_backlog"] == 7
    assert any(gate["gate"] == "packet_verifier_valid" for gate in runbook["pass_fail_gates"])
    assert all(row["Expected Result"] for row in rows)
    assert all(gate["Pass Condition"] and gate["Fail Condition"] for gate in gates)


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
    assert manifest["research_validation_plan"]["plan_id"] == "RVAL-APP-APEX-001"
    assert "not proof of sim-to-real transfer" in manifest["research_validation_plan"]["boundary"]
    assert any(item["workstream"] == "control_effectiveness_replication" for item in manifest["research_validation_plan"]["validation_workstreams"])
    assert manifest["commercial_traction_plan"]["plan_id"] == "TRACT-APP-APEX-001"
    assert "not evidence of signed customers" in manifest["commercial_traction_plan"]["boundary"]
    assert any(package["package_id"] == "policy_evidence_sprint" for package in manifest["commercial_traction_plan"]["commercial_packages"])
    assert manifest["claim_validation_ledger"]["ledger_id"] == "CLAIM-APP-APEX-001"
    assert "disallowed overclaims" in manifest["claim_validation_ledger"]["boundary"]
    assert any(claim["claim_id"] == "buyer_roi_economic_case" for claim in manifest["claim_validation_ledger"]["claims"])
    assert manifest["investor_proof_pipeline"]["pipeline_id"] == "PROOF-APP-APEX-001"
    assert "not evidence of signed customers" in manifest["investor_proof_pipeline"]["boundary"]
    assert any(gate["gate"] == "commercial_conversion_document" for gate in manifest["investor_proof_pipeline"]["proof_gates"])
    assert manifest["pricing_diligence"]["aggregate_control_delta_usd"] > 0
    assert "not filed actuarial pricing" in manifest["pricing_diligence"]["boundary"]
    assert manifest["investor_objection_register"]["register_id"] == "OBJ-TACO-SEED-DILIGENCE"
    assert len(manifest["investor_objection_register"]["objections"]) >= 6
    assert manifest["pilot_walkthrough_playbook"]["playbook_id"] == "WALK-APP-APEX-001"
    assert "not evidence of completed pilots" in manifest["pilot_walkthrough_playbook"]["boundary"]
    assert manifest["commercial_scale_model"]["model_id"] == "COMM-APP-APEX-001"
    assert "signed pipeline" in manifest["commercial_scale_model"]["boundary"]
    assert manifest["commercial_scale_model"]["base_case"]["modeled_arr_usd"] == 3_800_000
    assert manifest["capacity_roadmap"]["roadmap_id"] == "CAP-APP-APEX-001"
    assert "not legal advice" in manifest["capacity_roadmap"]["boundary"]
    assert manifest["enterprise_security_plan"]["plan_id"] == "SEC-APP-APEX-001"
    assert "not SOC 2 certification" in manifest["enterprise_security_plan"]["boundary"]
    assert manifest["technical_diligence_runbook"]["runbook_id"] == "TECH-APP-APEX-001"
    assert "not proof of live customer deployment" in manifest["technical_diligence_runbook"]["boundary"]
    assert manifest["external_validation_capture_kit"]["kit_id"] == "EXTVAL-APP-APEX-001"
    assert "not evidence of signed customers" in manifest["external_validation_capture_kit"]["boundary"]
    assert sum(item["weight"] for item in manifest["external_validation_capture_kit"]["scorecard"]) == 100
    assert manifest["actuarial_readiness_plan"]["plan_id"] == "ACT-APP-APEX-001"
    assert "not an actuarial opinion" in manifest["actuarial_readiness_plan"]["boundary"]
    assert any(source["source_id"] == "asop_56_modeling" for source in manifest["actuarial_readiness_plan"]["source_material"])
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
    assert "commercial/pilot_walkthrough_playbook.json" in summary["files"]
    assert "commercial/commercial_scale_model.json" in summary["files"]
    assert "commercial/capacity_roadmap.json" in summary["files"]
    assert "commercial/enterprise_security_plan.json" in summary["files"]
    assert "commercial/external_validation_capture_kit.json" in summary["files"]
    assert "commercial/actuarial_readiness_plan.json" in summary["files"]
    assert "commercial/buyer_roi_model.json" in summary["files"]
    assert "commercial/investor_proof_pipeline.json" in summary["files"]
    assert "commercial/commercial_traction_plan.json" in summary["files"]
    assert "research/claim_validation_ledger.json" in summary["files"]
    assert "research/research_validation_plan.json" in summary["files"]
    assert "technical/technical_diligence_runbook.json" in summary["files"]
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
        pilot_walkthrough = json.loads(archive.read("commercial/pilot_walkthrough_playbook.json"))
        commercial_model = json.loads(archive.read("commercial/commercial_scale_model.json"))
        capacity_roadmap = json.loads(archive.read("commercial/capacity_roadmap.json"))
        enterprise_security_plan = json.loads(archive.read("commercial/enterprise_security_plan.json"))
        external_validation_kit = json.loads(archive.read("commercial/external_validation_capture_kit.json"))
        actuarial_plan = json.loads(archive.read("commercial/actuarial_readiness_plan.json"))
        buyer_roi_model = json.loads(archive.read("commercial/buyer_roi_model.json"))
        investor_proof_pipeline = json.loads(archive.read("commercial/investor_proof_pipeline.json"))
        commercial_traction_plan = json.loads(archive.read("commercial/commercial_traction_plan.json"))
        claim_validation_ledger = json.loads(archive.read("research/claim_validation_ledger.json"))
        research_validation_plan = json.loads(archive.read("research/research_validation_plan.json"))
        technical_runbook = json.loads(archive.read("technical/technical_diligence_runbook.json"))
        methodology_map = json.loads(archive.read("research/methodology_evidence_map.json"))

    assert manifest["manifest_id"] == "DR-APP-APEX-001"
    assert index["packet_format"] == PACKET_FORMAT_V18
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
    assert pilot_walkthrough["playbook_id"] == "WALK-APP-APEX-001"
    assert pilot_walkthrough["status"] == "external_walkthrough_ready_not_completed"
    assert "not evidence of completed pilots" in pilot_walkthrough["boundary"]
    assert commercial_model["model_id"] == "COMM-APP-APEX-001"
    assert commercial_model["status"] == "scenario_model_not_revenue_forecast"
    assert commercial_model["base_case"]["modeled_arr_usd"] == 3_800_000
    assert capacity_roadmap["roadmap_id"] == "CAP-APP-APEX-001"
    assert capacity_roadmap["status"] == "capacity_path_defined_not_committed"
    assert "not legal advice" in capacity_roadmap["boundary"]
    assert enterprise_security_plan["plan_id"] == "SEC-APP-APEX-001"
    assert enterprise_security_plan["status"] == "security_plan_defined_not_audited"
    assert "not SOC 2 certification" in enterprise_security_plan["boundary"]
    assert technical_runbook["runbook_id"] == "TECH-APP-APEX-001"
    assert technical_runbook["status"] == "local_reproducibility_defined_live_evidence_optional"
    assert any(step["step_id"] == "verify_data_room_packet" for step in technical_runbook["local_repro_steps"])
    assert external_validation_kit["kit_id"] == "EXTVAL-APP-APEX-001"
    assert external_validation_kit["status"] == "capture_ready_external_evidence_not_collected"
    assert external_validation_kit["loi_or_pilot_scope_template"]["document_status"] == "template_only_not_signed"
    assert any(item["gate"] == "commercial_document_path" for item in external_validation_kit["scorecard"])
    assert actuarial_plan["plan_id"] == "ACT-APP-APEX-001"
    assert actuarial_plan["status"] == "actuarial_readiness_defined_not_opinion"
    assert any(gate["gate"] == "data_quality_reviewed" for gate in actuarial_plan["data_readiness_gates"])
    assert manifest["buyer_roi_model"]["roi_id"] == "ROI-APP-APEX-001"
    assert "not guaranteed savings" in manifest["buyer_roi_model"]["boundary"]
    assert any(gate["gate"] == "commercial_document_signed" for gate in manifest["buyer_roi_model"]["proof_gates"])
    assert buyer_roi_model["roi_id"] == "ROI-APP-APEX-001"
    assert buyer_roi_model["status"] == "modeled_buyer_economics_not_validated_savings"
    assert next(item for item in buyer_roi_model["roi_scenarios"] if item["scenario"] == "base")["net_value_usd"] > 0
    assert investor_proof_pipeline["pipeline_id"] == "PROOF-APP-APEX-001"
    assert investor_proof_pipeline["status"] == "credible_seed_story_needs_external_proof_execution"
    assert any(stage["stage"] == "4_seed_round_readiness" for stage in investor_proof_pipeline["workflow_stages"])
    assert any(rule["rule"] == "internals_claim_requires_trace" for rule in investor_proof_pipeline["data_room_upgrade_rules"])
    assert claim_validation_ledger["ledger_id"] == "CLAIM-APP-APEX-001"
    assert claim_validation_ledger["status"] == "claims_bounded_and_investor_ready_pending_external_validation"
    assert any(claim["claim_id"] == "external_validation_status" for claim in claim_validation_ledger["claims"])
    assert research_validation_plan["plan_id"] == "RVAL-APP-APEX-001"
    assert research_validation_plan["status"] == "research_validation_plan_ready_for_external_execution"
    assert any(item["hypothesis_id"] == "internal_activations_add_signal" for item in research_validation_plan["hypotheses"])
    assert any(rule["rule"] == "sim_to_real_failure_mismatch" for rule in research_validation_plan["downgrade_rules"])
    assert commercial_traction_plan["plan_id"] == "TRACT-APP-APEX-001"
    assert commercial_traction_plan["status"] == "traction_operating_plan_ready_not_revenue_claim"
    assert any(rule["rule"] == "signed_or_paid_commercial_artifact" for rule in commercial_traction_plan["counting_rules"])
    assert any(metric["metric"] == "verified_packet_walkthroughs" for metric in commercial_traction_plan["weekly_metrics"])
    assert methodology_map["map_id"] == "METHOD-APP-APEX-001"
    assert methodology_map["score"] >= 85
    assert metric["metrics_source"] == "recorded_activation_forward_hooks"
    assert "not an insurance offer" in readme
    assert "not an insurance offer, filed actuarial product, rate adequacy opinion" in readme
    assert "commercial/buyer_roi_model.json" in readme
    assert "commercial/investor_proof_pipeline.json" in readme
    assert "commercial/commercial_traction_plan.json" in readme
    assert "research/claim_validation_ledger.json" in readme
    assert "research/research_validation_plan.json" in readme
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
    assert "## Research Validation Plan" in memo
    assert "research_plan_strong_local_basis_needs_partner_validation" in memo
    assert "activation_incrementality" in memo
    assert "sim_to_real_failure_mismatch" in memo
    assert "## Investor Claim Validation Ledger" in memo
    assert "claims_bounded_and_investor_ready_pending_external_validation" in memo
    assert "buyer_roi_economic_case" in memo
    assert "Do not claim guaranteed savings" in memo
    assert "## Investor Proof Pipeline" in memo
    assert "credible_seed_story_needs_external_proof_execution" in memo
    assert "live_internals_or_dreamaudit_artifact" in memo
    assert "packet_reproduced_by_external_reviewer" in memo
    assert "## Commercial Traction Plan" in memo
    assert "traction_operating_plan_ready_not_revenue_claim" in memo
    assert "policy_evidence_sprint" in memo
    assert "packet_fingerprinted_review" in memo
    assert "## Pricing Diligence Sensitivity" in memo
    assert "not filed actuarial pricing" in memo
    assert "## Actuarial Readiness Plan" in memo
    assert "actuarial_readiness_defined_not_opinion" in memo
    assert "data_quality_reviewed" in memo
    assert "carrier_filing_or_program_review" in memo
    assert "## Buyer ROI Model" in memo
    assert "modeled_buyer_economics_not_validated_savings" in memo
    assert "buyer_confirms_delay_cost" in memo
    assert "commercial_document_signed" in memo
    assert "## Investor Objection Register" in memo
    assert "is_this_real_or_demo_theater" in memo
    assert "## Pilot Walkthrough Playbook" in memo
    assert "not evidence of completed pilots" in memo
    assert "feedback_memo_collected" in memo
    assert "## Commercial Scale Model" in memo
    assert "scenario_model_not_revenue_forecast" in memo
    assert "base_evidence_platform" in memo
    assert "## Insurance Capacity Roadmap" in memo
    assert "capacity_path_defined_not_committed" in memo
    assert "phase_0_evidence_vendor" in memo
    assert "## Enterprise Security Plan" in memo
    assert "security_plan_defined_not_audited" in memo
    assert "packet_chain_of_custody" in memo
    assert "## Technical Diligence Runbook" in memo
    assert "local_reproducibility_defined_live_evidence_optional" in memo
    assert "run_full_test_suite" in memo
    assert "## External Validation Capture Kit" in memo
    assert "capture_ready_external_evidence_not_collected" in memo
    assert "commercial_document_path" in memo
    assert "loi_or_paid_pilot" in memo


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
            "Invalid packet index: packet_format must be taco_data_room_zip_v1, taco_data_room_zip_v2, taco_data_room_zip_v3, taco_data_room_zip_v4, taco_data_room_zip_v5, taco_data_room_zip_v6, taco_data_room_zip_v7, taco_data_room_zip_v8, taco_data_room_zip_v9, taco_data_room_zip_v10, taco_data_room_zip_v11, taco_data_room_zip_v12, taco_data_room_zip_v13, taco_data_room_zip_v14, taco_data_room_zip_v15, taco_data_room_zip_v16, taco_data_room_zip_v17, or taco_data_room_zip_v18",
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


def test_data_room_bundle_verifier_accepts_legacy_v6_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V6}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V6"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V6,
        "manifest_id": "DR-LEGACY-V6",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V6 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v7_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V7}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V7"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V7,
        "manifest_id": "DR-LEGACY-V7",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V7 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v8_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V8}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V8"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V8,
        "manifest_id": "DR-LEGACY-V8",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V8 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v9_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V9}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V9"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V9,
        "manifest_id": "DR-LEGACY-V9",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V9 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v10_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V10}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V10"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V10,
        "manifest_id": "DR-LEGACY-V10",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V10 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v11_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V11}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V11"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V11,
        "manifest_id": "DR-LEGACY-V11",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V11 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v12_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V12}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V12"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V12,
        "manifest_id": "DR-LEGACY-V12",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V12 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v13_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V13}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V13"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V13,
        "manifest_id": "DR-LEGACY-V13",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V13 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v14_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V14}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V14"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V14,
        "manifest_id": "DR-LEGACY-V14",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V14 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v15_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V15}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V15"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V15,
        "manifest_id": "DR-LEGACY-V15",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V15 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v16_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V16}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V16"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V16,
        "manifest_id": "DR-LEGACY-V16",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V16 | {PACKET_INDEX_PATH}),
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


def test_data_room_bundle_verifier_accepts_legacy_v17_packets():
    payloads = {name: b"{}" if name.endswith(".json") else b"" for name in REQUIRED_BUNDLE_FILES_V17}
    payloads["manifest.json"] = b'{"manifest_id":"DR-LEGACY-V17"}'
    packet_index = {
        "packet_format": PACKET_FORMAT_V17,
        "manifest_id": "DR-LEGACY-V17",
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(payloads),
        "required_files": sorted(REQUIRED_BUNDLE_FILES_V17 | {PACKET_INDEX_PATH}),
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
