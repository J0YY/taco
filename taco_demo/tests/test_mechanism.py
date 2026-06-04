"""Tests for the mechanistic-interpretation flow chart and sources."""

from __future__ import annotations

from taco_demo import mechanism as m


def test_flowchart_is_graphviz_dot():
    dot = m.mechanism_flowchart_dot()
    assert dot.startswith("digraph")
    # Names the four pipeline stages.
    for token in ["Robot policy", "Sparse Autoencoder", "DreamAudit", "Insurance"]:
        assert token in dot


def test_sources_are_cited():
    assert m.MECH_SOURCES
    for src in m.MECH_SOURCES:
        assert src["source"] and src["url"].startswith("http")
    # The load-bearing SAE paper is present.
    assert any("Steerable Features" in s["source"] for s in m.MECH_SOURCES)


def test_steps_cover_record_to_steer():
    steps = [s["step"] for s in m.MECH_STEPS]
    assert steps[0] == "Record"
    assert any("Steer" in s for s in steps)
