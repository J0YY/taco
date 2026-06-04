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
- Pushed the suite to GitHub main at `82d02b4`, cloned it on `athena` under `/work/joy/taco`, and ran:
  - `~/remote_srun.sh --log --setup 'source ~/miniconda3/etc/profile.d/conda.sh && conda activate rma' /work/joy/taco python -m taco_demo.scripts.generate_maniskill_video_suite --force`
- Cluster result:
  - SLURM job allocated host `c2-g4-24`,
  - log path `/work/joy/taco/logs/run_1780557030_505530330.out`,
  - remote manifest verified `suite_size=40`,
  - remote video count verified `40` GIFs.
- Ran a second independent `codex review --base _review-loop-baseline` after adding the ManiSkill suite; reviewer found no observable regressions and noted that the added tests pass and the Streamlit app imports successfully.
- Completion audit found that `bootstrap_demo_data --force` rewrote the application `created_at` timestamp, leaving the worktree dirty after a required command. Fixed `default_application()` to use deterministic `DEMO_CREATED_AT`, regenerated `APP-APEX-001.json`, and added a schema/bootstrap regression test.
- Updated Streamlit width calls from deprecated `use_container_width=True` to `width="stretch"` after the app import emitted the 2026 deprecation warning.
- Pushed deterministic bootstrap fix at `c96234d` and ran a final independent `codex review --base _review-loop-baseline`; reviewer reported no actionable correctness issues relative to the specified base.

## 2026-06-04 - Improvement loop: insurance workflow examples

- Pulled `origin/main`; repository was already up to date at `072b7c9`.
- Added a reusable diligence memo generator that creates a single Markdown artifact for investors, brokers, and underwriters.
- Added 10 concrete insurance failure/pricing/workflow examples covering:
  - warehouse manipulation,
  - mobile picking,
  - retail restocking,
  - kitchen prep,
  - parcel sorting,
  - hospital delivery,
  - greenhouse harvesting,
  - inspection/repair,
  - deformable goods packing,
  - model-update re-audit.
- Added an `Insurance Examples` tab with failure evidence, pricing with/without controls, exclusions, and end-to-end workflows.
- Added an `Investor Diligence Memo` download in the Investor Case tab.
- Added pytest coverage for the 10 scenarios, pricing deltas, workflow completeness, and memo contents.
- Verification:
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 19 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.

## 2026-06-04 - Improvement loop: runtime compliance and renewal pricing

- Pulled `origin/main`; repository was already up to date at `a06a861`.
- Added deterministic runtime monitor events and incident/claims response evidence in `taco_demo/renewal_loop.py`.
- Added a `Renewal Loop` tab that shows:
  - runtime monitor pass/warn/fail events,
  - prevented-loss evidence,
  - incurred-loss evidence,
  - renewal premium impact,
  - re-audit requirement status,
  - incident coverage responses.
- Extended the investor diligence memo with the runtime compliance and renewal loop.
- Added pytest coverage for renewal summary math, clean-compliance renewal discount behavior, and memo inclusion.

## 2026-06-04 - Improvement loop: DreamAudit adapter and activation recorder

- Pulled `origin/main`; repository was already up to date at `1b193e5`.
- Added `taco_demo/dreamaudit_adapter.py`:
  - loads DreamAudit certificate JSONs without importing DreamAudit,
  - supports compact LIBERO/OpenVLA observation certificates,
  - supports richer `dreamaudit.types.Certificate`-style JSON,
  - normalizes certificate IDs, policy IDs, task IDs, failure families, perturbation costs, neighborhood failure rates, replay commands, patch recipes, and source metadata into TACO `FailureCertificate` objects.
- Added `taco_demo/activation_recorder.py`:
  - optional torch-compatible forward-hook recorder,
  - no torch dependency at import time,
  - selected-layer capture, summaries, hook cleanup, and NPZ persistence.
