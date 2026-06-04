"""Render a REAL LIBERO kitchen-task rollout on Modal using a downloadable
LeRobot LIBERO policy via lerobot-eval.

LIBERO is robosuite/MuJoCo based, so it renders headless via EGL on Modal
(SAPIEN/Vulkan does not work here; MuJoCo/EGL does). We eval N episodes,
parse the per-episode success flags from eval_info.json, and return the
rendered eval_episode_*.mp4 for one SUCCESS and one FAILURE episode.

LIBERO is a valid lerobot env type (--env.type=libero). Policy: lerobot/pi0_libero
(falls back configurable). Task suite: libero_goal contains kitchen scenes such as
"put the bowl on the stove" / "turn on the stove" / "put the wine bottle on the rack".
"""
import modal

app = modal.App("taco-libero-kitchen")

# Persistent cache for HF model/policy downloads + eval artifacts across retries.
cache = modal.Volume.from_name("taco-hf-cache", create_if_missing=True)

img = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install(
        "libegl1", "libgl1", "libopengl0", "libglib2.0-0", "libosmesa6",
        "ffmpeg", "git", "wget", "build-essential", "cmake",
    )
    # egl_probe (pulled by robomimic/robosuite) builds a CMake extension whose
    # CMakeLists requires CMake <3.5 compat; modern cmake refuses unless told.
    .env({"CMAKE_POLICY_VERSION_MINIMUM": "3.5"})
    # lerobot from git main (LIBERO env support / latest policies). The
    # [pi0] / [smolvla] extras pull transformers/accelerate to load the VLA.
    .pip_install("lerobot[pi0,smolvla] @ git+https://github.com/huggingface/lerobot.git@main")
    # LIBERO package. The PyPI/git wheel ships only dist-info (no importable
    # `libero/` tree), so clone and install EDITABLE so `import libero` works
    # and its bundled bddl_files / init_states / assets are on disk.
    .pip_install(
        "bddl", "robosuite==1.4.1", "av", "imageio[ffmpeg]",
        "numpy", "opencv-python", "easydict", "thop", "hydra-core",
        "robomimic", "cloudpickle",
        # LIBERO's envs/venv.py imports the LEGACY `gym` (not gymnasium) via
        # tianshou's vector-env shim; install it so OffScreenRenderEnv imports.
        "gym==0.25.2",
    )
    .run_commands(
        "git clone --depth 1 https://github.com/Lifelong-Robot-Learning/LIBERO.git /LIBERO",
        "pip install -e /LIBERO --no-deps",
        # configure robosuite private macros (silences warning, sets img conv)
        "python /usr/local/lib/python3.12/site-packages/robosuite/scripts/setup_macros.py || true",
        # drop a .pth pointing at the repo root so the
        # top-level `libero` package dir is importable (the editable finder
        # alone does not expose it).
        "python -c \"import site,os; p=site.getsitepackages()[0]; open(os.path.join(p,'libero_repo.pth'),'w').write('/LIBERO\\n'); print('wrote pth to', p)\"",
        # LIBERO's libero/libero/__init__.py PROMPTS interactively on first
        # import to create ~/.libero/config.yaml. Pre-write the config so the
        # import is fully non-interactive. Paths point at the repo's bundled
        # bddl_files / init_files / assets, and a /cache datasets dir.
        "mkdir -p /root/.libero /root/libero_datasets",
        "python - <<'PY'\n"
        "import os, yaml\n"
        "base='/LIBERO/libero/libero'\n"
        "cfg={'benchmark_root': base,\n"
        "     'bddl_files': os.path.join(base,'bddl_files'),\n"
        "     'init_states': os.path.join(base,'init_files'),\n"
        "     'datasets': '/root/libero_datasets',\n"
        "     'assets': os.path.join(base,'assets')}\n"
        "os.makedirs('/root/.libero', exist_ok=True)\n"
        "yaml.safe_dump(cfg, open('/root/.libero/config.yaml','w'))\n"
        "print('wrote config', cfg)\n"
        "PY",
        "python -c 'import libero; from libero.libero import benchmark; print(\"LIBERO OK\", list(benchmark.get_benchmark_dict().keys()))'",
    )
    .env({
        "MUJOCO_GL": "egl",
        "PYOPENGL_PLATFORM": "egl",
        "NVIDIA_DRIVER_CAPABILITIES": "all",
        "HF_HOME": "/cache/hf",
        "TOKENIZERS_PARALLELISM": "false",
    })
)


