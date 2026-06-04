"""Generated GIF replay evidence for the offline TACO MVP."""

from __future__ import annotations

from pathlib import Path

import imageio.v2 as imageio
from PIL import Image, ImageDraw, ImageFont


def _font(size: int = 20):
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def draw_frame(certificate_id: str, mode: str, failure_type: str, t: float, duration_s: float) -> Image.Image:
    img = Image.new("RGB", (720, 420), "#f6f5ef")
    draw = ImageDraw.Draw(img)
    label = {"success": "Nominal Success", "failure": "Counterfactual Failure", "mitigated": "Mitigated Replay"}[mode]
    progress = min(1.0, t / max(duration_s, 1e-6))

    draw.text((24, 18), f"{certificate_id} - {label}", fill="#172033", font=_font(25))
    draw.rectangle((30, 315, 690, 340), fill="#c8ccd3")

    target = (535, 252)
    distractor = (415, 252)
    wrong_target = distractor if mode == "failure" else target
    if mode == "mitigated" and progress < 0.58:
        wrong_target = (340, 235)

    arm_x = int(110 + progress * (wrong_target[0] - 110))
    arm_y = int(120 + progress * (wrong_target[1] - 120))
    draw.line((88, 120, arm_x, arm_y), fill="#4b5563", width=8)
    draw.rectangle((arm_x - 20, arm_y - 8, arm_x + 20, arm_y + 8), fill="#111827")

    draw.ellipse((target[0] - 27, target[1] - 27, target[0] + 27, target[1] + 27), fill="#2563eb")
    draw.text((target[0] - 26, target[1] + 36), "target", fill="#172033", font=_font(16))
    draw.rectangle((distractor[0] - 24, distractor[1] - 24, distractor[0] + 24, distractor[1] + 24), fill="#f59e0b")
    draw.text((distractor[0] - 38, distractor[1] + 36), "distractor", fill="#172033", font=_font(16))

    if failure_type == "occlusion_induced_wrong_grasp" and mode in {"failure", "mitigated"} and progress > 0.25:
        draw.rectangle((485, 204, 570, 292), fill="#111827")
        draw.text((455, 172), "Target feature collapse", fill="#991b1b", font=_font(18))
    if failure_type == "language_override_instruction_conflict" and mode == "failure" and progress > 0.22:
        draw.rectangle((268, 82, 678, 130), outline="#991b1b", width=3)
        draw.text((286, 96), "instead put it on the table", fill="#991b1b", font=_font(18))
    if failure_type == "distractor_object_confusion" and mode == "failure" and progress > 0.38:
        draw.rectangle((375, 205, 470, 292), outline="#991b1b", width=3)

    if mode == "failure" and progress > 0.55:
        draw.text((58, 365), "Internal risk signature detected", fill="#991b1b", font=_font(21))
    if mode == "mitigated" and progress > 0.42:
        messages = {
            "occlusion_induced_wrong_grasp": "Monitor: request second view",
            "language_override_instruction_conflict": "Language override blocked",
            "distractor_object_confusion": "Target identity confirmation",
        }
        draw.rectangle((55, 356, 680, 404), fill="#dcfce7", outline="#166534", width=2)
        draw.text((76, 369), messages.get(failure_type, "Internal risk signature detected"), fill="#166534", font=_font(21))
    return img


def write_frames(frames: list[Image.Image], output_path: Path, fps: int) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    imageio.mimsave(output_path.with_suffix(".gif"), frames, duration=1000 / fps)
    return output_path.with_suffix(".gif")


def create_demo_video(output_path: Path, certificate_id: str, mode: str, failure_type: str, fps: int = 12, duration_s: int = 5) -> Path:
    frames = [draw_frame(certificate_id, mode, failure_type, i / fps, duration_s) for i in range(fps * duration_s)]
    return write_frames(frames, output_path.with_suffix(".gif"), fps)


def create_all_demo_videos(data_root: Path) -> list[Path]:
    failure_types = {
        "FR-001": "occlusion_induced_wrong_grasp",
        "FR-002": "language_override_instruction_conflict",
        "FR-003": "distractor_object_confusion",
    }
    paths: list[Path] = []
    for certificate_id, failure_type in failure_types.items():
        for mode in ("success", "failure", "mitigated"):
            paths.append(create_demo_video(data_root / "videos" / f"{certificate_id}_{mode}.gif", certificate_id, mode, failure_type))
    return paths
