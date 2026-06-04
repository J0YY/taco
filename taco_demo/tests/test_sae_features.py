"""Tests for the real SAE feature-analysis artifacts (sae-scope / Octo-Base)."""

from __future__ import annotations

from taco_demo import sae_features as sf


def test_artifacts_available():
    assert sf.available() is True


def test_overview_real_numbers():
    ov = sf.sae_overview()
    assert ov["d_sae"] == 4096
    assert ov["d_model"] == 256
    assert ov["expansion"] == 16
    assert 0 < ov["alive_features"] < ov["d_sae"]
    assert 0.9 < ov["explained_variance"] <= 1.0
    assert ov["l0"] > 0
    assert "Octo" in ov["vla_model"]
    assert len(ov["top_by_frequency"]) >= 1


def test_temporal_heatmap_topk_shape():
    mat, fids, bins = sf.temporal_heatmap_topk(25)
    assert mat.shape[0] == len(fids) == 25
    assert mat.shape[1] == len(bins)
    # activation rates are in [0, 1]
    assert float(mat.min()) >= 0.0 and float(mat.max()) <= 1.0001


def test_top_feature_rows_have_stats():
    rows = sf.top_feature_rows()
    assert rows
    r = rows[0]
    for key in ("feature", "activation_frequency", "mean_activation", "temporal_variance", "classification"):
        assert key in r