- Added app and README explanation for the real internals path from DreamAudit certificates to activation NPZ traces.
- Added pytest coverage for compact DreamAudit certificates, rich DreamAudit certificates, directory adaptation, activation recording, NPZ save, and hook removal.
- Verification before independent review:
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 26 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.
- Pushed first implementation commit `97c4be1` to GitHub `main`.
- Independent `codex review --base _review-loop-baseline` found two adapter issues:
  - rich DreamAudit certificates with `semantic_rationale="CEM proposal over synthetic perturbation grammar"` could be misclassified as language failures,
  - `adapt_dreamaudit_certificates(..., limit=0)` returned one certificate.
- Fixed both:
  - raw DreamAudit failure modes now take precedence over generic rationale text,
  - `limit <= 0` returns an empty certificate list before scanning.
- Added regression tests for the search-grammar misclassification and zero-limit behavior.
- Verification after review fixes:
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests/test_dreamaudit_adapter.py taco_demo/tests/test_activation_recorder.py` -> 6 passed.
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 28 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.
- Pushed first review-fix commit `4265ec6` to GitHub `main`.
- Second independent `codex review --base _review-loop-baseline` found two remaining P2 issues:
  - activation captures could share storage with mutable torch CPU tensors,
  - adapted certificates did not preserve the raw DreamAudit `minimality` report.
- Fixed both:
  - activation recorder now copies arrays at hook capture time,
  - adapter metadata now includes the full raw `minimality` object.
- Added regression coverage for in-place post-hook mutation and minimality preservation.
- Verification after second review fixes:
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests/test_dreamaudit_adapter.py taco_demo/tests/test_activation_recorder.py` -> 7 passed.
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 29 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.
- Pushed second review-fix commit `c8e9fcf` to GitHub `main`.
- Third independent `codex review --base _review-loop-baseline` found two functional issues:
  - fallback DreamAudit `replay_command` used an invalid `validate_candidates.py --certificate` flag,
  - activation NPZ keys could collide when layer names sanitized to the same string.
- Fixed both:
  - fallback replay command now uses a valid `python -m json.tool <certificate>` certificate-inspection command unless DreamAudit provides a real replay video URI,
  - NPZ save keeps readable layer keys when unique and adds a stable hash suffix only when sanitized layer names collide.
- Added regression coverage for valid certificate replay command fallback and sanitized NPZ key collisions.
- Verification after third review fixes:
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests/test_dreamaudit_adapter.py taco_demo/tests/test_activation_recorder.py` -> 8 passed.
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 30 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.
- Pushed third review-fix commit `13b0c4b` to GitHub `main`.
- Fourth independent `codex review --base _review-loop-baseline` found two more integration issues:
  - non-visual DreamAudit certificates could lose meaningful perturbation costs when cost fields are action or language specific,
  - `ActivationRecorder.save_npz()` returned an unsuffixed path when `np.savez` actually wrote `<path>.npz`.
- Fixed both:
  - adapter cost extraction now handles `smallest_failing_sigma`, `noise_sigma`, action-distance fields, and semantic instruction edits with zero image delta,
  - `save_npz()` now returns the actual `.npz` path written.
- Added regression coverage for action-noise cost extraction, language semantic-edit cost extraction, and unsuffixed NPZ output paths.
- Verification after fourth review fixes:
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests/test_dreamaudit_adapter.py taco_demo/tests/test_activation_recorder.py` -> 10 passed.
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 32 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.
- Pushed fourth review-fix commit `09400a8` to GitHub `main`.
- Extra independent `codex review --base _review-loop-baseline` found one production-path issue:
  - bf16 torch tensors can fail NumPy conversion and be silently dropped by the activation recorder.
- Fixed bf16-like tensor handling:
  - activation recorder casts `bfloat16` tensor-like objects to float before NumPy conversion,
  - fallback conversion retries `.float().numpy()` if direct `.numpy()` raises `TypeError`.
- Added regression coverage with a fake bf16 tensor object.
- Verification after bf16 fix:
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests/test_activation_recorder.py taco_demo/tests/test_dreamaudit_adapter.py` -> 11 passed.
  - `/tmp/taco-demo-venv/bin/python -m pytest taco_demo/tests` -> 33 passed.
  - `/tmp/taco-demo-venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.
- Pushed bf16 fix commit `9a89d86` to GitHub `main`.
- Final independent `codex review --base _review-loop-baseline` reported no discrete functional regression in the DreamAudit adapter or activation recorder changes.

