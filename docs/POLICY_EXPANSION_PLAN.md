# TACO Policy-Expansion Plan — diverse embodiments, force failures, interpret, price

Goal: extend the TACO pipeline (download policy → force failure in sim → mechanistically
interpret → patch → price → add as a guided-flow policy card) to a wide range of robots:
robot dogs, home/kitchen robots, humanoids, wheeled humanoids. Researched June 2026.

## Ranked embodiment roadmap

| # | Embodiment | Open policy (downloadable?) | Sim | Force failure | Mech-interp | License |
|---|---|---|---|---|---|---|
| 1 | **Quadruped (robot dog)** | AnymalC / UnitreeGo2 PPO — **TRAIN** (no ckpt) | **ManiSkill3** (installed) | push / obs-noise / terrain → **fall** | probe the small PPO MLP | Apache |
| 2 | **Home kitchen** | `lerobot/smolvla_robocasa` — **DOWNLOAD** | RoboCasa (robosuite/MuJoCo) | object/scene-style swap, `composite_unseen` | SAE on SmolVLA residual stream | MIT/Apache/CC-BY |
| 3 | **Humanoid (bipedal)** | Unitree G1/H1 locomotion — **DOWNLOAD** (Unitree `unitree_rl_gym` `motion.pt`; luckyrobots ONNX) | MuJoCo / Isaac Gym; ManiSkill3 has G1/H1 assets | push / velocity-OOD → **fall** | probe the small RL MLP | BSD-3 / Apache |
| 4 | **Manipulation VLA (SAE-proven)** | `openvla/openvla-7b` (+LIBERO finetunes) — **DOWNLOAD** | SimplerEnv (ManiSkill2/SAPIEN) | Visual-Matching / Variant-Aggregation | SAE on residual stream | **MIT** |
| 5 | **Mobile-manip rearrangement** | MS-HAB `policy.pt` (pick/place/open/close) — **DOWNLOAD** | ManiSkill3 (`mshab` branch) | object/pose perturb, clutter | probes / SAE | Apache |
| 6 | **Humanoid foundation VLA (headline)** | **GR00T N1.7** (`nvidia/GR00T-N1.7-3B`) — **DOWNLOAD** | SimplerEnv / RoboCasa; GEAR-SONIC WBC (MuJoCo) for falls | OOD instruction/vision; push for WBC | SAE on VLM backbone | **Apache (N1.7)** |
| 7 | **Wheeled humanoid** | Galaxea `G0-VLA` — DOWNLOAD | real-data (weak sim) | — | SAE | ⚠ **CC BY-NC-SA (non-commercial)** |

### License guardrails (for a commercial-facing demo)
- ✅ Safe: ManiSkill3/SimplerEnv (Apache), OpenVLA (MIT), RoboCasa code (MIT)+assets (CC-BY), SmolVLA/LeRobot (Apache), Unitree RL (BSD-3), GR00T **N1.7** (Apache), RDT-1B (MIT).
- 🚫 Avoid: **GR00T N1.5 / N1 (NVIDIA non-commercial)**, **Galaxea G0 (CC BY-NC-SA)**, π0/π0.5 weights inherit **Gemma terms** (check before commercial use).

## Spike A — Robot dog (ManiSkill quadruped) — recommended first, uses existing infra

Grounded on the cluster: `mani_skill 3.0.0b22` in conda env `rma`; robots `anymal, unitree_go, unitree_g1, unitree_h1`; tasks `quadruped_reach` (AnymalC-Reach-v1, UnitreeGo2-Reach-v1), `quadruped_spin` (AnymalC-Spin-v1). Success = within 0.35 m of goal; **FAIL = body hits the ground (fall)**. No pretrained checkpoints → train PPO (fast).

**Step 0 (verify, no GPU):** confirm the ManiSkill PPO baseline. Either clone `haosulab/ManiSkill` `examples/baselines/ppo/ppo.py`, or reuse `/users/joy/cotracker-rma/ppo.py` (takes `--env_id`; built for RMA tasks, so prefer upstream for a stock env).

**Step 1 — train (athena GPU, via `~/remote_srun.sh`):**
```bash
python ppo.py --env_id=AnymalC-Reach-v1 --num_envs=1024 \
  --update_epochs=8 --num_minibatches=32 --total_timesteps=25_000_000 \
  --num-steps=200 --num-eval-steps=200 --gamma=0.99 --gae_lambda=0.95
```
(UnitreeGo2-Reach-v1 ≈ 50M steps.)

