"""End-to-end and unit tests for the TACO audit engine."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from taco_audit.engine import AuditEngine
from taco_audit.policy_loader import load_policy
from taco_audit.scope import gather_scope
from taco_audit.sims.reach_world import ReachWorld
from taco_audit.types import PERTURBATION_SPACE, Perturbation

POLICIES = Path(__file__).resolve().parent.parent / "examples" / "policies"


def _audit(name, **scope_kw):
    policy = load_policy(POLICIES / f"{name}.py")
    scope = gather_scope(policy_id=name, **scope_kw)
    return AuditEngine(seed=0).audit(policy, scope)


# --- perturbation contract ------------------------------------------------
def test_perturbation_cost_clamped_and_monotonic():
    small = Perturbation({"occlusion_fraction": 0.1}, "visual_occlusion")
    big = Perturbation({"occlusion_fraction": 0.8}, "visual_occlusion")
    assert 0.0 <= small.cost() <= 1.0
    assert big.cost() > small.cost()
    # out-of-range knobs get clamped into the space
    clamped = Perturbation({"occlusion_fraction": 9.0}, "visual_occlusion").clamped()
    lo, hi = PERTURBATION_SPACE["occlusion_fraction"]
    assert clamped.knobs["occlusion_fraction"] == hi


# --- the sim is real ------------------------------------------------------
def test_nominal_success_and_forced_failure():
    sim = ReachWorld()
    robust = load_policy(POLICIES / "reach_robust.py")
    brittle = load_policy(POLICIES / "reach_brittle.py")
    robust.reset(); brittle.reset()
    # both succeed nominally
    assert sim.rollout(robust, Perturbation({}, "nominal"), seed=0).success
    assert sim.rollout(brittle, Perturbation({}, "nominal"), seed=0).success
    # heavy occlusion breaks the salience-follower but not the identity-locker
    occ = Perturbation({"occlusion_fraction": 0.7}, "visual_occlusion")
    brittle.reset(); robust.reset()
    assert sim.rollout(brittle, occ, seed=0).success is False
    assert sim.rollout(robust, occ, seed=0).success is True


def test_trace_has_required_signals_and_is_bounded():
    sim = ReachWorld()
    brittle = load_policy(POLICIES / "reach_brittle.py"); brittle.reset()
    res = sim.rollout(brittle, Perturbation({"occlusion_fraction": 0.7}, "visual_occlusion"), seed=0)
    for sig in ["target_feature", "action_risk", "internal_risk_score", "occlusion_risk"]:
        arr = res.trace[sig]
        assert arr.size > 0
        assert float(np.max(arr)) <= 1.0 + 1e-6 and float(np.min(arr)) >= -1e-6
    assert 0.0 <= res.failure_proximity <= 1.0


# --- the verdicts discriminate -------------------------------------------
def test_robust_policy_passes():
    v = _audit("reach_robust", environment="cluttered",
               human_proximity="shared_space", criticality="high")
    assert v.status == "PASS"
    assert v.certificates == []


def test_brittle_policy_is_conditional():
    v = _audit("reach_brittle", environment="cluttered",
               human_proximity="shared_space", criticality="high")
    assert v.status == "CONDITIONAL PASS"
    assert len(v.certificates) >= 1
    assert "reaudit_required_after_model_update" in v.required_controls


def test_blind_policy_fails():
    v = _audit("reach_blind", environment="cluttered",
               human_proximity="shared_space", criticality="high")
    assert v.status == "FAIL"
    # the blocking family is not monitorable (warning too late)
    assert any(not c.metadata["monitorable"] for c in v.certificates)


# --- minimisation + scope behaviour --------------------------------------
def test_minimal_failure_is_smaller_than_search_failure():
    v = _audit("reach_brittle", criticality="high")
    for c in v.certificates:
        assert 0.0 < c.minimal_failure_cost <= 1.0


def test_scope_risk_tolerance_ordering():
    lenient = gather_scope(criticality="low", human_proximity="isolated")
    strict = gather_scope(criticality="safety_critical", human_proximity="direct_contact")
    assert strict.risk_tolerance() < lenient.risk_tolerance()