@app.function(image=img, timeout=600, volumes={"/cache": cache})
def diag():
    """Inspect lerobot's built-in LIBERO task suites to find kitchen tasks."""
    import json
    out = {}
    # List each suite's tasks with id + language goal so we can pick a kitchen one.
    try:
        from libero.libero import benchmark
        bm = benchmark.get_benchmark_dict()
        out["benchmarks"] = list(bm.keys())
        suites = {}
        for name in bm:
            try:
                b = bm[name]()
                suites[name] = [
                    {"id": i, "name": b.get_task(i).name,
                     "goal": b.get_task(i).language}
                    for i in range(b.n_tasks)
                ]
            except Exception as e:  # noqa
                suites[name] = f"ERR: {e}"
        out["suites"] = suites
    except Exception as e:  # noqa
        out["libero_import_error"] = repr(e)
    return out


@app.local_entrypoint()
def run_diag():
    import json
    print(json.dumps(diag.remote(), indent=2, default=str))


@app.function(
    gpu="A10G",
    image=img,
    timeout=3600,
    volumes={"/cache": cache},
    # pi0_libero pulls the GATED google/paligemma-3b-pt-224 tokenizer; provide
    # an HF token that has access (set up via `modal secret create`).
    secrets=[modal.Secret.from_name("huggingface-token")],
)
def run_eval(
    policy: str = "lerobot/pi05_libero_finetuned",
    task_suite: str = "libero_goal",
    task_ids: str = "",
    n_episodes: int = 10,
    n_action_steps: int = 10,
):
    """Run lerobot-eval on a LIBERO kitchen task and PERSIST results
    (eval_info.json + videos) into the /cache Volume so artifacts survive
    even if the local CLI detaches. Output is streamed for live progress.

    In lerobot's LIBERO env, --env.task is the SUITE name (e.g. libero_goal)
    and --env.task_ids selects specific task indices within that suite."""
    import json
    import shutil
    import subprocess
    from pathlib import Path

    out_dir = Path("/tmp/libero_eval_out")
    if out_dir.exists():
        shutil.rmtree(out_dir)

    cmd = [
        "lerobot-eval",
        f"--policy.path={policy}",
        "--env.type=libero",
        f"--env.task={task_suite}",
        "--eval.batch_size=1",
        f"--eval.n_episodes={n_episodes}",
        "--eval.use_async_envs=false",
        "--policy.device=cuda",
        f"--policy.n_action_steps={n_action_steps}",
        "--env.max_parallel_tasks=1",
        f"--output_dir={out_dir}",
    ]
    if task_ids:
        # draccus expects list[int] syntax, e.g. --env.task_ids=[1]
        ids = task_ids if task_ids.strip().startswith("[") else f"[{task_ids}]"
        cmd.append(f"--env.task_ids={ids}")
    print("RUNNING:", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd)
    print("=== EVAL RETURNCODE:", proc.returncode, "===", flush=True)

    # Persist everything to the Volume.
    persist = Path("/cache/libero_eval_out")
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
    """Read persisted eval results and pick a SUCCESS + FAILURE rendered
    episode video. Returns dict with mp4 bytes and metadata."""
    import json
    from pathlib import Path

    cache.reload()
    persist = Path("/cache/libero_eval_out")
    info_path = persist / "eval_info.json"
    result = {}
    if not info_path.exists():
        result["error"] = "no persisted eval_info.json"
        # show what IS there for debugging
        if persist.exists():
            import subprocess
            result["tree"] = subprocess.run(
                ["find", str(persist), "-maxdepth", "3"],
                capture_output=True, text=True).stdout
        return result

    info = json.loads(info_path.read_text())

    # lerobot eval_info.json schema (current): a top-level "per_task" list of
    #   {task_group, task_id, metrics: {successes: [bool...],
    #    video_paths: [".../eval_episode_<i>.mp4"...]}}
    # Each episode's success flag aligns by index with its video_path.
    episodes = []  # list of (success: bool, video_path: Path)
    for task in info.get("per_task", []):
        m = task.get("metrics", {})
        successes = m.get("successes", [])
        vpaths = m.get("video_paths", [])
        for i, succ in enumerate(successes):
            vp = vpaths[i] if i < len(vpaths) else None
            # video_paths are absolute /tmp/... from the eval run; map to the
            # persisted copy by filename under persist/videos/<group>_<id>/.
            local = None
            if vp:
                name = Path(vp).name
                grp = f"{task.get('task_group')}_{task.get('task_id')}"
                cand = persist / "videos" / grp / name
                local = cand if cand.exists() else None
            episodes.append({"success": bool(succ), "video": local,
                             "video_name": Path(vp).name if vp else None,
                             "task_group": task.get("task_group"),
                             "task_id": task.get("task_id")})

    # Fallback: legacy per_episode schema.
    if not episodes and info.get("per_episode"):
        all_vids = {int(v.stem.split("_")[-1]): v
                    for v in persist.rglob("eval_episode_*.mp4")}
        for e in info["per_episode"]:
            idx = e.get("episode_ix")
            episodes.append({"success": bool(e.get("success")),
                             "video": all_vids.get(idx),
                             "video_name": f"eval_episode_{idx}.mp4",
                             "task_group": None, "task_id": None})

    result["overall"] = info.get("overall") or info.get("aggregated") or {}
    result["n_episodes"] = len(episodes)
    result["n_success"] = sum(1 for e in episodes if e["success"])
    result["episodes"] = [
        {"success": e["success"], "video_name": e["video_name"],
         "has_video": e["video"] is not None} for e in episodes
    ]

    succ = next((e for e in episodes if e["success"] and e["video"]), None)
    fail = next((e for e in episodes if not e["success"] and e["video"]), None)
    result["success_video_name"] = succ["video_name"] if succ else None
    result["failure_video_name"] = fail["video_name"] if fail else None
    result["success_mp4"] = succ["video"].read_bytes() if succ else None
    result["failure_mp4"] = fail["video"].read_bytes() if fail else None
    return result


