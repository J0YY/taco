"""Research validation plan for TACO methodology diligence."""

from __future__ import annotations

from typing import Any

from .investor_case import RESEARCH_FOUNDATIONS
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


def build_research_validation_plan(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    methodology_map: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
    investor_proof_pipeline: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a falsifiable research plan for technical and investor diligence."""

    suite_cases = list(suite_manifest.get("cases", []))
    suite_size = int(suite_manifest.get("suite_size", len(suite_cases)) or 0)
    suite_families = sorted({str(case.get("failure_family", "unknown")) for case in suite_cases})
    metric_sources = sorted({metric.metrics_source for metric in metrics})
    real_activation_metrics = sum(1 for metric in metrics if metric.metrics_source in _real_activation_sources())
    dreamaudit_ready = _dreamaudit_ready(dreamaudit_intake)
    current_score = _research_score(
        methodology_map,
        claim_validation_ledger,
        investor_proof_pipeline,
        suite_size,
        len(suite_families),
        real_activation_metrics,
        len(metrics),
        dreamaudit_ready,
    )
    return {
        "plan_id": f"RVAL-{application.application_id}",
        "status": _status(current_score, dreamaudit_ready, real_activation_metrics, len(metrics)),
        "boundary": "This is a research validation plan, not proof of sim-to-real transfer, causal interpretability, actuarial credibility, external reviewer acceptance, filed pricing, or live loss reduction.",
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "robot_type": application.robot_type,
            "deployment_stage": application.deployment_stage,
            "telemetry_available": application.telemetry_available,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
        },
        "current_evidence_summary": {
            "methodology_score": int(methodology_map.get("score", 0) or 0),
            "claim_validation_score": int(claim_validation_ledger.get("evidence_score", 0) or 0),
            "proof_pipeline_score": int(investor_proof_pipeline.get("current_scores", {}).get("current_artifact_score", 0) or 0),
            "research_validation_score": current_score,
            "primary_certificates": len(certificates),
            "suite_size": suite_size,
            "suite_failure_families": len(suite_families),
            "metric_sources": metric_sources,
            "real_activation_metric_count": real_activation_metrics,
            "dreamaudit_carrier_ready": dreamaudit_ready,
        },
        "research_sources": _research_sources(),
        "hypotheses": _hypotheses(),
        "validation_workstreams": _validation_workstreams(
            certificates,
            metrics,
            suite_size,
            suite_families,
            dreamaudit_ready,
        ),
        "minimum_research_proof_package": [
            "carrier-ready DreamAudit corpus or partner-specific simulator certificate set with source paths",
            "success/failure/mitigated activation NPZ bundle for the same policy or task family",
            "layer-to-signal calibration memo and rejected-layer list",
            "control-on/control-off replay study with confidence-bounded effectiveness result",
            "external reviewer memo marking accepted, rejected, and missing methodology claims",
            "actuarial data-quality memo describing derived data, limitations, and allowed use",
        ],
        "downgrade_rules": [
            _rule(
                "sim_to_real_failure_mismatch",
                "Partner review shows simulated failure families do not appear in staged deployment, real logs, or accepted reviewer threat models.",
                "Downgrade replay claims to research_backed_needs_external_validation and stop using simulator breadth as buyer proof.",
            ),
            _rule(
                "internals_not_incremental",
                "Activation metrics do not improve early warning, failure-family separation, or mitigation ranking over output-only baselines.",
                "Downgrade internals claims and present activation capture only as future research infrastructure.",
            ),
            _rule(
                "control_effect_not_replicated",
                "Required controls fail to reduce replay risk, staged incident rate, or reviewer-accepted exposure under repeated runs.",
                "Remove premium-credit language for that control and preserve only exclusion or re-audit language.",
            ),
            _rule(
                "reviewer_rejects_artifact_format",
                "Broker, carrier, OEM, or risk reviewer cannot use the packet in an actual decision workflow.",
                "Downgrade fundraise story from evidence layer to technical demo until the workflow is redesigned.",
            ),
        ],
        "blocked_claims_until_validated": [
            "TACO has proven sim-to-real transfer for learned-policy insurance.",
            "Internal activations causally explain robot failures.",
            "TACO premium deltas are actuarially credible or filed rates.",
            "Control discounts are validated loss-reduction estimates.",
            "External reviewers or customers have accepted the methodology.",
        ],
    }


def research_validation_hypothesis_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly hypothesis rows."""

    return [
        {
            "Hypothesis": item["hypothesis_id"],
            "Research Anchor": item["research_anchor"],
            "Testable Prediction": item["testable_prediction"],
            "Blocked Claim": item["blocked_claim_until_passed"],
        }
        for item in plan["hypotheses"]
    ]


def research_validation_workstream_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly validation workstream rows."""

    return [
        {
            "Workstream": item["workstream"],
            "Current Evidence": item["current_evidence"],
            "Experiment": item["experiment"],
            "Acceptance Threshold": item["acceptance_threshold"],
            "Falsification Signal": item["falsification_signal"],
        }
        for item in plan["validation_workstreams"]
    ]


def research_validation_rule_rows(plan: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly downgrade rule rows."""

    return [
        {
            "Rule": item["rule"],
            "Trigger": item["trigger"],
            "Required Downgrade": item["required_downgrade"],
        }
        for item in plan["downgrade_rules"]
    ]


def _research_sources() -> list[dict[str, str]]:
    rows = []
    for index, source in enumerate(RESEARCH_FOUNDATIONS, start=1):
        rows.append(
            {
                "source_id": f"research_anchor_{index}",
                "source": source["source"],
                "url": source["url"],
                "claim_supported": source["claim"],
                "taco_translation": source["taco_translation"],
                "validation_boundary": "Research direction only; TACO must still pass local, partner-specific, and external-review validation gates.",
            }
        )
    return rows


def _hypotheses() -> list[dict[str, str]]:
    return [
        {
            "hypothesis_id": "simulation_replay_is_useful_predeployment_evidence",
            "research_anchor": "SIMPLER / CoRL 2024 plus domain randomization literature.",
            "testable_prediction": "Reviewer-accepted simulator certificates identify failure families, controls, or exclusions before fleet telemetry exists.",
            "blocked_claim_until_passed": "Simulator evidence predicts live loss frequency or field behavior.",
        },
        {
            "hypothesis_id": "perturbation_boundaries_rank_underwriting_risk",
            "research_anchor": "Domain randomization and counterfactual stress-testing literature.",
            "testable_prediction": "Lower minimal failure cost and higher neighborhood failure rate correlate with reviewer severity ranking or staged incidents.",
            "blocked_claim_until_passed": "Failure-boundary cost is a calibrated actuarial frequency or severity input.",
        },
        {
            "hypothesis_id": "internal_activations_add_signal",
            "research_anchor": "Sparse autoencoder and feature-mapping interpretability work.",
            "testable_prediction": "Recorded activations improve early warning, failure-family separation, or control-effect ranking over output-only baselines.",
            "blocked_claim_until_passed": "TACO has causal mechanistic explanations for robot failures.",
        },
        {
            "hypothesis_id": "controls_translate_evidence_into_terms",
            "research_anchor": "Feature-level monitoring and insurance control-workflow practice.",
            "testable_prediction": "Control-on/control-off studies show repeatable risk reduction that reviewers can map to exclusions, re-audit triggers, or conditional terms.",
            "blocked_claim_until_passed": "Control deltas are validated premium discounts or filed rates.",
        },
        {
            "hypothesis_id": "packetized_evidence_changes_reviewer_workflow",
            "research_anchor": "Data-quality, model-governance, and diligence-room practice.",
            "testable_prediction": "External reviewers can verify the packet, name accepted/rejected claims, and request specific missing evidence faster than with screenshots.",
            "blocked_claim_until_passed": "TACO has proven customer demand or procurement approval.",
        },
    ]


def _validation_workstreams(
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    suite_size: int,
    suite_families: list[str],
    dreamaudit_ready: bool,
) -> list[dict[str, str]]:
    metric_sources = sorted({metric.metrics_source for metric in metrics}) or ["none"]
    return [
        _workstream(
            "sim_to_real_or_reviewer_transfer",
            f"{len(certificates)} primary certificates; {suite_size} suite cases; {len(suite_families)} suite failure families; DreamAudit carrier-ready={dreamaudit_ready}.",
            "Run a partner-specific DreamAudit scan or reviewer threat-model mapping for the same policy/task family.",
            "At least 3 accepted failure families, source paths, replay commands, and one reviewer-confirmed underwriting implication.",
            "Reviewer rejects the failure families as irrelevant or source artifacts cannot be reproduced.",
        ),
        _workstream(
            "activation_incrementality",
            f"{len(metrics)} metric contracts; sources: {', '.join(metric_sources)}.",
            "Compare output-only baseline versus activation metrics for early warning, family classification, and mitigation ranking.",
            "Activation features improve at least one predeclared metric and do not degrade the other two.",
            "Activation metrics are flat, unstable, not reproducible, or no better than output-only labels.",
        ),
        _workstream(
            "control_effectiveness_replication",
            "Current controls are quote-engine requirements with mitigated replay traces and insurance workflow examples.",
            "Run repeated control-on/control-off replay pairs across accepted failure families and record confidence intervals.",
            "Each priced control shows repeatable directionally positive effect and reviewer-accepted operational feasibility.",
            "Control effect reverses, is non-repeatable, or the control cannot be deployed in the buyer workflow.",
        ),
        _workstream(
            "actuarial_data_quality_and_model_limits",
            "Actuarial readiness plan defines data-quality, modeling, credibility, communication, and filing gates.",
            "Have an actuary or carrier model reviewer classify each artifact as allowed, limited, or disallowed for future-cost work.",
            "Written memo accepts the artifact taxonomy for exploration while preserving limits against rate adequacy claims.",
            "Reviewer says artifacts are too synthetic, undocumented, or biased for even exploratory actuarial use.",
        ),
        _workstream(
            "external_workflow_utility",
            "Investor proof pipeline defines packet-fingerprinted reviewer walkthroughs and downgrade rules.",
            "Run external reviewer walkthroughs and compare accepted claims, missing evidence, and next-document conversion.",
            "At least two reviewers verify the packet and produce written missing-evidence or next-review documents.",
            "Reviewers cannot use the packet format or only provide non-actionable curiosity feedback.",
        ),
    ]


def _workstream(
    workstream: str,
    current_evidence: str,
    experiment: str,
    acceptance_threshold: str,
    falsification_signal: str,
) -> dict[str, str]:
    return {
        "workstream": workstream,
        "current_evidence": current_evidence,
        "experiment": experiment,
        "acceptance_threshold": acceptance_threshold,
        "falsification_signal": falsification_signal,
    }


def _rule(rule: str, trigger: str, required_downgrade: str) -> dict[str, str]:
    return {
        "rule": rule,
        "trigger": trigger,
        "required_downgrade": required_downgrade,
    }


def _research_score(
    methodology_map: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
    investor_proof_pipeline: dict[str, Any],
    suite_size: int,
    suite_family_count: int,
    real_activation_metrics: int,
    total_metrics: int,
    dreamaudit_ready: bool,
) -> int:
    score = 0
    score += min(20, round(int(methodology_map.get("score", 0) or 0) * 0.2))
    score += min(15, round(int(claim_validation_ledger.get("evidence_score", 0) or 0) * 0.15))
    score += min(15, round(int(investor_proof_pipeline.get("current_scores", {}).get("current_artifact_score", 0) or 0) * 0.15))
    score += 15 if suite_size >= 40 and suite_family_count >= 8 else 5
    score += 15 if dreamaudit_ready else 5
    if total_metrics and real_activation_metrics == total_metrics:
        score += 15
    elif total_metrics:
        score += 8
    else:
        score += 0
    score += 5 if len(RESEARCH_FOUNDATIONS) >= 4 else 0
    return min(100, score)


def _status(score: int, dreamaudit_ready: bool, real_activation_metrics: int, total_metrics: int) -> str:
    activation_ready = bool(total_metrics) and real_activation_metrics == total_metrics
    if score >= 85 and dreamaudit_ready and activation_ready:
        return "research_validation_plan_ready_for_external_execution"
    if score >= 70:
        return "research_plan_strong_local_basis_needs_partner_validation"
    if score >= 50:
        return "research_plan_defined_needs_live_evidence"
    return "research_plan_needs_stronger_artifacts"


def _dreamaudit_ready(dreamaudit_intake: dict[str, Any] | None) -> bool:
    if not dreamaudit_intake or not dreamaudit_intake.get("root_exists"):
        return False
    readiness = dreamaudit_intake.get("readiness", {})
    ladder = list(dreamaudit_intake.get("evidence_depth_ladder", []))
    return str(readiness.get("status", "")) == "carrier_review_ready" or any(
        row.get("status") == "carrier_review_ready" for row in ladder
    )


def _real_activation_sources() -> set[str]:
    return {"recorded_activation_forward_hooks", "activation_recorder_npz"}
