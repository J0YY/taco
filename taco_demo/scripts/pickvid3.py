import glob, os, shutil, sys, json
d, out, mode = sys.argv[1], sys.argv[2], sys.argv[3]
vids = sorted(glob.glob(os.path.join(d, "*.mp4")),
              key=lambda p: int(os.path.basename(p).split('.')[0]) if os.path.basename(p).split('.')[0].isdigit() else 999)
try: eps = json.load(open(os.path.join(d, "trajectory.json")))["episodes"]
except Exception:
    if vids: shutil.copy(vids[0], out); print("NO_TRAJ", os.path.basename(vids[0]) if vids else "none"); sys.exit(0)
def ok(e):  # higher = better/working
    if "success" in e: return 1 if e["success"] else 0
    if "fail" in e: return 0 if e["fail"] else 1
    return 0
def score(e): return (ok(e), e.get("elapsed_steps", 0))
order = sorted(range(len(eps)), key=lambda i: score(eps[i]), reverse=(mode == "best"))
i = order[0]; src = vids[i] if i < len(vids) else vids[0]
shutil.copy(src, out)
print(f"{mode}: ep{i} ok={ok(eps[i])} steps={eps[i].get('elapsed_steps')} | ok_vals={[ok(e) for e in eps]}")
