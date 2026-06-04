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

## 2026-06-04 - TACO MVP refactor from updated instructions.spec

- Updated `instructions.spec` narrowed the MVP: `trace_scoring.py`, `binder.py`, `data/certificates`, `data/binders`, one bootstrap script, no torch path, no extra adapter/precompute scripts, and a stronger "Perfetto for robot failures + underwriting evidence" narrative.
- Refactored the scaffold to match the new required surface:
  - Replaced `NormalizedDreamAuditCertificate`/issuer flow with `FailureCertificate` and `PolicyBinder`.
  - Replaced `feature_scoring.py` with `trace_scoring.py` using the revised concept signals and metric weights.
  - Replaced `policy_issuer.py` with `binder.py`.
  - Removed first-version optional modules/scripts: DreamAudit adapter, activation recorder, precompute, normalizer, replay wrapper, and ManiSkill gallery module/media.
  - Regenerated demo data under `taco_demo/data/certificates`, `traces`, `videos`, and `binders`.
- Validation used `/tmp/taco-demo-venv`:
  - `/tmp/taco-demo-venv/bin/python -m taco_demo.scripts.bootstrap_demo_data --force`
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 11 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed, with expected Streamlit bare-mode warnings.
- After independent review round 1 passed, tuned generated traces so the exact quote formula lands in the updated spec's target range: monitors enabled -> `$29,800/month`; occlusion monitor disabled -> `$51,500/month`. Re-ran tests and import verification successfully.

## 2026-06-04 - Investor-grade fundraise iteration

- Pulled `origin/main`; repository was already up to date and clean.
- Added `taco_demo/investor_case.py` to make the fundraise story executable:
  - research foundations with source links,
  - underwriting workflow artifacts by role,
  - moat hypotheses,
  - seed-stage derisking milestones,
  - investor proof-point summary derived from application, certificates, metrics, and quote.
- Added an Investor Case tab and research/workflow expanders in the Streamlit UI.
- Expanded `taco_demo/README.md` with:
  - venture-scale thesis,
  - research backing,
  - buyer workflow,
  - calibrated quote behavior,
  - VC pitch track,
  - moat and derisking milestones.
- Research sources reviewed and linked in README/app:
  - SIMPLER / CoRL 2024 simulation-based robot policy evaluation,
  - Muratore et al. domain randomization / CoRL 2018,
  - ICLR 2024 sparse autoencoder interpretability,
  - Anthropic 2024 model-feature mapping and monitoring discussion.
- Independent `codex review --base _review-loop-baseline` found no actionable bugs in the investor-case diff.
- Added a supplemental ManiSkill/RMA-style evidence suite:
  - `taco_demo/maniskill_suite.py`,
  - `taco_demo/scripts/generate_maniskill_video_suite.py`,
  - `taco_demo/data/maniskill_suite/manifest.json`,
  - 40 generated replay GIFs across eight failure families and five ManiSkill-style RMA environments.
- The suite records what TACO identifies from each replay: risk signal, underwriting interpretation, required control, severity, minimal failure cost, and neighborhood failure rate.
