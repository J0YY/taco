"""Activation evidence contract for internals-based diligence."""

from __future__ import annotations

from typing import Any

from .activation_recorder import torch_available
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


REAL_ACTIVATION_SOURCES = {"recorded_activation_forward_hooks", "activation_recorder_npz"}


def build_activation_evidence_contract(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    methodology_validation_protocol: dict[str, Any],
    technical_runbook: dict[str, Any],
) -> dict[str, Any]:
    """Return a reviewer-verifiable contract for activation evidence capture."""

    primary_ids = {cert.certificate_id for cert in certificates}
    primary_metrics = [metric for metric in metrics if metric.certificate_id in primary_ids]
    real_activation_metric_ids = {
        metric.certificate_id
        for metric in primary_metrics
        if metric.metrics_source in REAL_ACTIVATION_SOURCES
    }
    real_activation_metric_count = len(real_activation_metric_ids)
    complete_primary_coverage = bool(primary_ids) and {metric.certificate_id for metric in primary_metrics} == primary_ids
    return {
        "contract_id": f"AEV-{application.application_id}",
        "status": _status(complete_primary_coverage, real_activation_metric_count, len(primary_ids)),
        "boundary": (
            "This contract defines how policy activations become scoreable underwriting traces; it is not proof that "
            "activations are causal explanations, that the layer map is externally validated, that a customer policy "
            "has been recorded, or that activation-derived pricing is actuarially credible."
        ),
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "robot_type": application.robot_type,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
        },
        "current_evidence": {
            "primary_certificate_count": len(certificates),
            "metric_count": len(metrics),
            "primary_metric_count": len(primary_metrics),
            "real_activation_metric_count": real_activation_metric_count,
            "complete_primary_metric_coverage": complete_primary_coverage,
            "metric_sources": sorted({metric.metrics_source for metric in metrics}) or ["none"],
            "torch_available_in_current_env": torch_available(),
            "recorder_module": "taco_demo/activation_recorder.py",
            "trace_scoring_module": "taco_demo/trace_scoring.py",
            "protocol_endpoint": "activation_incrementality_over_outputs",
            "technical_runbook_step": "activation_recorder_trace_export",
        },
        "required_trace_bundle": _required_trace_bundle(),
        "layer_signal_map": _layer_signal_map(),
        "calibration_gates": _calibration_gates(),
        "artifact_checks": _artifact_checks(methodology_validation_protocol, technical_runbook),
        "reviewer_workflow": _reviewer_workflow(),
        "failure_conditions": _failure_conditions(),
        "do_not_claim": [
            "Do not claim internals-based underwriting unless success, failure, and mitigated NPZ traces exist for the same certificate.",
            "Do not claim causal explanation unless the methodology protocol's activation incrementality endpoint passes.",
            "Do not claim a layer map is reusable across policies until rejected-layer logs and reviewer calibration notes exist.",
            "Do not claim premium discounts are validated by activation traces without control-effect replication and actuarial review.",
        ],
    }


