"""VC data-room checklist generation for TACO diligence."""

from __future__ import annotations

import io
import hashlib
import json
import re
from typing import Any
import zipfile
import zlib

from .activation_evidence_contract import build_activation_evidence_contract
from .actuarial_readiness import build_actuarial_readiness_plan
from .buyer_roi import build_buyer_roi_model
from .claim_validation import build_claim_validation_ledger
from .commercial_traction import build_commercial_traction_plan
from .commercial_unit_economics import build_commercial_unit_economics
from .competitive_positioning import build_competitive_positioning
from .design_partner_plan import build_design_partner_plan
from .dreamaudit_corpus_reconciliation import build_dreamaudit_corpus_reconciliation
from .evidence_provenance import build_evidence_provenance_audit
from .external_validation import build_external_validation_capture_kit
from .external_proof_registry import build_external_proof_registry
from .commercial_model import build_commercial_scale_model
from .capacity_roadmap import build_capacity_roadmap
from .fundraise_narrative import build_fundraise_narrative_memo
from .fundraise_readiness import build_fundraise_readiness
from .insurance_scenarios import INSURANCE_SCENARIOS
from .investor_case import RESEARCH_FOUNDATIONS, investor_summary
from .investor_objections import build_investor_objection_register
from .investor_proof_pipeline import build_investor_proof_pipeline
from .methodology_evidence import build_methodology_evidence_map
from .methodology_validation_protocol import build_methodology_validation_protocol
from .pilot_walkthrough import build_pilot_walkthrough_playbook
from .pricing_diligence import build_pricing_diligence
from .research_validation import build_research_validation_plan
from .renewal_loop import renewal_summary
from .security_plan import build_enterprise_security_plan
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown, dataclass_to_dict
from .seed_financing_plan import build_seed_financing_plan
from .seed_round_close import build_seed_round_close_plan
from .technical_runbook import build_technical_diligence_runbook


ZIP_TIMESTAMP = (2026, 6, 4, 0, 0, 0)
PACKET_INDEX_PATH = "packet/index.json"
PACKET_FORMAT_V1 = "taco_data_room_zip_v1"
PACKET_FORMAT_V2 = "taco_data_room_zip_v2"
PACKET_FORMAT_V3 = "taco_data_room_zip_v3"
PACKET_FORMAT_V4 = "taco_data_room_zip_v4"
PACKET_FORMAT_V5 = "taco_data_room_zip_v5"
PACKET_FORMAT_V6 = "taco_data_room_zip_v6"
PACKET_FORMAT_V7 = "taco_data_room_zip_v7"
PACKET_FORMAT_V8 = "taco_data_room_zip_v8"
PACKET_FORMAT_V9 = "taco_data_room_zip_v9"
PACKET_FORMAT_V10 = "taco_data_room_zip_v10"
PACKET_FORMAT_V11 = "taco_data_room_zip_v11"
PACKET_FORMAT_V12 = "taco_data_room_zip_v12"
PACKET_FORMAT_V13 = "taco_data_room_zip_v13"
PACKET_FORMAT_V14 = "taco_data_room_zip_v14"
PACKET_FORMAT_V15 = "taco_data_room_zip_v15"
PACKET_FORMAT_V16 = "taco_data_room_zip_v16"
PACKET_FORMAT_V17 = "taco_data_room_zip_v17"
PACKET_FORMAT_V18 = "taco_data_room_zip_v18"
PACKET_FORMAT_V19 = "taco_data_room_zip_v19"
PACKET_FORMAT_V20 = "taco_data_room_zip_v20"
PACKET_FORMAT_V21 = "taco_data_room_zip_v21"
PACKET_FORMAT_V22 = "taco_data_room_zip_v22"
PACKET_FORMAT_V23 = "taco_data_room_zip_v23"
PACKET_FORMAT_V24 = "taco_data_room_zip_v24"
PACKET_FORMAT_V25 = "taco_data_room_zip_v25"
PACKET_FORMAT_V26 = "taco_data_room_zip_v26"
PACKET_FORMAT_V27 = "taco_data_room_zip_v27"
MAX_PACKET_BYTES = 10_000_000
MAX_ZIP_MEMBERS = 256
MAX_TOTAL_UNCOMPRESSED_BYTES = 10_000_000
MAX_ZIP_MEMBER_BYTES = 2_000_000
REQUIRED_BUNDLE_FILES_V1 = {
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
}
REQUIRED_BUNDLE_FILES_V2 = REQUIRED_BUNDLE_FILES_V1 | {
    "commercial/design_partner_plan.json",
}
REQUIRED_BUNDLE_FILES_V3 = REQUIRED_BUNDLE_FILES_V2 | {
    "commercial/seed_financing_plan.json",
}
REQUIRED_BUNDLE_FILES_V4 = REQUIRED_BUNDLE_FILES_V3 | {
    "research/methodology_evidence_map.json",
}
REQUIRED_BUNDLE_FILES_V5 = REQUIRED_BUNDLE_FILES_V4 | {
    "commercial/pricing_diligence.json",
}
REQUIRED_BUNDLE_FILES_V6 = REQUIRED_BUNDLE_FILES_V5 | {
    "commercial/investor_objection_register.json",
}
REQUIRED_BUNDLE_FILES_V7 = REQUIRED_BUNDLE_FILES_V6 | {
    "commercial/pilot_walkthrough_playbook.json",
}
REQUIRED_BUNDLE_FILES_V8 = REQUIRED_BUNDLE_FILES_V7 | {
    "commercial/commercial_scale_model.json",
}
REQUIRED_BUNDLE_FILES_V9 = REQUIRED_BUNDLE_FILES_V8 | {
    "commercial/capacity_roadmap.json",
}
REQUIRED_BUNDLE_FILES_V10 = REQUIRED_BUNDLE_FILES_V9 | {
    "commercial/enterprise_security_plan.json",
}
REQUIRED_BUNDLE_FILES_V11 = REQUIRED_BUNDLE_FILES_V10 | {
    "technical/technical_diligence_runbook.json",
}
REQUIRED_BUNDLE_FILES_V12 = REQUIRED_BUNDLE_FILES_V11 | {
    "commercial/external_validation_capture_kit.json",
}
REQUIRED_BUNDLE_FILES_V13 = REQUIRED_BUNDLE_FILES_V12 | {
    "commercial/actuarial_readiness_plan.json",
}
REQUIRED_BUNDLE_FILES_V14 = REQUIRED_BUNDLE_FILES_V13 | {
    "commercial/buyer_roi_model.json",
}
REQUIRED_BUNDLE_FILES_V15 = REQUIRED_BUNDLE_FILES_V14 | {
    "research/claim_validation_ledger.json",
}
REQUIRED_BUNDLE_FILES_V16 = REQUIRED_BUNDLE_FILES_V15 | {
    "commercial/investor_proof_pipeline.json",
}
REQUIRED_BUNDLE_FILES_V17 = REQUIRED_BUNDLE_FILES_V16 | {
    "research/research_validation_plan.json",
}
REQUIRED_BUNDLE_FILES_V18 = REQUIRED_BUNDLE_FILES_V17 | {
    "commercial/commercial_traction_plan.json",
}
REQUIRED_BUNDLE_FILES_V19 = REQUIRED_BUNDLE_FILES_V18 | {
    "commercial/commercial_unit_economics.json",
}
REQUIRED_BUNDLE_FILES_V20 = REQUIRED_BUNDLE_FILES_V19 | {
    "commercial/seed_round_close_plan.json",
}
REQUIRED_BUNDLE_FILES_V21 = REQUIRED_BUNDLE_FILES_V20 | {
    "commercial/external_proof_registry.json",
}
REQUIRED_BUNDLE_FILES_V22 = REQUIRED_BUNDLE_FILES_V21 | {
    "research/methodology_validation_protocol.json",
}
REQUIRED_BUNDLE_FILES_V23 = REQUIRED_BUNDLE_FILES_V22 | {
    "commercial/competitive_positioning.json",
}
REQUIRED_BUNDLE_FILES_V24 = REQUIRED_BUNDLE_FILES_V23 | {
    "research/activation_evidence_contract.json",
}
REQUIRED_BUNDLE_FILES_V25 = REQUIRED_BUNDLE_FILES_V24 | {
    "dreamaudit/corpus_reconciliation.json",
}
REQUIRED_BUNDLE_FILES_V26 = REQUIRED_BUNDLE_FILES_V25 | {
    "commercial/fundraise_narrative_memo.json",
}
REQUIRED_BUNDLE_FILES = REQUIRED_BUNDLE_FILES_V26 | {
    "evidence/provenance_audit.json",
}


