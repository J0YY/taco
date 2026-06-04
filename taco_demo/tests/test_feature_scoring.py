import numpy as np

from taco_demo.feature_scoring import (
    compute_causal_mitigability,
    compute_early_warning_margin,
    compute_feature_stability,
    compute_internal_metrics,
)
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.scripts.bootstrap_demo_data import make_trace


def test_metrics_are_clamped_between_zero_and_one():
    cert = DEMO_CERTIFICATES[0]
    metrics = compute_internal_metrics(cert, make_trace("FR-001", "success"), make_trace("FR-001", "failure"), make_trace("FR-001", "mitigated"))
    for value in [
        metrics.concept_coverage_score,
        metrics.feature_stability_score,
        metrics.unsafe_dominance_score,
        metrics.causal_mitigability_score,
        metrics.internal_risk_score,
    ]:
        assert 0 <= value <= 1


def test_early_warning_margin_positive_when_risk_crosses_before_failure():
    trace = {"time_s": np.arange(10, dtype=float), "internal_risk_score": np.array([0, 0, 0.7, 0.8, 0.9, 0.9, 0.9, 0, 0, 0])}
    assert compute_early_warning_margin(trace, 6) == 4.0


def test_mitigability_higher_when_mitigated_action_risk_lower():
    cert = DEMO_CERTIFICATES[0]
    failure = {"action_risk": np.ones(40) * 0.8}
    mitigated = {"action_risk": np.ones(40) * 0.2}
    assert compute_causal_mitigability(cert, failure, mitigated) > 0.5


def test_feature_stability_drops_when_target_feature_collapses():
    success = {"target_feature": np.ones(50) * 0.9}
    failure = {"target_feature": np.ones(50) * 0.2}
    assert compute_feature_stability(success, failure, 40) < 0.5

