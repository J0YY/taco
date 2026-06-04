"""Optional activation recorder for torch-style robot policy models.

The module is torch-compatible but does not require torch at import time. It
uses the standard ``register_forward_hook`` API, so tests can exercise it with
small fake modules while production users can attach it to torch.nn.Module trees.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np


def torch_available() -> bool:
    """Return whether torch can be imported in the current environment."""

    try:
        import torch  # noqa: F401
    except ImportError:
        return False
    return True


def _extract_first_array_like(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "detach") or hasattr(value, "numpy"):
        return value
    if isinstance(value, dict):
        for item in value.values():
            extracted = _extract_first_array_like(item)
            if extracted is not None:
                return extracted
        return None
    if isinstance(value, (list, tuple)):
        for item in value:
            extracted = _extract_first_array_like(item)
            if extracted is not None:
                return extracted
        return None
    try:
        return np.asarray(value)
    except (TypeError, ValueError):
        return None


def _to_numpy(value: Any, *, detach: bool, device: str) -> np.ndarray | None:
    item = _extract_first_array_like(value)
    if item is None:
        return None
    if detach and hasattr(item, "detach"):
        item = item.detach()
    if device and hasattr(item, "to"):
        try:
            item = item.to(device)
        except (TypeError, RuntimeError):
            pass
    if hasattr(item, "cpu"):
        try:
            item = item.cpu()
        except TypeError:
            pass
    if hasattr(item, "numpy"):
        try:
            return np.asarray(item.numpy())
        except TypeError:
            pass
    try:
        return np.asarray(item)
    except (TypeError, ValueError):
        return None


def _sanitize_key(key: str) -> str:
    sanitized = re.sub(r"[^0-9A-Za-z_]+", "_", key).strip("_")
    return sanitized or "activation"


class ActivationRecorder:
    """Record intermediate activations from modules with forward hooks."""

    def __init__(
        self,
        layer_names: list[str] | None = None,
        *,
        detach: bool = True,
        device: str = "cpu",
        max_batches: int | None = None,
    ) -> None:
        self.layer_names = set(layer_names) if layer_names is not None else None
        self.detach = detach
        self.device = device
        self.max_batches = max_batches
        self.captures: dict[str, list[np.ndarray]] = {}
        self._handles: list[Any] = []

    def __enter__(self) -> "ActivationRecorder":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.remove()

    def _should_record(self, name: str) -> bool:
        return self.layer_names is None or name in self.layer_names

    def _hook(self, name: str):
        def record(_module: Any, _inputs: tuple[Any, ...], output: Any) -> None:
            bucket = self.captures.setdefault(name, [])
            if self.max_batches is not None and len(bucket) >= self.max_batches:
                return
            array = _to_numpy(output, detach=self.detach, device=self.device)
            if array is not None:
                bucket.append(np.asarray(array).copy())

        return record

    def attach(self, model: Any, named_modules: Iterable[tuple[str, Any]] | None = None) -> "ActivationRecorder":
        """Attach hooks to selected modules and return ``self``."""

        self.remove()
        modules = named_modules if named_modules is not None else model.named_modules()
        for name, module in modules:
            if not name or not self._should_record(name) or not hasattr(module, "register_forward_hook"):
                continue
            self._handles.append(module.register_forward_hook(self._hook(name)))
            self.captures.setdefault(name, [])
        return self

    def clear(self) -> None:
        self.captures.clear()

    def remove(self) -> None:
        for handle in self._handles:
            if hasattr(handle, "remove"):
                handle.remove()
        self._handles = []

    def summary(self) -> dict[str, dict[str, Any]]:
        """Summarize recorded activations by layer."""

        result: dict[str, dict[str, Any]] = {}
        for name, arrays in self.captures.items():
            if not arrays:
                result[name] = {"count": 0, "shape": None, "mean": None, "std": None, "max_abs": None}
                continue
            flattened = np.concatenate([np.asarray(array, dtype=float).reshape(-1) for array in arrays])
            result[name] = {
                "count": len(arrays),
                "shape": list(arrays[-1].shape),
                "mean": round(float(np.mean(flattened)), 6),
                "std": round(float(np.std(flattened)), 6),
                "max_abs": round(float(np.max(np.abs(flattened))), 6),
            }
        return result

    def save_npz(self, path: Path | str) -> Path:
        """Persist captured activations to an NPZ file."""

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, np.ndarray] = {}
        for name, arrays in self.captures.items():
            for idx, array in enumerate(arrays):
                payload[f"{_sanitize_key(name)}__{idx:04d}"] = np.asarray(array)
        np.savez(output_path, **payload)
        return output_path


def record_forward_pass(
    model: Any,
    inputs: Any,
    *,
    layer_names: list[str] | None = None,
    output_path: Path | str | None = None,
    max_batches: int | None = None,
) -> tuple[Any, ActivationRecorder]:
    """Run one model forward pass while recording selected layer activations."""

    recorder = ActivationRecorder(layer_names=layer_names, max_batches=max_batches).attach(model)
    try:
        if isinstance(inputs, dict):
            output = model(**inputs)
        elif isinstance(inputs, (list, tuple)):
            output = model(*inputs)
        else:
            output = model(inputs)
        if output_path is not None:
            recorder.save_npz(output_path)
        return output, recorder
    finally:
        recorder.remove()
