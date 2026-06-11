# TACO mechanistic audit engine (`experiments/`)

Submit **one policy file**, describe the deployment in a few questions, and the
engine stress-tests the policy in simulation until it finds the situations that
break it — then returns a **PASS / CONDITIONAL PASS / FAIL** verdict with
replayable failure certificates and the runtime controls that would make it
deployable.

This is the closed-loop audit engine behind TACO's certifier story, built as a
self-contained package so it runs anywhere (CPU-only by default; GPU/Cosmos
optional).

```
   policy.py ──▶ scope ──▶ ┌──────────────── falsification loop ────────────────┐
                           │  proposer ──▶ perturbation ──▶ sim.rollout(policy)  │
                           │      ▲                              │               │
                           │      └──── failure-proximity ◀──────┘  (until fail) │
                           └────────────────────────────────────────────────────┘
                                   │ minimise · neighborhood · monitorability · patch
                                   ▼
                          PASS / CONDITIONAL PASS / FAIL  (+ certificates, controls)
```

## The algorithm

A *proposer* emits a bounded **perturbation** of the situation; a *simulator*
rolls the policy out under it and returns a **trace**; a Monte-Carlo
cross-entropy search pushes toward the **failure boundary**. This is policy
**falsification / adaptive stress testing**. Four design choices make it useful
rather than just "random until it breaks":

1. **Continuous failure-proximity, not pass/fail.** Every rollout returns how
   *close* it came to failing, so the search gets gradient signal before the
   first real failure — and finds the **minimal** perturbation that breaks the
   policy (`minimal_failure_cost`), the most damning kind of certificate.
2. **Characterise, don't just trip.** A verdict needs statistics: the
   **neighborhood failure rate**, the **severity**, and whether an internal
   signal **precedes** the failure (**monitorability**). The engine minimises the
   failure, probes its neighborhood, and scores its trace.
3. **Mechanistic early-warning.** From the policy's own actions the sim derives a
   model-agnostic monitor (`internal_risk_score`, `action_risk`, `target_feature`
   collapse, …). A failure is *monitorable* only if that signal crosses early
   enough for a runtime monitor to act — the difference between CONDITIONAL PASS
   and FAIL.
4. **Test the fix.** For each family the engine re-runs the minimal failure with
   the recommended runtime control enabled; if success is restored the patch is
   **verified**, not just recommended.

## Proposers (pluggable)

| proposer | needs | role |
|---|---|---|
| `heuristic` (default) | numpy only | Monte-Carlo cross-entropy search over the perturbation knobs. Runs anywhere. |
| `llm` | `ANTHROPIC_API_KEY` | Claude proposes the next perturbation as a validated JSON spec (the "language model outputs a sim state" route). |
| `cosmos` | GPU + `diffusers` | NVIDIA Cosmos renders the perturbed scene as an evidence frame / observation (the "Cosmos creates new sim states" route). |

> **Cosmos note.** "Cosmos 3" (the June-2026 16B/65B omnimodel) does **not** fit a
> 32 GB GPU. The realistic on-device world model is **`Cosmos-Predict2.5-2B`**
> (~32 GB @720p, fits @480p with offload). The cosmos backend targets it and
> degrades gracefully to the heuristic proposer if the weights/toolchain aren't
> available. See `taco_audit/proposers/cosmos.py`.

## Quickstart

```bash
cd experiments
python -m taco_audit.cli audit examples/policies/reach_robust.py     # -> PASS
python -m taco_audit.cli audit examples/policies/reach_brittle.py    # -> CONDITIONAL PASS
python -m taco_audit.cli audit examples/policies/reach_blind.py \    # -> FAIL
    --environment cluttered --proximity shared_space --criticality high --out runs/blind

python examples/run_demo.py        # runs all three and prints a table
python -m pytest tests             # the test suite
streamlit run app.py               # the web interface (submit a policy, pick scope, get a verdict)
```

Pick the proposer with `--proposer {heuristic,llm,cosmos}`. `llm` activates when
`ANTHROPIC_API_KEY` is set (Claude proposes perturbations); `cosmos` renders
perturbed scenes on a GPU. Both fall back to the heuristic if unavailable, so the
audit always runs.

Add `--interactive` to be prompted for the deployment scope, or pass it on the
flags: `--robot-type`, `--task`, `--environment`, `--proximity`, `--criticality`,
`--units`, `--budget`, `--out`.

## Submitting your own policy

The policy file may define any one of:

```python
class Policy:                  # preferred
    def reset(self): ...       # optional; called before each rollout
    def act(self, obs): return action

def policy(obs): return action            # or a module-level function
def build_policy(): return callable       # or a factory
```

`obs` is a dict: `gripper` (xy), `instruction` (str), `instruction_conflict`
(float), `detections` (list of `{pos, salience, match_score}` — no ground-truth
ids), `t`, `time_left`. `action` is a 2-D velocity in `[-1, 1]`. A policy may also
return `(action, {"internal": {...}})` to feed *real* internal features into the
monitor instead of the behavioural estimate.

## What is real vs. modelled

- **Real:** the closed-loop falsification search, minimal-failure minimisation,
  neighborhood-rate estimation, trace scoring (mirrors `taco_demo.trace_scoring`),
  monitorability test, control-verification re-run, and the verdict mapping.
- **Modelled (MVP):** `ReachWorld` is a compact 2-D tabletop sim, and the internal
  monitor is *behavioural* (derived from actions), not SAE activations. The seams
  for a heavier sim (gymnasium/MuJoCo) and real Cosmos rendering are in place.

Not an insurance product or a safety guarantee — findings are bounded by the
simulator and the search budget.
