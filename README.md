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
  |      collision-safe raw NPZ export
  |      explicit layer-to-signal export into the TACO trace schema
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
  |
  +--> Data room + reviewer walkthrough
         checksum-indexed evidence packet
         methodology, pricing, and objection artifacts
         role-specific external-review agenda
         evidence capture form for pilots, LOIs, or reviewer memos
         commercial scale model with market sources, buyer segments, and proof gates
         insurance capacity roadmap with licensing, MGA/fronting, filing, and claims gates
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

signal_map = {
    "vision_encoder": "target_feature",
    "grasp_head": "general_grasp_feature",
    "planner": "transport_feature",
    "memory_probe": "memorized_trajectory_feature",
    "safety_head": "unsafe_trajectory_dominance",
    "action_head": "action_risk",
}

recorder = ActivationRecorder(layer_names=list(signal_map), max_batches=16)
recorder.attach(model)
for observation in rollout_observations:
    model(observation)
trace_path = recorder.save_taco_trace_npz(
    "taco_demo/data/traces/openvla_failure_trace.npz",
    signal_map,
)
recorder.remove()
```

The recorder does not make torch a required dependency for the local demo. In a torch runtime, it uses module forward hooks, snapshots captured outputs before later mutation, handles bf16-style tensors, and writes NPZ files that can feed the internal-risk scoring layer. The layer-to-signal map is explicit: TACO records real activations, then the operator names which layer corresponds to each underwriting signal instead of pretending the mapping is automatically discovered. One-off exports require calibrated `[0, 1]` signal values or an explicit `signal_calibration`; rollout bundles can apply shared calibration across success, failure, and mitigated traces so downstream metrics compare the same scale.

For a full success/failure/mitigated rollout bundle:

```python
from taco_demo.activation_recorder import record_taco_trace_bundle
from taco_demo.trace_scoring import compute_internal_metrics, load_trace

paths = record_taco_trace_bundle(
    model,
    {"success": success_frames, "failure": failure_frames, "mitigated": mitigated_frames},
    layer_names=list(signal_map),
    signal_map=signal_map,
    output_dir="taco_demo/data/traces",
    certificate_id="FR-LIVE-001",
)
metrics = compute_internal_metrics(cert, load_trace(paths["success"]), load_trace(paths["failure"]), load_trace(paths["mitigated"]))
```

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

The Investor Case tab includes pricing diligence sensitivity so reviewers can inspect the factor stack, toggle-derived control deltas, disabled-control exclusions, and the explicit boundary between demo quote logic and actuarially filed pricing.

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
* investor case, VC readiness gates, methodology evidence map, pricing diligence sensitivity, investor objection register, pilot walkthrough playbook, commercial scale model, insurance capacity roadmap, VC data-room checklist, design-partner diligence plan, proposed $5M seed financing plan, data-room manifest export, diligence memo download, hash-indexed ZIP data-room packet export, and uploaded packet verification with a SHA-256 chain-of-custody fingerprint,
* live DreamAudit artifact intake,
* architecture/spec view.

The `DreamAudit Intake` tab scans a local artifact directory and reports not just counts, but underwriting readiness: mapped controls, evidence gaps, minimality coverage, replay/certificate command coverage, behavioral fragility, and an evidence-depth ladder that shows when a broader scan becomes carrier-review-ready. The Investor Case tab can attach that live intake summary to its VC readiness gates, separating demo-only proof points from a carrier-ready real DreamAudit corpus. The current control taxonomy covers occlusion, language override, distractor confusion, action-noise sensitivity, vision-shift sensitivity, calibration sensitivity, and grasp-miss behavior as named underwriting requirements rather than opaque failure labels.

## Research Backing

The methodology is intentionally research-adjacent without overstating actuarial validity:

* SIMPLER / CoRL 2024: simulation can provide scalable, reproducible robot-policy evaluation under distribution shift.
* Domain randomization / CoRL 2018: simulator optimization needs robustness and transfer controls.
* Sparse autoencoder interpretability / ICLR 2024: internal activations can expose behavior-relevant features.
* Anthropic feature mapping research: feature-level interpretability can support operational monitoring.

TACO translates those directions into an insurance workflow: failure evidence, internal risk signatures, required controls, exclusions, binders, and renewal signals.

The Investor Case tab now includes a methodology evidence map. It separates research-backed direction, local artifact evidence, live DreamAudit transfer evidence, and still-open assumptions so the product does not imply that demo traces are actuarial validation or that simulator evidence alone is enough for launch.

It also includes an investor objection register that maps likely VC and carrier pushback to current artifacts, open gaps, and the next proof to collect. This keeps the pitch honest: objection answers can be artifact-backed while still requiring external validation.

The pilot walkthrough playbook converts the data-room artifacts into a reviewer meeting workflow. It gives broker, MGA, OEM, carrier, and reinsurer reviewers a checksum-verification step, role-specific questions, pass/fail criteria, evidence capture fields, conversion gates, and red flags. It is a capture workflow for external evidence, not a claim that those pilots, LOIs, or capacity discussions have already happened.

The commercial scale model adds the missing VC lens: market-context sources, buyer segments, first-product motions, modeled revenue scenarios, and proof gates that would make a $5M seed round rational. It is explicitly a scenario model, not audited TAM, committed revenue, signed pipeline, insurance capacity, or an actuarial filing.

The insurance capacity roadmap makes the regulatory path diligence-readable. It separates evidence-only revenue from licensed producer/referral, MGA/fronting, carrier/reinsurer capacity, rate/form, actuarial, claims, renewal, and data-governance workstreams. It is not legal advice, regulatory approval, capacity, or an insurance offer.

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

The financing plan in the Investor Case tab connects a proposed $5M seed round to 18 months of milestones: production internals integration, broader simulator evidence, design-partner pilots, insurance compliance/actuarial work, and secure enterprise data-room operations. It is a diligence artifact, not a claim that capital, capacity, or customers are already committed.

## Boundaries

This repository is a local proof of concept and not an offer of insurance. The shipped evidence set is there so the workflow can be tested offline. The design-partner plan and pilot walkthrough playbook are external-validation workflows, not evidence of signed partners, completed pilots, or customer demand. The commercial scale model is a bounded scenario model, not committed revenue or audited market sizing. The insurance capacity roadmap is not legal advice, regulatory approval, carrier capacity, or filed pricing. The seed financing plan is a proposed use-of-funds and milestone plan, not committed financing. Real deployment would require carrier partnerships, compliance review, filed pricing or MGA structure, design-partner evidence, and live simulator/model integrations.
