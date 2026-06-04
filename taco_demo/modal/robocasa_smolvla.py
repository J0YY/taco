"""Render a REAL RoboCasa kitchen-task rollout on Modal using the
lerobot/smolvla_robocasa policy via lerobot-eval.

Task: CloseFridge (atomic, fixture-centric, no objaverse pack needed -- this is
one of the tasks in LeRobot's CI smoke eval). We eval N episodes, parse the
per-episode success flags from eval_info.json, and return the rendered
eval_episode_*.mp4 for one SUCCESS and one FAILURE episode.

Follows the official LeRobot RoboCasa docs:
https://huggingface.co/docs/lerobot/main/robocasa
"""
import modal

app = modal.App("taco-robocasa-smolvla")

# Persistent cache for HF model/policy downloads across retries.
cache = modal.Volume.from_name("taco-hf-cache", create_if_missing=True)

img = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install(
        "libegl1", "libgl1", "libglib2.0-0", "libosmesa6",
        "ffmpeg", "git", "wget", "build-essential",
    )
    # RoboCasa env support (--env.type=robocasa) is only on lerobot's main
    # branch -- the released PyPI wheel (0.4.4) does NOT include it. The
    # [smolvla] extra pulls transformers/num2words/accelerate needed to load
    # the SmolVLA policy. Install lerobot[smolvla] from git main.
    .pip_install("lerobot[smolvla] @ git+https://github.com/huggingface/lerobot.git@main")
    # robocasa + robosuite are not on PyPI; install as editable clones.
    .run_commands(
        "git clone --depth 1 https://github.com/robocasa/robocasa.git /robocasa",
        "git clone --depth 1 https://github.com/ARISE-Initiative/robosuite.git /robosuite",
        "pip install -e /robocasa --no-deps",
        "pip install -e /robosuite",
    )
    # robocasa/__init__.py hard-asserts mujoco==3.3.1 and numpy==2.2.5.
    # "av" (PyAV) is needed by lerobot to ENCODE the eval episode videos.
    .pip_install(
        "numpy==2.2.5", "numba", "scipy", "mujoco==3.3.1", "pygame", "Pillow",
        "opencv-python", "pyyaml", "tqdm", "termcolor", "imageio",
        "h5py", "lxml", "tianshou", "gymnasium", "av",
    )
    # Configure robocasa macros. setup_macros.py resolves robocasa.__path__[0]
    # to the repo ROOT (/robocasa) under an editable install, but macros.py
    # actually lives at /robocasa/robocasa/macros.py -- so copy it ourselves
    # next to the real macros.py (where robocasa imports macros_private from).
    .run_commands(
        'python -c "import robocasa, os, shutil, glob; '
        "b=robocasa.__path__[0]; "
        "cands=[os.path.join(b,'macros.py'), os.path.join(b,'robocasa','macros.py')]; "
        "cands+=glob.glob('/robocasa/**/macros.py', recursive=True); "
        "src=next(p for p in cands if os.path.exists(p)); "
        "[shutil.copyfile(src, os.path.join(os.path.dirname(p),'macros_private.py')) "
        " for p in cands if os.path.isdir(os.path.dirname(p))]; "
        "print('copied macros_private from', src)\"",
    )
    # NOTE: asset download moved to a runtime step (see download_assets fn) so we
    # can resolve robocasa.__path__ at run time and target the correct tree.
    .env({
        "MUJOCO_GL": "egl",
        "NVIDIA_DRIVER_CAPABILITIES": "all",
        "HF_HOME": "/cache/hf",
    })
)


@app.function(image=img, timeout=300)
def diag():
    import robocasa, os, subprocess
    p = robocasa.__path__[0]
    out = {
        "robocasa.__path__": list(robocasa.__path__),
        "robocasa.__file__": getattr(robocasa, "__file__", None),
        "listdir(path[0])": sorted(os.listdir(p))[:50],
        "exists models/assets/box_links (at path[0])":
            os.path.exists(os.path.join(p, "models", "assets", "box_links", "box_links_assets.json")),
        "find box_links_assets.json":
            subprocess.run(["find", "/robocasa", "-name", "box_links_assets.json"],
                           capture_output=True, text=True).stdout,
        "find models/assets dir":
            subprocess.run(["bash", "-lc", "ls -d /robocasa/**/models/assets 2>/dev/null; ls -d /robocasa/models/assets 2>/dev/null"],
                           capture_output=True, text=True).stdout,
    }
    return out


