"""Tests for the guided 4-stage certification flow."""

from __future__ import annotations

from pathlib import Path

from taco_demo import guided_flow as g


def test_policies_reference_known_exhibits():
    for policy in g.POLICIES:
        assert policy["certs"]
        for cid in policy["certs"]:
            assert cid in g.EXHIBITS


def test_exhibit_videos_exist():
    for cid, ex in g.EXHIBITS.items():
        assert Path(ex["success"]).exists(), f"{cid} success video missing"
        assert Path(ex["failure"]).exists(), f"{cid} failure video missing"


def test_exhibits_have_certification_fields():
    for cid, ex in g.EXHIBITS.items():
        for key in ("mech_method", "internal_finding", "recommended_patch",
                    "monitorable", "verified_patch", "severity", "neighborhood_rate"):
            assert key in ex, f"{cid} missing {key}"


def test_crossing_chart_finds_signature_before_failure():
    ex = g.EXHIBITS["FR-004"]
    trace = g._exhibit_trace(ex)
    fig, lead, unit = g._crossing_chart(trace, ex["failure_ts"])
    assert lead is not None and lead > 0


def test_real_trace_loads_for_npz_exhibit():
    ex = g.EXHIBITS["FR-002"]
    trace = g._exhibit_trace(ex)
    assert "internal_risk_score" in trace
