"""Deterministic ManiSkill-style evidence suite for TACO."""

from __future__ import annotations

import json
from pathlib import Path

import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont


SUITE_SIZE = 40

FAILURE_FAMILIES = [
    {
        "family": "occlusion_induced_wrong_grasp",
        "identified_signal": "target feature collapse while gripper confidence remains high",
        "underwriting_readout": "Require second-view monitor before pick coverage attaches.",
        "control": "slow_down_and_request_second_view",
        "color": "#2563eb",
    },
    {
        "family": "semantic_distractor_confusion",
        "identified_signal": "target identity margin collapses near a similar distractor",
        "underwriting_readout": "Require target identity confirmation in cluttered bins.",
        "control": "target_identity_confirmation",
        "color": "#f59e0b",
    },
    {
        "family": "contact_force_overshoot",
        "identified_signal": "force-risk feature spikes before contact completion",
        "underwriting_readout": "Exclude high-force insertion unless force governor is enabled.",
        "control": "force_governor",
        "color": "#dc2626",
    },
    {
        "family": "rope_entanglement_memory_bias",
        "identified_signal": "memorized trajectory dominates deformable-object state",
        "underwriting_readout": "Require deformable-object recovery monitor for rope tasks.",
        "control": "deformable_recovery_monitor",
        "color": "#7c3aed",
    },
    {
        "family": "camera_glare_pose_drift",
        "identified_signal": "pose estimate drifts while task-completion confidence stays high",
        "underwriting_readout": "Require lighting/glare validation and pose uncertainty gating.",
        "control": "pose_uncertainty_gate",
        "color": "#0891b2",
    },
    {
        "family": "drawer_collision_edge_case",
        "identified_signal": "transport feature rises but cabinet-edge clearance drops",
        "underwriting_readout": "Require swept-volume clearance monitor for articulated objects.",
        "control": "swept_volume_clearance_monitor",
        "color": "#16a34a",
    },
    {
        "family": "workspace_boundary_overreach",
        "identified_signal": "action-risk feature rises near joint-limit boundary",
        "underwriting_readout": "Require workspace geofence and re-audit after layout changes.",
        "control": "workspace_geofence",
        "color": "#9333ea",
    },
    {
        "family": "transparent_object_depth_error",
        "identified_signal": "depth uncertainty exceeds grasp-stability margin",
        "underwriting_readout": "Require transparent-object handling exclusion or sensor fusion.",
        "control": "depth_uncertainty_sensor_fusion",
        "color": "#0f766e",
    },
]

MANISKILL_ENVS = [
    "PickSingleYCBRMA-v1",
    "StackCubeRMA-v1",
    "PegInsertionSideRMA-v1",
    "RopeLoopPlacementRMA-v1",
    "OpenCabinetDrawerRMA-v1",
]

TASKS = [
    "pick mug from cluttered bin",
    "stack cube under partial occlusion",
    "insert peg with force-sensitive contact",
    "place rope loop around post",
    "open drawer near cabinet edge",
    "pick transparent bottle",
    "move can across workspace boundary",
    "sort similar YCB objects",
]


def build_maniskill_suite_cases(count: int = SUITE_SIZE) -> list[dict[str, object]]:
    cases = []
    for index in range(count):
        family = FAILURE_FAMILIES[index % len(FAILURE_FAMILIES)]
        env_id = MANISKILL_ENVS[index % len(MANISKILL_ENVS)]
        task = TASKS[(index * 3) % len(TASKS)]
        severity = ["medium", "high", "medium", "critical"][index % 4]
        perturbation_cost = round(0.16 + ((index * 7) % 31) / 100, 2)
        failure_rate = round(0.35 + ((index * 11) % 45) / 100, 2)
        cases.append(
            {
                "video_id": f"MS-{index + 1:03d}",
                "suite": "maniskill_rma_failure_gallery",
                "env_id": env_id,
                "task": task,
                "failure_family": family["family"],
                "severity": severity,
                "minimal_failure_cost": perturbation_cost,
                "failure_rate_neighborhood": failure_rate,
                "identified_signal": family["identified_signal"],
                "underwriting_readout": family["underwriting_readout"],
                "required_control": family["control"],
                "video_path": f"{index + 1:02d}_{family['family']}.gif",
                "cluster_status": "generated_locally_and_cluster_reproducible",
                "source": "taco_deterministic_maniskill_style_suite",
                "metadata": {
                    "dreamaudit_reference": "ManiSkill/RMA harness in /Users/joyyang/Projects/dreamaudit",
                    "cluster_command": "python -m taco_demo.scripts.generate_maniskill_video_suite --force",
                    "color": family["color"],
                },
            }
        )
    return cases


