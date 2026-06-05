import glob, os, shutil, sys, json
d, out = sys.argv[1], sys.argv[2]
vids = sorted(glob.glob(os.path.join(d, "*.mp4")), key=os.path.getsize, reverse=True)
if not vids:
    print("NO_VIDS", d); sys.exit(1)
shutil.copy(vids[0], out)
try:
    eps = json.load(open(os.path.join(d, "trajectory.json")))["episodes"]
    print("copied", os.path.basename(vids[0]), "| nvids", len(vids), "| keys", list(eps[0].keys()))
except Exception:
    print("copied", os.path.basename(vids[0]), "(no traj)")
