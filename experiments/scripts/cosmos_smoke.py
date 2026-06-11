"""Attempt a real NVIDIA Cosmos generation on this box and report what happens.

This is the bring-up experiment for the Cosmos route. It (1) prints diagnostics,
(2) tries to load the configured Cosmos pipeline via HF Diffusers, and (3) renders
one frame from a perturbed-scene prompt. Every failure is caught and reported so
we learn exactly what breaks on RTX 5090 / CUDA 13 / torch 2.11 rather than
crashing.

    cd experiments
    python scripts/cosmos_smoke.py                     # default model
    TACO_COSMOS_MODEL=nvidia/Cosmos-Predict2-2B-Text2Image python scripts/cosmos_smoke.py

Note: first run downloads tens of GB of weights from Hugging Face and needs the
NVIDIA Open Model License accepted on the model page (set HF_TOKEN).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from taco_audit.proposers.cosmos import DEFAULT_MODEL, CosmosRenderer, status
from taco_audit.types import Perturbation


def main() -> int:
    print("=== Cosmos bring-up diagnostics ===")
    for k, v in status().items():
        print(f"  {k}: {v}")
    print(f"\nLoading + rendering with {DEFAULT_MODEL} (this can take minutes / download weights)...\n")

    pert = Perturbation(
        {"occlusion_fraction": 0.5, "distractor_similarity": 0.6, "lighting": 0.4},
        family="visual_occlusion", source="cosmos",
    )
    out = Path("runs/cosmos_smoke/perturbed_scene.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    renderer = CosmosRenderer()
    t0 = time.time()
    path = renderer.render_perturbation(pert, str(out))
    dt = time.time() - t0

    if path:
        print(f"\n✅ Cosmos render OK in {dt:.1f}s -> {path}")
        return 0
    print(f"\n❌ Cosmos render did not produce a frame ({dt:.1f}s elapsed). "
          "See the [cosmos] error above. The audit engine runs without it.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
