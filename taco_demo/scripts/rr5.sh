set -u
source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma
export MS_ASSET_DIR=/work/joy/maniskill_data
cd /work/joy/ManiSkill/examples/baselines/ppo
TAG="$1"; ENV="$2"; NS="${3:-800}"
nums=$(ls runs/$TAG/ckpt_*.pt 2>/dev/null | sed 's/.*ckpt_//;s/\.pt//' | sort -n)
n=$(echo "$nums" | wc -l); best=$(echo "$nums" | tail -1)
eidx=$(( n/6 )); [ $eidx -lt 2 ] && eidx=2; early=$(echo "$nums" | sed -n "${eidx}p")
echo "[$TAG] n=$n best=$best early=$early"
ev(){ rm -rf runs/$TAG/test_videos; yes | python ppo.py --evaluate --checkpoint=runs/$TAG/ckpt_${1}.pt --env_id="$ENV" --capture_video --num_eval_envs=1 --num-eval-steps=$NS >/dev/null 2>&1 || true; }
ev $best;  python /work/joy/pickvid3.py runs/$TAG/test_videos /work/joy/taco_render_out/${TAG}_succ.mp4 best
ev $early; python /work/joy/pickvid3.py runs/$TAG/test_videos /work/joy/taco_render_out/${TAG}_fail.mp4 worst
echo "${TAG}_R5DONE"
