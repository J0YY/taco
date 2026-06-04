# TACO - The Autonomous Casualty Office

A hackathon demo of learned-policy liability insurance for robotics, underwritten from replayable robot failures and internal model risk signatures.

## Product Thesis

Traditional robotics underwriting needs deployment telemetry and claims history. Frontier robot policies often do not have that data before deployment. TACO creates synthetic actuarial evidence by stress-testing robot policies in simulation, recording replayable failures, computing internal risk signatures, and issuing a conditional learned-policy liability quote.

The shorthand is: Perfetto for robot failures plus underwriting evidence for robot insurance. The UI makes one story obvious: application blocked, internal audit, replayable failures, internal traces, conditional quote, binder.

## What The Demo Shows

Apex Robotics wants Learned-Policy Liability coverage for 200 warehouse manipulation arms. The deployment is pre-telemetry, so traditional underwriting is blocked. TACO bootstraps three replayable failure certificates, generates success/failure/mitigated GIFs, computes internal trace metrics from NPZ arrays, prices coverage, and issues a conditional binder.

The visual centerpiece is a robot succeeding, failing under a plausible counterfactual, then being mitigated by a required runtime control. The premium and exclusions change when those controls are disabled.

## Why This Could Be Venture-Scale

The fundable version of TACO is not "a dashboard for robot QA." It is an evidence layer for making autonomy insurable, certifiable, and deployable before claims history exists. The buyer does not need another benchmark score; they need a file that a robotics risk lead, broker, carrier, reinsurer, and enterprise procurement team can all reason about.

The wedge is pre-deployment learned-policy liability for robotics OEMs and enterprise robot buyers. The expansion path is a system of record for model-risk evidence: failure certificates, internal-risk signatures, mitigations, exclusions, runtime monitor compliance, renewal data, and claims outcomes.

The $5M+ seed story is credible only if the demo is framed as a wedge into a larger evidence network:

* Robot policies are becoming harder to evaluate from pass/fail benchmark scores alone.
* Insurers and enterprise buyers need structured evidence before fleet telemetry exists.
* Replayed failures and internal traces can become underwriting artifacts.
* Required controls turn safety engineering into policy conditions, exclusions, and premium deltas.
* Over time, the evidence graph can compound into proprietary autonomy-risk data.

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

## Research Backing

TACO's MVP uses deterministic placeholder traces, but the methodology is intentionally aligned with active research directions:

