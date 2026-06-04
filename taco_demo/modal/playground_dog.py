import modal

app = modal.App("taco-playground-dog")
img = (
    modal.Image.debian_slim()
    .apt_install("libegl1", "libgl1", "libglib2.0-0", "ffmpeg", "git")
    .pip_install("jax[cuda12]", "mujoco", "mujoco-mjx", "brax", "playground", "imageio[ffmpeg]")
    .env({"MUJOCO_GL": "egl", "NVIDIA_DRIVER_CAPABILITIES": "all", "XLA_PYTHON_CLIENT_PREALLOCATE": "false"})
)

@app.function(gpu="A10G", image=img, timeout=900)
def dog_smoke(env_name: str = "Go1JoystickFlatTerrain", steps: int = 150):
    import os, io, numpy as np, imageio.v2 as imageio
    os.environ["MUJOCO_GL"] = "egl"
    import jax
    from mujoco_playground import registry
    avail = [e for e in registry.ALL_ENVS] if hasattr(registry, "ALL_ENVS") else "n/a"
    env = registry.load(env_name)
    rng = jax.random.PRNGKey(0)
    state = jax.jit(env.reset)(rng)
    step = jax.jit(env.step)
    rollout = [state]
    for i in range(steps):
        # random actions -> an untrained controller; the dog will struggle/fall (a real failure rollout)
        act = jax.random.uniform(jax.random.PRNGKey(i + 1), (env.action_size,), minval=-1.0, maxval=1.0)
        state = step(state, act)
        rollout.append(state)
    frames = env.render(rollout, height=240, width=320)
    buf = io.BytesIO(); imageio.mimsave(buf, [np.asarray(f, dtype="uint8") for f in frames], format="mp4", fps=30)
    return {"env": env_name, "action_size": int(env.action_size), "n_frames": len(frames),
            "available_sample": str(avail)[:300], "mp4": buf.getvalue()}

@app.local_entrypoint()
def main():
    r = dog_smoke.remote()
    out = "taco_demo/data/videos/incoming/modal_go1_random.mp4"
    open(out, "wb").write(r["mp4"])
    print(f"env={r['env']} action_size={r['action_size']} frames={r['n_frames']}")
    print(f"WROTE {out} ({len(r['mp4'])} bytes)")
