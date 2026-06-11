"""Cosmos backend — NVIDIA world-foundation-model rendering of perturbed sim states.

This is the "use Cosmos to create new sim states" route. A world model like Cosmos
generates *pixels*, not physics state, so it plays two honest roles here:

  1. `CosmosRenderer` turns a chosen Perturbation into a photoreal observation /
     evidence frame of the stressed scene — the "imagined failure" attached to a
     certificate. (Drives a vision policy, or documents the finding.)
  2. `CosmosProposer` is a thin Proposer that delegates knob selection to the
     Monte-Carlo heuristic and tags the result `source="cosmos"`, so the same
     falsification loop runs with Cosmos as the scenario generator.

Reality check (June 2026): "Cosmos 3" (the 16B/65B omnimodel) does NOT fit a 32 GB
GPU. The realistic on-device world model is **`nvidia/Cosmos-Predict2.5-2B`**
(~32 GB @720p, fits @480p with offload, via HF Diffusers). If the weights or the
Blackwell/CUDA toolchain aren't available, `available()` returns False and the
engine simply skips Cosmos evidence — the audit still runs on the heuristic path.
Override the model with `TACO_COSMOS_MODEL` (e.g. the confirmed-on-5090
`nvidia/Cosmos-Predict2-2B-Text2Image` fallback).
"""

from __future__ import annotations

import os

from ..types import Perturbation
from .base import History, Proposer
from .heuristic import HeuristicProposer

DEFAULT_MODEL = os.environ.get("TACO_COSMOS_MODEL", "nvidia/Cosmos-Predict2.5-2B")


def status() -> dict:
    """Diagnostics for whether a Cosmos render can run on this box."""
    info = {"model": DEFAULT_MODEL, "torch": None, "cuda": False,
            "device": None, "diffusers": None, "ready": False, "note": ""}
    try:
        import torch
        info["torch"] = torch.__version__
        info["cuda"] = bool(torch.cuda.is_available())
        if info["cuda"]:
            info["device"] = torch.cuda.get_device_name(0)
    except Exception as e:  # pragma: no cover
        info["note"] = f"torch unavailable: {e}"
        return info
    try:
        import diffusers
        info["diffusers"] = diffusers.__version__
    except Exception as e:  # pragma: no cover
        info["note"] = f"diffusers unavailable: {e}"
        return info
    info["ready"] = info["cuda"]
    if not info["cuda"]:
        info["note"] = "no CUDA device"
    return info


def prompt_for_perturbation(pert: Perturbation) -> str:
    """Turn a bounded perturbation into a Cosmos text prompt describing the scene."""
    k = pert.knobs
    parts = ["a robot arm gripper above a tabletop with a small target cube and a "
             "similar distractor object, photorealistic, eye-level camera"]
    if k.get("occlusion_fraction", 0) > 0.2:
        parts.append("the target cube is partly hidden behind a cardboard box (occlusion)")
    if k.get("distractor_similarity", 0) > 0.3:
        parts.append("the distractor object looks almost identical to the target")
    if abs(k.get("camera_yaw_deg", 0)) > 5:
        parts.append("the camera is rotated to an oblique side angle")
    if k.get("lighting", 0) > 0.3:
        parts.append("harsh uneven lighting with strong shadows washing out colors")
    if k.get("sensor_noise", 0) > 0.1:
        parts.append("slight motion blur and sensor noise")
    return ", ".join(parts)


class CosmosRenderer:
    """Lazily loads a Cosmos diffusion pipeline and renders one frame per call."""

    def __init__(self, model_id: str | None = None, height: int = 480, width: int = 832,
                 steps: int = 28):
        self.model_id = model_id or DEFAULT_MODEL
        self.height, self.width, self.steps = height, width, steps
        self._pipe = None
        self._failed = False

    def available(self) -> bool:
        s = status()
        return bool(s["ready"]) and not self._failed

    def _load(self):  # pragma: no cover - requires GPU + weights
        if self._pipe is not None:
            return self._pipe
        import torch
        from diffusers import DiffusionPipeline
        pipe = DiffusionPipeline.from_pretrained(self.model_id, torch_dtype=torch.bfloat16)
        # keep within 32 GB: offload guardrail/text-encoder + the model itself to CPU
        if hasattr(pipe, "enable_model_cpu_offload"):
            pipe.enable_model_cpu_offload()
        else:
            pipe = pipe.to("cuda")
        self._pipe = pipe
        return pipe

    def render(self, prompt: str, out_path: str) -> str | None:  # pragma: no cover - GPU
        """Generate one frame for `prompt`, save to `out_path`. Returns path or None."""
        try:
            import imageio.v2 as imageio
            import numpy as np
            pipe = self._load()
            result = pipe(prompt=prompt, height=self.height, width=self.width,
                          num_inference_steps=self.steps)
            frame = None
            for attr in ("frames", "images"):
                seq = getattr(result, attr, None)
                if seq:
                    frame = seq[0][0] if attr == "frames" else seq[0]
                    break
            if frame is None:
                return None
            os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
            imageio.imwrite(out_path, np.asarray(frame))
            return out_path
        except Exception as e:
            self._failed = True
            print(f"[cosmos] render failed ({type(e).__name__}: {e}); "
                  "skipping Cosmos evidence.")
            return None

    def render_perturbation(self, pert: Perturbation, out_path: str) -> str | None:
        return self.render(prompt_for_perturbation(pert), out_path)


class CosmosProposer(Proposer):
    """Knob selection by Monte-Carlo heuristic; scenes generated by Cosmos."""

    name = "cosmos"

    def __init__(self, seed: int = 0):
        self._inner = HeuristicProposer(seed=seed)
        self.renderer = CosmosRenderer()

    def propose(self, family: str, history: History) -> Perturbation:
        pert = self._inner.propose(family, history)
        return Perturbation(knobs=pert.knobs, family=family, source="cosmos")
