import glob, os, shutil, sys, json
d, out, mode = sys.argv[1], sys.argv[2], sys.argv[3]  # mode: best|worst
vids = sorted(glob.glob(os.path.join(d, "*.mp4")),
              key=lambda p: int(os.path.basename(p).split('.')[0]) if os.path.basename(p).split('.')[0].isdigit() else 999)
try:
    eps = json.load(open(os.path.join(d, "trajectory.json")))["episodes"]
except Exception as e:
    if vids: shutil.copy(vids[0], out)
    print("NO_TRAJ copied", os.path.basename(vids[0]) if vids else "none"); sys.exit(0)
def score(e):
    if "success" in e: return (1 if e["success"] else 0, e.get("return", e.get("elapsed_steps", 0)))
    return (0, e.get("return", e.get("reward", e.get("elapsed_steps", 0))))
order = sorted(range(len(eps)), key=lambda i: score(eps[i]), reverse=(mode == "best"))
i = order[0]
src = vids[i] if i < len(vids) else vids[0]
shutil.copy(src, out)
print(f"{mode}: ep{i} score={score(eps[i])} keys={list(eps[0].keys())} | returns={[round(float(score(e)[1]),1) for e in eps][:8]}")
