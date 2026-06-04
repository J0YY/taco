import modal

app = modal.App("taco-maniskill")

img = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-cudnn-devel-ubuntu22.04", add_python="3.11")
    .apt_install("libvulkan1", "vulkan-tools", "libgl1", "libglvnd0", "libegl1",
                 "libxext6", "libsm6", "ffmpeg", "git", "wget", "build-essential", "cmake", "clang")
    .run_commands("python -m pip install --upgrade pip setuptools wheel")
    .pip_install("numpy<2", "cython", "setuptools", "wheel")
    .pip_install("toppra", extra_options="--no-build-isolation")
    .pip_install("torch", "mani_skill", "imageio[ffmpeg]", "tyro")
    .run_commands(
        "mkdir -p /usr/share/vulkan/icd.d",
        'printf \'{"file_format_version":"1.0.0","ICD":{"library_path":"libGLX_nvidia.so.0","api_version":"1.3.277"}}\' > /usr/share/vulkan/icd.d/nvidia_icd.json',
    )
    .env({"NVIDIA_DRIVER_CAPABILITIES": "all", "NVIDIA_VISIBLE_DEVICES": "all"})
)


@app.function(gpu="A10G", image=img, timeout=600)
def render_smoke(env_id: str = "PickCube-v1", steps: int = 30):
    import os
    os.environ["VK_ICD_FILENAMES"] = "/usr/local/lib/python3.11/site-packages/sapien/vulkan_library/nvidia_icd.json"
    os.environ.setdefault("XDG_RUNTIME_DIR", "/tmp")
    import numpy as np, imageio.v2 as imageio, gymnasium as gym
    import mani_skill.envs  # noqa
    env = gym.make(env_id, num_envs=1, render_mode="rgb_array")
    env.reset(seed=0)
    frames = []
    for _ in range(steps):
        a = env.action_space.sample()
        env.step(a)
        img = env.render()
        arr = img[0].cpu().numpy() if hasattr(img, "cpu") else np.asarray(img)[0] if np.asarray(img).ndim == 4 else np.asarray(img)
        frames.append(arr.astype("uint8"))
    env.close()
    import io
    buf = io.BytesIO()
    imageio.mimsave(buf, frames, format="mp4", fps=15)
    return buf.getvalue()


@app.local_entrypoint()
def main():
    data = render_smoke.remote()
    out = "taco_demo/data/videos/incoming/modal_pickcube_smoke.mp4"
    with open(out, "wb") as f:
        f.write(data)
    print(f"WROTE {out} ({len(data)} bytes)")


@app.function(gpu="A10G", image=img, timeout=300)
def vk_diag():
    import subprocess, glob, os
    def run(c): 
        try: return subprocess.run(c, capture_output=True, text=True, shell=True).stdout[-1500:]
        except Exception as e: return str(e)
    return {
        "vulkaninfo": run("vulkaninfo --summary 2>&1 | head -40"),
        "nvidia_vk_libs": run("ls -1 /usr/lib/x86_64-linux-gnu/ 2>/dev/null | grep -iE 'nvidia|vulkan|GLX' ; echo ---; find / -name 'libGLX_nvidia.so*' 2>/dev/null | head"),
        "icd_files": run("ls -1 /usr/share/vulkan/icd.d/ 2>/dev/null; echo ---; find / -name '*nvidia*icd*.json' 2>/dev/null | head"),
        "vk_env": {k: v for k, v in os.environ.items() if "VK" in k or "NVIDIA" in k},
    }


@app.local_entrypoint()
def diag():
    import json
    print(json.dumps(vk_diag.remote(), indent=1))
