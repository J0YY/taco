set -u
source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma
export MS_ASSET_DIR=/work/joy/maniskill_data
cd /work/joy/ManiSkill/examples/baselines/ppo
mkdir -p /work/joy/taco_render_out
TAG="$1"; ENV="$2"; NS="${3:-300}"
nums=$(ls runs/$TAG/ckpt_*.pt 2>/dev/null | sed 's/.*ckpt_//;s/\.pt//' | sort -n)
n=$(echo "$nums" | wc -l); best=$(echo "$nums" | tail -1)
eidx=$(( n/5 )); [ $eidx -lt 2 ] && eidx=2; early=$(echo "$nums" | sed -n "${eidx}p")
echo "[$TAG] n=$n best=$best early=$early"
clip(){ rm -rf runs/$TAG/test_videos
  yes | python ppo.py --evaluate --checkpoint=runs/$TAG/ckpt_${1}.pt --env_id="$ENV" --capture_video --num_eval_envs=1 --num-eval-steps=$NS >/dev/null 2>&1 || true
  python /work/joy/pickvid.py "runs/$TAG/test_videos" "$2"; }
clip $best /work/joy/taco_render_out/${TAG}_succ.mp4
clip $early /work/joy/taco_render_out/${TAG}_fail.mp4
echo "${TAG}_RDONE"
