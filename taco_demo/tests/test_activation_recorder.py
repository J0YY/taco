from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from taco_demo.activation_recorder import ActivationRecorder, record_forward_pass, record_taco_trace_bundle
from taco_demo.sample_data import DEMO_CERTIFICATES
from taco_demo.trace_scoring import compute_internal_metrics, load_trace


class FakeHandle:
    def __init__(self, hooks, hook):
        self.hooks = hooks
        self.hook = hook

    def remove(self):
        if self.hook in self.hooks:
            self.hooks.remove(self.hook)


class FakeLayer:
    def __init__(self, scale):
        self.scale = scale
        self.hooks = []

    def register_forward_hook(self, hook):
        self.hooks.append(hook)
        return FakeHandle(self.hooks, hook)

    def forward(self, value):
        output = np.asarray(value) * self.scale
        for hook in list(self.hooks):
            hook(self, (value,), output)
        return output


class MutatingFakeLayer(FakeLayer):
    def forward(self, value):
        output = np.asarray(value, dtype=float) * self.scale
        for hook in list(self.hooks):
            hook(self, (value,), output)
        output *= -1
        return output


class FakeModel:
    def __init__(self):
        self.encoder = FakeLayer(2.0)
        self.head = FakeLayer(3.0)

    def named_modules(self):
        return [("", self), ("policy.encoder", self.encoder), ("policy.head", self.head)]

    def __call__(self, value):
        return self.head.forward(self.encoder.forward(value))


class FakeTraceModel:
    def __init__(self, layer_names):
        self.layers = {name: FakeLayer(1.0) for name in layer_names}

    def named_modules(self):
        return [("", self)] + list(self.layers.items())

    def __call__(self, frame):
        for layer_name, value in frame.items():
            self.layers[layer_name].forward(np.array([value], dtype=float))
        return True


class FakeBFloat16Tensor:
    dtype = "torch.bfloat16"

    def __init__(self, values, casted=False):
        self.values = np.asarray(values, dtype=np.float32)
        self.casted = casted

    def detach(self):
        return self

    def to(self, _device):
        return self

    def cpu(self):
        return self

    def float(self):
        return FakeBFloat16Tensor(self.values, casted=True)

    def numpy(self):
        if not self.casted:
            raise TypeError("Got unsupported ScalarType BFloat16")
        return self.values


def test_activation_recorder_records_selected_layer_and_saves_npz(tmp_path):
    model = FakeModel()
    recorder = ActivationRecorder(layer_names=["policy.encoder"], max_batches=1).attach(model)

    output = model(np.array([1.0, 2.0, 3.0]))
    model(np.array([4.0, 5.0, 6.0]))
    summary = recorder.summary()
    path = recorder.save_npz(tmp_path / "activations.npz")
    recorder.remove()

    assert np.allclose(output, np.array([6.0, 12.0, 18.0]))
    assert list(recorder.captures) == ["policy.encoder"]
    assert summary["policy.encoder"]["count"] == 1
    assert summary["policy.encoder"]["shape"] == [3]
    assert summary["policy.encoder"]["mean"] == 4.0
    with np.load(path) as data:
        assert data.files == ["policy_encoder__0000"]
        assert np.allclose(data["policy_encoder__0000"], np.array([2.0, 4.0, 6.0]))


def test_record_forward_pass_removes_hooks_after_run(tmp_path):
    model = FakeModel()

    output, recorder = record_forward_pass(
        model,
        np.array([2.0]),
        layer_names=["policy.encoder", "policy.head"],
        output_path=tmp_path / "single_pass.npz",
    )

    assert np.allclose(output, np.array([12.0]))
    assert recorder.summary()["policy.head"]["count"] == 1
    assert model.encoder.hooks == []
    assert model.head.hooks == []
    assert (tmp_path / "single_pass.npz").exists()


def test_save_npz_disambiguates_sanitized_layer_name_collisions(tmp_path):
    layer_one = FakeLayer(2.0)
    layer_two = FakeLayer(3.0)
    recorder = ActivationRecorder().attach(None, named_modules=[("vision.encoder", layer_one), ("vision_encoder", layer_two)])

    layer_one.forward(np.array([1.0]))
    layer_two.forward(np.array([1.0]))
    path = recorder.save_npz(tmp_path / "colliding_layers.npz")

    with np.load(path) as data:
        assert len(data.files) == 2
        assert len(set(data.files)) == 2
        assert sorted(float(data[key][0]) for key in data.files) == [2.0, 3.0]


