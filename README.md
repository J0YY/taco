# TACO - The Autonomous Casualty Office

TACO is a working local proof of concept for learned-policy liability insurance for robotics. It turns robot-policy failure evidence into underwriting artifacts: replayable failure certificates, internal model-risk traces, required controls, exclusions, quote terms, binders, renewal signals, and investor diligence material.

The wedge is pre-deployment robotics insurance. A robot OEM or enterprise buyer may not have fleet telemetry or claims history yet, but they can still produce structured evidence from simulator replays, DreamAudit certificates, model activations, and control effectiveness. TACO packages that evidence in a form that a robotics engineering lead, broker, carrier, reinsurer, and enterprise risk team can all inspect.

## Run Locally

Use the repo-local virtual environment that has already been installed on this machine:

```bash
source .venv/bin/activate
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py
```

Fresh checkout setup:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r taco_demo/requirements-taco.txt
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py
```

If Streamlit cannot be launched in the current shell, this import check verifies the app can load:

```bash
python -c "import taco_demo.app"
```

## Demo Story

Apex Robotics wants $10M of Learned-Policy Liability coverage for 200 warehouse manipulation arms. They are pre-deployment, so traditional underwriting is blocked by the absence of loss history and fleet telemetry. TACO runs an internal underwriting audit instead:

```text
Application
-> failure certificate ingestion
-> replay evidence
-> internal activation / trace scoring
-> required controls and exclusions
-> conditional quote
-> binder
-> runtime compliance and renewal loop
```

The first-screen workflow is meant to read like an insurance desk, not a generic ML dashboard: application blocked, internal audit, replayable failures, internal signals, pricing, binder, renewal evidence, and investor case.

## Architecture

```text
Robot OEM / enterprise buyer
  |
  v
InsuranceApplication
  |
  +--> DreamAudit adapter
  |      accepts compact LIBERO/OpenVLA certificates
  |      accepts richer dreamaudit.types.Certificate-style JSON
  |      preserves validation, minimality, perturbation, patch recipe, and source metadata
  |
  +--> Replay evidence
  |      simulator videos, GIF replays, certificate commands, ManiSkill/RMA-style evidence suite
  |
  +--> Activation recorder
  |      optional torch-style forward hooks
  |      selected layer capture
  |      bf16-safe conversion
  |      collision-safe NPZ export
  |
  +--> Internal trace scoring
  |      concept coverage
  |      feature stability
  |      unsafe dominance
  |      early warning margin
  |      causal mitigability
  |
  +--> Quote engine
  |      behavioral fragility multiplier
  |      internal risk multiplier
  |      mitigation discount
  |      exclusions when controls are disabled
  |
  +--> Binder + renewal loop
         JSON/Markdown binder
         monitor compliance events
         incident/claims response
         renewal premium impact
```

## Real Integration Path

TACO is designed to run in two modes:

* **Offline evidence mode:** ships with local certificates, trace arrays, videos, insurance scenarios, and ManiSkill/RMA-style examples so the product can be tested without GPUs, Docker, cloud services, or external APIs.
* **Live evidence mode:** ingests DreamAudit certificate JSONs and records policy activations through hook-based capture when a robot policy runtime is available.

The important point is that the code path is not just a presentation shell. The same schemas, metrics, quote logic, and binder generation are used whether evidence comes from the local fixture set or from DreamAudit and model activations.

### DreamAudit Certificates

```python
from taco_demo.dreamaudit_adapter import adapt_dreamaudit_certificates, summarize_adapted_certificates

certs = adapt_dreamaudit_certificates(
    "/Users/joyyang/Projects/dreamaudit/artifacts/libero_openvla_observation_proposal_balanced_lp2_h160/validate/counterfactual_certificates",
    limit=30,
)
print(summarize_adapted_certificates(certs))
```

The adapter preserves source paths, simulator/perturbed validation, world-model discovery, minimality reports, perturbation payloads, patch recipes, and replay or certificate-inspection commands. It supports visual perturbations, action-noise certificates, language perturbations, and rich synthetic DreamAudit certificates.

### Activation Recording

```python
from taco_demo.activation_recorder import ActivationRecorder

recorder = ActivationRecorder(layer_names=["vision_encoder", "action_head"], max_batches=16)
recorder.attach(model)
for observation in rollout_observations:
    model(observation)
