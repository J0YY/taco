"""Render the TACO ManimGL explainer on Modal.

Run from the repo root:
    modal run manim_explainer/modal_render.py

The active Modal token is read by the Modal CLI. Do not put credentials in this
file.
"""

from __future__ import annotations

from pathlib import Path

import modal


app = modal.App("taco-manim-explainer")

ROOT = Path(__file__).resolve().parents[1]

CHAPTER_SCENES = [
    "Explainer01Opening",
    "Explainer02Activations",
    "Explainer03Features",
    "Explainer04Superposition",
    "Explainer05SAEMechanics",
    "Explainer06TopK",
    "Explainer07MonitorRule",
    "Explainer08ReplayTiming",
    "Explainer09SAEPrism",
    "Explainer10FeatureQuality",
    "Explainer11DreamAudit",
    "Explainer12Certification",
    "Explainer13Claim",
]

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "ffmpeg",
        "git",
        "build-essential",
        "pkg-config",
        "xvfb",
        "libegl1",
        "libgl1",
        "libgl1-mesa-dri",
        "libglib2.0-0",
        "libxrender1",
        "libxext6",
        "libsm6",
        "libcairo2",
        "libcairo2-dev",
        "libpango-1.0-0",
        "libpango1.0-dev",
        "fonts-dejavu-core",
    )
    .pip_install("numpy>=1.26", "manimgl>=1.7.2")
    .env(
        {
            "PYTHONPATH": "/root",
            "DISPLAY": ":99",
            "LIBGL_ALWAYS_SOFTWARE": "1",
            "MESA_GL_VERSION_OVERRIDE": "3.3",
        }
    )
    .add_local_dir(ROOT / "manim_explainer", remote_path="/root/manim_explainer")
    .add_local_file(ROOT / "taco_demo" / "__init__.py", remote_path="/root/taco_demo/__init__.py")
    .add_local_file(ROOT / "taco_demo" / "external_evidence.py", remote_path="/root/taco_demo/external_evidence.py")
    .add_local_file(ROOT / "taco_demo" / "sae_features.py", remote_path="/root/taco_demo/sae_features.py")
    .add_local_dir(
        ROOT / "taco_demo" / "data" / "sae_features" / "octo",
        remote_path="/root/taco_demo/data/sae_features/octo",
    )
    .add_local_file(
        ROOT / "taco_demo" / "data" / "videos" / "real_external" / "saescope" / "manifest.json",
        remote_path="/root/taco_demo/data/videos/real_external/saescope/manifest.json",
    )
)


@app.function(image=image, timeout=1200, cpu=4, memory=8192)
def render_explainer(scene: str = "TacoSAEDreamAuditExplainer") -> tuple[bytes, str]:
    import os
    import subprocess
    from pathlib import Path

    workdir = Path("/root")
    output_root = workdir / "media"
    output_root.mkdir(exist_ok=True)

    data_check = subprocess.run(
        [
            "xvfb-run",
            "-a",
            "-s",
            "-screen 0 1280x720x24",
            "python",
            "/root/manim_explainer/taco_sae_dreamaudit.py",
        ],
        cwd=workdir,
        env={**os.environ, "PYTHONPATH": "/root"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    if data_check.returncode != 0:
        raise RuntimeError(data_check.stderr[-4000:] or data_check.stdout[-4000:])

    cmd = [
        "xvfb-run",
        "-a",
        "-s",
        "-screen 0 1920x1080x24",
        "manimgl",
        "/root/manim_explainer/taco_sae_dreamaudit.py",
        scene,
        "-w",
        "--video_dir",
        str(output_root),
    ]
    result = subprocess.run(
        cmd,
        cwd=workdir,
        env={**os.environ, "PYTHONPATH": "/root"},
        capture_output=True,
        text=True,
        timeout=1100,
    )
    log = result.stdout + "\n" + result.stderr
    if result.returncode != 0:
        raise RuntimeError(log[-8000:])

    candidates = sorted(output_root.rglob(f"{scene}.mp4"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        candidates = sorted(output_root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise FileNotFoundError(f"No MP4 produced. Render log tail:\n{log[-4000:]}")
    video = candidates[-1]
    return video.read_bytes(), log[-4000:]


@app.function(image=image, timeout=1800, cpu=4, memory=8192)
def render_explainer_chapters(scenes: list[str] | None = None) -> list[tuple[str, bytes, str]]:
    import os
    import subprocess
    from pathlib import Path

    scene_names = scenes or CHAPTER_SCENES
    workdir = Path("/root")
    output_root = workdir / "media_chapters"
    output_root.mkdir(exist_ok=True)

    data_check = subprocess.run(
        [
            "xvfb-run",
            "-a",
            "-s",
            "-screen 0 1280x720x24",
            "python",
            "/root/manim_explainer/taco_sae_dreamaudit.py",
        ],
        cwd=workdir,
        env={**os.environ, "PYTHONPATH": "/root"},
        capture_output=True,
        text=True,
        timeout=60,
    )
    if data_check.returncode != 0:
        raise RuntimeError(data_check.stderr[-4000:] or data_check.stdout[-4000:])

    rendered: list[tuple[str, bytes, str]] = []
    for scene in scene_names:
        cmd = [
            "xvfb-run",
            "-a",
            "-s",
            "-screen 0 1920x1080x24",
            "manimgl",
            "/root/manim_explainer/taco_sae_dreamaudit.py",
            scene,
            "-w",
            "--video_dir",
            str(output_root),
        ]
        result = subprocess.run(
            cmd,
            cwd=workdir,
            env={**os.environ, "PYTHONPATH": "/root"},
            capture_output=True,
            text=True,
            timeout=300,
        )
        log = result.stdout + "\n" + result.stderr
        if result.returncode != 0:
            raise RuntimeError(f"{scene} failed:\n{log[-8000:]}")

        candidates = sorted(output_root.rglob(f"{scene}.mp4"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            candidates = sorted(output_root.rglob("*.mp4"), key=lambda p: p.stat().st_mtime)
        if not candidates:
            raise FileNotFoundError(f"No MP4 produced for {scene}. Render log tail:\n{log[-4000:]}")
        video = candidates[-1]
        rendered.append((scene, video.read_bytes(), log[-1500:]))
    return rendered


@app.local_entrypoint()
def main(scene: str = "TacoSAEDreamAuditExplainer", chapters: bool = False):
    if chapters:
        out_dir = ROOT / "manim_explainer" / "renders" / "chapters"
        out_dir.mkdir(parents=True, exist_ok=True)
        rendered = render_explainer_chapters.remote(CHAPTER_SCENES)
        for scene_name, data, log_tail in rendered:
            out_path = out_dir / f"{scene_name}.mp4"
            out_path.write_bytes(data)
            print(f"WROTE {out_path} ({len(data)} bytes)")
            print(f"{scene_name} render log tail:")
            print(log_tail)
        return

    out_dir = ROOT / "manim_explainer" / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    data, log_tail = render_explainer.remote(scene)
    out_path = out_dir / f"{scene}.mp4"
    out_path.write_bytes(data)
    print(f"WROTE {out_path} ({len(data)} bytes)")
    print("Render log tail:")
    print(log_tail)
