"""ManiSkill/RMA gallery wiring for TACO demo evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .schemas import read_json, write_json
from .video_utils import create_maniskill_demo_video


def load_dreamaudit_maniskill_results(dreamaudit_root: Path) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for path in sorted((dreamaudit_root / "artifacts").glob("maniskill*_*/result.json")) + sorted((dreamaudit_root / "artifacts").glob("maniskill*/result.json")):
        try:
            raw = read_json(path)
        except Exception:
            continue
        raw["source_path"] = str(path)
        results.append(raw)
    return results


def default_maniskill_examples() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    pick_failures = [
        ("MS-PICK-001", "PickSingleYCBRMA-v1", "random_policy", "object_pose_shift", "approaches object but misses goal placement"),
        ("MS-PICK-002", "PickSingleYCBRMA-v1", "random_policy", "grasp_contact_dropout", "gripper contact appears but stable grasp is not achieved"),
        ("MS-PICK-003", "PickSingleYCBRMA-v1", "random_policy", "goal_offset_boundary", "object remains outside goal tolerance"),
        ("MS-PICK-004", "PickSingleYCBRMA-v1", "random_policy", "robot_static_violation", "motion persists after attempted placement"),
        ("MS-PICK-005", "PickSingleYCBRMA-v1", "random_policy", "workspace_edge_case", "target lies near reachable workspace boundary"),
        ("MS-PICK-006", "PickSingleYCBRMA-v1", "random_policy", "occluded_ycb_object", "camera evidence is insufficient for robust target lock"),
        ("MS-PICK-007", "PickSingleYCBRMA-v1", "random_policy", "distractor_ycb_similarity", "semantic target representation competes with distractor"),
        ("MS-PICK-008", "PickSingleYCBRMA-v1", "random_policy", "late_action_instability", "action risk rises after near-correct approach"),
    ]
    rope_failures = [
        ("MS-ROPE-001", "RopeLoopPlacementRMA-v1", "rma_policy_eval", "loop_not_enclosing_target", "rope loop forms but does not enclose target"),
        ("MS-ROPE-002", "RopeLoopPlacementRMA-v1", "rma_policy_eval", "closure_distance_high", "loop closure distance remains above control threshold"),
        ("MS-ROPE-003", "RopeLoopPlacementRMA-v1", "rma_policy_eval", "center_offset_failure", "loop center remains offset from target"),
        ("MS-ROPE-004", "RopeLoopPlacementRMA-v1", "rma_policy_eval", "controlled_hold_missing", "policy never reaches controlled hold condition"),
    ]
    for idx, (example_id, env_id, mode, family, summary) in enumerate(pick_failures + rope_failures):
        examples.append(
            {
                "example_id": example_id,
                "env_id": env_id,
                "mode": mode,
                "failure_family": family,
                "summary": summary,
                "pipeline_stage": "DreamAudit -> ManiSkill/RMA simulator replay -> TACO internal underwriting evidence",
                "source": "demo_generated_placeholder_data",
                "seed": idx,
                "video_path": f"videos/maniskill_examples/{example_id}.gif",
            }
        )
    return examples


def build_maniskill_gallery(data_root: Path, dreamaudit_root: Path | None = None, force: bool = False) -> Path:
    manifest_path = data_root / "maniskill_gallery.json"
    if manifest_path.exists() and not force:
        return manifest_path
    examples = default_maniskill_examples()
    if dreamaudit_root:
        real_results = load_dreamaudit_maniskill_results(dreamaudit_root)
        for i, result in enumerate(real_results[: len(examples)]):
            examples[i]["dreamaudit_result"] = {
                "env_id": result.get("env_id"),
                "ok": result.get("ok"),
                "num_envs": result.get("num_envs"),
                "source_path": result.get("source_path"),
                "metrics": result.get("metrics", {}),
                "final_info": result.get("final_info", {}),
            }
            examples[i]["source"] = "dreamaudit_result_plus_demo_generated_video"
    for example in examples:
        video_path = data_root / example["video_path"]
        if force or not video_path.exists():
            create_maniskill_demo_video(video_path, example)
    write_json({"examples": examples}, manifest_path)
    return manifest_path

