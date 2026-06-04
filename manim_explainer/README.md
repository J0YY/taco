# TACO Manim Explainer

Standalone ManimGL animation explaining TACO's interpretability story: SAE
features plus DreamAudit-style replay evidence become monitorable
pre-deployment certification evidence.

## Install

Use the repo venv:

```bash
.venv/bin/python -m pip install -r manim_explainer/requirements.txt
```

ManimGL also needs FFmpeg and OpenGL. On macOS, the upstream repo recommends
Homebrew FFmpeg and a LaTeX distribution for TeX-heavy scenes. This explainer
uses plain `Text`, so LaTeX should not be required for the first render.

## Render

### Modal

The preferred path for this repo is Modal:

```bash
modal run manim_explainer/modal_render.py
```

That writes:

```text
manim_explainer/renders/TacoSAEDreamAuditExplainer.mp4
```

To render the smaller chapter MP4s used by the Streamlit app:

```bash
modal run manim_explainer/modal_render.py --chapters
```

That writes one MP4 per chapter under:

```text
manim_explainer/renders/chapters/
```

Then copy them into the app data folder and generate the GIFs:

```bash
.venv/bin/python manim_explainer/export_chapter_assets.py
```

That writes matching `.mp4` and `.gif` files under:

```text
taco_demo/data/videos/explainer/
```

### Local

```bash
.venv/bin/manimgl manim_explainer/taco_sae_dreamaudit.py TacoSAEDreamAuditExplainer -w
```

For a quick final-frame smoke check:

```bash
.venv/bin/manimgl manim_explainer/taco_sae_dreamaudit.py TacoSAEDreamAuditExplainer -s
```

## What It Uses From TACO

- `taco_demo.sae_features.sae_overview()` for the real TopK SAE headline metrics.
- `taco_demo.external_evidence.saescope_summary()` for the real FR-004 internal
  monitor statistics.
- `taco_demo.external_evidence.fr004_certificate()` for the certificate wording.

The scene deliberately does not edit or regenerate any files under
`taco_demo/data/videos/real*`.

## Source Notes

- 3b1b ManimGL: https://github.com/3b1b/manim
- Sparse autoencoders for interpretable features: https://arxiv.org/abs/2309.08600
- Dr. VLA / SAE-on-VLA paper and project: https://arxiv.org/abs/2603.19183 and
  https://drvla.github.io
