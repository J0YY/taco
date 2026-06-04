# AGENTS.md — TACO (The Autonomous Casualty Office)

Standing instructions for any agent (Codex, Claude, etc.) working in this repo.
Read this before editing. The original product brief is `instructions.spec`; the
running log is `bitacora.md`.

## What TACO is

A local, offline demo of **learned-policy liability insurance for robotics**. It
prices a conditional quote from (1) replayable robot failure certificates,
(2) internal model-risk signals, (3) mitigation evidence, and (4) required
runtime controls + exclusions. It should feel like an insurance product, not an
ML dashboard. It does **not** require real OpenVLA/Cosmos/Isaac at runtime, but
the evidence it shows should be as real as possible.

## Golden rules (most important first)

1. **Real evidence beats narrative.** The demo's credibility is real rendered
   rollouts and real internal-monitor signals. Before adding ANY new
   fundraise/investor/commercial/seed narrative module, don't — there are
   already 40+. Consolidate, don't multiply.
2. **Never break the real video wiring.** Do not overwrite or delete:
   - `taco_demo/data/videos/real/` — real LIBERO/OpenVLA clips (FR-001, FR-002)
   - `taco_demo/data/videos/real_external/` — sae-scope FR-004 + nla4vla breadth
   - `taco_demo/data/videos/real_maniskill/` — cluster-rendered ManiSkill rope
   - the `_artifacts`/`_replay_path`/`REAL_REPLAY_META` logic in `app.py`
   - the "Real Cross-Policy Evidence" tab and `taco_demo/external_evidence.py`
3. **Prefer real over synthetic when improving.** Replace synthetic NPZ traces
   and drawn GIFs with real rollout data / real internal signals where possible.
4. **Keep the 3-cert Apex quote pipeline stable.** `DEMO_CERTIFICATES`
   (`sample_data.py`) is FR-001/FR-002/FR-003 only. FR-004 is intentionally a
   separate real-evidence exhibit (different policy/env) and must NOT be added to
   `DEMO_CERTIFICATES` — several tests assert a count of 3.
5. **Tests must stay green.** Run the full suite before every commit.
6. **One concern per commit**; don't stage files you didn't change. If another
   agent has uncommitted work in the tree, commit only your own paths.

## Headline demo flow

Application (underwriting blocked, no telemetry) → Underwriting Audit → **Replay
Evidence** (defaults to FR-002 language override: real success → real
override **failure** → real sanitizer-repaired **success**) → Internal Signals →
Quote (toggle controls; premium + exclusions move) → Binder → **Real
Cross-Policy Evidence** (FR-004: internal monitor fires ~48 steps before failure;
OpenVLA/SmolVLA/ManiSkill breadth).

## Repo map

- `taco_demo/app.py` — Streamlit UI (tabbed). Main script; re-read on rerun.
- `taco_demo/schemas.py` — dataclasses + JSON IO.
- `taco_demo/sample_data.py` — `DEMO_CERTIFICATES` (FR-001..FR-003 Apex).
- `taco_demo/quote_engine.py` — deterministic premium/controls/exclusions.
- `taco_demo/trace_scoring.py` — internal-risk metrics from NPZ traces.
- `taco_demo/external_evidence.py` — real cross-policy evidence (FR-004 sae-scope
  monitor stats, nla4vla breadth, ManiSkill render summary). All numbers come
  from the copied `manifest.json` files; do not fabricate.
- `taco_demo/scripts/bootstrap_demo_data.py` — regenerates certs/traces/synthetic
  GIFs (writes `data/`; never writes `data/videos/real*`).
- `taco_demo/binder.py`, `renewal_loop.py`, `investor_case.py`, `data_room.py`,
  `dreamaudit_*` — supporting modules.
- `taco_demo/tests/` — pytest suite (keep all passing).

## Commands

Use the repo virtualenv (`.venv`); the system has `python3`, not `python`.

```bash
.venv/bin/python -m pip install -r taco_demo/requirements-taco.txt   # first time
.venv/bin/python -m taco_demo.scripts.bootstrap_demo_data --force    # regen demo data
.venv/bin/python -m pytest taco_demo/tests                           # full suite (~90s)
.venv/bin/python -c "import taco_demo.app"                           # import smoke check
.venv/bin/python -m streamlit run taco_demo/app.py                   # run the UI
```

Note: the demo is often run with `--server.fileWatcherType none`, so a running
Streamlit will NOT hot-reload code changes — restart it to see edits.

## Real data provenance (don't claim more than this)

- FR-001/FR-002 videos: real LIBERO/OpenVLA replays (DreamAudit supplemental).
- FR-004: real VLA-diffusion rollouts on SimplerEnv `move_near` with an internal
  SAE monitor (sae-scope). Real: internal monitor first alert at step 32, 48-step
  lead, recall 1.0, precision 0.857, 60% neighborhood failure rate.
- nla4vla: real OpenVLA (LIBERO) + SmolVLA (MetaWorld) rollouts incl. a
  destructive-token failure.
- ManiSkill rope: rendered on the athena GPU cluster (RopeLoopPlacementRMA-v1),
  16/16 envs failed (100% neighborhood failure; no success contrast available).
- Still synthetic/illustrative (label as such): NPZ internal-signal traces,
  FR-003 placeholder, FR-001/FR-003 "mitigated" columns, the quote formula.

## Verify before commit

`pytest` green, `import taco_demo.app` clean, `git diff --check` clean, and you
have not staged another agent's in-progress files.
