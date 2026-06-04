from __future__ import annotations

import json

from taco_demo.dreamaudit_intake import build_dreamaudit_intake_summary, certificate_rows
from taco_demo.dreamaudit_adapter import adapt_dreamaudit_certificate


def test_build_dreamaudit_intake_summary_handles_missing_root(tmp_path):
    summary = build_dreamaudit_intake_summary(tmp_path / "missing")

    assert summary["root_exists"] is False
    assert summary["summary"]["certificates"] == 0
    assert summary["rows"] == []


def test_build_dreamaudit_intake_summary_counts_adapted_certificates(tmp_path):
    payload = {
        "backend": "LIBERO",
        "certificate_id": "libero-openvla-observation-object-t00-e00-center_occ_35",
        "minimality": {"method": "not_run"},
        "native_validation": {"steps": 128, "success": True},
        "patch_recipe": {"edits_to_sample": ["center_occ_35"], "generator": "libero_observation_replay_v0"},
        "perturbation": {
            "type": "openvla_observation_occlusion",
            "perturbation_name": "center_occ_35",
            "mean_image_l1": 0.044,
        },
        "perturbed_validation": {"failure_mode": "observation_counterfactual_failure", "steps": 171, "success": False},
        "policy": {"name": "OpenVLA"},
        "task": {"suite": "object", "task_idx": 0, "episode_idx": 0, "task_name": "pick_up_soup"},
    }
    (tmp_path / "cert.json").write_text(json.dumps(payload), encoding="utf-8")

    summary = build_dreamaudit_intake_summary(tmp_path, limit=10)

    assert summary["root_exists"] is True
    assert summary["summary"]["certificates"] == 1
    assert summary["failure_counts"] == {"occlusion_induced_wrong_grasp": 1}
    assert summary["schema_counts"] == {"compact": 1}
    assert summary["backend_counts"] == {"LIBERO": 1}
    assert summary["rows"][0]["Policy"] == "OpenVLA"


def test_certificate_rows_limits_output():
    cert = adapt_dreamaudit_certificate(
        {
            "certificate_id": "cert-1",
            "policy": {"name": "policy"},
            "task": {"task_id": "task"},
            "perturbation": {"type": "scene", "perturbation_cost": 0.2},
            "simulator_validation": {"simulator_success": False, "failure_mode": "grasp_miss", "failure_frame": 12},
        }
    )

    assert len(certificate_rows([cert, cert], max_rows=1)) == 1