@app.local_entrypoint()
def run_diag():
    import json
    print(json.dumps(diag.remote(), indent=2))


@app.function(
    gpu="A10G",
    image=img,
    timeout=3600,
    volumes={"/cache": cache},
)
def run_eval(task: str = "CloseFridge", n_episodes: int = 6):
    """Run the eval and PERSIST results (eval_info.json + videos) into the
    /cache Volume under /cache/eval_out so artifacts survive even if the local
    CLI detaches. Output is streamed (not captured) so progress is visible."""
    import json
    import shutil
    import subprocess
    from pathlib import Path

    # Download the LIGHTWEIGHT kitchen assets at runtime (path resolves
    # correctly here, unlike during image build). The robocasa download script
    # is interactive (asks Y/n), so feed it "y".
    subprocess.run(
        ["python", "-m", "robocasa.scripts.download_kitchen_assets",
         "--type", "tex", "tex_generative", "fixtures_lw", "objs_lw"],
        input="y\ny\ny\ny\ny\n", text=True,
    )
    print("=== ASSET DOWNLOAD DONE ===", flush=True)

    out_dir = Path("/tmp/eval_out")
    rename_map = (
        '{"observation.images.robot0_agentview_left": "observation.images.camera1", '
        '"observation.images.robot0_eye_in_hand": "observation.images.camera2", '
        '"observation.images.robot0_agentview_right": "observation.images.camera3"}'
    )
    cmd = [
        "lerobot-eval",
        "--policy.path=lerobot/smolvla_robocasa",
        "--env.type=robocasa",
        f"--env.task={task}",
        "--eval.batch_size=1",
        f"--eval.n_episodes={n_episodes}",
        "--eval.use_async_envs=false",
        "--policy.device=cuda",
        f"--output_dir={out_dir}",
        f"--rename_map={rename_map}",
    ]
    print("RUNNING:", " ".join(cmd), flush=True)
    # Stream stdout/stderr so we can watch episode progress live.
    proc = subprocess.run(cmd)
    print("=== EVAL RETURNCODE:", proc.returncode, "===", flush=True)

    # Persist everything to the Volume.
    persist = Path("/cache/eval_out")
    if persist.exists():
        shutil.rmtree(persist)
    if out_dir.exists():
        shutil.copytree(out_dir, persist)
    cache.commit()

    info_path = out_dir / "eval_info.json"
    if info_path.exists():
        info = json.loads(info_path.read_text())
        print("AGGREGATED:", info.get("aggregated", {}), flush=True)
        for e in info.get("per_episode", []):
            print(f"  ep {e.get('episode_ix')}: success={e.get('success')} "
                  f"sum_reward={e.get('sum_reward')} seed={e.get('seed')}", flush=True)
    else:
        print("eval_info.json NOT FOUND", flush=True)
        print(subprocess.run(["find", str(out_dir), "-maxdepth", "3"],
                             capture_output=True, text=True).stdout, flush=True)
    return proc.returncode