## 2026-06-04 - Testrun install and README consolidation

- Pulled `origin/main`; repository was already up to date at `169cb05`.
- Created a repo-local `.venv` and installed `taco_demo/requirements-taco.txt` for local testruns.
- Added `.gitignore` entries for `.venv/`, Python caches, and pytest caches so local install artifacts stay out of Git.
- Consolidated documentation into a single root `README.md`:
  - merged the root quickstart, `README_TACO.md`, and `taco_demo/README.md`,
  - removed `README_TACO.md` and `taco_demo/README.md`,
  - reframed the architecture as offline evidence mode plus live DreamAudit/activation-capture mode,
  - documented the local `.venv` testrun path,
  - removed README phrasing that made the system read as hardcoded or only deterministic.
- Updated the Streamlit Spec tab to read the root `README.md`.
- Tightened user-facing app and diligence memo copy from "synthetic/deterministic placeholders" to local evidence fixtures and live integration paths.
- Verification from `.venv`:
  - `.venv/bin/python -m taco_demo.scripts.bootstrap_demo_data --force` -> passed.
  - `.venv/bin/python -m pytest taco_demo/tests` -> 33 passed.
  - `.venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.

## 2026-06-04 - Improvement loop: live DreamAudit intake tab

- Pulled `origin/main`; repository was already up to date at `f85fb1b`.
- Added `taco_demo/dreamaudit_intake.py` to summarize live DreamAudit artifact directories through the existing adapter.
- Added a Streamlit `DreamAudit Intake` tab:
  - accepts a local DreamAudit artifacts path,
  - scans certificates on demand,
  - shows adapted certificate count, failure-family count, high-severity count, mean neighborhood failure rate, schema/backend counts, source examples, and sample certificate rows.
- Added tests for missing roots, adapted certificate counts, schema/backend/failure summaries, and row limiting.
- Updated the root README product surface to include live DreamAudit artifact intake.
- Verified the intake path against `/Users/joyyang/Projects/dreamaudit/artifacts`:
  - 250 adapted certificates at scan limit 250,
  - failure families included action-noise, language override, occlusion, and vision perturbation certificates,
  - 25 sample rows returned for display.
- Verification from `.venv`:
  - `.venv/bin/python -m pytest taco_demo/tests/test_dreamaudit_intake.py taco_demo/tests/test_dreamaudit_adapter.py` -> 8 passed.
  - `.venv/bin/python -m pytest taco_demo/tests` -> 36 passed.
  - `.venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.

## 2026-06-04 - Improvement loop: DreamAudit underwriting readiness

- Pulled `origin/main`; repository was already up to date at `b6f1064`.
- Extended `taco_demo/dreamaudit_intake.py` with underwriting-readiness analysis:
  - readiness score,
  - carrier-review status,
  - required controls implied by imported certificates,
  - unmapped failure families,
  - minimality report coverage,
  - replay/certificate command coverage,
  - behavioral fragility multiplier,
  - evidence gaps before carrier review.
- Updated the `DreamAudit Intake` Streamlit tab to show the readiness score, status, controls, behavioral multiplier, and gaps above the raw counts.
- Made `adapt_dreamaudit_certificate(..., source_path=...)` tolerate string paths as well as `Path` objects.
- Added tests for broad mapped evidence scoring as carrier-review ready and for missing/partial evidence scoring as not ready.
- Verified against `/Users/joyyang/Projects/dreamaudit/artifacts` at scan limit 250:
  - 250 adapted certificates,
  - readiness score `80/100`,
  - status `needs_more_evidence`,
  - identified unmapped action-noise and vision-perturbation families as the current control-mapping gap.
- Verification from `.venv`:
  - `.venv/bin/python -m pytest taco_demo/tests/test_dreamaudit_intake.py taco_demo/tests/test_dreamaudit_adapter.py` -> 9 passed.
  - `.venv/bin/python -m pytest taco_demo/tests` -> 37 passed.
  - `.venv/bin/python -c "import taco_demo.app"` -> passed with expected Streamlit bare-mode warnings.
  - `git diff --check` -> clean.