def build_data_room_checklist(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return diligence packet items investors and carriers will ask to inspect."""

    suite_cases = list(suite_manifest.get("cases", []))
    suite_size = int(suite_manifest.get("suite_size", len(suite_cases)) or 0)
    suite_families = {str(case.get("failure_family", "unknown")) for case in suite_cases}
    metric_ids = {metric.certificate_id for metric in metrics}
    covered_metrics = sum(1 for cert in certificates if cert.certificate_id in metric_ids)
    metric_sources = sorted({metric.metrics_source for metric in metrics})
    metric_source_text = ", ".join(metric_sources) if metric_sources else "none"
    dreamaudit = _dreamaudit_status(dreamaudit_intake)
    dreamaudit_reconciliation = build_dreamaudit_corpus_reconciliation(application, dreamaudit_intake)
    dreamaudit_gate_failures = [
        gate for gate in dreamaudit_reconciliation["evidence_gates"] if gate["status"] != "pass"
    ]
    items = [
        _item(
            "Application And Coverage File",
            "ready" if application.application_id and quote.quote_id else "needs_work",
            f"{application.application_id}; ${application.coverage_requested_usd:,.0f} requested coverage; quote {quote.quote_id}.",
            "Keep the application JSON, quote breakdown, and coverage request in the diligence packet.",
        ),
        _item(
            "Replay Failure Certificates",
            "ready" if len(certificates) >= 3 else "needs_work",
            f"{len(certificates)} primary replayable failure certificates attached.",
            "Attach at least three primary certificates with replay commands and required controls.",
        ),
        _item(
            "Internal Risk Trace Coverage",
            "ready" if certificates and covered_metrics == len(certificates) else "needs_work",
            f"{covered_metrics}/{len(certificates)} certificates have internal risk metrics; sources: {metric_source_text}.",
            "Attach activation/trace NPZ evidence for every primary certificate.",
        ),
        _item(
            "Activation Evidence Contract",
            "ready" if certificates and covered_metrics == len(certificates) else "needs_work",
            "Layer-to-signal map, trace bundle requirements, calibration gates, artifact checks, and no-claim rules are attached.",
            "Run policy-specific ActivationRecorder capture before upgrading internals claims beyond local/demo evidence.",
        ),
        _item(
            "ManiSkill/RMA Video Suite",
            "ready" if suite_size >= 40 and len(suite_families) >= 8 else "needs_work",
            f"{suite_size} videos across {len(suite_families)} failure families.",
            "Keep the 40-video replay suite and manifest in the data room.",
        ),
        _item(
            "Insurance Workflow And Pricing Examples",
            "ready" if len(INSURANCE_SCENARIOS) >= 10 else "needs_work",
            f"{len(INSURANCE_SCENARIOS)} priced end-to-end insurance workflows.",
            "Include 10+ workflows with controls, exclusions, and premium deltas.",
        ),
        _item(
            "Live DreamAudit Corpus",
            dreamaudit["status"],
            dreamaudit["evidence"],
            dreamaudit["next_action"],
        ),
        _item(
            "DreamAudit Corpus Reconciliation",
            "ready" if dreamaudit_reconciliation["status"] != "not_scanned" else "needs_live_scan",
            (
                f"{dreamaudit_reconciliation['current_evidence']['selected_certificates']} selected certificates; "
                f"{len(dreamaudit_gate_failures)} corpus gates still failing."
            ),
            "Close the listed corpus gates before upgrading DreamAudit evidence beyond private diligence import.",
        ),
        _item(
            "Research And Methodology Sources",
            "ready" if len(RESEARCH_FOUNDATIONS) >= 4 else "needs_work",
            f"{len(RESEARCH_FOUNDATIONS)} linked research anchors.",
            "Attach primary-source references for simulation, perturbation, interpretability, and monitoring claims.",
        ),
        _item(
            "Research Validation Plan",
            "ready" if len(RESEARCH_FOUNDATIONS) >= 4 and suite_size >= 40 else "needs_work",
            "Falsifiable hypotheses, validation experiments, acceptance thresholds, downgrade rules, and blocked claims are attached.",
            "Run the validation workstreams with partner-specific DreamAudit, activation, control, reviewer, and actuarial evidence before upgrading research-backed claims.",
        ),
        _item(
            "Methodology Validation Protocol",
            "ready" if len(RESEARCH_FOUNDATIONS) >= 4 and suite_size >= 40 and certificates and metrics else "needs_work",
            "Prospective endpoints, baselines, sample-size rungs, execution workflows, artifact package, and claim-upgrade boundaries are attached.",
            "Pre-register the packet hash and run endpoint-specific baselines before saying the methodology has been externally validated.",
        ),
        _item(
            "Commercial Scale Model",
            "ready" if application.coverage_requested_usd > 0 and quote.final_monthly_premium_usd > 0 else "needs_work",
            "Market-context, buyer-segment, revenue-scenario, and proof-gate model is attached with explicit boundaries.",
            "Validate ACV, packet fees, and paid pilot conversion with external reviewers.",
        ),
        _item(
            "Competitive Positioning",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "Category definition, alternative-category comparisons, wedge strategy, defensibility hypotheses, and validation actions are attached.",
            "Collect reviewer evidence naming which incumbent workflow TACO replaces, augments, or fails to fit before claiming category pull.",
        ),
        _item(
            "Insurance Capacity Roadmap",
            "ready" if quote.final_monthly_premium_usd > 0 and bool(quote.required_controls) else "needs_work",
            "Capacity, licensing, MGA/fronting, rate/form, actuarial, and claims workstreams are attached with non-offer boundaries.",
            "Collect counsel memo, licensed-partner path, capacity term sheet, and actuarial/filing plan before launch.",
        ),
        _item(
            "Enterprise Security Plan",
            "ready" if application.application_id and certificates and metrics else "needs_work",
            "Security, data-governance, access-control, retention, incident-response, and SOC2/NIST readiness plan is attached.",
            "Implement workspace RBAC, audit logs, retention policy, incident tabletop, and SOC2 readiness assessment before production pilots.",
        ),
        _item(
            "Technical Diligence Runbook",
            "ready" if application.application_id and suite_size >= 40 else "needs_work",
            "Reviewer runbook for local reproduction, tests, app import, packet verification, DreamAudit intake, activation recording, and cluster video regeneration is attached.",
            "Have an external reviewer execute the runbook and attach command outputs or missing-evidence notes.",
        ),
        _item(
            "External Validation Capture Kit",
            "ready" if application.application_id and suite_size >= 40 else "needs_work",
            "Scorecard, reviewer feedback form, LOI/pilot-scope template, evidence-status ladder, and permission-to-quote controls are attached.",
            "Run the capture kit with real broker, carrier, OEM, or reinsurer reviewers and attach only written artifacts with permission metadata.",
        ),
        _item(
            "Actuarial Readiness Plan",
            "ready" if quote.final_monthly_premium_usd > 0 and bool(certificates) and bool(metrics) else "needs_work",
            "Future-cost elements, data-quality gates, modeling controls, credibility ramp, filing handoff, and claims-loop requirements are attached.",
            "Have an actuary, carrier, or reinsurer review the plan before using any output as pricing, rate adequacy, reserve, or filing support.",
        ),
        _item(
            "Buyer ROI Model",
            "ready" if application.deployment_units > 0 and quote.final_monthly_premium_usd > 0 else "needs_work",
            "Modeled buyer economics, stakeholder value drivers, payback cases, procurement proof gates, and sensitivity cases are attached.",
            "Replace modeled assumptions with buyer-confirmed delay cost, evidence-ops time study, control-credit review, and signed pilot evidence.",
        ),
        _item(
            "Investor Claim Validation Ledger",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "Investor-safe claims, evidence levels, upgrade gates, and disallowed overclaims are attached.",
            "Use the ledger during VC, broker, carrier, and design-partner reviews so demo-backed claims are not overstated.",
        ),
        _item(
            "Investor Proof Pipeline",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "Weekly operating workflow, reviewer targets, external-proof gates, and data-room upgrade rules are attached.",
            "Execute the workflow with external reviewers and attach only written artifacts with packet fingerprints and permission metadata.",
        ),
        _item(
            "Commercial Traction Plan",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "ICP targets, paid package ladder, weekly traction metrics, investor reporting rules, and count/do-not-count controls are attached.",
            "Convert walkthroughs into packet-fingerprinted reviewer memos, paid scopes, source-data paths, or permission-to-quote artifacts before calling it traction.",
        ),
        _item(
            "Commercial Unit Economics",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "Modeled revenue mix, delivery cost, gross margin, CAC/payback assumptions, and seed milestone gates are attached with risk-bearing economics excluded.",
            "Attach paid-scope invoices, delivery-cost logs, source-data reuse evidence, and sales-source attribution before claiming proven margins or payback.",
        ),
        _item(
            "Seed Round Close Plan",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "Investor segmenting, weekly close motion, lead-partner gates, minimum close package, meeting prompts, and no-count rules are attached.",
            "Use the close plan to convert reviewer proof and commercial artifacts into a lead-process path without overstating investor interest or customer demand.",
        ),
        _item(
            "Fundraise Narrative Memo",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "One-line thesis, seven-minute demo path, proof stack, investor questions, 30-day close workflow, and do-not-claim rules are attached.",
            "Use this memo to run seed conversations from packet evidence instead of slides or unsupported traction claims.",
        ),
        _item(
            "Evidence Provenance Audit",
            "ready" if certificates and covered_metrics == len(certificates) and suite_size >= 40 else "needs_work",
            "Certificate, activation metric, and video sources are classified by fixture/generated, adapted DreamAudit, or recorded activation provenance.",
            "Attach reviewer reproduction notes, simulator commands, source paths, and activation calibration notes before upgrading claims.",
        ),
        _item(
            "External Proof Registry",
            "ready" if quote.final_monthly_premium_usd > 0 and suite_size >= 40 else "needs_work",
            "Proof slots, packet fingerprint requirements, permission-to-quote states, redaction gates, claim-upgrade rules, and investor-update controls are attached.",
            "Fill the registry with written reviewer artifacts only after packet SHA-256, permission, redaction, and claim-linkage fields are complete.",
        ),
        _item(
            "Design-Partner References",
            "external_pending",
            "Structured broker/carrier/OEM pilot plan is attached; signed external reviews are not represented in local demo artifacts.",
            "Run the design-partner plan and add written feedback, signed pilot scopes, or LOIs to the data room.",
        ),
    ]
    ready_items = sum(1 for item in items if item["status"] == "ready")
    internal_items = [item for item in items if item["status"] != "external_pending"]
    internal_ready = sum(1 for item in internal_items if item["status"] == "ready")
    return {
        "ready_items": ready_items,
        "total_items": len(items),
        "internal_ready_items": internal_ready,
        "internal_total_items": len(internal_items),
        "internal_packet_score": round(100 * internal_ready / len(internal_items)) if internal_items else 0,
        "external_pending_items": sum(1 for item in items if item["status"] == "external_pending"),
        "items": items,
    }


def data_room_rows(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    """Return table rows for the Streamlit UI and Markdown memo."""

    return [
        {
            "Artifact": item["artifact"],
            "Status": item["status"].replace("_", " ").title(),
            "Evidence": item["evidence"],
            "Next Action": item["next_action"],
        }
        for item in checklist["items"]
    ]


def build_data_room_manifest(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a machine-readable diligence manifest for export."""

    checklist = build_data_room_checklist(application, certificates, metrics, quote, suite_manifest, dreamaudit_intake)
    suite_cases = list(suite_manifest.get("cases", []))
    dreamaudit_summary = _dreamaudit_manifest_summary(dreamaudit_intake)
    dreamaudit_corpus_reconciliation = build_dreamaudit_corpus_reconciliation(application, dreamaudit_intake)
    design_partner_plan = build_design_partner_plan(application, quote)
    fundraise_readiness = build_fundraise_readiness(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        dreamaudit_intake,
    )
    seed_financing_plan = build_seed_financing_plan(application, quote, fundraise_readiness, design_partner_plan)
    methodology_evidence_map = build_methodology_evidence_map(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        dreamaudit_intake,
    )
    pricing_diligence = build_pricing_diligence(application, certificates, metrics, quote)
    objection_register = build_investor_objection_register(
        fundraise_readiness,
        methodology_evidence_map,
        pricing_diligence,
        design_partner_plan,
        seed_financing_plan,
    )
    pilot_walkthrough_playbook = build_pilot_walkthrough_playbook(
        application,
        quote,
        design_partner_plan,
        objection_register,
        methodology_evidence_map,
        pricing_diligence,
    )
    commercial_scale_model = build_commercial_scale_model(
        application,
        quote,
        fundraise_readiness,
        seed_financing_plan,
        pilot_walkthrough_playbook,
    )
    capacity_roadmap = build_capacity_roadmap(
        application,
        quote,
        pricing_diligence,
        commercial_scale_model,
        pilot_walkthrough_playbook,
    )
    enterprise_security_plan = build_enterprise_security_plan(
        application,
        quote,
        {"manifest_id": f"DR-{application.application_id}", "primary_certificates": certificates, "internal_metrics": metrics},
        dreamaudit_summary,
        capacity_roadmap,
    )
    technical_diligence_runbook = build_technical_diligence_runbook(
        application,
        quote,
        suite_manifest,
        dreamaudit_summary,
        enterprise_security_plan,
    )
    external_validation_capture_kit = build_external_validation_capture_kit(
        application,
        quote,
        design_partner_plan,
        pilot_walkthrough_playbook,
        {
            "manifest_id": f"DR-{application.application_id}",
            "packet_files": sorted(REQUIRED_BUNDLE_FILES | {PACKET_INDEX_PATH}),
        },
    )
    actuarial_readiness_plan = build_actuarial_readiness_plan(
        application,
        certificates,
        metrics,
        quote,
        pricing_diligence,
        capacity_roadmap,
    )
    buyer_roi_model = build_buyer_roi_model(
        application,
        quote,
        renewal_summary(quote),
        commercial_scale_model,
        external_validation_capture_kit,
        pricing_diligence,
    )
    claim_validation_ledger = build_claim_validation_ledger(
        application,
        quote,
        fundraise_readiness,
        methodology_evidence_map,
        pricing_diligence,
        commercial_scale_model,
        buyer_roi_model,
        actuarial_readiness_plan,
        external_validation_capture_kit,
        technical_diligence_runbook,
        dreamaudit_intake,
    )
    investor_proof_pipeline = build_investor_proof_pipeline(
        application,
        quote,
        fundraise_readiness,
        design_partner_plan,
        pilot_walkthrough_playbook,
        external_validation_capture_kit,
        claim_validation_ledger,
        buyer_roi_model,
    )
    research_validation_plan = build_research_validation_plan(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        methodology_evidence_map,
        claim_validation_ledger,
        investor_proof_pipeline,
        dreamaudit_intake,
    )
    commercial_traction_plan = build_commercial_traction_plan(
        application,
        quote,
        commercial_scale_model,
        buyer_roi_model,
        investor_proof_pipeline,
        external_validation_capture_kit,
        claim_validation_ledger,
        research_validation_plan,
        design_partner_plan,
        seed_financing_plan,
    )
    commercial_unit_economics = build_commercial_unit_economics(
        application,
        quote,
        commercial_scale_model,
        commercial_traction_plan,
        seed_financing_plan,
        buyer_roi_model,
    )
    seed_round_close_plan = build_seed_round_close_plan(
        application,
        quote,
        fundraise_readiness,
        seed_financing_plan,
        investor_proof_pipeline,
        commercial_traction_plan,
        commercial_unit_economics,
        claim_validation_ledger,
    )
    external_proof_registry = build_external_proof_registry(
        application,
        quote,
        external_validation_capture_kit,
        investor_proof_pipeline,
        claim_validation_ledger,
        seed_round_close_plan,
    )
    methodology_validation_protocol = build_methodology_validation_protocol(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        research_validation_plan,
        external_proof_registry,
    )
    competitive_positioning = build_competitive_positioning(
        application,
        quote,
        methodology_evidence_map,
        commercial_scale_model,
        investor_proof_pipeline,
        methodology_validation_protocol,
    )
    activation_evidence_contract = build_activation_evidence_contract(
        application,
        certificates,
        metrics,
        quote,
        methodology_validation_protocol,
        technical_diligence_runbook,
    )
    evidence_provenance_audit = build_evidence_provenance_audit(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        dreamaudit_intake,
    )
    fundraise_narrative_memo = build_fundraise_narrative_memo(
        application,
        quote,
        investor_summary(application, certificates, metrics, quote),
        fundraise_readiness,
        seed_financing_plan,
        seed_round_close_plan,
        commercial_traction_plan,
        dreamaudit_corpus_reconciliation,
        activation_evidence_contract,
        claim_validation_ledger,
    )
    return {
        "manifest_id": f"DR-{application.application_id}",
        "purpose": "VC/carrier diligence packet for learned-policy liability underwriting evidence.",
        "application": dataclass_to_dict(application),
        "quote": dataclass_to_dict(quote),
        "checklist": checklist,
        "primary_certificates": [dataclass_to_dict(cert) for cert in certificates],
        "internal_metrics": [dataclass_to_dict(metric) for metric in metrics],
        "suite_summary": {
            "suite_name": suite_manifest.get("suite_name", "unknown"),
            "suite_size": int(suite_manifest.get("suite_size", len(suite_cases)) or 0),
            "failure_families": sorted({str(case.get("failure_family", "unknown")) for case in suite_cases}),
            "video_paths": [str(case.get("video_path", "")) for case in suite_cases if case.get("video_path")],
        },
        "dreamaudit": dreamaudit_summary,
        "dreamaudit_corpus_reconciliation": dreamaudit_corpus_reconciliation,
        "design_partner_plan": design_partner_plan,
        "seed_financing_plan": seed_financing_plan,
        "methodology_evidence_map": methodology_evidence_map,
        "pricing_diligence": pricing_diligence,
        "investor_objection_register": objection_register,
        "pilot_walkthrough_playbook": pilot_walkthrough_playbook,
        "commercial_scale_model": commercial_scale_model,
        "competitive_positioning": competitive_positioning,
        "capacity_roadmap": capacity_roadmap,
        "enterprise_security_plan": enterprise_security_plan,
        "technical_diligence_runbook": technical_diligence_runbook,
        "external_validation_capture_kit": external_validation_capture_kit,
        "actuarial_readiness_plan": actuarial_readiness_plan,
        "buyer_roi_model": buyer_roi_model,
        "claim_validation_ledger": claim_validation_ledger,
        "investor_proof_pipeline": investor_proof_pipeline,
        "research_validation_plan": research_validation_plan,
        "methodology_validation_protocol": methodology_validation_protocol,
        "activation_evidence_contract": activation_evidence_contract,
        "evidence_provenance_audit": evidence_provenance_audit,
        "commercial_traction_plan": commercial_traction_plan,
        "commercial_unit_economics": commercial_unit_economics,
        "seed_round_close_plan": seed_round_close_plan,
        "fundraise_narrative_memo": fundraise_narrative_memo,
        "external_proof_registry": external_proof_registry,
    }


def build_data_room_bundle(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    diligence_memo: str,
    dreamaudit_intake: dict[str, Any] | None = None,
) -> bytes:
    """Build a ZIP diligence packet with machine-readable contracts and memo."""

    manifest = build_data_room_manifest(application, certificates, metrics, quote, suite_manifest, dreamaudit_intake)
    entries: list[tuple[str, bytes]] = [
        ("README.md", _text_bytes(_bundle_readme(manifest))),
        ("manifest.json", _json_bytes(manifest)),
        ("application.json", _json_bytes(manifest["application"])),
        ("quote.json", _json_bytes(manifest["quote"])),
        ("checklist.json", _json_bytes(manifest["checklist"])),
        ("diligence_memo.md", _text_bytes(diligence_memo)),
        ("insurance/workflow_examples.json", _json_bytes(INSURANCE_SCENARIOS)),
        ("research/sources.json", _json_bytes(RESEARCH_FOUNDATIONS)),
        ("research/methodology_evidence_map.json", _json_bytes(manifest["methodology_evidence_map"])),
        ("research/claim_validation_ledger.json", _json_bytes(manifest["claim_validation_ledger"])),
        ("research/research_validation_plan.json", _json_bytes(manifest["research_validation_plan"])),
        ("research/methodology_validation_protocol.json", _json_bytes(manifest["methodology_validation_protocol"])),
        ("research/activation_evidence_contract.json", _json_bytes(manifest["activation_evidence_contract"])),
        ("evidence/provenance_audit.json", _json_bytes(manifest["evidence_provenance_audit"])),
        ("suite/video_index.json", _json_bytes(manifest["suite_summary"])),
        ("dreamaudit/summary.json", _json_bytes(manifest["dreamaudit"])),
        ("dreamaudit/corpus_reconciliation.json", _json_bytes(manifest["dreamaudit_corpus_reconciliation"])),
        ("commercial/design_partner_plan.json", _json_bytes(manifest["design_partner_plan"])),
        ("commercial/seed_financing_plan.json", _json_bytes(manifest["seed_financing_plan"])),
        ("commercial/pricing_diligence.json", _json_bytes(manifest["pricing_diligence"])),
        ("commercial/investor_objection_register.json", _json_bytes(manifest["investor_objection_register"])),
        ("commercial/pilot_walkthrough_playbook.json", _json_bytes(manifest["pilot_walkthrough_playbook"])),
        ("commercial/commercial_scale_model.json", _json_bytes(manifest["commercial_scale_model"])),
        ("commercial/competitive_positioning.json", _json_bytes(manifest["competitive_positioning"])),
        ("commercial/capacity_roadmap.json", _json_bytes(manifest["capacity_roadmap"])),
        ("commercial/enterprise_security_plan.json", _json_bytes(manifest["enterprise_security_plan"])),
        ("commercial/external_validation_capture_kit.json", _json_bytes(manifest["external_validation_capture_kit"])),
        ("commercial/actuarial_readiness_plan.json", _json_bytes(manifest["actuarial_readiness_plan"])),
        ("commercial/buyer_roi_model.json", _json_bytes(manifest["buyer_roi_model"])),
        ("commercial/investor_proof_pipeline.json", _json_bytes(manifest["investor_proof_pipeline"])),
        ("commercial/commercial_traction_plan.json", _json_bytes(manifest["commercial_traction_plan"])),
        ("commercial/commercial_unit_economics.json", _json_bytes(manifest["commercial_unit_economics"])),
        ("commercial/seed_round_close_plan.json", _json_bytes(manifest["seed_round_close_plan"])),
        ("commercial/fundraise_narrative_memo.json", _json_bytes(manifest["fundraise_narrative_memo"])),
        ("commercial/external_proof_registry.json", _json_bytes(manifest["external_proof_registry"])),
        ("technical/technical_diligence_runbook.json", _json_bytes(manifest["technical_diligence_runbook"])),
    ]
    certificate_names: set[str] = set()
    for cert in certificates:
        name = _safe_zip_stem(cert.certificate_id, certificate_names)
        entries.append((f"certificates/{name}.json", _json_bytes(dataclass_to_dict(cert))))
    metric_names: set[str] = set()
    for metric in metrics:
        name = _safe_zip_stem(metric.certificate_id, metric_names)
        entries.append((f"metrics/{name}.json", _json_bytes(dataclass_to_dict(metric))))
    packet_index = _packet_index(manifest["manifest_id"], entries)
    entries.append((PACKET_INDEX_PATH, _json_bytes(packet_index)))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries:
            _write_zip_bytes(archive, name, payload)
    return buffer.getvalue()


def data_room_bundle_summary(bundle_bytes: bytes) -> dict[str, Any]:
    """Return lightweight facts about a generated data-room ZIP."""

    with zipfile.ZipFile(io.BytesIO(bundle_bytes), mode="r") as archive:
        names = sorted(archive.namelist())
    return {
        "file_count": len(names),
        "packet_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        "contains_manifest": "manifest.json" in names,
        "contains_memo": "diligence_memo.md" in names,
        "contains_video_index": "suite/video_index.json" in names,
        "contains_packet_index": PACKET_INDEX_PATH in names,
        "files": names,
    }


def verify_data_room_bundle(bundle_bytes: bytes) -> dict[str, Any]:
    """Verify ZIP member safety and packet-index checksums."""

    issues: list[str] = []
    names: list[str] = []
    index: dict[str, Any] | None = None
    indexed_file_count = 0
    if len(bundle_bytes) > MAX_PACKET_BYTES:
        issues.append(f"Packet exceeds maximum byte size: {len(bundle_bytes)} > {MAX_PACKET_BYTES}")
        return {
            "valid": False,
            "issues": issues,
            "file_count": 0,
            "indexed_file_count": 0,
            "packet_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
        }
    try:
        with zipfile.ZipFile(io.BytesIO(bundle_bytes), mode="r") as archive:
            infos = archive.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                issues.append(f"ZIP member count exceeds limit: {len(infos)} > {MAX_ZIP_MEMBERS}")
                return {
                    "valid": False,
                    "issues": issues,
                    "file_count": len(infos),
                    "indexed_file_count": 0,
                    "packet_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
                }
            names = sorted(archive.namelist())
            infos_by_name = {info.filename: info for info in infos}
            total_uncompressed = sum(info.file_size for info in infos)
            size_limit_failed = False
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                issues.append(
                    f"ZIP uncompressed size exceeds limit: {total_uncompressed} > {MAX_TOTAL_UNCOMPRESSED_BYTES}"
                )
                size_limit_failed = True
            oversized_names = sorted(info.filename for info in infos if info.file_size > MAX_ZIP_MEMBER_BYTES)
            if oversized_names:
                issues.extend(f"ZIP member too large: {name}" for name in oversized_names)
                size_limit_failed = True
            unsafe_names = [name for name in names if _unsafe_zip_name(name)]
            if unsafe_names:
                issues.extend(f"Unsafe ZIP member path: {name}" for name in unsafe_names)
            duplicate_names = sorted({name for name in names if names.count(name) > 1})
            if duplicate_names:
                issues.extend(f"Duplicate ZIP member path: {name}" for name in duplicate_names)
            if PACKET_INDEX_PATH not in names:
                issues.append(f"Missing required file: {PACKET_INDEX_PATH}")
            elif size_limit_failed:
                issues.append("Packet index not read because ZIP size limits failed")
            else:
                index_info = infos_by_name.get(PACKET_INDEX_PATH)
                if index_info is not None and index_info.file_size <= MAX_ZIP_MEMBER_BYTES:
                    raw_index = json.loads(archive.read(PACKET_INDEX_PATH))
                    if isinstance(raw_index, dict):
                        index = raw_index
                    else:
                        issues.append("Invalid packet index: expected JSON object")
                else:
                        issues.append("Invalid packet index: packet index exceeds member size limit")
            if index is not None:
                expected_required_files = _required_files_for_packet_format(str(index.get("packet_format", "")))
                if expected_required_files is None:
                    issues.append(
                        "Invalid packet index: packet_format must be taco_data_room_zip_v1, "
                        "taco_data_room_zip_v2, taco_data_room_zip_v3, taco_data_room_zip_v4, "
                        "taco_data_room_zip_v5, taco_data_room_zip_v6, taco_data_room_zip_v7, "
                        "taco_data_room_zip_v8, taco_data_room_zip_v9, taco_data_room_zip_v10, "
                        "taco_data_room_zip_v11, taco_data_room_zip_v12, taco_data_room_zip_v13, "
                        "taco_data_room_zip_v14, taco_data_room_zip_v15, taco_data_room_zip_v16, "
                        "taco_data_room_zip_v17, taco_data_room_zip_v18, taco_data_room_zip_v19, "
                        "taco_data_room_zip_v20, taco_data_room_zip_v21, taco_data_room_zip_v22, "
                        "taco_data_room_zip_v23, taco_data_room_zip_v24, taco_data_room_zip_v25, "
                        "taco_data_room_zip_v26, or taco_data_room_zip_v27"
                    )
                    expected_required_files = REQUIRED_BUNDLE_FILES
                if index.get("checksum_algorithm") != "sha256":
                    issues.append("Invalid packet index: checksum_algorithm must be sha256")
                required_missing = sorted(expected_required_files - set(names))
                if required_missing:
                    issues.extend(f"Missing required file: {name}" for name in required_missing)
                if index.get("required_files") != sorted(expected_required_files | {PACKET_INDEX_PATH}):
                    issues.append("Invalid packet index: required_files does not match packet requirements")
                if "manifest.json" in names:
                    manifest = json.loads(archive.read("manifest.json"))
                    if not isinstance(manifest, dict) or index.get("manifest_id") != manifest.get("manifest_id"):
                        issues.append("Invalid packet index: manifest_id does not match manifest.json")
                indexed_items = index.get("files")
                if not isinstance(indexed_items, list) or not indexed_items:
                    issues.append("Invalid packet index: files must be a non-empty list")
                    indexed_items = []
                indexed_files = {}
                for item in indexed_items:
                    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                        issues.append("Invalid packet index: file entries must be objects with string paths")
                        continue
                    if not isinstance(item.get("bytes"), int) or isinstance(item.get("bytes"), bool):
                        issues.append(f"Invalid packet index: file bytes must be an integer for {item['path']}")
                        continue
                    if item["path"] in indexed_files:
                        issues.append(f"Duplicate packet index path: {item['path']}")
                        continue
                    indexed_files[item["path"]] = item
                indexed_file_count = len(indexed_files)
                expected_indexed_count = index.get("indexed_file_count")
                if not isinstance(expected_indexed_count, int) or isinstance(expected_indexed_count, bool):
                    issues.append("Invalid packet index: indexed_file_count must be an integer")
                elif expected_indexed_count != indexed_file_count:
                    issues.append("Invalid packet index: indexed_file_count does not match files")
                for name, item in indexed_files.items():
                    if name not in names:
                        issues.append(f"Indexed file missing from ZIP: {name}")
                        continue
                    info = infos_by_name.get(name)
                    if info is not None and info.file_size > MAX_ZIP_MEMBER_BYTES:
                        continue
                    payload = archive.read(name)
                    expected = str(item.get("sha256", ""))
                    actual = hashlib.sha256(payload).hexdigest()
                    if actual != expected:
                        issues.append(f"Checksum mismatch: {name}")
                    if len(payload) != item["bytes"]:
                        issues.append(f"Byte length mismatch: {name}")
                unindexed = sorted(set(names) - set(indexed_files) - {PACKET_INDEX_PATH})
                if unindexed:
                    issues.extend(f"ZIP file missing from packet index: {name}" for name in unindexed)
    except (
        KeyError,
        TypeError,
        ValueError,
        RuntimeError,
        NotImplementedError,
        zipfile.BadZipFile,
        json.JSONDecodeError,
        zlib.error,
    ) as exc:
        issues.append(f"Invalid data-room packet: {exc}")
    return {
        "valid": not issues,
        "issues": issues,
        "file_count": len(names),
        "indexed_file_count": indexed_file_count,
        "packet_sha256": hashlib.sha256(bundle_bytes).hexdigest(),
    }


def _dreamaudit_status(dreamaudit_intake: dict[str, Any] | None) -> dict[str, str]:
    if not dreamaudit_intake:
        return {
            "status": "needs_live_scan",
            "evidence": "No DreamAudit intake scan is attached.",
            "next_action": "Run DreamAudit Intake and attach the carrier-readiness ladder.",
        }
    if not dreamaudit_intake.get("root_exists"):
        return {
            "status": "needs_live_scan",
            "evidence": f"DreamAudit path not found: {dreamaudit_intake.get('root', 'unknown')}.",
            "next_action": "Point DreamAudit Intake at an existing artifact directory.",
        }
    readiness = dreamaudit_intake.get("readiness", {})
    ladder = list(dreamaudit_intake.get("evidence_depth_ladder", []))
    recommended = dreamaudit_intake.get("recommended_scan_limit")
    carrier_ready = readiness.get("status") == "carrier_review_ready" or any(
        row.get("status") == "carrier_review_ready" for row in ladder
    )
    selected_count = int(dreamaudit_intake.get("summary", {}).get("certificates", 0) or 0)
    selected_score = int(readiness.get("readiness_score", 0) or 0)
    status = "ready" if carrier_ready else "needs_live_scan"
    evidence = (
        f"{selected_count} selected DreamAudit certificates; selected readiness {selected_score}/100; "
        f"recommended carrier-ready depth {recommended or 'not found'}."
    )
    next_action = (
        "Attach the carrier-ready ladder and representative source paths to the data room."
        if carrier_ready
        else "Expand the DreamAudit scan until a carrier-ready ladder depth is available."
    )
    return {"status": status, "evidence": evidence, "next_action": next_action}


def _dreamaudit_manifest_summary(dreamaudit_intake: dict[str, Any] | None) -> dict[str, Any]:
    if not dreamaudit_intake:
        return {"attached": False, "status": "not_scanned"}
    readiness = dreamaudit_intake.get("readiness", {})
    return {
        "attached": True,
        "root": dreamaudit_intake.get("root"),
        "root_exists": bool(dreamaudit_intake.get("root_exists")),
        "selected_certificates": int(dreamaudit_intake.get("summary", {}).get("certificates", 0) or 0),
        "readiness_score": int(readiness.get("readiness_score", 0) or 0),
        "readiness_status": readiness.get("status", "unknown"),
        "recommended_scan_limit": dreamaudit_intake.get("recommended_scan_limit"),
        "evidence_depth_ladder": dreamaudit_intake.get("evidence_depth_ladder", []),
        "gaps": readiness.get("gaps", []),
    }


def _item(artifact: str, status: str, evidence: str, next_action: str) -> dict[str, str]:
    return {
        "artifact": artifact,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _text_bytes(payload: str) -> bytes:
    return payload.encode("utf-8")


def _write_zip_bytes(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, payload)


def _packet_index(manifest_id: str, entries: list[tuple[str, bytes]]) -> dict[str, Any]:
    return {
        "packet_format": PACKET_FORMAT_V27,
        "manifest_id": manifest_id,
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(entries),
        "required_files": sorted(REQUIRED_BUNDLE_FILES | {PACKET_INDEX_PATH}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in sorted(entries)
        ],
    }


def _required_files_for_packet_format(packet_format: str) -> set[str] | None:
    if packet_format == PACKET_FORMAT_V1:
        return REQUIRED_BUNDLE_FILES_V1
    if packet_format == PACKET_FORMAT_V2:
        return REQUIRED_BUNDLE_FILES_V2
    if packet_format == PACKET_FORMAT_V3:
        return REQUIRED_BUNDLE_FILES_V3
    if packet_format == PACKET_FORMAT_V4:
        return REQUIRED_BUNDLE_FILES_V4
    if packet_format == PACKET_FORMAT_V5:
        return REQUIRED_BUNDLE_FILES_V5
    if packet_format == PACKET_FORMAT_V6:
        return REQUIRED_BUNDLE_FILES_V6
    if packet_format == PACKET_FORMAT_V7:
        return REQUIRED_BUNDLE_FILES_V7
    if packet_format == PACKET_FORMAT_V8:
        return REQUIRED_BUNDLE_FILES_V8
    if packet_format == PACKET_FORMAT_V9:
        return REQUIRED_BUNDLE_FILES_V9
    if packet_format == PACKET_FORMAT_V10:
        return REQUIRED_BUNDLE_FILES_V10
    if packet_format == PACKET_FORMAT_V11:
        return REQUIRED_BUNDLE_FILES_V11
    if packet_format == PACKET_FORMAT_V12:
        return REQUIRED_BUNDLE_FILES_V12
    if packet_format == PACKET_FORMAT_V13:
        return REQUIRED_BUNDLE_FILES_V13
    if packet_format == PACKET_FORMAT_V14:
        return REQUIRED_BUNDLE_FILES_V14
    if packet_format == PACKET_FORMAT_V15:
        return REQUIRED_BUNDLE_FILES_V15
    if packet_format == PACKET_FORMAT_V16:
        return REQUIRED_BUNDLE_FILES_V16
    if packet_format == PACKET_FORMAT_V17:
        return REQUIRED_BUNDLE_FILES_V17
    if packet_format == PACKET_FORMAT_V18:
        return REQUIRED_BUNDLE_FILES_V18
    if packet_format == PACKET_FORMAT_V19:
        return REQUIRED_BUNDLE_FILES_V19
    if packet_format == PACKET_FORMAT_V20:
        return REQUIRED_BUNDLE_FILES_V20
    if packet_format == PACKET_FORMAT_V21:
        return REQUIRED_BUNDLE_FILES_V21
    if packet_format == PACKET_FORMAT_V22:
        return REQUIRED_BUNDLE_FILES_V22
    if packet_format == PACKET_FORMAT_V23:
        return REQUIRED_BUNDLE_FILES_V23
    if packet_format == PACKET_FORMAT_V24:
        return REQUIRED_BUNDLE_FILES_V24
    if packet_format == PACKET_FORMAT_V25:
        return REQUIRED_BUNDLE_FILES_V25
    if packet_format == PACKET_FORMAT_V26:
        return REQUIRED_BUNDLE_FILES_V26
    if packet_format == PACKET_FORMAT_V27:
        return REQUIRED_BUNDLE_FILES
    return None


def _unsafe_zip_name(name: str) -> bool:
    return (
        name.startswith("/")
        or "\\" in name
        or bool(re.match(r"^[A-Za-z]:", name))
        or any(part in {"", ".", ".."} for part in name.split("/"))
    )


def _safe_zip_stem(raw_id: str, used: set[str]) -> str:
    stem = re.sub(r"[^0-9A-Za-z._-]+", "_", str(raw_id)).strip("._-")
    if not stem or stem in {".", ".."}:
        stem = "evidence"
    candidate = stem
    counter = 2
    while candidate in used:
        candidate = f"{stem}__{counter}"
        counter += 1
    used.add(candidate)
    return candidate


def _bundle_readme(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# TACO Data Room Packet",
            "",
            f"Manifest: {manifest['manifest_id']}",
            "",
            "This packet contains the machine-readable underwriting contracts and diligence memo for the TACO learned-policy liability demo.",
            "Replay videos and DreamAudit source artifacts are indexed by path rather than embedded, so reviewers can verify local evidence without treating generated media as opaque marketing collateral.",
            "",
            "Core files:",
            "",
            "* `manifest.json` - full packet index",
            "* `application.json` - insurance application",
            "* `quote.json` - quote breakdown",
            "* `checklist.json` - VC/carrier readiness checklist",
            "* `diligence_memo.md` - investor and underwriting memo",
            "* `packet/index.json` - SHA-256 checksum index for packet verification",
            "* `insurance/workflow_examples.json` - priced workflow examples",
            "* `research/sources.json` - research-methodology anchors",
            "* `research/methodology_evidence_map.json` - claim-by-claim methodology evidence map",
            "* `research/claim_validation_ledger.json` - investor-safe claims, evidence levels, upgrade gates, and disallowed overclaims",
            "* `research/research_validation_plan.json` - falsifiable hypotheses, validation workstreams, acceptance thresholds, and downgrade rules",
            "* `research/methodology_validation_protocol.json` - prospective endpoints, baselines, sample-size rungs, execution workflows, and artifact gates",
            "* `research/activation_evidence_contract.json` - layer-to-signal map, trace-bundle requirements, calibration gates, artifact checks, and no-claim rules",
            "* `evidence/provenance_audit.json` - source classification for certificates, internal metrics, generated videos, claim boundaries, and upgrade gates",
            "* `certificates/` - primary replay failure certificates",
            "* `metrics/` - internal-risk metric contracts",
            "* `suite/video_index.json` - 40-video ManiSkill/RMA suite index",
            "* `dreamaudit/summary.json` - attached DreamAudit intake summary",
            "* `dreamaudit/corpus_reconciliation.json` - live corpus gates, gaps, claim-upgrade paths, and source-path policy",
            "* `commercial/design_partner_plan.json` - external-validation plan for broker/carrier/OEM pilots",
            "* `commercial/seed_financing_plan.json` - proposed $5M seed use-of-funds and milestone plan",
            "* `commercial/pricing_diligence.json` - quote-factor and control-sensitivity diligence artifact",
            "* `commercial/investor_objection_register.json` - evidence-linked investor and carrier objection register",
            "* `commercial/pilot_walkthrough_playbook.json` - reviewer walkthrough agenda, role tracks, and evidence capture form",
            "* `commercial/commercial_scale_model.json` - market-context, buyer-segment, revenue-scenario, and proof-gate model",
            "* `commercial/competitive_positioning.json` - category definition, alternatives, wedge strategy, defensibility hypotheses, and validation actions",
            "* `commercial/capacity_roadmap.json` - insurance capacity, licensing, filing, actuarial, and claims-readiness roadmap",
            "* `commercial/enterprise_security_plan.json` - security, data governance, retention, incident response, and SOC2/NIST readiness plan",
            "* `commercial/external_validation_capture_kit.json` - reviewer feedback, scorecard, LOI/pilot-scope, and permission-to-quote capture kit",
            "* `commercial/actuarial_readiness_plan.json` - future-cost, data-quality, modeling, credibility, filing, and claims-loop readiness plan",
            "* `commercial/buyer_roi_model.json` - modeled buyer economics, payback scenarios, proof gates, and ROI sensitivity cases",
            "* `commercial/investor_proof_pipeline.json` - weekly external-proof workflow, reviewer targets, proof gates, and data-room upgrade rules",
            "* `commercial/commercial_traction_plan.json` - ICP targets, paid package ladder, weekly traction metrics, investor reporting rules, and count/do-not-count controls",
            "* `commercial/commercial_unit_economics.json` - modeled revenue mix, delivery cost, gross margin, CAC/payback assumptions, and seed milestone gates",
            "* `commercial/seed_round_close_plan.json` - investor segmentation, weekly close motion, lead-partner gates, minimum close package, and no-count rules",
            "* `commercial/fundraise_narrative_memo.json` - one-line thesis, seven-minute demo, proof stack, investor questions, and close workflow",
            "* `commercial/external_proof_registry.json` - proof slots, packet fingerprint requirements, permission-to-quote states, redaction gates, and claim-upgrade rules",
            "* `technical/technical_diligence_runbook.json` - local reproduction, live-evidence, packet-verification, and cluster-regeneration runbook",
            "",
            "Boundary: this packet is diligence evidence for a local proof of concept, not an insurance offer, filed actuarial product, rate adequacy opinion, committed financing, or signed customer demand.",
            "",
        ]
    )