@app.function(image=img, timeout=300, volumes={"/cache": cache})
def fetch_results():
    """Read persisted eval results from the Volume and pick a SUCCESS + FAILURE
    episode video. Handles lerobot 0.5.2 schema where eval_info.json has
    per_task[].metrics.{successes, video_paths} aligned by index, and videos
    live in a nested videos/<task>_<id>/eval_episode_<n>.mp4 layout."""
    import json
    from pathlib import Path

    cache.reload()
    persist = Path("/cache/eval_out")
    info_path = persist / "eval_info.json"
    result = {}
    if not info_path.exists():
        result["error"] = "no persisted eval_info.json"
        return result

    info = json.loads(info_path.read_text())

    # Build (success_flag -> list of absolute video paths) from per_task metrics.
    pairs = []  # (success: bool, abs_path: Path)
    for task in info.get("per_task", []):
        m = task.get("metrics", {})
        succ = m.get("successes", [])
        vids = m.get("video_paths", [])
        for s, vp in zip(succ, vids):
            # vp is like /tmp/eval_out/videos/CloseFridge_0/eval_episode_0.mp4
            rel = Path(vp)
            try:
                rel = rel.relative_to("/tmp/eval_out")
            except ValueError:
                rel = Path(*rel.parts[rel.parts.index("videos"):]) if "videos" in rel.parts else rel
            pairs.append((bool(s), persist / rel))

    # Fallback: if no per_task, just glob all videos and mark unknown.
    if not pairs:
        for v in sorted(persist.glob("videos/**/*.mp4")):
            pairs.append((None, v))

    result["summary"] = [
        {"success": s, "path": str(p), "exists": p.exists()} for s, p in pairs
    ]
    result["overall"] = info.get("overall", info.get("aggregated", {}))

    def read(p):
        return p.read_bytes() if p and p.exists() else None

    succ_path = next((p for s, p in pairs if s and p.exists()), None)
    fail_path = next((p for s, p in pairs if s is False and p.exists()), None)
    # If success flags are unknown, leave success empty (we won't fabricate).
    result["success_path"] = str(succ_path) if succ_path else None
    result["failure_path"] = str(fail_path) if fail_path else None
    result["success_mp4"] = read(succ_path)
    result["failure_mp4"] = read(fail_path)
    return result


@app.function(image=img, timeout=300, volumes={"/cache": cache})
def fetch_episode(idx: int = 0):
    """Return the mp4 bytes + success flag for a specific episode index from the
    persisted eval (whatever task is currently in the Volume)."""
    import json
    from pathlib import Path
    cache.reload()
    persist = Path("/cache/eval_out")
    info = json.loads((persist / "eval_info.json").read_text())
    for task in info.get("per_task", []):
        m = task.get("metrics", {})
        for i, (s, vp) in enumerate(zip(m.get("successes", []), m.get("video_paths", []))):
            if i == idx:
                rel = Path(vp)
                try:
                    rel = rel.relative_to("/tmp/eval_out")
                except ValueError:
                    pass
                p = persist / rel
                return {"idx": idx, "success": bool(s), "task": task.get("task_group"),
                        "mp4": p.read_bytes() if p.exists() else None}
    return {"idx": idx, "error": "not found"}


@app.local_entrypoint()
def fetch_two():
    """Write two distinct REAL policy-rollout clips (episodes 0 and 1) from the
    Volume to clip_a.mp4 / clip_b.mp4, labeling each by its real success flag."""
    import os
    out_root = "taco_demo/data/videos/incoming/kitchen_modal"
    os.makedirs(out_root, exist_ok=True)
    for idx, name in [(0, "clip_a.mp4"), (1, "clip_b.mp4")]:
        r = fetch_episode.remote(idx=idx)
        print(f"episode {idx}: task={r.get('task')} success={r.get('success')}")
        data = r.get("mp4")
        if data:
            p = os.path.join(out_root, name)
            open(p, "wb").write(data)
            print(f"WROTE {p} ({len(data)} bytes)")
        else:
            print(f"NO data for episode {idx}: {r.get('error')}")


@app.local_entrypoint()
def main(task: str = "CloseFridge", n_episodes: int = 6):
    rc = run_eval.remote(task=task, n_episodes=n_episodes)
    print("eval returncode:", rc)
    fetch()


@app.local_entrypoint()
def fetch():
    """Pull persisted results from the Volume and write success/failure mp4s."""
    import os
    r = fetch_results.remote()
    if r.get("error"):
        print("ERROR:", r["error"])
        return
    print("overall:", r.get("overall"))
    for s in r.get("summary", []):
        print(f"  success={s['success']} exists={s['exists']} {s['path']}")
    print("success_path:", r.get("success_path"))
    print("failure_path:", r.get("failure_path"))

    out_root = "taco_demo/data/videos/incoming/kitchen_modal"
    os.makedirs(out_root, exist_ok=True)
    for key, name in [("success_mp4", "success.mp4"), ("failure_mp4", "failure.mp4")]:
        data = r.get(key)
        if data:
            p = os.path.join(out_root, name)
            open(p, "wb").write(data)
            print(f"WROTE {p} ({len(data)} bytes)")
        else:
            print(f"NO {name} available")
