set -u
source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma
export MS_ASSET_DIR=/work/joy/maniskill_data
cd /work/joy/ManiSkill/examples/baselines/ppo
mkdir -p /work/joy/taco_render_out
ENV=$1; TAG=$2; STEPS=$3
echo "===== TRAIN $ENV gamma=0.99 steps=$STEPS ====="
yes | python ppo.py --env_id=$ENV --num_envs=1024 --update_epochs=8 --num_minibatches=32 \
  --total_timesteps=$STEPS --num-steps=200 --num-eval-steps=200 --gamma=0.99 --gae_lambda=0.95 \
  --capture_video --save_model --exp_name=$TAG 2>&1 | grep -iE "eval_success_once_mean|Epoch: 1,|model saved" | tail -25
best=$(ls runs/$TAG/ckpt_*.pt 2>/dev/null | sed 's/.*ckpt_//;s/\.pt//' | sort -n | tail -1)
best="runs/$TAG/ckpt_${best}.pt"
echo "[$TAG] best=$best"
yes | python ppo.py --evaluate --checkpoint=$best --env_id=$ENV --capture_video --num_eval_envs=16 --num-eval-steps=350 2>&1 | grep -iE "success_once|Evaluated" | tail -2
python - "$best" <<'PY'
import json,sys,os
f=os.path.join(os.path.dirname(sys.argv[1]),"test_videos","trajectory.json")
try:
  e=json.load(open(f))["episodes"]; n=sum(1 for x in e if x["success"]); print(f"REAL_SUCC {n}/{len(e)}")
except Exception as ex: print("REAL_SUCC 0/0",ex)
PY
cp "$(dirname $best)/test_videos/0.mp4" /work/joy/taco_render_out/${TAG}_success.mp4 2>/dev/null && echo "[$TAG] success clip copied"
yes | python ppo.py --evaluate --checkpoint=runs/$TAG/ckpt_1.pt --env_id=$ENV --capture_video --num_eval_envs=16 --num-eval-steps=350 >/dev/null 2>&1
cp runs/$TAG/test_videos/0.mp4 /work/joy/taco_render_out/${TAG}_fail.mp4 2>/dev/null && echo "[$TAG] fail clip copied"
echo "${TAG}_DONE"
