## 2026-06-04 - TACO scaffold

- Read `instructions.spec` and inspected `/Users/joyyang/Projects/dreamaudit` for DreamAudit certificate, minimality, patch, replay, LIBERO/OpenVLA, video, rollout, and artifact patterns.
- Confirmed `taco` is on `main` with remote `https://github.com/J0YY/taco.git`; GitHub CLI is installed and authenticated as `J0YY`.
- Began scaffolding `taco_demo/` as a self-contained offline-first insurance underwriting demo with DreamAudit normalization support.
- Added deterministic bootstrap, certificate normalization, replay-video wrapper, and precompute scripts. The bootstrap path generates Apex Robotics application data, three DreamAudit-like certificates, NPZ traces, and synthetic replay videos.
- Added the Streamlit insurance-office UI, root quickstart README, and full `taco_demo/README.md` product/technical spec.
- Added pytest coverage for quote behavior, internal feature scoring, dataclass/certificate serialization, and DreamAudit adapter normalization/bootstrap loading.
- User requested cluster usage if needed and many ManiSkill videos. Inspected DreamAudit ManiSkill/RMA harnesses and artifacts (`maniskill_rma_smoke`, `maniskill_rma_smoke_8env`, `maniskill_rma_policy_rope_eval_bash2`). Added a ManiSkill/RMA gallery manifest and 12 deterministic placeholder replay videos wired into the UI; documented replacement with cluster-rendered clips.
- Validation used `/tmp/taco-demo-venv` because Homebrew Python blocked direct pip installs under PEP 668 and the system has `python3` but no `python` executable. Commands run:
  - `/tmp/taco-demo-venv/bin/python -m taco_demo.scripts.bootstrap_demo_data --force`
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 14 passed.
  - `/tmp/taco-demo-venv/bin/python -m taco_demo.scripts.precompute_demo` -> wrote JSON and markdown binders under `taco_demo/data/quotes/`.
