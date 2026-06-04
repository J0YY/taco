import modal

app = modal.App("taco-menagerie-dog")
img = (
    modal.Image.debian_slim()
    .apt_install("libegl1", "libgl1", "libglib2.0-0", "ffmpeg", "git")
    .pip_install("mujoco", "imageio[ffmpeg]", "numpy")
    .run_commands("git clone --depth 1 https://github.com/google-deepmind/mujoco_menagerie /menagerie")
    .env({"MUJOCO_GL": "egl", "NVIDIA_DRIVER_CAPABILITIES": "all"})
)

@app.function(gpu="A10G", image=img, timeout=600)
def render(robot: str = "unitree_go2", mode: str = "gait", steps: int = 200):
    import os, io, numpy as np, imageio.v2 as imageio, mujoco
    os.environ["MUJOCO_GL"] = "egl"
    scene = f"/menagerie/{robot}/scene.xml"
    model = mujoco.MjModel.from_xml_path(scene)
    data = mujoco.MjData(model)
    if model.nkey > 0:
        mujoco.mj_resetDataKeyframe(model, data, 0)
    home = data.ctrl.copy() if model.nu == data.ctrl.shape[0] else np.zeros(model.nu)
    rng = np.random.default_rng(0)
    r = mujoco.Renderer(model, 360, 480)
    frames = []
    for t in range(steps):
        if mode == "gait":
            phase = 2 * np.pi * t / 40.0
            data.ctrl[:] = home + 0.6 * np.sin(phase + np.linspace(0, np.pi, model.nu))
        else:  # random torques -> the dog destabilizes and collapses (failure)
            data.ctrl[:] = home + rng.uniform(-1.5, 1.5, model.nu)
        mujoco.mj_step(model, data)
        if t % 2 == 0:
            r.update_scene(data)
            frames.append(r.render())
    buf = io.BytesIO(); imageio.mimsave(buf, frames, format="mp4", fps=30)
    return buf.getvalue()

@app.local_entrypoint()
def main():
    import os
    os.makedirs("taco_demo/data/videos/incoming/modal_dog", exist_ok=True)
    for mode, name in [("gait", "go2_gait_success.mp4"), ("random", "go2_random_fall.mp4")]:
        data = render.remote(mode=mode)
        out = f"taco_demo/data/videos/incoming/modal_dog/{name}"
        open(out, "wb").write(data)
        print(f"WROTE {out} ({len(data)} bytes)")


@app.local_entrypoint()
def humanoid():
    import os
    os.makedirs("taco_demo/data/videos/incoming/modal_humanoid", exist_ok=True)
    for mode, name in [("gait", "g1_gait.mp4"), ("random", "g1_random_fall.mp4")]:
        data = render.remote(robot="unitree_g1", mode=mode)
        out = f"taco_demo/data/videos/incoming/modal_humanoid/{name}"
        open(out, "wb").write(data)
        print(f"WROTE {out} ({len(data)} bytes)")