* Simulation-based robot evaluation: SIMPLER reports that simulated manipulation evaluation can be scalable and reproducible, and can reflect real policy behavior modes under distribution shift. TACO translates that into pre-deployment underwriting evidence. Source: [Evaluating Real-World Robot Manipulation Policies in Simulation](https://www.oiermees.com/publication/simpler/).
* Robust simulation and transfer: domain randomization research highlights that simulation can be useful but must manage simulation optimization bias and transferability. TACO handles this commercially by pricing fragile failure boundaries and requiring controls. Source: [Domain Randomization for Simulation-Based Policy Optimization with Transferability Assessment](https://proceedings.mlr.press/v87/muratore18a.html).
* Internal feature interpretability: sparse autoencoder work shows internal activations can be decomposed into more interpretable features and linked to counterfactual behavior. TACO's current trace metrics are lightweight proxies for a future SAE/VLA feature layer. Source: [Sparse Autoencoders Find Highly Interpretable Features in Language Models](https://proceedings.iclr.cc/paper_files/paper/2024/hash/1fa1ab11f4bd5f94b2ec20e794dbfa3b-Abstract-Conference.html).
* Operational model monitoring: Anthropic's interpretability research describes dictionary-learning features and explicitly points toward monitoring dangerous behaviors. TACO translates internal signatures into monitors, exclusions, and re-audit triggers. Source: [Mapping the Mind of a Large Language Model](https://www.anthropic.com/research/mapping-mind-language-model).

The core claim is therefore research-adjacent but not overclaimed: this demo does not prove actuarial validity. It proves that replayable failures, internal traces, controls, exclusions, and binders can be represented as one coherent underwriting workflow.

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
taco_demo/data/maniskill_suite/ supplemental 40-video ManiSkill/RMA-style evidence suite
taco_demo/data/binders/        issued JSON and Markdown binders
```

## Buyer Workflow

```text
Robot OEM / Enterprise Buyer
  submits pre-deployment application
  -> TACO generates replayable failure evidence
  -> engineering team reviews failure boundary and monitor
  -> underwriter reviews quote, controls, exclusions
  -> binder is issued with re-audit triggers
  -> runtime compliance and incident logs feed renewals
```

Artifacts by role:

* Robotics VP Engineering: replay GIFs, failure certificates, trace plots.
* Risk manager: conditional quote, exclusions, required controls.
* Broker/MGA: binder, premium breakdown, known failure family taxonomy.
* Carrier/reinsurer: actuarial evidence memo, mitigability scores, re-audit conditions.

## ManiSkill/RMA Video Evidence Suite

The demo includes a supplemental 40-video ManiSkill/RMA-style gallery under `taco_demo/data/maniskill_suite/`. Each case has:

* a generated replay GIF,
* a ManiSkill environment label,
* a failure family,
* the internal/behavioral signal TACO identifies,
* an underwriting interpretation,
* a required control.

The suite covers eight failure families across five ManiSkill-style RMA environments: occlusion-induced wrong grasp, semantic distractor confusion, contact force overshoot, rope entanglement memory bias, camera glare pose drift, drawer collision edge cases, workspace boundary overreach, and transparent-object depth error.

Generate it locally or on the cluster with:

```bash
python -m taco_demo.scripts.generate_maniskill_video_suite --force
```

## Insurance Failure And Pricing Workflows

The app includes 10 concrete insurance examples in the `Insurance Examples` tab. Each example shows:

* the insured and robot deployment,
* the failure that would create a claim or exclusion,
* what TACO identifies from replay/internal evidence,
* pricing with controls vs. without controls,
* the required control,
* the exclusion if the control is missing,
* the end-to-end workflow from application to renewal or claim linkage.

The examples cover warehouse manipulation, mobile picking, retail restocking, kitchen prep, parcel sorting, hospital delivery, greenhouse harvesting, inspection/repair, deformable goods packing, and model-update re-audit workflows. The `Investor Case` tab can also download a diligence memo that folds these scenarios into the quote, certificate, metric, and 40-video evidence package.

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

The current demo is calibrated so the Apex Robotics quote lands in a believable visible range:

* All controls enabled: about `$29,800/month`.
* Occlusion monitor disabled: about `$51,500/month` plus a known-family exclusion.

That spread is the commercial point of the demo: controls do not just improve safety; they change the insurance terms.

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

## VC Pitch Track

One-liner: TACO is the evidence layer that makes frontier robot autonomy insurable before claims history exists.

Problem: robot deployments are moving faster than loss-history underwriting. Enterprise buyers want assurance, carriers want evidence, and robot OEMs need a path to coverage.

Product: a structured underwriting workflow that converts replayable failures and internal model signatures into quotes, controls, exclusions, and binders.

Why now: generalist robot policies and VLA-style systems are pushing into higher-variance environments, while interpretability and simulation tooling are finally good enough to generate richer pre-deployment evidence.

Moat hypotheses:

* Evidence graph: replay certificates, trace metrics, mitigations, exclusions, and claims outcomes compound into proprietary underwriting data.
* Workflow lock-in: brokers, carriers, robotics OEMs, and enterprise risk teams need a shared artifact format for autonomy risk.
* Model-risk taxonomy: repeated failure families become a defensible schema for learned-policy liability.
* Control marketplace: required monitors can become insurability prerequisites for robot deployments.

Seed-stage derisking milestones:

* Convert 3 fallback certificates into 30+ real DreamAudit simulator certificates across LIBERO, ManiSkill, and RoboCasa-style tasks.
* Replace heuristic trace probes with recorded VLA activations and SAE feature dictionaries for at least one open policy.
* Run 2-3 design-partner underwriting reviews with robotics OEMs, specialty brokers, or autonomy insurers.
* Produce a reinsurer-facing loss-evidence memo linking failure families to control effectiveness and premium deltas.
* Log monitor compliance over replay and staged deployment runs to show a renewal data loop.

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
