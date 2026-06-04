from __future__ import annotations

import numpy as np

from taco_demo.activation_recorder import ActivationRecorder, record_forward_pass


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


def test_activation_recorder_snapshots_before_in_place_mutation():
    layer = MutatingFakeLayer(2.0)
    recorder = ActivationRecorder().attach(None, named_modules=[("policy.mutable", layer)])

    output = layer.forward(np.array([1.0, 2.0]))

    assert np.allclose(output, np.array([-2.0, -4.0]))
    assert np.allclose(recorder.captures["policy.mutable"][0], np.array([2.0, 4.0]))