def test_save_npz_returns_actual_path_when_suffix_omitted(tmp_path):
    recorder = ActivationRecorder()
    recorder.captures = {"policy.encoder": [np.array([1.0])]}

    path = recorder.save_npz(tmp_path / "activations")

    assert path == tmp_path / "activations.npz"
    assert path.exists()


def test_activation_recorder_casts_bfloat16_like_tensor_before_numpy():
    layer = FakeLayer(1.0)
    recorder = ActivationRecorder().attach(None, named_modules=[("policy.bf16", layer)])

    for hook in list(layer.hooks):
        hook(layer, (), FakeBFloat16Tensor([1.0, 2.0]))

    assert np.allclose(recorder.captures["policy.bf16"][0], np.array([1.0, 2.0], dtype=np.float32))


def test_activation_recorder_snapshots_before_in_place_mutation():
    layer = MutatingFakeLayer(2.0)
    recorder = ActivationRecorder().attach(None, named_modules=[("policy.mutable", layer)])

    output = layer.forward(np.array([1.0, 2.0]))

    assert np.allclose(output, np.array([-2.0, -4.0]))
    assert np.allclose(recorder.captures["policy.mutable"][0], np.array([2.0, 4.0]))


def test_save_taco_trace_npz_feeds_internal_metric_scoring(tmp_path):
    signal_map = {
        "policy.target": "target_feature",
        "policy.grasp": "general_grasp_feature",
        "policy.transport": "transport_feature",
        "policy.memory": "memorized_trajectory_feature",
        "policy.unsafe": "unsafe_trajectory_dominance",
        "policy.action": "action_risk",
    }
    recorder = ActivationRecorder()
    recorder.captures = {
        "policy.target": [np.array([0.25]), np.array([0.22]), np.array([0.2]), np.array([0.18]), np.array([0.16])],
        "policy.grasp": [np.array([0.55]), np.array([0.58]), np.array([0.6]), np.array([0.62]), np.array([0.64])],
        "policy.transport": [np.array([0.45]), np.array([0.48]), np.array([0.51]), np.array([0.54]), np.array([0.57])],
        "policy.memory": [np.array([0.12]), np.array([0.25]), np.array([0.35]), np.array([0.45]), np.array([0.55])],
        "policy.unsafe": [np.array([0.2]), np.array([0.7]), np.array([0.76]), np.array([0.8]), np.array([0.82])],
        "policy.action": [np.array([0.18]), np.array([0.72]), np.array([0.78]), np.array([0.84]), np.array([0.86])],
    }

    path = recorder.save_taco_trace_npz(tmp_path / "failure_trace", signal_map)
    trace = load_trace(path)

    assert path == tmp_path / "failure_trace.npz"
    assert trace["trace_source"][0] == "recorded_activation_forward_hooks"
    assert int(trace["recorded_required_signal_count"][0]) == 6
    assert set(signal_map.values()).issubset(trace)


def test_record_taco_trace_bundle_scores_recorded_activation_source(tmp_path):
    layer_names = [
        "policy.target",
        "policy.grasp",
        "policy.transport",
        "policy.memory",
        "policy.unsafe",
        "policy.action",
    ]
    signal_map = {
        "policy.target": "target_feature",
        "policy.grasp": "general_grasp_feature",
        "policy.transport": "transport_feature",
        "policy.memory": "memorized_trajectory_feature",
        "policy.unsafe": "unsafe_trajectory_dominance",
        "policy.action": "action_risk",
    }
    model = FakeTraceModel(layer_names)
    paths = record_taco_trace_bundle(
        model,
        {
            "success": [
                ({
                    "policy.target": 0.88,
                    "policy.grasp": 0.72 + step * 0.02,
                    "policy.transport": 0.65 + step * 0.02,
                    "policy.memory": 0.10 + step * 0.02,
                    "policy.unsafe": 0.12 + step * 0.02,
                    "policy.action": 0.14 + step * 0.02,
                },)
                for step in range(8)
            ],
            "failure": [
                ({
                    "policy.target": 0.88 - step * 0.09,
                    "policy.grasp": 0.68 + step * 0.02,
                    "policy.transport": 0.62 + step * 0.02,
                    "policy.memory": 0.10 + step * 0.07,
                    "policy.unsafe": 0.14 + step * 0.11,
                    "policy.action": 0.15 + step * 0.12,
                },)
                for step in range(8)
            ],
            "mitigated": [
                ({
                    "policy.target": 0.82 - step * 0.04,
                    "policy.grasp": 0.70 + step * 0.015,
                    "policy.transport": 0.65 + step * 0.015,
                    "policy.memory": 0.11 + step * 0.04,
                    "policy.unsafe": 0.16 + step * 0.04,
                    "policy.action": 0.14 + step * 0.025,
                },)
                for step in range(8)
            ],
        },
        layer_names=layer_names,
        signal_map=signal_map,
        output_dir=tmp_path,
        certificate_id="FR-001-live",
    )

    certificate = replace(DEMO_CERTIFICATES[0], failure_timestep=6)
    metrics = compute_internal_metrics(
        certificate,
        load_trace(paths["success"]),
        load_trace(paths["failure"]),
        load_trace(paths["mitigated"]),
    )

    assert set(paths) == {"success", "failure", "mitigated"}
    assert metrics.metrics_source == "recorded_activation_forward_hooks"
    assert metrics.concept_coverage_score == 1.0
    assert metrics.details["recorded_required_signal_count"] == 6
    assert metrics.causal_mitigability_score > 0.4


