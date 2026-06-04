# TACO - The Autonomous Casualty Office

A hackathon demo of learned-policy liability insurance for robotics, underwritten from replayable robot failures and internal model risk signatures.

## Product Thesis

Traditional robotics underwriting needs deployment telemetry and claims history. Frontier robot policies often do not have that data before deployment. TACO creates synthetic actuarial evidence by stress-testing robot policies in simulation, recording replayable failures, computing internal risk signatures, and issuing a conditional learned-policy liability quote.

The shorthand is: Perfetto for robot failures plus underwriting evidence for robot insurance. The UI makes one story obvious: application blocked, internal audit, replayable failures, internal traces, conditional quote, binder.

## What The Demo Shows

Apex Robotics wants Learned-Policy Liability coverage for 200 warehouse manipulation arms. The deployment is pre-telemetry, so traditional underwriting is blocked. TACO bootstraps three replayable failure certificates, generates success/failure/mitigated GIFs, computes internal trace metrics from NPZ arrays, prices coverage, and issues a conditional binder.

The visual centerpiece is a robot succeeding, failing under a plausible counterfactual, then being mitigated by a required runtime control. The premium and exclusions change when those controls are disabled.

## Architecture

```text
Apex Robotics Application
-> TACO Underwriting UI
-> Failure Certificate Loader
-> Replay Evidence Viewer
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

```text
taco_demo/data/applications/   insurance applications
taco_demo/data/certificates/   replayable failure certificate JSON
taco_demo/data/traces/         success/failure/mitigated NPZ traces
taco_demo/data/videos/         generated replay GIFs
taco_demo/data/binders/        issued JSON and Markdown binders
```

## Internal Underwriting Metrics

Concept Coverage Score measures whether the trace contains non-flat concept signals: `target_feature`, `general_grasp_feature`, `transport_feature`, `memorized_trajectory_feature`, `unsafe_trajectory_dominance`, and `action_risk`.

Feature Stability Score compares pre-failure target feature strength in success and failure traces. Low score means target feature collapse.

Unsafe Dominance Score is the maximum pre-failure mean of unsafe trajectory dominance, action risk, and memorized trajectory feature.

Early Warning Margin is the time between the first `internal_risk_score > 0.65` crossing and the physical failure timestep.

Causal Mitigability Score compares post-warning action risk in failure and mitigated traces.

Internal Risk Score is:

```text
0.20 * (1 - concept_coverage_score)
+ 0.25 * (1 - feature_stability_score)
+ 0.25 * unsafe_dominance_score
+ 0.20 * (1 - causal_mitigability_score)
+ 0.10 * early_warning_penalty
```

## Quote Formula

Base monthly premium:

```text
coverage_requested_usd * 0.0008 + deployment_units * 35
```

Behavioral fragility rises when minimal failure cost is low and neighborhood failure rate is high:

```text
cost_factor = 1 + max(0, 0.6 - minimal_failure_cost)
rate_factor = 1 + 0.75 * failure_rate_neighborhood
```

TACO blends max and mean behavioral multipliers, blends max and mean internal risk, applies `1 + 1.25 * aggregate_internal_risk`, and discounts the premium only when required controls are enabled. Disabling controls creates exclusions for known failure families.

## What Is Real Vs Fallback

Real:

* schemas
* generated certificates
* generated traces
* generated replay videos
* deterministic risk metric computation
* deterministic quote engine
* binder generation
* tests

Fallback:

* videos are synthetic drawings
* traces are deterministic generated placeholders
* no real VLA model is executed
* no real Cosmos scenario generation is executed
* no real insurance product is being offered

## Demo Script For Judges

Apex Robotics wants $10M of Learned-Policy Liability coverage for 200 warehouse manipulation arms. They have no fleet telemetry because this is pre-deployment, so traditional underwriting is blocked. TACO runs internal underwriting instead. It loads three replayable failure certificates, shows nominal/failure/mitigated replays, plots internal risk traces that cross before physical failure, and prices a conditional quote. Disable the occlusion monitor and the premium increases or an FR-001 exclusion appears. Re-enable it and the status returns to conditionally approved. Finally, TACO issues a JSON and Markdown binder.

## Future Roadmap

* ingest real DreamAudit certificates
* replace GIFs with real simulator replay videos
* attach activation hooks to OpenVLA / pi0-style policies
* train SAE dictionaries on rollout activations
* use Cosmos-style world or scenario proposers to suggest candidate stress tests
* price risk using historical incident data
* integrate with certification and insurance workflows

## Disclaimer

This is a hackathon demo and not an actual offer of insurance.
