import modal

app = modal.App("taco-zoo")
img = (
    modal.Image.debian_slim()
    .apt_install("libegl1", "libgl1", "libglib2.0-0", "ffmpeg", "git")
    .pip_install("mujoco", "imageio[ffmpeg]", "numpy")
    .run_commands("git clone --depth 1 https://github.com/google-deepmind/mujoco_menagerie /menagerie")
    .env({"MUJOCO_GL": "egl", "NVIDIA_DRIVER_CAPABILITIES": "all"})
)

ROBOTS = ["google_robot","hello_robot_stretch_3","pal_tiago_dual","kuka_iiwa_14","universal_robots_ur5e","ufactory_xarm7","wonik_allegro","shadow_hand","skydio_x2","trossen_vx300s","berkeley_humanoid","booster_t1","fourier_gr1","pal_talos"]

@app.function(gpu="A10G", image=img, timeout=600, max_containers=10)
def render(args):
    robot, mode = args
    import os, io, glob, numpy as np, imageio.v2 as imageio, mujoco
    os.environ["MUJOCO_GL"] = "egl"
    cands = sorted(glob.glob(f"/menagerie/{robot}/scene*.xml")) or sorted(glob.glob(f"/menagerie/{robot}/*.xml"))
    if not cands:
        return (robot, mode, b"")
    try:
        model = mujoco.MjModel.from_xml_path(cands[0]); data = mujoco.MjData(model)
        if model.nkey > 0:
            mujoco.mj_resetDataKeyframe(model, data, 0)
        home = data.ctrl.copy()
        rng = np.random.default_rng(0)
        r = mujoco.Renderer(model, 360, 480); frames = []
        for t in range(200):
            if mode == "gait":
                data.ctrl[:] = home + 0.5 * np.sin(2*np.pi*t/40.0 + np.linspace(0, np.pi, model.nu))
            else:
                data.ctrl[:] = home + rng.uniform(-1.5, 1.5, model.nu)
            mujoco.mj_step(model, data)
            if t % 2 == 0:
                r.update_scene(data); frames.append(r.render())
        buf = io.BytesIO(); imageio.mimsave(buf, frames, format="mp4", fps=30)
        return (robot, mode, buf.getvalue())
    except Exception as e:
        return (robot, mode, f"ERR:{e}".encode()[:200])

@app.local_entrypoint()
def main():
    import os
    os.makedirs("taco_demo/data/videos/incoming/modal_zoo", exist_ok=True)
    jobs = [(r, m) for r in ROBOTS for m in ("gait", "random")]
    ok = 0
    for robot, mode, data in render.map(jobs):
        if data and not data.startswith(b"ERR:"):
            open(f"taco_demo/data/videos/incoming/modal_zoo/{robot}_{mode}.mp4", "wb").write(data); ok += 1
            print(f"OK  {robot}_{mode} ({len(data)}b)")
        else:
            print(f"SKIP {robot}_{mode}: {data[:120]}")
    print(f"=== {ok}/{len(jobs)} clips ===")