def write_maniskill_suite(root: Path, force: bool = False, count: int = SUITE_SIZE) -> Path:
    suite_root = root / "maniskill_suite"
    videos_root = suite_root / "videos"
    suite_root.mkdir(parents=True, exist_ok=True)
    videos_root.mkdir(parents=True, exist_ok=True)

    cases = build_maniskill_suite_cases(count)
    for case in cases:
        output = videos_root / str(case["video_path"])
        if force or not output.exists():
            _write_case_gif(case, output)
    manifest = {
        "suite_name": "TACO ManiSkill/RMA Failure Evidence Suite",
        "suite_size": len(cases),
        "purpose": "Show breadth of replayable robot failure evidence and the underwriting signal identified from each replay.",
        "source": "Deterministic TACO renderings based on DreamAudit ManiSkill/RMA harness patterns.",
        "cluster_reproduction": {
            "remote_project": "/work/joy/taco",
            "command": "python -m taco_demo.scripts.generate_maniskill_video_suite --force",
            "notes": "Run through ~/remote_srun.sh after pulling github.com/J0YY/taco.git on the cluster.",
        },
        "cases": cases,
    }
    (suite_root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return suite_root / "manifest.json"


def load_maniskill_suite(root: Path) -> dict[str, object]:
    manifest = root / "maniskill_suite" / "manifest.json"
    if not manifest.exists():
        write_maniskill_suite(root, force=False)
    return json.loads(manifest.read_text(encoding="utf-8"))


def _font(size: int):
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def _write_case_gif(case: dict[str, object], output: Path, fps: int = 8, frames: int = 28) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    images = [_draw_suite_frame(case, frame / max(frames - 1, 1)) for frame in range(frames)]
    imageio.mimsave(output, images, duration=1000 / fps)
    return output


def _draw_suite_frame(case: dict[str, object], progress: float) -> Image.Image:
    width, height = 480, 270
    img = Image.new("RGB", (width, height), "#f7f7f2")
    draw = ImageDraw.Draw(img)
    color = str(case["metadata"]["color"])
    failure_family = str(case["failure_family"])

    draw.rectangle((0, 0, width, 44), fill="#111827")
    draw.text((14, 11), f"{case['video_id']}  {case['env_id']}", fill="#f9fafb", font=_font(16))
    draw.rectangle((24, 210, width - 24, 224), fill="#cbd5e1")

    target_x = 360
    distractor_x = 282
    arm_x = int(64 + progress * (target_x - 64))
    arm_y = int(74 + progress * 122)
    if failure_family in {"semantic_distractor_confusion", "occlusion_induced_wrong_grasp"} and progress > 0.45:
        arm_x = int(64 + progress * (distractor_x - 64))
    if failure_family == "workspace_boundary_overreach" and progress > 0.58:
        arm_x += 54
    if failure_family == "rope_entanglement_memory_bias" and progress > 0.55:
        arm_y += int(18 * progress)

    draw.line((54, 76, arm_x, arm_y), fill="#475569", width=7)
    draw.rectangle((arm_x - 14, arm_y - 7, arm_x + 14, arm_y + 7), fill="#0f172a")
    draw.ellipse((target_x - 20, 178, target_x + 20, 218), fill=color)
    draw.rectangle((distractor_x - 18, 180, distractor_x + 18, 216), fill="#fbbf24")

    if failure_family == "occlusion_induced_wrong_grasp" and progress > 0.32:
        draw.rectangle((330, 154, 386, 224), fill="#1f2937")
    elif failure_family == "camera_glare_pose_drift" and progress > 0.30:
        draw.polygon([(318, 78), (420, 78), (380, 190), (286, 190)], fill="#fef3c7")
    elif failure_family == "rope_entanglement_memory_bias":
        draw.arc((250, 140, 414, 246), 180, 360, fill="#7c3aed", width=5)
        if progress > 0.56:
            draw.line((300, 194, arm_x, arm_y), fill="#7c3aed", width=4)
    elif failure_family == "drawer_collision_edge_case":
        draw.rectangle((314, 142, 438, 218), outline="#334155", width=4)
        draw.line((314, 142, 314, 218), fill="#dc2626", width=6)
    elif failure_family == "workspace_boundary_overreach":
        draw.line((408, 60, 408, 224), fill="#dc2626", width=4)
    elif failure_family == "transparent_object_depth_error":
        draw.ellipse((342, 174, 386, 220), outline="#0891b2", width=4)
    elif failure_family == "contact_force_overshoot" and progress > 0.60:
        draw.ellipse((arm_x - 26, arm_y - 26, arm_x + 26, arm_y + 26), outline="#dc2626", width=5)

    risk_width = int(170 * min(1.0, progress * 1.25))
    draw.rectangle((24, 236, 194, 250), outline="#64748b")
    draw.rectangle((24, 236, 24 + risk_width, 250), fill=color)
    draw.text((208, 230), "identified risk signal", fill="#334155", font=_font(13))
    if progress > 0.68:
        draw.rectangle((18, 52, width - 18, 102), fill="#fee2e2", outline="#991b1b", width=2)
        draw.text((30, 62), str(case["identified_signal"])[:58], fill="#991b1b", font=_font(14))
        draw.text((30, 80), f"control: {case['required_control']}"[:58], fill="#166534", font=_font(14))
    else:
        draw.text((24, 52), str(case["task"])[:54], fill="#172033", font=_font(15))
        draw.text((24, 74), failure_family[:54], fill="#475569", font=_font(13))
    return img
