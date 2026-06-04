"""Optional activation recorder for torch-style robot policy models.

The module is torch-compatible but does not require torch at import time. It
uses the standard ``register_forward_hook`` API, so tests can exercise it with
small fake modules while production users can attach it to torch.nn.Module trees.

Recorded layer outputs can also be exported into TACO's scoreable trace schema
when the caller supplies an explicit layer-to-signal map. That keeps the local
demo offline while giving live policy runs a real path into the underwriting
metrics.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from .trace_scoring import REQUIRED_SIGNALS


def torch_available() -> bool:
    """Return whether torch can be imported in the current environment."""

    try:
        import torch  # noqa: F401
    except Exception:
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
    if "bfloat16" in str(getattr(item, "dtype", "")) and hasattr(item, "float"):
        try:
            item = item.float()
        except (TypeError, RuntimeError):
            pass
    if hasattr(item, "numpy"):
        try:
            return np.asarray(item.numpy())
        except TypeError:
            if hasattr(item, "float"):
                try:
                    return np.asarray(item.float().numpy())
                except (TypeError, RuntimeError):
                    pass
    try:
        return np.asarray(item)
    except (TypeError, ValueError):
        return None


def _sanitize_key(key: str) -> str:
    sanitized = re.sub(r"[^0-9A-Za-z_]+", "_", key).strip("_")
    return sanitized or "activation"


def _stable_suffix(key: str) -> str:
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:8]


def _activation_scalar(array: np.ndarray) -> float:
    numeric = np.asarray(array, dtype=float)
    if numeric.size == 0:
        return 0.0
    return float(np.nanmean(numeric))


SignalCalibration = dict[str, tuple[float, float]]


def _finite_bounds(values: np.ndarray) -> tuple[float, float]:
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        raise ValueError("Activation signal contains no finite values")
    return float(np.min(finite)), float(np.max(finite))


def _calibrate_series(series: np.ndarray, signal_name: str, signal_calibration: SignalCalibration | None) -> np.ndarray:
    values = np.asarray(series, dtype=float).reshape(-1)
    if values.size == 0:
        return values
    if signal_calibration and signal_name in signal_calibration:
        lower, upper = signal_calibration[signal_name]
        spread = float(upper - lower)
        if spread < 1e-9:
            return np.full(len(values), 0.5, dtype=float)
        return np.clip((values - lower) / spread, 0.0, 1.0)
    lower, upper = _finite_bounds(values)
    if lower >= 0.0 and upper <= 1.0:
        return np.clip(values, 0.0, 1.0)
    raise ValueError(
        f"Activation signal {signal_name!r} is outside [0, 1]; provide shared signal_calibration "
        "or use record_taco_trace_bundle(auto_calibrate=True)."
    )


def _pad_series(series: np.ndarray, length: int) -> np.ndarray:
    values = np.asarray(series, dtype=float).reshape(-1)
    if len(values) == length:
        return values
    if len(values) == 0:
        return np.zeros(length, dtype=float)
    if len(values) > length:
        return values[:length]
    pad = np.full(length - len(values), values[-1], dtype=float)
    return np.concatenate([values, pad])


def build_taco_trace_from_activations(
    captures: dict[str, list[np.ndarray]],
    signal_map: dict[str, str],
    *,
    timestep_hz: float = 20.0,
    trace_source: str = "recorded_activation_forward_hooks",
    signal_calibration: SignalCalibration | None = None,
) -> dict[str, np.ndarray]:
    """Convert captured layer outputs into TACO's internal-risk trace schema.

    ``signal_map`` maps recorded layer names to underwriting signal names, for
    example ``{"vision.encoder": "target_feature"}``. Missing required
    signals are intentionally left absent so concept coverage reflects actual
    instrumentation rather than fabricated completeness.
    """

    if not signal_map:
        raise ValueError("signal_map must map recorded layer names to TACO trace signal names")

    trace: dict[str, np.ndarray] = {}
    max_length = 0
    for layer_name, signal_name in signal_map.items():
        arrays = captures.get(layer_name, [])
        if not arrays:
            continue
        raw_series = np.asarray([_activation_scalar(array) for array in arrays], dtype=float)
        series = _calibrate_series(raw_series, signal_name, signal_calibration)
        trace[signal_name] = series
        max_length = max(max_length, len(series))

    if max_length == 0:
        raise ValueError("No captured activations matched signal_map")

    for signal_name, series in list(trace.items()):
        trace[signal_name] = _pad_series(series, max_length)

    if "time_s" not in trace:
        hz = timestep_hz if timestep_hz > 0 else 20.0
        trace["time_s"] = np.arange(max_length, dtype=float) / hz

    if "internal_risk_score" not in trace:
        risk_signals = [
            trace[key]
            for key in ("unsafe_trajectory_dominance", "action_risk", "memorized_trajectory_feature")
            if key in trace
        ]
        trace["internal_risk_score"] = np.maximum.reduce(risk_signals) if risk_signals else np.zeros(max_length, dtype=float)

    trace["trace_source"] = np.asarray([trace_source])
    trace["recorded_required_signal_count"] = np.asarray([sum(1 for signal in REQUIRED_SIGNALS if signal in trace)], dtype=int)
    return trace


def save_taco_trace_npz(
    captures: dict[str, list[np.ndarray]],
    path: Path | str,
    signal_map: dict[str, str],
    *,
    timestep_hz: float = 20.0,
    trace_source: str = "recorded_activation_forward_hooks",
    signal_calibration: SignalCalibration | None = None,
) -> Path:
    """Persist captured activations as a scoreable TACO trace NPZ."""

    output_path = Path(path)
    save_path = output_path if output_path.suffix == ".npz" else Path(f"{output_path}.npz")
    trace = build_taco_trace_from_activations(
        captures,
        signal_map,
        timestep_hz=timestep_hz,
        trace_source=trace_source,
        signal_calibration=signal_calibration,
    )
    save_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez(save_path, **trace)
    return save_path


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
        save_path = output_path if output_path.suffix == ".npz" else Path(f"{output_path}.npz")
        save_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, np.ndarray] = {}
        sanitized_counts: dict[str, int] = {}
        for name in self.captures:
            base = _sanitize_key(name)
            sanitized_counts[base] = sanitized_counts.get(base, 0) + 1
        for name, arrays in self.captures.items():
            base = _sanitize_key(name)
            key_prefix = base if sanitized_counts[base] == 1 else f"{base}__{_stable_suffix(name)}"
            for idx, array in enumerate(arrays):
                payload[f"{key_prefix}__{idx:04d}"] = np.asarray(array)
        np.savez(save_path, **payload)
        return save_path

    def save_taco_trace_npz(
        self,
        path: Path | str,
        signal_map: dict[str, str],
        *,
        timestep_hz: float = 20.0,
        trace_source: str = "recorded_activation_forward_hooks",
        signal_calibration: SignalCalibration | None = None,
    ) -> Path:
        """Persist captured activations as a scoreable TACO trace NPZ."""

        return save_taco_trace_npz(
            self.captures,
            path,
            signal_map,
            timestep_hz=timestep_hz,
            trace_source=trace_source,
            signal_calibration=signal_calibration,
        )


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


def record_taco_trace_bundle(
    model: Any,
    inputs_by_mode: dict[str, Iterable[Any]],
    *,
    layer_names: list[str],
    signal_map: dict[str, str],
    output_dir: Path | str,
    certificate_id: str,
    timestep_hz: float = 20.0,
    auto_calibrate: bool = True,
) -> dict[str, Path]:
    """Record success/failure/mitigated rollouts into scoreable trace files.

    ``inputs_by_mode`` usually contains ``success``, ``failure``, and
    ``mitigated`` sequences. Each item is passed to the model using the same
    calling convention as :func:`record_forward_pass`.
    """

    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    captures_by_mode: dict[str, dict[str, list[np.ndarray]]] = {}
    paths: dict[str, Path] = {}
    for mode, rollout_inputs in inputs_by_mode.items():
        recorder = ActivationRecorder(layer_names=layer_names).attach(model)
        try:
            for inputs in rollout_inputs:
                if isinstance(inputs, dict):
                    model(**inputs)
                elif isinstance(inputs, (list, tuple)):
                    model(*inputs)
                else:
                    model(inputs)
            captures_by_mode[mode] = {
                name: [array.copy() for array in arrays]
                for name, arrays in recorder.captures.items()
            }
        finally:
            recorder.remove()
    signal_calibration = _shared_signal_calibration(captures_by_mode, signal_map) if auto_calibrate else None
    for mode, captures in captures_by_mode.items():
        paths[mode] = save_taco_trace_npz(
            captures,
            output_root / f"{certificate_id}_{mode}.npz",
            signal_map,
            timestep_hz=timestep_hz,
            signal_calibration=signal_calibration,
        )
    return paths


def _shared_signal_calibration(
    captures_by_mode: dict[str, dict[str, list[np.ndarray]]],
    signal_map: dict[str, str],
) -> SignalCalibration:
    calibration: SignalCalibration = {}
    values_by_signal: dict[str, list[float]] = {}
    for captures in captures_by_mode.values():
        for layer_name, signal_name in signal_map.items():
            values_by_signal.setdefault(signal_name, [])
            values_by_signal[signal_name].extend(_activation_scalar(array) for array in captures.get(layer_name, []))
    for signal_name, values in values_by_signal.items():
        series = np.asarray(values, dtype=float)
        if series.size == 0:
            continue
        lower, upper = _finite_bounds(series)
        if lower < 0.0 or upper > 1.0:
            calibration[signal_name] = (lower, upper)
    return calibration
