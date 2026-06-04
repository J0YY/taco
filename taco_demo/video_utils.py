"""Deterministic fallback replay videos for the offline TACO demo."""

from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont


def _font(size: int = 22):
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_frame(certificate_id: str, mode: str, failure_type: str, t: float, duration_s: float) -> Image.Image:
    img = Image.new("RGB", (720, 420), "#f7f6f1")
    draw = ImageDraw.Draw(img)
    title = {"success": "Nominal success", "failure": "Counterfactual failure", "mitigated": "Mitigated replay"}[mode]
    draw.text((24, 18), f"{certificate_id} - {title}", fill="#1f2933", font=_font(24))
    draw.rectangle((34, 310, 680, 338), fill="#d1d5db")
    progress = t / max(duration_s, 1e-6)
    target = (520, 250)
    distractor = (430, 250)
    wrong = distractor if mode == "failure" else target
    arm_x = int(130 + progress * ((wrong[0] if mode != "mitigated" or progress > 0.45 else 330) - 130))
    arm_y = int(120 + progress * (wrong[1] - 120))
    draw.line((90, 120, arm_x, arm_y), fill="#374151", width=8)
    draw.ellipse((arm_x - 14, arm_y - 14, arm_x + 14, arm_y + 14), fill="#111827")
    draw.ellipse((target[0] - 26, target[1] - 26, target[0] + 26, target[1] + 26), fill="#2563eb")
    draw.text((target[0] - 30, target[1] + 34), "target", fill="#1f2933", font=_font(16))
    draw.rectangle((distractor[0] - 24, distractor[1] - 24, distractor[0] + 24, distractor[1] + 24), fill="#f59e0b")
    draw.text((distractor[0] - 36, distractor[1] + 34), "distractor", fill="#1f2933", font=_font(16))

    if "occlusion" in failure_type and mode in {"failure", "mitigated"} and progress > 0.25:
        draw.rectangle((475, 205, 565, 290), fill="#111827")
        draw.text((462, 174), "Target feature collapse", fill="#991b1b", font=_font(18))
    if "language" in failure_type and mode == "failure" and progress > 0.2:
        draw.rectangle((285, 82, 666, 128), outline="#991b1b", width=3)
        draw.text((300, 94), "...instead put it on the table", fill="#991b1b", font=_font(18))
    if mode == "mitigated" and progress > 0.38:
        messages = {
            "occlusion_induced_wrong_grasp": "Monitor: request second view",
            "language_override_instruction_conflict": "Language override blocked",
            "distractor_object_confusion": "Target identity confirmation",
        }
        draw.rectangle((65, 360, 675, 404), fill="#dcfce7", outline="#166534", width=2)
        draw.text((82, 371), messages.get(failure_type, "Internal risk signature detected"), fill="#166534", font=_font(20))
    if mode == "failure" and progress > 0.55:
        draw.text((60, 360), "Internal risk signature detected", fill="#991b1b", font=_font(20))
    return img


def write_frames(frames: list[Image.Image], output_path: Path, fps: int) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        imageio.mimsave(output_path, [frame for frame in frames], fps=fps)
        return output_path
    except Exception:
        gif_path = output_path.with_suffix(".gif")
        imageio.mimsave(gif_path, frames, duration=1 / fps)
        return gif_path


def create_demo_video(output_path: Path, certificate_id: str, mode: str, failure_type: str, fps: int = 12, duration_s: int = 5) -> Path:
    frames = [draw_frame(certificate_id, mode, failure_type, i / fps, duration_s) for i in range(fps * duration_s)]
    return write_frames(frames, output_path, fps)


def create_all_demo_videos(data_root: Path) -> list[Path]:
    certs = {
        "FR-001": "occlusion_induced_wrong_grasp",
        "FR-002": "language_override_instruction_conflict",
        "FR-003": "distractor_object_confusion",
    }
    paths = []
    for cert_id, failure_type in certs.items():
        for mode in ("success", "failure", "mitigated"):
            paths.append(create_demo_video(data_root / "videos" / f"{cert_id}_{mode}.mp4", cert_id, mode, failure_type))
    return paths


def draw_maniskill_frame(example: dict, t: float, duration_s: float) -> Image.Image:
    img = Image.new("RGB", (720, 420), "#f4f6f8")
    draw = ImageDraw.Draw(img)
    progress = t / max(duration_s, 1e-6)
    env_id = example.get("env_id", "ManiSkill/RMA")
    family = example.get("failure_family", "failure_family")
    draw.text((24, 18), f"{example.get('example_id')} - {env_id}", fill="#111827", font=_font(23))
    draw.text((24, 48), family.replace("_", " "), fill="#374151", font=_font(18))
    draw.rectangle((30, 318, 690, 342), fill="#cbd5e1")
    draw.rectangle((540, 235, 620, 315), outline="#2563eb", width=3)
    draw.text((546, 214), "goal", fill="#2563eb", font=_font(16))
    if "Rope" in env_id:
        center_x = int(260 + 260 * progress)
        center_y = int(235 + 18 * progress)
        radius = int(42 + 8 * progress)
        closure_gap = int(44 * (1 - progress * 0.55))
        draw.arc((center_x - radius, center_y - radius, center_x + radius, center_y + radius), 20 + closure_gap, 350, fill="#7c3aed", width=8)
        draw.line((120, 130, center_x - radius, center_y), fill="#475569", width=7)
        draw.ellipse((112, 122, 136, 146), fill="#111827")
        draw.text((58, 365), "ManiSkill/RMA replay: loop geometry metrics feed Known Failure Family evidence", fill="#334155", font=_font(17))
        if progress > 0.55:
            draw.rectangle((384, 82, 680, 126), fill="#fee2e2", outline="#991b1b", width=2)
            draw.text((398, 94), "Failure: loop does not enclose target", fill="#991b1b", font=_font(17))
    else:
        obj_x = int(180 + 335 * progress)
        obj_y = int(255 - 20 * progress)
        gripper_x = int(105 + 360 * progress)
        gripper_y = int(120 + 120 * progress)
        draw.line((86, 120, gripper_x, gripper_y), fill="#475569", width=8)
        draw.rectangle((gripper_x - 18, gripper_y - 8, gripper_x + 18, gripper_y + 8), fill="#111827")
        draw.ellipse((obj_x - 24, obj_y - 24, obj_x + 24, obj_y + 24), fill="#f97316")
        draw.text((58, 365), "ManiSkill/RMA replay: contact, grasp, goal-distance, and static predicates feed TACO", fill="#334155", font=_font(17))
        if progress > 0.58:
            draw.rectangle((386, 82, 680, 126), fill="#fee2e2", outline="#991b1b", width=2)
            draw.text((400, 94), "Failure boundary: placement not certified", fill="#991b1b", font=_font(17))
    draw.rectangle((24, 384, int(24 + 650 * progress), 398), fill="#0f766e")
    return img


def create_maniskill_demo_video(output_path: Path, example: dict, fps: int = 10, duration_s: int = 4) -> Path:
    frames = [draw_maniskill_frame(example, i / fps, duration_s) for i in range(fps * duration_s)]
    return write_frames(frames, output_path, fps)
