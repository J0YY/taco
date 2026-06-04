"""Tests for the guided 4-stage narrative flow."""

from __future__ import annotations

from pathlib import Path

from taco_demo import guided_flow as g


def test_policies_reference_known_exhibits():
    for policy in g.POLICIES:
        assert policy["certs"], "policy must list at least one failure family"
        for cert_id in policy["certs"]:
            assert cert_id in g.EXHIBITS


def test_exhibit_videos_exist():
    for cert_id, ex in g.EXHIBITS.items():
        assert Path(ex["success"]).exists(), f"{cert_id} success video missing"
        assert Path(ex["failure"]).exists(), f"{cert_id} failure video missing"


def test_real_trace_animation_and_crossing():
    trace = g._exhibit_trace("FR-002")
    fig = g._activation_animation(trace, "language_override_risk", 88)
    assert len(fig.frames) > 1
    _, lead, cross = g._crossing_chart(trace, 88)
    # The internal risk signature must cross before the physical failure.
    assert cross is not None
    assert lead > 0


def test_fr004_schematic_is_step_based_with_early_warning():
    trace = g._schematic_fr004_trace()
    assert g.EXHIBITS_is_steps(trace) is True
    _, lead, cross = g._crossing_chart(trace, 80)
    assert cross is not None
    assert lead > 0
