# TACO - The Autonomous Casualty Office

A hackathon demo of learned-policy liability insurance for robotics, underwritten from DreamAudit failures and internal model risk signatures.

## Product Thesis

Robotics insurers normally need deployment history, fleet telemetry, and claims history. Frontier robot policies often need enterprise coverage before that evidence exists. TACO creates synthetic actuarial evidence by stress-testing learned robot policies in simulation, normalizing DreamAudit replayable failure certificates, recording internal traces, and pricing liability coverage from both behavioral failures and internal risk signatures.

The quote depends on robot internals, not just benchmark pass/fail. A failure family with early internal warning and a verified monitor can receive a conditional premium discount; the same failure family without controls creates exclusions.

## What The Demo Shows

The app walks through an Apex Robotics application for 200 warehouse manipulation robots seeking $10M of Learned-Policy Liability coverage. Traditional underwriting is blocked because no telemetry exists. TACO loads DreamAudit certificates, shows success/failure/mitigated replay evidence, computes internal risk metrics from NPZ traces, calculates a premium, and issues a conditional binder.

## Architecture

```text
Apex Robotics Application
  -> TACO Underwriting UI
  -> DreamAudit Adapter
  -> Replay / Certificate Loader
  -> Internal Trace Analyzer
  -> Quote Engine
  -> Conditional Binder
```

## Quickstart

```bash
python -m pip install -r taco_demo/requirements-taco.txt
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py
```

## Data Layout

`taco_demo/data/applications` stores insurance applications. `dreamaudit_certs` stores normalized DreamAudit certificates. `traces` stores success, failure, and mitigated NPZ activation traces. `videos` stores replay media. `quotes` stores issued JSON and markdown binders.

Fallback data is explicitly demo-generated placeholder data. Replace it with real DreamAudit renderings and real activation traces for production-style evidence.

The bootstrap also writes `maniskill_gallery.json` and a dozen `videos/maniskill_examples/*.gif` clips. These are deterministic visual placeholders that show how DreamAudit ManiSkill/RMA simulator replay evidence can flow into TACO. The local DreamAudit artifacts currently provide ManiSkill/RMA result JSONs for `PickSingleYCBRMA-v1` and `RopeLoopPlacementRMA-v1`; cluster-rendered videos can replace the placeholder GIFs at the same paths.

## DreamAudit Integration

Put real certificates in `taco_demo/data/dreamaudit_certs` or run:

```bash
python -m taco_demo.scripts.normalize_existing_certs --input-dir /path/to/dreamaudit/artifacts --output-dir taco_demo/data/dreamaudit_certs --overwrite
```

The adapter handles `certificate_id`, `patch_recipe`, `replay_command`, `minimality`, `minimal_cost`, `failure_type`, `policy_id`, `task_id`, replay/video URIs, and nested DreamAudit structures where present. It fills deterministic defaults for missing fields and marks metadata as `normalized_missing_fields`.

To replace fallback videos, write real replay media to `taco_demo/data/videos/FR-001_failure.mp4` style paths. To record real traces, attach `ActivationRecorder` to OpenVLA/VLA layers, run nominal, failure, and mitigated replays, and save NPZ files to `taco_demo/data/traces`.

For ManiSkill/RMA examples, use DreamAudit's `scripts/run_maniskill_rma_smoke.py` or the cluster wrapper documented in DreamAudit's `BITACORA.md`, then place rendered clips under `taco_demo/data/videos/maniskill_examples/`. TACO will display them from the manifest without requiring simulator imports.

Environment variables:

- `DREAMAUDIT_ROOT`: real DreamAudit repo root.
- `TACO_DEMO_DATA_ROOT`: alternate TACO data directory.
- `DREAMAUDIT_CERT_DIR`: optional certificate source for external scripts.
- `TACO_ALLOW_REAL_REPLAY`: set to `1` before the replay wrapper attempts a real command.

## Internal Underwriting Metrics

Concept Coverage Score is the share of required concept signals that are present and non-flat: `target_feature`, `occlusion_risk`, `language_override_risk`, `unsafe_trajectory_dominance`, and `action_risk`.

Feature Stability Score compares the pre-failure target feature in success and failure traces: `1 - max(0, success_mean - failure_mean)`.

Unsafe Dominance Score blends pre-failure unsafe trajectory dominance and action risk.

Early Warning Margin is the time between the first internal risk threshold crossing and the physical failure timestep. A margin of at least 0.25 seconds means a monitor is possible.

Causal Mitigability Score compares failure action risk with mitigated action risk after monitor onset.

Internal Risk Score is:

```text
0.25 * (1 - concept_coverage)
+ 0.25 * (1 - feature_stability)
+ 0.25 * unsafe_dominance
+ 0.15 * (1 - causal_mitigability)
+ 0.10 * early_warning_penalty
```

## Insurance Quote Formula

Base monthly premium is `coverage_requested_usd * 0.0008 + deployment_units * 35`. Deployment multiplier is `1 + min(1.5, units / 500)`.

Behavioral fragility rises when minimal failure cost is low and neighborhood failure rate is high:

```text
cost_factor = 1 + max(0, 0.6 - minimal_failure_cost)
rate_factor = 1 + 0.75 * failure_rate_neighborhood
```

Internal risk multiplier is `1 + 1.25 * aggregate_internal_risk_score`. Monitor discount is `1 - min(0.45, 0.45 * aggregate_causal_mitigability_score)` when required controls are enabled.

Statuses are `blocked_no_telemetry`, `approved_with_exclusions`, or `conditionally_approved`. Required controls include re-audit after model update, occlusion-risk monitoring, language override sanitization, and target identity confirmation as dictated by failure families.

## Certificate Schema

Issued binders contain TACO branding, the application, robot policy metadata, DreamAudit behavioral evidence, internal evidence, mitigation evidence, quote decision, required controls, exclusions, and disclaimer.

```json
{
  "branding": "TACO - The Autonomous Casualty Office",
  "bundle": {
    "certificate_id": "TACO-IUC-APP-APEX-001-FR-001",
    "source_dreamaudit_certificate_id": "FR-001",
    "insurance_decision": {
      "coverage_type": "Learned-Policy Liability",
      "status": "conditionally_approved"
    }
  }
}
```

## Demo Script For Judges

Apex Robotics wants $10M coverage for 200 warehouse manipulation robots. There is no deployment telemetry, so traditional underwriting cannot price the risk. TACO runs internal underwriting instead. DreamAudit finds three replayable failure families: occlusion-induced wrong grasp, language override conflict, and distractor confusion. TACO shows nominal, failure, and mitigated replays, then computes internal risk signatures from hidden-state traces. The quote changes when required controls are disabled, proving that the insurance product is tied to model internals. Finally, TACO issues a conditional Learned-Policy Liability Binder.

## What Is Real Vs Fallback

Real in this scaffold: JSON contracts, certificate normalization, quote computation, metric computation from arrays, binder generation, tests, and Streamlit UI.

Fallback in this scaffold: generated videos and NPZ traces unless replaced with DreamAudit recordings.

Integration-ready: real certificates, replay paths, DreamAudit commands, and VLA activation traces can be dropped into the same data layout.

## Future Roadmap

- Real VLA activation hooks.
- SAE feature dictionaries.
- Event-grounded feature labeling.
- Carrier and reinsurer integration.
- Claims triage.
- Runtime compliance logs.
- Formal policy wording.

## Disclaimer

This is a hackathon demo and not an actual offer of insurance.
