"""Copy rendered Manim chapters into the app data folder and make GIFs.

Run after:
    modal run manim_explainer/modal_render.py --chapters

Then:
    .venv/bin/python manim_explainer/export_chapter_assets.py
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "manim_explainer" / "renders" / "chapters"
TARGET_DIR = ROOT / "taco_demo" / "data" / "videos" / "explainer"

CHAPTERS = [
    ("Explainer01Opening", "01_opening"),
    ("Explainer02Activations", "02_activations"),
    ("Explainer03Features", "03_features"),
    ("Explainer04Superposition", "04_superposition"),
    ("Explainer05SAEMechanics", "05_sae_mechanics"),
    ("Explainer06TopK", "06_topk"),
    ("Explainer07MonitorRule", "07_monitor_rule"),
    ("Explainer08ReplayTiming", "08_replay_timing"),
    ("Explainer09SAEPrism", "09_sae_prism"),
    ("Explainer10FeatureQuality", "10_feature_quality"),
    ("Explainer11DreamAudit", "11_dreamaudit"),
    ("Explainer12Certification", "12_readiness_tier"),
    ("Explainer13Claim", "13_certificate_claim"),
]


def convert_to_gif(mp4_path: Path, gif_path: Path) -> None:
    gif_path.parent.mkdir(parents=True, exist_ok=True)
    filtergraph = "fps=10,scale=960:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(mp4_path),
            "-vf",
            filtergraph,
            "-loop",
            "0",
            str(gif_path),
        ],
        check=True,
    )


def main() -> None:
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    for scene, slug in CHAPTERS:
        source = SOURCE_DIR / f"{scene}.mp4"
        if not source.exists():
            raise FileNotFoundError(f"Missing rendered chapter: {source}")
        target_mp4 = TARGET_DIR / f"{slug}.mp4"
        target_gif = TARGET_DIR / f"{slug}.gif"
        shutil.copy2(source, target_mp4)
        convert_to_gif(target_mp4, target_gif)
        print(f"WROTE {target_mp4}")
        print(f"WROTE {target_gif}")


if __name__ == "__main__":
    main()
