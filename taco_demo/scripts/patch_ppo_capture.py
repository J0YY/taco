p = "/work/joy/ManiSkill/examples/baselines/ppo/ppo.py"
src = open(p).read()
A = "    if args.checkpoint:\n        agent.load_state_dict(torch.load(args.checkpoint))\n"
A2 = A + (
'    _TACO_ACT = {}\n'
'    def _taco_hook(name):\n'
'        def h(m, i, o):\n'
'            _TACO_ACT[name] = o.detach().float().cpu().numpy()\n'
'        return h\n'
'    agent.actor_mean[1].register_forward_hook(_taco_hook("h1"))\n'
'    agent.actor_mean[3].register_forward_hook(_taco_hook("h2"))\n'
'    agent.actor_mean[5].register_forward_hook(_taco_hook("h3"))\n'
'    _TACO_TRACE = []\n'
)
B = "                    eval_obs, eval_rew, eval_terminations, eval_truncations, eval_infos = eval_envs.step(agent.get_action(eval_obs, deterministic=True))\n"
B2 = B + '                    _TACO_TRACE.append({**{k: v.copy() for k, v in _TACO_ACT.items()}, "rew": eval_rew.detach().float().cpu().numpy(), "term": eval_terminations.detach().cpu().numpy().astype("float32")})\n'
C = "            if args.evaluate:\n                break\n"
C2 = (
'            if args.evaluate:\n'
'                import numpy as _np\n'
'                _arrs = {k: _np.stack([t[k] for t in _TACO_TRACE]) for k in _TACO_TRACE[0]}\n'
'                _np.savez_compressed(f"{eval_output_dir}/activations.npz", **_arrs)\n'
'                print("TACO_SAVED " + str({k: v.shape for k, v in _arrs.items()}))\n'
'                break\n'
)
for old in (A, B, C):
    assert old in src, f"anchor not found: {old[:50]!r}"
src = src.replace(A, A2).replace(B, B2).replace(C, C2)
open("/work/joy/ManiSkill/examples/baselines/ppo/ppo_capture.py", "w").write(src)
print("patched ppo_capture.py")
