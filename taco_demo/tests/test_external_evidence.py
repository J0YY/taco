"""Tests for real cross-policy evidence imported from sibling robotics projects."""

from __future__ import annotations

from taco_demo import external_evidence as ee


def test_saescope_summary_real_numbers():
    summary = ee.saescope_summary()
    assert summary["available"] is True
    # 10 curated clips: 4 successes (incl. one false-handoff), 6 failures.
    assert summary["total_clips"] == 10
    assert summary["failure_count"] == 6
    assert summary["success_count"] == 4
    # Every failure was flagged by the internal monitor; recall is perfect.
    assert summary["failures_detected_by_monitor"] == 6
    assert summary["recall"] == 1.0
    # One success raised an alert -> precision below 1.
    assert summary["false_alert_count"] == 1
    assert 0.8 <= summary["precision"] < 1.0
    # The headline early-warning lead is real and positive.
    assert summary["mean_early_warning_lead_steps"] > 0
    assert summary["first_alert_step"] == 32


def test_fr004_certificate_uses_real_lead():
    cert = ee.fr004_certificate()
    assert cert["certificate_id"] == "FR-004"
    assert cert["real_internal_evidence"] is True
    assert cert["early_warning_lead_steps"] == ee.saescope_summary()["mean_early_warning_lead_steps"]
    assert "lead" in cert["provenance"].lower()


def test_saescope_catalog_pairs_success_and_failure():
    rows = ee.saescope_catalog_rows()
    outcomes = {r["outcome"] for r in rows}
    assert "success" in outcomes and "FAILURE" in outcomes
    failure = next(r for r in rows if r["outcome"] == "FAILURE")
    assert failure["internal_alert_step"] is not None
    assert failure["early_warning_lead_steps"] is not None


def test_nla4vla_catalog_has_breadth_and_outcomes():
    rows = ee.nla4vla_catalog()
    assert rows, "expected nla4vla breadth clips"
    policies = {str(r["policy"]).lower() for r in rows}
    # OpenVLA and SmolVLA both represented.
    assert any("openvla" in p for p in policies)
    assert any("smolvla" in p for p in policies)
    assert any(r["outcome"] == "FAILURE" for r in rows)
