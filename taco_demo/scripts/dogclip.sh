set -u
source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma
export MS_ASSET_DIR=/work/joy/maniskill_data
cd /work/joy/ManiSkill/examples/baselines/ppo
mkdir -p /work/joy/taco_render_out
TAG=$1; ENV=$2
nums=$(ls runs/$TAG/ckpt_*.pt 2>/dev/null | sed 's/.*ckpt_//;s/\.pt//' | sort -n)
best=$(echo "$nums" | tail -1)
# pick a MID checkpoint (moves but lower success) for the failure clip
mid=$(echo "$nums" | awk 'NR>1' | head -1); midmid=$(echo "$nums" | awk '{a[NR]=$0} END{print a[int(NR/2)]}')
echo "[$TAG] ckpts: $nums | best=$best mid=$midmid"
pick(){ ck=$1; out=$2; want=$3   # want: succ|fail
  rm -rf "$(dirname $ck)/test_videos"
  yes | python ppo.py --evaluate --checkpoint=$ck --env_id=$ENV --capture_video --num_eval_envs=1 --num-eval-steps=1400 >/dev/null 2>&1 || true
  python - "$ck" "$out" "$want" <<'PY'
import json,sys,os,shutil,glob
d=os.path.join(os.path.dirname(sys.argv[1]),"test_videos"); out=sys.argv[2]; want=sys.argv[3]
eps=json.load(open(os.path.join(d,"trajectory.json")))["episodes"]
vids=sorted(glob.glob(os.path.join(d,"*.mp4")), key=lambda p:(int(os.path.basename(p).split('.')[0]) if os.path.basename(p).split('.')[0].isdigit() else 999))
target=True if want=="succ" else False
# prefer an episode that ran long enough to show motion (elapsed_steps high) AND matches want
cand=[i for i,e in enumerate(eps) if e["success"]==target]
if not cand: cand=list(range(len(eps)))
idx=max(cand, key=lambda i: eps[i].get("elapsed_steps",0))
src=vids[idx] if idx<len(vids) else vids[0]
shutil.copy(src,out); print(f"{out} <- ep{idx} success={eps[idx]['success']} steps={eps[idx].get('elapsed_steps')} ({sum(e['success'] for e in eps)}/{len(eps)} succ)")
PY
}
pick runs/$TAG/ckpt_${best}.pt /work/joy/taco_render_out/${TAG}_succ_single.mp4 succ
pick runs/$TAG/ckpt_${midmid}.pt /work/joy/taco_render_out/${TAG}_fail_single.mp4 fail
echo "${TAG}_CLIP2_DONE"