**Step 2 — eval + record success/failure video:**
```bash
python ppo.py --env_id=AnymalC-Reach-v1 --evaluate --checkpoint=runs/<run>/final_ckpt.pt \
  --num_eval_envs=1 --num-eval-steps=1000   # writes runs/<run>/test_videos/
```

**Step 3 — force failures (new DreamAudit perturbation family "locomotion"):** at eval, enable obs noise / external push / terrain / mass-friction randomization (quadruped env kwargs) so the dog falls; record the neighborhood failure rate (fraction of envs that fall).

**Step 4 — mechanistic interpretation:** the policy is a small actor MLP (obs→joint targets). Record hidden activations; train **linear probes** for "about-to-fall" / CoM-velocity / contact-state. Probe firing before the fall = the early-warning signal (no SAE needed). (Note: humanoid/quadruped policy mech-interp is genuine whitespace — Swann et al. only did VLAs.)

**Step 5 — patch + price:** required control = recovery/geofence monitor triggered by the about-to-fall probe; TACO prices premium with/without it. Add as a new guided-flow policy card (success vs fall video + locomotion certificate + probe early-warning + price).

## Spike B — Home kitchen (RoboCasa + SmolVLA) — most "robot people have at home", downloadable

```bash
# install RoboCasa (robosuite/MuJoCo; not pip-installable — editable clone + kitchen assets)
lerobot-eval --policy.path=lerobot/smolvla_robocasa \
  --env.type=robocasa --env.task=CloseFridge --eval.n_episodes=20
```
Force failure: swap object registry / scene style / use `composite_unseen` task group → OOD failures; success is binary per task. Mech-interp: SmolVLA is a transformer VLA → reuse the sae-scope (Dr. VLA) SAE-on-residual-stream pipeline. Caveat: ManiSkill3 ingests RoboCasa *scenes* but not the kitchen *task suite* — use RoboCasa-on-robosuite for the policy eval. Asset pack ~30 GB.

## Spike C — Humanoid fall (Unitree G1/H1) — crisp downloadable fall failure
Use Unitree `unitree_rl_gym` pretrained `deploy/pre_train/{g1,h1}/motion.pt` (BSD-3) or luckyrobots ONNX walker; run in MuJoCo; push/velocity-OOD → fall; probe the MLP. ManiSkill3 also has `UnitreeG1Stand-v1`/`UnitreeH1Stand-v1` (train-only).

## Spike D — Foundation-VLA headline
GR00T **N1.7** (Apache, commercial) SAE on the VLM backbone for a humanoid VLA story, or OpenVLA-7B (MIT) on SimplerEnv (best-documented SAE target). RLinf OpenVLA-PPO-ManiSkill3-25ood is a ~15 GB downloadable policy with a documented 25-way OOD failure profile (vision/semantic/position).

## How each becomes a TACO artifact
Per policy: nominal-success video + forced-failure video (+ mitigated if a patch exists) → a failure certificate (perturbation + minimal cost + neighborhood rate) → mechanistic evidence (probe or SAE feature + early-warning lead) → required control + price → a new policy card in `guided_flow.POLICIES`/`EXHIBITS` and the Real Cross-Policy Evidence tab.

## Key sources
- ManiSkill3 — https://arxiv.org/abs/2410.00425 · quadruped tasks https://maniskill.readthedocs.io/en/latest/tasks/quadruped/ · PPO baselines https://github.com/haosulab/ManiSkill/blob/main/examples/baselines/ppo/
- MS-HAB checkpoints — https://huggingface.co/arth-shukla/mshab_checkpoints
- RLinf OpenVLA-PPO-ManiSkill3-25ood — https://huggingface.co/RLinf/RLinf-OpenVLA-PPO-ManiSkill3-25ood
- SimplerEnv (+OpenVLA fork) — https://github.com/DelinQu/SimplerEnv-OpenVLA
- RoboCasa — https://github.com/robocasa/robocasa · SmolVLA https://huggingface.co/lerobot/smolvla_robocasa
- Unitree RL — https://github.com/unitreerobotics/unitree_rl_gym · MuJoCo Playground https://github.com/google-deepmind/mujoco_playground
- GR00T N1.7 (Apache) — https://huggingface.co/blog/nvidia/gr00t-n1-7 ; GEAR-SONIC https://github.com/NVlabs/GR00T-WholeBodyControl
- SAE-on-VLA (mech-interp basis) — https://arxiv.org/abs/2603.19183 · https://drvla.github.io
