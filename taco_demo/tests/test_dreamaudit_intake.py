from __future__ import annotations

import json
from pathlib import Path

from taco_demo.dreamaudit_intake import build_dreamaudit_intake_summary, certificate_rows, underwriting_readiness
from taco_demo.dreamaudit_adapter import adapt_dreamaudit_certificate


def test_build_dreamaudit_intake_summary_handles_missing_root(tmp_path):
    summary = build_dreamaudit_intake_summary(tmp_path / "missing")

    assert summary["root_exists"] is False
    assert summary["summary"]["certificates"] == 0
    assert summary["rows"] == []
    assert summary["readiness"]["status"] == "no_evidence"


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
    assert summary["readiness"]["readiness_score"] < 80
    assert "occlusion_risk_monitor_enabled" in summary["readiness"]["required_controls"]
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


def test_underwriting_readiness_scores_broad_mapped_evidence():
    certs = [
        adapt_dreamaudit_certificate(
            {
                "certificate_id": f"occ-{idx}",
                "policy": {"name": "OpenVLA"},
                "task": {"task_id": f"task-{idx}"},
                "perturbation": {"type": "openvla_observation_occlusion", "mean_image_l1": 0.08},
                "perturbed_validation": {"failure_mode": "observation_counterfactual_failure", "steps": 100, "success": False},
                "native_validation": {"success": True},
                "minimality": {"method": "sweep", "failure_rate_at_0_75_cost": 0.7},
            },
            source_path=Path(f"/tmp/taco/source-a/occ-{idx}.json"),
        )
        for idx in range(10)
    ]
    certs.extend(
        adapt_dreamaudit_certificate(
            {
                "certificate_id": f"lang-{idx}",
                "policy": {"name": "OpenVLA"},
                "task": {"task_id": f"task-lang-{idx}"},
                "perturbation": {"type": "openvla_language_language_append", "instruction_changed": True},
                "perturbed_validation": {"failure_mode": "language_counterfactual_failure", "steps": 100, "success": False},
                "native_validation": {"success": True},
                "minimality": {"method": "sweep", "failure_rate_at_0_75_cost": 0.7},
            },
            source_path=Path(f"/tmp/taco/source-b/lang-{idx}.json"),
        )
        for idx in range(10)
    )
    certs.extend(
        adapt_dreamaudit_certificate(
            {
                "certificate_id": f"dist-{idx}",
                "policy": {"name": "OpenVLA"},
                "task": {"task_id": f"task-dist-{idx}"},
                "perturbation": {"type": "semantic_distractor", "perturbation_cost": 0.2},
                "perturbed_validation": {"failure_mode": "wrong_object_grasp", "steps": 100, "success": False},
                "native_validation": {"success": True},
                "minimality": {"method": "sweep", "failure_rate_at_0_75_cost": 0.7},
            },
            source_path=Path(f"/tmp/taco/source-c/dist-{idx}.json"),
        )
        for idx in range(10)
    )

    readiness = underwriting_readiness(certs)

    assert readiness["readiness_score"] >= 80
    assert readiness["status"] == "carrier_review_ready"
    assert readiness["unmapped_failure_families"] == []
    assert readiness["minimality_reports"] == 30
    assert readiness["replay_commands"] == 30
