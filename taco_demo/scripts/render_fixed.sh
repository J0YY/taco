set -u
source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma
export MS_ASSET_DIR=/work/joy/maniskill_data
cd /work/joy/ManiSkill/examples/baselines/ppo
mkdir -p /work/joy/taco_render_out
OUT=/work/joy/taco_render_out
realsucc(){ python - "$1" <<'PY'
import json,sys,os
f=os.path.join(os.path.dirname(sys.argv[1]),"test_videos","trajectory.json")
try:
  e=json.load(open(f))["episodes"]; n=sum(1 for x in e if x["success"]); print(f"SUCC {n}/{len(e)}")
except Exception as ex: print("SUCC 0/0", ex)
PY
}
run(){ env=$1; tag=$2; steps=$3; hs=$4
  echo "===== TRAIN $env tag=$tag steps=$steps ====="
  yes | python ppo.py --env_id=$env --num_envs=1024 --total_timesteps=$steps --num-steps=$hs --num-eval-steps=$hs --update_epochs=8 --num_minibatches=32 --capture_video --save_model --exp_name=ck${tag} 2>&1 | tail -8
  # pick latest ckpt by trailing number (basename-safe)
  best=$(ls runs/ck${tag}/ckpt_*.pt 2>/dev/null | sed 's/.*ckpt_//; s/\.pt//' | sort -n | tail -1)
  best="runs/ck${tag}/ckpt_${best}.pt"
  echo "[$tag] best=$best"
  yes | python ppo.py --evaluate --checkpoint=$best --env_id=$env --capture_video --num_eval_envs=16 --num-eval-steps=350 2>&1 | grep -iE "success_once|Evaluated" | tail -2
  s=$(realsucc "$best"); echo "[$tag] $s"
  case "$s" in "SUCC 0/"*) echo "[$tag] NO real success, skipping success clip" ;;
    *) cp "$(dirname $best)/test_videos/0.mp4" $OUT/${tag}_success.mp4 2>/dev/null && echo "[$tag] SUCCESS clip ok ($s)" ;; esac
  yes | python ppo.py --evaluate --checkpoint=runs/ck${tag}/ckpt_1.pt --env_id=$env --capture_video --num_eval_envs=16 --num-eval-steps=350 2>&1 | grep -iE "Evaluated" | tail -1
  cp runs/ck${tag}/test_videos/0.mp4 $OUT/${tag}_fail.mp4 2>/dev/null && echo "[$tag] FAIL clip ok"
}
run PokeCube-v1 poke 8000000 50
run PushT-v1 pusht 10000000 100
run PickCube-v1 pick2 6000000 50
echo FIXED_DONE
