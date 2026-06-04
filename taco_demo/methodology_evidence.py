"""Methodology evidence map for investor and carrier diligence."""

from __future__ import annotations

from typing import Any

from .investor_case import RESEARCH_FOUNDATIONS
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


CLAIM_SCORE = {
    "research_and_artifact_backed": 1.0,
    "demo_backed_needs_live_evidence": 0.65,
    "research_backed_needs_external_validation": 0.5,
    "needs_work": 0.0,
}


def build_methodology_evidence_map(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return claim-by-claim evidence, verification steps, and boundaries."""

    suite_cases = list(suite_manifest.get("cases", []))
    suite_size = int(suite_manifest.get("suite_size", len(suite_cases)) or 0)
    suite_families = sorted({str(case.get("failure_family", "unknown")) for case in suite_cases})
    metric_ids = {metric.certificate_id for metric in metrics}
    metric_coverage = sum(1 for cert in certificates if cert.certificate_id in metric_ids)
    metric_sources = sorted({metric.metrics_source for metric in metrics})
    dreamaudit_summary = dreamaudit_intake.get("summary", {}) if dreamaudit_intake else {}
    dreamaudit_count = int(dreamaudit_summary.get("certificates", 0) or 0)
    dreamaudit_readiness = dreamaudit_intake.get("readiness", {}) if dreamaudit_intake else {}
    dreamaudit_ready = (
        bool(dreamaudit_intake)
        and bool(dreamaudit_intake.get("root_exists"))
        and str(dreamaudit_readiness.get("status", "")) == "carrier_review_ready"
    )

    claims = [
        _claim(
            "pre_telemetry_underwriting_gap",
            "Traditional robotics underwriting can be blocked before deployment telemetry and claims history exist.",
            "Can the buyer show why conventional loss-history underwriting is unavailable?",
            "research_and_artifact_backed" if not application.telemetry_available else "needs_work",
            ["SIMPLER / CoRL 2024"],
            ["application.json", "quote.json"],
            f"{application.company_name} is marked {application.deployment_stage} with telemetry_available={application.telemetry_available}.",
            "Inspect InsuranceApplication and confirm the submission is pre-deployment.",
            "This proves a workflow gap, not a bound market-size or loss-ratio claim.",
        ),
        _claim(
            "replayable_failure_boundaries",
            "Replayable counterfactual failures can become underwriting evidence objects.",
            "Can reviewers reproduce specific failure families and see the perturbation boundary?",
            "research_and_artifact_backed" if len(certificates) >= 3 and all(cert.replay_command for cert in certificates) else "needs_work",
            ["Muratore et al., CoRL 2018", "SIMPLER / CoRL 2024"],
            ["certificates/*.json", "suite/video_index.json"],
            f"{len(certificates)} primary certificates and {suite_size} suite cases across {len(suite_families)} families.",
            "Open certificate JSONs, inspect replay commands, and sample the ManiSkill/RMA video index.",
            "Replay evidence is pre-deployment stress evidence, not proof of live-field frequency.",
        ),
        _claim(
            "internal_activation_risk_path",
            "Internal traces can expose behavior-relevant risk signals not visible from output-only pass/fail labels.",
            "Do the internal-risk metrics come from trace artifacts for the same certificates?",
            _internals_status(certificates, metrics, dreamaudit_ready),
            [
                "Sparse Autoencoders Find Highly Interpretable Features, ICLR 2024",
                "Anthropic, Mapping the Mind of a Large Language Model, 2024",
            ],
            ["metrics/*.json", "taco_demo/data/traces/*.npz", "taco_demo/activation_recorder.py"],
            f"{metric_coverage}/{len(certificates)} primary certificates have metrics; sources: {', '.join(metric_sources) if metric_sources else 'none'}.",
            "Compare certificate IDs to metric IDs, then inspect NPZ traces or recorded activation exports.",
            "Current metrics support an internals-based path; real underwriting needs policy-specific recorded activations and calibration.",
        ),
        _claim(
            "control_linked_pricing",
            "Controls and exclusions can translate robot-policy evidence into conditional insurance terms.",
            "Can a reviewer trace each premium delta or exclusion back to a required control?",
            "research_and_artifact_backed" if quote.final_monthly_premium_usd > 0 and quote.required_controls else "needs_work",
            ["Anthropic, Mapping the Mind of a Large Language Model, 2024"],
            ["quote.json", "insurance/workflow_examples.json", "diligence_memo.md"],
            f"${quote.final_monthly_premium_usd:,.0f}/mo conditional premium with {len(quote.required_controls)} required controls.",
            "Toggle controls in the quote tab and compare pricing, exclusions, and workflow examples.",
            "The quote is a transparent demo formula, not filed actuarial pricing or an insurance offer.",
        ),
        _claim(
            "live_corpus_transfer",
            "The methodology should transfer from local fixtures to real DreamAudit certificate corpora.",
            "Is the data room backed by a live DreamAudit scan rather than only local fixtures?",
            "research_and_artifact_backed"
            if dreamaudit_ready
            else ("demo_backed_needs_live_evidence" if dreamaudit_count > 0 else "needs_work"),
            ["SIMPLER / CoRL 2024", "Muratore et al., CoRL 2018"],
            ["dreamaudit/summary.json", "taco_demo/dreamaudit_adapter.py", "taco_demo/dreamaudit_intake.py"],
            f"{dreamaudit_count} DreamAudit certificates attached; readiness status {dreamaudit_readiness.get('status', 'not_scanned')}.",
            "Run the DreamAudit Intake tab and verify source paths, readiness ladder, minimality coverage, and mapped controls.",
            "A carrier-ready corpus reduces demo risk but still needs external reviewer acceptance and partner-specific policy evidence.",
        ),
        _claim(
            "auditable_packet_workflow",
            "A shared data-room packet can make autonomy-risk evidence reviewable by engineers, brokers, carriers, and investors.",
            "Can a transferred ZIP be verified without trusting screenshots or presentation copy?",
            "research_and_artifact_backed",
            [],
            ["packet/index.json", "manifest.json", "diligence_memo.md"],
            "Generated packets include a SHA-256 index, required-file list, and bounded verifier.",
            "Download the Data Room Packet, upload it back into the verifier, and compare the packet fingerprint.",
            "Packet integrity proves artifact transfer and tamper detection, not commercial adoption.",
        ),
    ]
    score = round(100 * sum(CLAIM_SCORE[claim["status"]] for claim in claims) / len(claims)) if claims else 0
    return {
        "map_id": f"METHOD-{application.application_id}",
        "status": _posture(score),
        "score": score,
        "boundary": "This map links research directions to local diligence evidence; it does not claim actuarial validation, regulatory approval, or external reviewer acceptance.",
        "research_source_count": len(RESEARCH_FOUNDATIONS),
        "claims": claims,
        "open_methodology_risks": [
            "Simulation evidence still needs partner-specific transfer checks.",
            "Internal-risk traces need real policy activations and calibration before live underwriting claims.",
            "Premium effects need actuarial, compliance, and capacity review before launch.",
            "Design-partner feedback must confirm that the evidence format changes real buyer or carrier decisions.",
        ],
    }


def methodology_evidence_rows(evidence_map: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly claim rows."""

    return [
        {
            "Claim": claim["claim_id"],
            "Status": claim["status"].replace("_", " ").title(),
            "Diligence Question": claim["diligence_question"],
            "Current Evidence": claim["current_evidence"],
            "Boundary": claim["boundary"],
        }
        for claim in evidence_map["claims"]
    ]


def _internals_status(
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    dreamaudit_ready: bool,
) -> str:
    if not certificates or not metrics:
        return "needs_work"
    metric_ids = {metric.certificate_id for metric in metrics}
    complete = all(cert.certificate_id in metric_ids for cert in certificates)
    if not complete:
        return "needs_work"
    real_activation_sources = {"recorded_activation_forward_hooks", "activation_recorder_npz"}
    if any(metric.metrics_source in real_activation_sources for metric in metrics) or dreamaudit_ready:
        return "research_and_artifact_backed"
    return "demo_backed_needs_live_evidence"


def _claim(
    claim_id: str,
    thesis_claim: str,
    diligence_question: str,
    status: str,
    research_anchors: list[str],
    local_artifacts: list[str],
    current_evidence: str,
    verification_workflow: str,
    boundary: str,
) -> dict[str, Any]:
    return {
        "claim_id": claim_id,
        "thesis_claim": thesis_claim,
        "diligence_question": diligence_question,
        "status": status,
        "research_anchors": research_anchors,
        "local_artifacts": local_artifacts,
        "current_evidence": current_evidence,
        "verification_workflow": verification_workflow,
        "boundary": boundary,
    }


def _posture(score: int) -> str:
    if score >= 85:
        return "methodology_diligence_ready_with_boundaries"
    if score >= 65:
        return "credible_methodology_needs_live_evidence"
    return "methodology_story_needs_more_artifacts"
