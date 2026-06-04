"""Optional PyTorch activation recorder for real DreamAudit replay traces."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None


class ActivationRecorder:
    def __init__(self, model: Any, layer_name_substrings: list[str]):
        if torch is None:
            raise RuntimeError("PyTorch is not installed. The fallback demo uses precomputed NPZ traces.")
        self.model = model
        self.layer_name_substrings = layer_name_substrings
        self.handles: list[Any] = []
        self.records: dict[str, list[np.ndarray]] = {}

    def attach(self):
        def hook(name: str):
            def _hook(_module, _inputs, output):
                tensor = output[0] if isinstance(output, tuple) else output
                if hasattr(tensor, "detach"):
                    arr = tensor.detach().float().cpu().numpy()
                    self.records.setdefault(name, []).append(arr)
            return _hook

        for name, module in self.model.named_modules():
            if any(part in name for part in self.layer_name_substrings):
                self.handles.append(module.register_forward_hook(hook(name)))
        return self

    def detach(self):
        for handle in self.handles:
            handle.remove()
        self.handles = []

    def clear(self):
        self.records.clear()

    def export_npz(self, path: Path, certificate_id: str, rollout_mode: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        arrays = {name.replace(".", "_"): np.asarray(values, dtype=object) for name, values in self.records.items()}
        arrays["certificate_id"] = np.asarray(certificate_id)
        arrays["rollout_mode"] = np.asarray(rollout_mode)
        np.savez(path, **arrays)
        return path

