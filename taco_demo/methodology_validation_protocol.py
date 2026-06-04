"""Prospective validation protocol for TACO methodology diligence."""

from __future__ import annotations

from typing import Any

from .investor_case import RESEARCH_FOUNDATIONS
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


def build_methodology_validation_protocol(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    research_validation_plan: dict[str, Any],
    external_proof_registry: dict[str, Any],
) -> dict[str, Any]:
    """Return an executable validation protocol before external evidence exists."""

    suite_cases = list(suite_manifest.get("cases", []))
    suite_size = int(suite_manifest.get("suite_size", len(suite_cases)) or 0)
    failure_families = sorted({str(case.get("failure_family", "unknown")) for case in suite_cases})
    real_activation_metrics = sum(1 for metric in metrics if metric.metrics_source in _real_activation_sources())
    return {
        "protocol_id": f"VALPROTO-{application.application_id}",
        "status": "protocol_ready_pre_registration_required",
        "boundary": (
            "This protocol defines prospective validation design, endpoints, baselines, sample-size rungs, "
            "artifact gates, and falsification rules; it is not evidence that TACO has completed external "
            "validation, proven sim-to-real transfer, produced causal mechanistic explanations, or generated "
            "actuarially credible pricing."
        ),
        "packet_context": {
            "target_packet_format": "taco_data_room_zip_v25",
            "source_research_plan": research_validation_plan["plan_id"],
            "external_registry": external_proof_registry["registry_id"],
            "packet_sha256_required_before_execution": True,
            "pre_registration_required": True,
        },
        "current_design_inputs": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "primary_certificate_count": len(certificates),
            "suite_size": suite_size,
            "suite_failure_family_count": len(failure_families),
            "metric_count": len(metrics),
            "real_activation_metric_count": real_activation_metrics,
        },
        "research_basis": _research_basis(),
        "primary_endpoints": _primary_endpoints(),
        "baseline_comparisons": _baseline_comparisons(),
        "sample_size_rungs": _sample_size_rungs(suite_size, len(failure_families)),
        "execution_workflows": _execution_workflows(external_proof_registry),
        "acceptance_matrix": _acceptance_matrix(),
        "artifact_package": _artifact_package(),
        "no_claim_until_passed": [
            "Do not say simulator evidence predicts live robot loss frequency until the transfer endpoint passes on partner-specific evidence.",
            "Do not say internal activations are causal explanations until incrementality and calibration endpoints pass against baselines.",
            "Do not say control deltas are validated premium discounts until repeated control-effect and actuarial-review endpoints pass.",
            "Do not say reviewers accepted the method until packet-fingerprinted written reviewer artifacts are attached with permission state.",
        ],
    }


