set -u
source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma
export MS_ASSET_DIR=/work/joy/maniskill_data
cd /work/joy/ManiSkill/examples/baselines/ppo
mkdir -p /work/joy/probe
run(){ TAG=$1; ENV=$2; NS=$3
  nums=$(ls runs/$TAG/ckpt_*.pt | sed 's/.*ckpt_//;s/\.pt//' | sort -n); n=$(echo "$nums"|wc -l)
  best=$(echo "$nums"|tail -1); ei=$(( n/5 )); [ $ei -lt 2 ] && ei=2; early=$(echo "$nums"|sed -n "${ei}p")
  for ck in $best $early; do
    rm -rf runs/$TAG/test_videos
    yes | python ppo_capture.py --evaluate --checkpoint=runs/$TAG/ckpt_${ck}.pt --env_id="$ENV" --num_eval_envs=8 --num-eval-steps=$NS >/dev/null 2>&1 || true
    cp runs/$TAG/test_videos/activations.npz /work/joy/probe/${TAG}_${ck}.npz 2>/dev/null
  done
  python /work/joy/probe_fit.py /work/joy/probe/${TAG}_${best}.npz /work/joy/probe/${TAG}_${early}.npz $TAG 2>/dev/null
}
run ckpick2 PickCube-v1 100
run ckpoke PokeCube-v1 100
run taco_stackcube StackCube-v1 100
run taco_pullcube PullCube-v1 100
run ckanymal3 AnymalC-Reach-v1 200
run ckgo23 UnitreeGo2-Reach-v1 200
run hum_g1box UnitreeG1TransportBox-v1 100
run dog_spin AnymalC-Spin-v1 200
echo PROBE_ALL_DONE