@app.local_entrypoint()
def main(
    policy: str = "lerobot/pi05_libero_finetuned",
    task_suite: str = "libero_goal",
    task_ids: str = "",
    n_episodes: int = 10,
):
    rc = run_eval.remote(policy=policy, task_suite=task_suite, task_ids=task_ids,
                         n_episodes=n_episodes)
    print("eval returncode:", rc)
    fetch()


@app.local_entrypoint()
def fetch():
    """Pull persisted results from the Volume and write success/failure mp4s."""
    import os
    r = fetch_results.remote()
    if r.get("error"):
        print("ERROR:", r["error"])
        if r.get("tree"):
            print(r["tree"])
        return
    print("overall:", r.get("overall"))
    print(f"n_success={r.get('n_success')}/{r.get('n_episodes')}")
    for i, e in enumerate(r.get("episodes", [])):
        print(f"  ep {i}: success={e['success']} video={e['video_name']} "
              f"has_video={e['has_video']}")
    print("success_video:", r.get("success_video_name"),
          "failure_video:", r.get("failure_video_name"))

    out_root = "taco_demo/data/videos/incoming/kitchen_libero"
    os.makedirs(out_root, exist_ok=True)
    for key, name in [("success_mp4", "success.mp4"), ("failure_mp4", "failure.mp4")]:
        data = r.get(key)
        if data:
            p = os.path.join(out_root, name)
            open(p, "wb").write(data)
            print(f"WROTE {p} ({len(data)} bytes)")
        else:
            print(f"NO {name} available")