def activation_layer_rows(contract: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for layer-to-signal mapping."""

    return [
        {
            "Layer Role": item["layer_role"],
            "Example Layer Pattern": item["example_layer_pattern"],
            "TACO Signal": item["taco_signal"],
            "Reviewer Question": item["reviewer_question"],
        }
        for item in contract["layer_signal_map"]
    ]


def activation_gate_rows(contract: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for activation calibration gates."""

    return [
        {
            "Gate": item["gate"],
            "Pass Condition": item["pass_condition"],
            "Failure Action": item["failure_action"],
        }
        for item in contract["calibration_gates"]
    ]


def activation_artifact_check_rows(contract: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for activation artifact checks."""

    return [
        {
            "Check": item["check"],
            "Evidence": item["evidence"],
            "Blocks": item["blocks"],
        }
        for item in contract["artifact_checks"]
    ]


def activation_workflow_rows(contract: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for reviewer workflow steps."""

    return [
        {
            "Step": item["step"],
            "Owner": item["owner"],
            "Input": item["input"],
            "Output": item["output"],
        }
        for item in contract["reviewer_workflow"]
    ]


def _status(complete_primary_coverage: bool, real_activation_metric_count: int, primary_certificate_count: int) -> str:
    if complete_primary_coverage and primary_certificate_count and real_activation_metric_count == primary_certificate_count:
        return "recorded_activation_contract_ready_needs_external_calibration"
    if complete_primary_coverage:
        return "trace_contract_ready_demo_metrics_need_recorded_activations"
    return "activation_contract_ready_needs_primary_trace_coverage"


def _required_trace_bundle() -> list[dict[str, str]]:
    return [
        {
            "mode": "success",
            "file_pattern": "{certificate_id}_success.npz",
            "required_use": "baseline behavior for concept coverage, feature stability, and output-only comparison",
        },
        {
            "mode": "failure",
            "file_pattern": "{certificate_id}_failure.npz",
            "required_use": "counterfactual failure behavior for unsafe dominance, early warning, and family separation",
        },
        {
            "mode": "mitigated",
            "file_pattern": "{certificate_id}_mitigated.npz",
            "required_use": "control-on behavior for causal mitigability and premium-control sensitivity",
        },
    ]


def _layer_signal_map() -> list[dict[str, str]]:
    return [
        _mapping("target_identity", "vision.*target* or policy.*target*", "target_feature", "Does the target signal degrade before the failure?"),
        _mapping("grasp_affordance", "policy.*grasp* or action_head.*grasp*", "general_grasp_feature", "Does grasp confidence hide or reveal the failure?"),
        _mapping("transport_plan", "policy.*transport* or planner.*path*", "transport_feature", "Does transport planning stay stable across success/failure/mitigation?"),
        _mapping("trajectory_memory", "policy.*memory* or latent.*trajectory*", "memorized_trajectory_feature", "Does memorized trajectory dominate the current scene?"),
        _mapping("unsafe_trajectory", "safety.*unsafe* or critic.*risk*", "unsafe_trajectory_dominance", "Does an unsafe latent feature spike before completion?"),
        _mapping("action_risk", "policy.*action* or action_head.*logits*", "action_risk", "Does action risk separate failure from success and mitigation?"),
    ]


def _mapping(layer_role: str, example_layer_pattern: str, taco_signal: str, reviewer_question: str) -> dict[str, str]:
    return {
        "layer_role": layer_role,
        "example_layer_pattern": example_layer_pattern,
        "taco_signal": taco_signal,
        "reviewer_question": reviewer_question,
    }


def _calibration_gates() -> list[dict[str, str]]:
    return [
        _gate(
            "explicit_layer_names",
            "Recorder configuration lists exact layer names or reviewer-approved patterns before capture.",
            "Downgrade internals claim to demo trace fixture until the map is frozen.",
        ),
        _gate(
            "shared_signal_calibration",
            "Success, failure, and mitigated modes use one shared calibration range per signal.",
            "Reject per-mode normalization because it can erase separation between failure and mitigation.",
        ),
        _gate(
            "required_signal_coverage",
            "All six TACO required signals are present or the missing-signal list is attached.",
            "Reduce concept coverage and block research_and_artifact_backed internals status.",
        ),
        _gate(
            "activation_incrementality",
            "Activation features beat output-only labels on at least one predeclared endpoint without degrading the others.",
            "Downgrade internals wording to future research infrastructure.",
        ),
        _gate(
            "control_on_off_alignment",
            "Mitigated traces correspond to the same certificate, task, and rollout family as the failure trace.",
            "Remove control-credit language for that certificate family.",
        ),
    ]


def _gate(gate: str, pass_condition: str, failure_action: str) -> dict[str, str]:
    return {"gate": gate, "pass_condition": pass_condition, "failure_action": failure_action}


def _artifact_checks(methodology_validation_protocol: dict[str, Any], technical_runbook: dict[str, Any]) -> list[dict[str, str]]:
    protocol_id = methodology_validation_protocol.get("protocol_id", "methodology_validation_protocol")
    runbook_id = technical_runbook.get("runbook_id", "technical_diligence_runbook")
    return [
        _check("npz_schema", "NPZ contains time_s, trace_source, recorded_required_signal_count, and mapped signal arrays.", "scoreable_internal_metrics"),
        _check("source_linkage", "Each metric certificate_id matches the certificate and trace file stem.", "primary_trace_coverage"),
        _check("recorder_hook_path", "Capture uses ActivationRecorder or record_taco_trace_bundle, not hand-authored metric JSON.", "internals_based_claim"),
        _check("protocol_linkage", f"{protocol_id} includes activation_incrementality_over_outputs endpoint.", "claim_upgrade"),
        _check("runbook_linkage", f"{runbook_id} includes activation_recorder_trace_export step.", "reviewer_reproduction"),
    ]


def _check(check: str, evidence: str, blocks: str) -> dict[str, str]:
    return {"check": check, "evidence": evidence, "blocks": blocks}


def _reviewer_workflow() -> list[dict[str, str]]:
    return [
        _workflow("freeze_layer_map", "technical owner", "policy architecture and candidate layer list", "layer-to-signal map with rejected layers"),
        _workflow("record_rollout_triplet", "technical owner", "success/failure/mitigated inputs for one certificate", "three NPZ traces plus raw activation NPZ if allowed"),
        _workflow("score_internal_metrics", "technical owner", "trace NPZ triplet", "InternalRiskMetrics with recorded_activation_forward_hooks source"),
        _workflow("run_output_only_baseline", "research reviewer", "pass/fail labels and replay metadata", "baseline comparison table"),
        _workflow("classify_claim", "founder/reviewer", "metrics, baseline result, and packet hash", "accepted, downgraded, or blocked internals claim"),
    ]


def _workflow(step: str, owner: str, input_artifact: str, output_artifact: str) -> dict[str, str]:
    return {"step": step, "owner": owner, "input": input_artifact, "output": output_artifact}


def _failure_conditions() -> list[dict[str, str]]:
    return [
        _failure("missing_mode", "Any of success, failure, or mitigated traces are missing for a certificate.", "Block internals-based claim for that certificate."),
        _failure("flat_or_nan_activations", "Mapped activations are flat, NaN-heavy, or outside calibration bounds.", "Reject the layer map and rerun capture."),
        _failure("per_mode_normalization", "Each mode is normalized independently.", "Reject the comparison because failure separation can be manufactured."),
        _failure("output_only_equivalent", "Output-only baseline performs as well as activation features.", "Downgrade internals to non-incremental research infrastructure."),
        _failure("unreviewed_customer_model", "Customer policy activations are captured without redaction and retention classification.", "Keep evidence private and block public data-room export."),
    ]


def _failure(condition: str, trigger: str, required_response: str) -> dict[str, str]:
    return {"condition": condition, "trigger": trigger, "required_response": required_response}