trace_path = recorder.save_npz("taco_demo/data/traces/openvla_activations.npz")
recorder.remove()
```

The recorder does not make torch a required dependency for the local demo. In a torch runtime, it uses module forward hooks, snapshots captured outputs before later mutation, handles bf16-style tensors, and writes NPZ files that can feed the internal-risk scoring layer.

## Evidence Objects

TACO uses stable dataclass JSON contracts in `taco_demo/schemas.py`:

* `InsuranceApplication`
* `FailureCertificate`
* `ReplayArtifacts`
* `InternalRiskMetrics`
* `QuoteBreakdown`
* `PolicyBinder`

Data and generated artifacts live under:

```text
taco_demo/data/applications/      insurance applications
taco_demo/data/certificates/      failure certificate JSON
taco_demo/data/traces/            internal trace NPZ files
taco_demo/data/videos/            replay GIFs
taco_demo/data/maniskill_suite/   40-video ManiSkill/RMA-style evidence suite
taco_demo/data/binders/           issued JSON and Markdown binders
```

## Underwriting Metrics

TACO scores internal risk from trace arrays:

* **Concept Coverage:** whether required internal signals are available and non-flat.
* **Feature Stability:** whether target-relevant features collapse before failure.
* **Unsafe Dominance:** whether unsafe/action-risk features dominate the pre-failure window.
* **Early Warning Margin:** time between risk crossing and physical failure.
* **Causal Mitigability:** reduction in action risk after the required control is applied.

Internal risk score:

```text
0.20 * (1 - concept_coverage_score)
+ 0.25 * (1 - feature_stability_score)
+ 0.25 * unsafe_dominance_score
+ 0.20 * (1 - causal_mitigability_score)
+ 0.10 * early_warning_penalty
```

## Quote Logic

Base monthly premium:

```text
coverage_requested_usd * 0.0008 + deployment_units * 35
```

Behavioral fragility rises when the failure boundary is cheap and the neighborhood failure rate is high:

```text
cost_factor = 1 + max(0, 0.6 - minimal_failure_cost)
rate_factor = 1 + 0.75 * failure_rate_neighborhood
```

TACO blends behavioral fragility, internal risk, and mitigability. Required controls reduce the quote only when enabled. Disabled controls create known-family exclusions.

For the Apex Robotics scenario, controls enabled lands around `$29,800/month`; disabling the occlusion-risk monitor moves the quote to about `$51,500/month` with a known-family exclusion. The commercial point is that controls and evidence change insurance terms, not just safety scores.

## Product Surface

The Streamlit app includes:

* application intake and traditional-underwriting block,
* internal underwriting audit,
* replay evidence viewer,
* internal signal plots,
* quote controls and exclusions,
* conditional binder generation,
* 40 ManiSkill/RMA-style failure examples,
* 10 insurance failure/pricing workflows,
* runtime compliance and renewal loop,
* investor case and diligence memo download,
* live DreamAudit artifact intake,
* architecture/spec view.

The `DreamAudit Intake` tab scans a local artifact directory and reports not just counts, but underwriting readiness: mapped controls, evidence gaps, minimality coverage, replay/certificate command coverage, and behavioral fragility. The current control taxonomy covers occlusion, language override, distractor confusion, action-noise sensitivity, and vision-shift sensitivity as named underwriting requirements rather than opaque failure labels.

## Research Backing

The methodology is intentionally research-adjacent without overstating actuarial validity:

* SIMPLER / CoRL 2024: simulation can provide scalable, reproducible robot-policy evaluation under distribution shift.
* Domain randomization / CoRL 2018: simulator optimization needs robustness and transfer controls.
* Sparse autoencoder interpretability / ICLR 2024: internal activations can expose behavior-relevant features.
* Anthropic feature mapping research: feature-level interpretability can support operational monitoring.

TACO translates those directions into an insurance workflow: failure evidence, internal risk signatures, required controls, exclusions, binders, and renewal signals.

## Venture Thesis

TACO is not just robot QA. The larger opportunity is a system of record for autonomy-risk evidence:

* replay certificates,
* trace and activation metrics,
* mitigations,
* exclusions,
* runtime monitor compliance,
* renewal outcomes,
* claims linkage.

The wedge is learned-policy liability for robotics OEMs and enterprise buyers before claims history exists. The expansion path is an evidence network shared by robotics companies, brokers, carriers, reinsurers, certification partners, and enterprise procurement teams.

## Boundaries

This repository is a local proof of concept and not an offer of insurance. The shipped evidence set is there so the workflow can be tested offline. Real deployment would require carrier partnerships, compliance review, filed pricing or MGA structure, design-partner evidence, and live simulator/model integrations.
