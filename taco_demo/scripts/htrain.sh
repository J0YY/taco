set -u
source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma
export MS_ASSET_DIR=/work/joy/maniskill_data
cd /work/joy/ManiSkill/examples/baselines/ppo
mkdir -p /work/joy/taco_render_out
ENV="$1"; TAG="$2"; STEPS="$3"; NS="$4"; NE="$5"; EXTRA="$6"
echo "===== TRAIN $ENV tag=$TAG steps=$STEPS extra=$EXTRA ====="
yes | python ppo.py --env_id="$ENV" --num_envs=1024 --update_epochs=8 --num_minibatches=32 \
  --total_timesteps=$STEPS --num-steps=$NS --num-eval-steps=$NE $EXTRA \
  --capture_video --save_model --exp_name=$TAG 2>&1 | grep -iE "eval_success_once_mean|model saved" | tail -30
nums=$(ls runs/$TAG/ckpt_*.pt 2>/dev/null | sed 's/.*ckpt_//;s/\.pt//' | sort -n)
n=$(echo "$nums" | wc -l); best=$(echo "$nums" | tail -1)
# early-but-moving checkpoint for the failure clip: ~1/4 through
fidx=$(( n/4 )); [ $fidx -lt 2 ] && fidx=2
failck=$(echo "$nums" | sed -n "${fidx}p")
echo "[$TAG] ckpts=$n best=$best failck=$failck"
clip(){ ck=$1; out=$2; want=$3
  rm -rf runs/$TAG/test_videos
  yes | python ppo.py --evaluate --checkpoint=runs/$TAG/ckpt_${ck}.pt --env_id="$ENV" --capture_video --num_eval_envs=1 --num-eval-steps=$(( NS*8 )) >/dev/null 2>&1 || true
  python - "$TAG" "$out" "$want" <<'PY'
import json,glob,os,shutil,sys
tag,out,want=sys.argv[1],sys.argv[2],sys.argv[3]; d=f"runs/{tag}/test_videos"
try:
  eps=json.load(open(d+"/trajectory.json"))["episodes"]
  tgt= want=="succ"
  cand=[i for i,e in enumerate(eps) if e["success"]==tgt] or list(range(len(eps)))
  i=max(cand,key=lambda i:eps[i].get("elapsed_steps",0))
  vids=sorted(glob.glob(d+"/*.mp4"),key=lambda p:int(os.path.basename(p).split('.')[0]) if os.path.basename(p).split('.')[0].isdigit() else 999)
  shutil.copy(vids[i],out); print(f"{want}: ep{i} success={eps[i]['success']} steps={eps[i].get('elapsed_steps')} | {sum(e['success'] for e in eps)}/{len(eps)} succ")
except Exception as ex: print("ERR",want,ex)
PY
}
clip $best /work/joy/taco_render_out/${TAG}_succ.mp4 succ
clip $failck /work/joy/taco_render_out/${TAG}_fail.mp4 fail
echo "${TAG}_HDONE"