def validation_endpoint_rows(protocol: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for primary endpoints."""

    return [
        {
            "Endpoint": item["endpoint"],
            "Question": item["diligence_question"],
            "Metric": item["metric"],
            "Pass Threshold": item["pass_threshold"],
            "Blocks Claim": item["blocks_claim"],
        }
        for item in protocol["primary_endpoints"]
    ]


def validation_baseline_rows(protocol: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for baseline comparisons."""

    return [
        {
            "Baseline": item["baseline"],
            "Compared Against": item["compared_against"],
            "Why It Matters": item["why_it_matters"],
            "Failure Mode": item["failure_mode"],
        }
        for item in protocol["baseline_comparisons"]
    ]


def validation_rung_rows(protocol: dict[str, Any]) -> list[dict[str, Any]]:
    """Return rows for sample-size rungs."""

    return [
        {
            "Rung": item["rung"],
            "Minimum Artifacts": item["minimum_artifacts"],
            "Reviewer Role": item["reviewer_role"],
            "Promotes To": item["promotes_to"],
            "Do Not Use For": item["do_not_use_for"],
        }
        for item in protocol["sample_size_rungs"]
    ]


def validation_workflow_rows(protocol: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for execution workflows."""

    return [
        {
            "Workflow": item["workflow"],
            "Owner": item["owner"],
            "Input": item["input_artifact"],
            "Output": item["output_artifact"],
            "Gate": item["gate"],
        }
        for item in protocol["execution_workflows"]
    ]


def _research_basis() -> list[dict[str, str]]:
    return [
        {
            "source": item["source"],
            "claim": item["claim"],
            "protocol_use": _protocol_use(item["claim"]),
            "boundary": "Research motivates the protocol design but does not replace prospective validation.",
        }
        for item in RESEARCH_FOUNDATIONS
    ]


def _primary_endpoints() -> list[dict[str, str]]:
    return [
        _endpoint(
            "failure_family_transfer",
            "Do partner-specific certificates surface reviewer-accepted failure families?",
            "accepted failure families with replay/source path and reviewer implication",
            ">=3 accepted families and zero unreproducible primary artifacts",
            "sim_to_real_transfer_or_underwriting_relevance",
        ),
        _endpoint(
            "activation_incrementality_over_outputs",
            "Do activation-derived signals add useful warning or ranking beyond pass/fail labels?",
            "improvement on early warning, family separation, or mitigation ranking over output-only baseline",
            "positive lift on at least one endpoint with no material degradation on the others",
            "internals_based_risk_signal",
        ),
        _endpoint(
            "control_effect_directionality",
            "Do required controls repeatedly reduce replay risk in the accepted failure families?",
            "control-on/control-off risk delta direction and reviewer feasibility",
            "directionally positive replicated effect for every priced control or removal of that control credit",
            "control_linked_pricing_sensitivity",
        ),
        _endpoint(
            "packet_review_utility",
            "Can reviewers use the packet to accept, reject, or request missing evidence without presentation trust?",
            "written reviewer artifact with packet SHA-256, accepted/rejected claim IDs, and missing-evidence list",
            ">=2 written artifacts from distinct reviewer roles",
            "external_validation_status",
        ),
        _endpoint(
            "actuarial_data_quality_classification",
            "Can an actuarial or carrier reviewer classify each artifact for allowed exploratory use?",
            "allowed/limited/disallowed artifact taxonomy and communication boundary",
            "written memo preserves limits and accepts the taxonomy for exploratory review",
            "actuarial_readiness",
        ),
    ]


def _endpoint(
    endpoint: str,
    diligence_question: str,
    metric: str,
    pass_threshold: str,
    blocks_claim: str,
) -> dict[str, str]:
    return {
        "endpoint": endpoint,
        "diligence_question": diligence_question,
        "metric": metric,
        "pass_threshold": pass_threshold,
        "blocks_claim": blocks_claim,
    }


def _baseline_comparisons() -> list[dict[str, str]]:
    return [
        {
            "baseline": "output_only_failure_labels",
            "compared_against": "activation-derived early warning and mitigation ranking",
            "why_it_matters": "Separates an internals-based underwriting signal from a labeled replay dashboard.",
            "failure_mode": "If activation features do not add signal, downgrade internals claims to future research infrastructure.",
        },
        {
            "baseline": "random_or_unstructured_perturbations",
            "compared_against": "DreamAudit-style minimal failure boundaries and named failure families",
            "why_it_matters": "Tests whether structured counterfactuals produce more useful underwriting artifacts.",
            "failure_mode": "If random perturbations perform as well, remove claims about failure-boundary search quality.",
        },
        {
            "baseline": "control_absent_replay",
            "compared_against": "control-on mitigated replay for the same certificate family",
            "why_it_matters": "Prevents premium-control stories from resting on static exclusions or screenshots.",
            "failure_mode": "If controls do not reduce replay risk directionally, remove the premium-credit explanation.",
        },
        {
            "baseline": "slide_or_screenshot_review",
            "compared_against": "hash-indexed packet review with claim ledger and proof registry",
            "why_it_matters": "Tests whether TACO is a review workflow, not just a polished demo.",
            "failure_mode": "If reviewers cannot use the packet, downgrade the commercial story until workflow redesign.",
        },
    ]


def _sample_size_rungs(suite_size: int, failure_family_count: int) -> list[dict[str, Any]]:
    return [
        {
            "rung": "local_fixture_sanity",
            "minimum_artifacts": f"3 primary certificates, 3 trace triplets, and current suite size {suite_size}",
            "reviewer_role": "internal reviewer or technical founder",
            "promotes_to": "demo-backed local reproducibility only",
            "do_not_use_for": "external validation, customer demand, or actuarial credibility",
        },
        {
            "rung": "partner_task_family",
            "minimum_artifacts": ">=30 partner-specific certificates across >=5 accepted failure families",
            "reviewer_role": "robotics OEM or autonomy engineering reviewer",
            "promotes_to": "partner-specific workflow relevance",
            "do_not_use_for": "field-frequency or loss-ratio claims",
        },
        {
            "rung": "carrier_review_packet",
            "minimum_artifacts": f">=100 certificates or accepted DreamAudit ladder depth, >=8 families; current families {failure_family_count}",
            "reviewer_role": "broker, MGA, carrier, reinsurer, or actuarial reviewer",
            "promotes_to": "carrier-review-ready exploratory evidence",
            "do_not_use_for": "filed pricing or binding capacity",
        },
        {
            "rung": "prospective_control_study",
            "minimum_artifacts": "repeated control-on/off runs for each priced control plus reviewer memo and redaction approval",
            "reviewer_role": "buyer risk owner plus technical reviewer",
            "promotes_to": "control-effect evidence for commercial pilots",
            "do_not_use_for": "guaranteed savings or validated premium discount",
        },
    ]


def _execution_workflows(external_proof_registry: dict[str, Any]) -> list[dict[str, str]]:
    registry_id = external_proof_registry.get("registry_id", "external_proof_registry")
    return [
        _workflow(
            "pre_register_packet",
            "founder or technical diligence owner",
            "data-room ZIP and packet/index.json",
            "protocol run sheet with packet SHA-256 and frozen endpoint list",
            "No endpoint can be counted if the packet hash is missing.",
        ),
        _workflow(
            "run_baselines",
            "technical owner",
            "output-only labels, trace NPZs, control-on/off replays",
            "baseline comparison table with failures and rejected runs",
            "Every promoted endpoint must name the baseline it beat or failed to beat.",
        ),
        _workflow(
            "collect_reviewer_artifacts",
            "commercial owner",
            f"{registry_id} proof slots",
            "written reviewer memo or missing-evidence note with permission state",
            "Private, anonymous, or named quote state must be attached before investor use.",
        ),
        _workflow(
            "redact_and_classify",
            "technical owner plus counsel/founder",
            "source paths, activation traces, reviewer wording, and commercial documents",
            "public-ready or private-diligence-only artifact classification",
            "No raw source path, customer identifier, or unpermissioned quote can enter the public packet.",
        ),
        _workflow(
            "update_claim_ledger",
            "diligence owner",
            "endpoint outcomes, baselines, reviewer artifacts, and redaction decisions",
            "claim upgrade/downgrade diff against the previous packet",
            "A failed endpoint must create an explicit claim downgrade or no-upgrade note.",
        ),
    ]


def _workflow(
    workflow: str,
    owner: str,
    input_artifact: str,
    output_artifact: str,
    gate: str,
) -> dict[str, str]:
    return {
        "workflow": workflow,
        "owner": owner,
        "input_artifact": input_artifact,
        "output_artifact": output_artifact,
        "gate": gate,
    }


def _acceptance_matrix() -> list[dict[str, str]]:
    return [
        {
            "outcome": "pass",
            "investor_use": "May report endpoint passed with packet hash, reviewer role, artifact count, and boundary.",
            "claim_action": "Upgrade only linked claim IDs and preserve remaining blocked claims.",
        },
        {
            "outcome": "mixed",
            "investor_use": "May report what passed and what failed, without implying whole-method validation.",
            "claim_action": "Upgrade no claim unless its endpoint-specific threshold passed.",
        },
        {
            "outcome": "fail",
            "investor_use": "Report the falsification result as methodology learning, not proof.",
            "claim_action": "Downgrade linked claims and update no-claim rules before the next packet export.",
        },
    ]


def _artifact_package() -> list[dict[str, str]]:
    return [
        {
            "artifact": "pre_registration_run_sheet",
            "required_fields": "packet_sha256, frozen endpoints, baseline definitions, owner, date, excluded runs policy",
        },
        {
            "artifact": "baseline_result_table",
            "required_fields": "endpoint, baseline, metric, pass/fail, confidence note, rejected-run count",
        },
        {
            "artifact": "reviewer_feedback_memo",
            "required_fields": "reviewer role, packet_sha256, accepted claims, rejected claims, missing evidence, permission state",
        },
        {
            "artifact": "redaction_decision_log",
            "required_fields": "source path policy, activation trace policy, quote permission, commercial document scope",
        },
        {
            "artifact": "claim_ledger_diff",
            "required_fields": "claim_id, previous evidence level, new evidence level, proof slot, downgrade reason if any",
        },
    ]


def _protocol_use(claim: str) -> str:
    text = claim.lower()
    if "simulation" in text:
        return "Defines transfer and reviewer-acceptance endpoints for replay evidence."
    if "randomization" in text or "robust" in text:
        return "Defines perturbation-boundary and control-effect baselines."
    if "internal" in text or "activations" in text:
        return "Defines activation-incrementality tests against output-only baselines."
    if "monitor" in text:
        return "Defines control-on/off and operational-feasibility endpoints."
    return "Supports prospective methodology validation design."


def _real_activation_sources() -> set[str]:
    return {"recorded_activation_forward_hooks", "activation_recorder_npz"}