def test_single_trace_export_requires_calibrated_activation_values(tmp_path):
    recorder = ActivationRecorder()
    recorder.captures = {"policy.action": [np.array([10.0]), np.array([11.0])]}
    signal_map = {"policy.action": "action_risk"}

    with pytest.raises(ValueError, match=r"outside \[0, 1\]"):
        recorder.save_taco_trace_npz(tmp_path / "uncalibrated.npz", signal_map)

    calibrated_path = recorder.save_taco_trace_npz(
        tmp_path / "calibrated.npz",
        signal_map,
        signal_calibration={"action_risk": (0.0, 20.0)},
    )

    trace = load_trace(calibrated_path)
    assert np.allclose(trace["action_risk"], np.array([0.5, 0.55]))


def test_record_taco_trace_bundle_uses_shared_calibration_for_raw_activation_ranges(tmp_path):
    layer_names = [
        "policy.target",
        "policy.grasp",
        "policy.transport",
        "policy.memory",
        "policy.unsafe",
        "policy.action",
    ]
    signal_map = {
        "policy.target": "target_feature",
        "policy.grasp": "general_grasp_feature",
        "policy.transport": "transport_feature",
        "policy.memory": "memorized_trajectory_feature",
        "policy.unsafe": "unsafe_trajectory_dominance",
        "policy.action": "action_risk",
    }
    model = FakeTraceModel(layer_names)
    paths = record_taco_trace_bundle(
        model,
        {
            "success": [
                ({
                    "policy.target": 10.0 + step * 0.2,
                    "policy.grasp": 2.0 + step * 0.1,
                    "policy.transport": 3.0 + step * 0.1,
                    "policy.memory": 0.10 + step * 0.03,
                    "policy.unsafe": 0.12 + step * 0.03,
                    "policy.action": 0.14 + step * 0.03,
                },)
                for step in range(8)
            ],
            "failure": [
                ({
                    "policy.target": 1.0 + step * 0.05,
                    "policy.grasp": 2.0 + step * 0.15,
                    "policy.transport": 3.0 + step * 0.15,
                    "policy.memory": 0.20 + step * 0.08,
                    "policy.unsafe": 8.0 + step * 0.40,
                    "policy.action": 10.0 + step * 0.50,
                },)
                for step in range(8)
            ],
            "mitigated": [
                ({
                    "policy.target": 8.0 + step * 0.1,
                    "policy.grasp": 2.0 + step * 0.1,
                    "policy.transport": 3.0 + step * 0.1,
                    "policy.memory": 0.10 + step * 0.03,
                    "policy.unsafe": 1.0 + step * 0.10,
                    "policy.action": 0.10 + step * 0.10,
                },)
                for step in range(8)
            ],
        },
        layer_names=layer_names,
        signal_map=signal_map,
        output_dir=tmp_path,
        certificate_id="FR-RAW-ACTIVATIONS",
    )

    certificate = replace(DEMO_CERTIFICATES[0], certificate_id="FR-RAW-ACTIVATIONS", failure_timestep=6)
    success = load_trace(paths["success"])
    failure = load_trace(paths["failure"])
    mitigated = load_trace(paths["mitigated"])
    metrics = compute_internal_metrics(certificate, success, failure, mitigated)

    assert np.mean(failure["action_risk"]) > np.mean(mitigated["action_risk"])
    assert np.mean(success["target_feature"]) > np.mean(failure["target_feature"])
    assert metrics.causal_mitigability_score > 0.7
    assert metrics.feature_stability_score < 0.5
