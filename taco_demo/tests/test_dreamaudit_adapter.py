from __future__ import annotations

import json

from taco_demo.dreamaudit_adapter import adapt_dreamaudit_certificate, adapt_dreamaudit_certificates, summarize_adapted_certificates
from taco_demo.schemas import FailureCertificate


def test_adapts_compact_openvla_observation_certificate(tmp_path):
    payload = {
        "backend": "LIBERO",
        "certificate_id": "libero-openvla-observation-object-t00-e00-center_occ_35",
        "minimality": {"method": "not_run"},
        "native_validation": {"steps": 128, "success": True},
        "patch_recipe": {
            "edits_to_sample": ["center_occ_35"],
            "generator": "libero_observation_replay_v0",
            "num_scenes_recommended": 50,
        },
        "perturbation": {
            "type": "openvla_observation_occlusion",
            "perturbation_name": "center_occ_35",
            "mean_image_l1": 0.04415688833646607,
            "perturbation_params": {"fraction": 0.35},
        },
        "perturbed_validation": {"failure_mode": "observation_counterfactual_failure", "steps": 171, "success": False},
        "policy": {"adapter": "dreamaudit.openvla_observation_perturbations", "name": "OpenVLA"},
        "task": {
            "suite": "object",
            "task_idx": 0,
            "episode_idx": 0,
            "task_name": "pick_up_the_alphabet_soup_and_place_it_in_the_basket",
        },
        "world_model_discovery": {"predicted_failure": "observation_counterfactual_failure"},
    }
    path = tmp_path / "compact.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    cert = adapt_dreamaudit_certificate(path)

    assert isinstance(cert, FailureCertificate)
    assert cert.certificate_id == payload["certificate_id"]
    assert cert.policy_id == "OpenVLA"
    assert "object:task_0:episode_0" in cert.task_id
    assert cert.failure_type == "occlusion_induced_wrong_grasp"
    assert cert.severity == "high"
    assert cert.minimal_failure_cost > 0
    assert cert.failure_rate_neighborhood == 1.0
    assert cert.failure_timestep == 171
    assert cert.source.startswith("dreamaudit:")
    assert cert.replay_command == f"python -m json.tool {path}"
    assert "taco_required_control" in cert.patch_recipe


def test_adapts_rich_dreamaudit_certificate_and_directory(tmp_path):
    payload = {
        "certificate_id": "dreamaudit-synthetic-123-000001",
        "policy": {"name": "synthetic-policy-v1"},
        "task": {
            "benchmark": "SyntheticBench",
            "suite": "contact",
            "task_id": "push_can_001",
            "instruction_original": "push the can without colliding",
        },
        "perturbation": {
            "type": "scene_parameter",
            "perturbation_cost": 0.31,
            "semantic_rationale": "narrow contact margin",
        },
        "simulator_validation": {"simulator_success": False, "failure_mode": "contact_force_overshoot", "failure_frame": 94},
        "minimality": {"smallest_failing_cost_found": 0.22, "failure_rate_at_0_75_cost": 0.6},
        "patch_recipe": {"generator": "synthetic_patch_v0", "edits_to_sample": ["object_pose"], "num_scenes_recommended": 25},
        "world_model_discovery": {"predicted_failure": "contact_force_overshoot"},
    }
    path = tmp_path / "rich.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    (tmp_path / "not_a_cert.json").write_text("{}", encoding="utf-8")

    cert = adapt_dreamaudit_certificate(payload, source_path=path)
    certs = adapt_dreamaudit_certificates(tmp_path)
    summary = summarize_adapted_certificates(certs)

    assert cert.policy_id == "synthetic-policy-v1"
    assert cert.failure_type == "contact_force_overshoot"
    assert cert.minimal_failure_cost == 0.22
    assert cert.failure_rate_neighborhood == 0.6
    assert cert.failure_timestep == 94
    assert cert.metadata["dreamaudit_schema"] == "rich"
    assert cert.metadata["minimality"] == payload["minimality"]
    assert [item.certificate_id for item in certs] == ["dreamaudit-synthetic-123-000001"]
    assert summary["certificates"] == 1
    assert summary["failure_families"] == ["contact_force_overshoot"]


def test_rich_search_grammar_rationale_does_not_force_language_failure(tmp_path):
    payload = {
        "certificate_id": "dreamaudit-synthetic-123-000002",
        "policy": {"name": "synthetic-policy-v1"},
        "task": {
            "benchmark": "SyntheticBench",
            "suite": "pick",
            "task_id": "wrong_mug_001",
            "instruction_original": "pick the target mug",
        },
        "perturbation": {
            "type": "synthetic_multi_axis",
            "perturbation_cost": 0.41,
            "semantic_rationale": "CEM proposal over synthetic perturbation grammar",
        },
        "simulator_validation": {"simulator_success": False, "failure_mode": "wrong_object_grasp", "failure_frame": 77},
        "minimality": {"smallest_failing_cost_found": 0.33, "failure_rate_at_0_75_cost": 0.55},
        "patch_recipe": {"generator": "synthetic_patch_v0", "edits_to_sample": ["visual_similarity"], "num_scenes_recommended": 25},
        "world_model_discovery": {"predicted_failure": "wrong_object_grasp"},
    }

    cert = adapt_dreamaudit_certificate(payload)

    assert cert.failure_type == "distractor_object_confusion"
    assert cert.patch_recipe["taco_required_control"] == "target identity confirmation before irreversible grasp"


def test_adapt_dreamaudit_certificates_honors_zero_limit(tmp_path):
    payload = {
        "certificate_id": "dreamaudit-synthetic-123-000003",
        "policy": {"name": "synthetic-policy-v1"},
        "task": {"task_id": "one"},
        "perturbation": {"type": "scene", "perturbation_cost": 0.2},
        "simulator_validation": {"simulator_success": False, "failure_mode": "grasp_miss", "failure_frame": 12},
        "minimality": {"smallest_failing_cost_found": 0.2, "failure_rate_at_0_75_cost": 0.4},
    }
    (tmp_path / "cert.json").write_text(json.dumps(payload), encoding="utf-8")

    assert adapt_dreamaudit_certificates(tmp_path, limit=0) == []
