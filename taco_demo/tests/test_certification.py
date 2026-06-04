"""Tests for pre-deployment certification tiers."""

from __future__ import annotations

from taco_demo.certification import certificate_record, certify


def test_verified_patch_is_tier1():
    t = certify(monitorable=True, verified_patch=True, severity="high", neighborhood_rate=0.5)
    assert t["tier"] == 1


def test_monitorable_unverified_is_tier2():
    t = certify(monitorable=True, verified_patch=False, severity="high", neighborhood_rate=0.6)
    assert t["tier"] == 2


def test_not_monitorable_is_tier3_or_4():
    t = certify(monitorable=False, verified_patch=False, severity="high", neighborhood_rate=0.9)
    assert t["tier"] == 3
    crit = certify(monitorable=False, verified_patch=False, severity="critical", neighborhood_rate=0.9)
    assert crit["tier"] == 4


def test_disabling_control_blocks_conditional_cert():
    t = certify(monitorable=True, verified_patch=True, severity="high", neighborhood_rate=0.5,
                control_enabled=False)
    assert t["tier"] == 3


def test_certificate_record_has_no_pricing():
    tier = certify(monitorable=True, verified_patch=True, severity="high", neighborhood_rate=0.5)
    rec = certificate_record(policy_id="p", task="t", failure_type="f", tier=tier,
                             recommended_patch="ctrl", internal_finding="x", early_warning="y")
    assert rec["certification_tier"] == 1
    assert not any("premium" in k or "price" in k for k in rec)
    assert rec["status"] == "conditionally_certified"
