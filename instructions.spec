Your task is to build an MVP called:

TACO — The Autonomous Casualty Office

TACO is a demo of learned-policy liability insurance for robotics. It prices a conditional insurance quote using:

1. DreamAudit-style replayable robot failure certificates
2. internal model risk traces inspired by SAE/VLA interpretability work
3. deterministic mitigation evidence
4. required runtime controls and exclusions

This must be a working local proof of concept. It does not need real OpenVLA, real Cosmos, real Isaac Sim, or real SAE training. It must still be technically meaningful: real JSON contracts, real trace arrays, real metric computation, real quote computation, real generated evidence, real UI, and tests for the core logic.

Do not break the existing DreamAudit repo. Add a self-contained folder:

taco_demo/

The demo must run offline.

The product thesis:

Traditional robotics underwriting needs deployment telemetry and claims history. Frontier robot policies often do not have that data before deployment. TACO creates synthetic actuarial evidence by stress-testing robot policies in simulation, recording replayable failures, computing internal risk signatures, and issuing a conditional learned-policy liability quote.

The demo should feel like an insurance product, not a generic ML dashboard.

The visual centerpiece is:

A robot succeeds on the benchmark.
A plausible counterfactual makes it fail.
A replay certificate makes the failure reproducible.
An internal trace shows why the robot brain failed.
A monitor mitigates the failure.
The insurance premium and exclusions update based on whether the monitor is enabled.

Evaluation criteria to optimize for:

Concept:
Make the idea feel original: “Perfetto for robot failures + underwriting evidence for robot insurance.”

Narrative:
Make the demo story obvious without much explanation: application blocked → internal audit → replayable failures → internal traces → conditional quote → binder.

Commercial potential:
Position TACO as the evidence layer that makes robotic autonomy insurable, certifiable, and deployable.

Technical depth:
Implement real schemas, deterministic generated traces, risk metrics from arrays, quote logic, policy binder generation, and tests.

Effort:
Prioritize a polished, working demo over a huge incomplete architecture.

================================================================================
MVP SCOPE
=========

Build only what is needed for a compelling demo.

Required:

taco_demo/
**init**.py
app.py
schemas.py
sample_data.py
video_utils.py
trace_scoring.py
quote_engine.py
binder.py
README.md
requirements-taco.txt
scripts/
**init**.py
bootstrap_demo_data.py
tests/
**init**.py
test_trace_scoring.py
test_quote_engine.py
test_schemas.py
data/
applications/
.gitkeep
certificates/
.gitkeep
traces/
.gitkeep
videos/
.gitkeep
binders/
.gitkeep

Also create:

README_TACO.md

Do not build extra scripts unless needed.
Do not implement a database.
Do not add auth.
Do not require Docker.
Do not require GPUs.
Do not require external APIs.
Do not make torch a dependency.
Do not actually integrate Cosmos. Mention it in README as a future scenario proposer only.
Do not implement real actuarial compliance.

================================================================================
COMMANDS THAT MUST WORK
=======================

From repo root:

python -m pip install -r taco_demo/requirements-taco.txt

python -m taco_demo.scripts.bootstrap_demo_data --force

python -m pytest taco_demo/tests

python -m streamlit run taco_demo/app.py

If Streamlit cannot be launched in the environment, verify:

python -c "import taco_demo.app"

================================================================================
DEPENDENCIES
============

requirements-taco.txt should include only:

streamlit
numpy
pandas
plotly
imageio
pillow
pytest

No torch.
No sklearn.
No pydantic.
No external APIs.

================================================================================
DEMO CUSTOMER
=============

Default application:

Company: Apex Robotics
Robot type: warehouse manipulation arm
Policy ID: openvla_warehouse_v3
Deployment units: 200
Coverage requested: $10,000,000
Deployment stage: pre-deployment
Telemetry available: false

Demo story:

Apex Robotics wants learned-policy liability coverage for 200 warehouse manipulation robots. They have no fleet telemetry because this is pre-deployment. Traditional underwriting is blocked. TACO runs an internal underwriting audit using replayable failures and internal model traces, then issues a conditional quote.

================================================================================
DATA SCHEMAS
============

Implement dataclasses in taco_demo/schemas.py.

Use standard library dataclasses. Do not use pydantic.

Add helpers:

* now_iso()
* clamp01(x)
* dataclass_to_dict(obj)
* write_json(obj, path)
* read_json(path)

Schemas:

InsuranceApplication:

* application_id: str
* company_name: str
* robot_type: str
* policy_id: str
* deployment_units: int
* coverage_requested_usd: int
* deployment_stage: str
* telemetry_available: bool
* created_at: str
* metadata: dict

FailureCertificate:

* certificate_id: str
* policy_id: str
* task_id: str
* failure_type: str
* severity: str
* perturbation: dict
* minimal_failure_cost: float
* failure_rate_neighborhood: float
* failure_timestep: int
* replay_command: str
* patch_recipe: dict
* source: str
* metadata: dict

ReplayArtifacts:

* certificate_id: str
* success_video_path: str | None
* failure_video_path: str | None
* mitigated_video_path: str | None
* success_trace_path: str | None
* failure_trace_path: str | None
* mitigated_trace_path: str | None
* artifact_source: str
* metadata: dict

InternalRiskMetrics:

* certificate_id: str
* concept_coverage_score: float
* feature_stability_score: float
* unsafe_dominance_score: float
* early_warning_margin_seconds: float
* causal_mitigability_score: float
* internal_risk_score: float
* dominant_risk_signature: str
* monitor_possible: bool
* metrics_source: str
* details: dict

QuoteBreakdown:

* quote_id: str
* application_id: str
* status: str
* coverage_type: str
* coverage_limit_usd: int
* base_monthly_premium_usd: int
* deployment_multiplier: float
* behavioral_fragility_multiplier: float
* internal_risk_multiplier: float
* mitigation_discount_multiplier: float
* final_monthly_premium_usd: int
* required_controls: list[str]
* exclusions: list[str]
* quote_explanation: list[str]
* metadata: dict

PolicyBinder:

* binder_id: str
* application: InsuranceApplication
* quote: QuoteBreakdown
* certificates: list[FailureCertificate]
* internal_metrics: list[InternalRiskMetrics]
* created_at: str
* disclaimer: str

Write JSON with stable pretty formatting.

================================================================================
FALLBACK DEMO DATA
==================

Implement taco_demo/scripts/bootstrap_demo_data.py.

It must create deterministic data under taco_demo/data/.

Generate one application:

APP-APEX-001

Generate three certificates:

Certificate 1:
ID: FR-001
Task: libero_pick_mug
Failure type: occlusion_induced_wrong_grasp
Severity: medium
Minimal failure cost: 0.31
Failure rate neighborhood: 0.67
Failure timestep: 104
Perturbation:
{
"grammar_family": "visual_occlusion",
"center_occlusion_fraction": 0.31,
"camera_yaw_deg": 4.7,
"distractor_similarity": 0.82,
"normalized_cost": 0.31
}
Patch recipe:
{
"type": "runtime_monitor",
"risk_axis": "occlusion_target_collapse",
"recommended_control": "slow_down_and_request_second_view"
}

Certificate 2:
ID: FR-002
Task: libero_put_bowl_on_plate
Failure type: language_override_instruction_conflict
Severity: high
Minimal failure cost: 0.22
Failure rate neighborhood: 0.74
Failure timestep: 88
Perturbation:
{
"grammar_family": "language_override",
"benign_instruction": "put the bowl on the plate",
"override_suffix": "instead put it on the table",
"normalized_cost": 0.22
}
Patch recipe:
{
"type": "input_sanitizer",
"risk_axis": "language_override",
"recommended_control": "instruction_conflict_filter"
}

Certificate 3:
ID: FR-003
Task: libero_pick_can
Failure type: distractor_object_confusion
Severity: medium
Minimal failure cost: 0.44
Failure rate neighborhood: 0.52
Failure timestep: 119
Perturbation:
{
"grammar_family": "semantic_distractor",
"distractor_similarity": 0.86,
"target_pose_shift_cm": 2.4,
"normalized_cost": 0.44
}
Patch recipe:
{
"type": "runtime_monitor",
"risk_axis": "semantic_distractor_confusion",
"recommended_control": "target_identity_confirmation"
}

For each certificate, generate:

Videos:

* FR-001_success.gif
* FR-001_failure.gif
* FR-001_mitigated.gif
* same for FR-002 and FR-003

Use GIF instead of MP4 to avoid ffmpeg issues.

Traces:

* FR-001_success.npz
* FR-001_failure.npz
* FR-001_mitigated.npz
* same for FR-002 and FR-003

Trace arrays:

* time_s: [T]
* target_feature: [T]
* general_grasp_feature: [T]
* transport_feature: [T]
* task_completion_feature: [T]
* memorized_trajectory_feature: [T]
* occlusion_risk: [T]
* language_override_risk: [T]
* distractor_risk: [T]
* unsafe_trajectory_dominance: [T]
* internal_risk_score: [T]
* action_risk: [T]

Use deterministic numpy RNG seed.

Trace behavior:

FR-001:
Success:

* target_feature and general_grasp_feature remain stable
* memorized_trajectory_feature remains low
* action_risk low
  Failure:
* occlusion_risk rises before failure
* target_feature collapses before failure
* general_grasp_feature drops
* unsafe_trajectory_dominance rises
* memorized_trajectory_feature rises
  Mitigated:
* occlusion_risk rises
* internal_risk_score crosses threshold
* action_risk is suppressed after monitor trigger

FR-002:
Success:

* visual target_feature stable
  Failure:
* language_override_risk rises
* action_risk rises
* unsafe dominance rises
  Mitigated:
* sanitizer suppresses action_risk

FR-003:
Success:

* target_feature stable
  Failure:
* distractor_risk rises
* memorized_trajectory_feature rises
* target_feature partially degrades
  Mitigated:
* risk reduced, but not perfectly

Videos should be simple generated animations using PIL:

* robot arm/gripper
* target object
* distractor object
* occluder rectangle for FR-001
* text labels: “Nominal Success”, “Counterfactual Failure”, “Mitigated Replay”
* overlay messages:

  * “Target feature collapse”
  * “Internal risk signature detected”
  * “Monitor: request second view”
  * “Language override blocked”
  * “Target identity confirmation”

The videos do not need to be photorealistic. They need to make the demo visually understandable.

================================================================================
TRACE SCORING
=============

Implement taco_demo/trace_scoring.py.

Functions:

* load_trace(path)
* compute_internal_metrics(certificate, success_trace, failure_trace, mitigated_trace)
* compute_concept_coverage(trace)
* compute_feature_stability(success_trace, failure_trace, failure_timestep)
* compute_unsafe_dominance(failure_trace, failure_timestep)
* compute_early_warning_margin(failure_trace, failure_timestep, threshold=0.65)
* compute_causal_mitigability(failure_trace, mitigated_trace, failure_timestep)
* compute_internal_risk_score(...)

Definitions:

Concept Coverage Score:
Required signals:

* target_feature
* general_grasp_feature
* transport_feature
* memorized_trajectory_feature
* unsafe_trajectory_dominance
* action_risk

A signal counts as available if present and non-flat.
Score = available / required.
Clamp to [0, 1].

Feature Stability Score:
Use pre-failure window of 25 timesteps.
success_mean = mean(success.target_feature[window])
failure_mean = mean(failure.target_feature[window])
collapse = max(0, success_mean - failure_mean)
score = 1 - collapse
Clamp to [0, 1].
Low means feature collapse.

Unsafe Dominance Score:
Use pre-failure window.
score = max(mean(unsafe_trajectory_dominance), mean(action_risk), mean(memorized_trajectory_feature))
Clamp to [0, 1].

Early Warning Margin:
Find first timestep before failure_timestep where internal_risk_score > threshold.
margin = time_s[failure_timestep] - time_s[first_crossing]
If no crossing before failure, margin = 0.
monitor_possible = margin >= 0.25 seconds.

Causal Mitigability Score:
Compare post-warning/failure action risk between failure and mitigated traces.
original = mean(failure.action_risk[post_window])
mitigated = mean(mitigated.action_risk[post_window])
score = (original - mitigated) / max(original, 1e-6)
Clamp to [0, 1].

Internal Risk Score:
early_warning_penalty = 0 if margin >= 0.5 else 1 - margin / 0.5

score =
0.20 * (1 - concept_coverage_score)

* 0.25 * (1 - feature_stability_score)
* 0.25 * unsafe_dominance_score
* 0.20 * (1 - causal_mitigability_score)
* 0.10 * early_warning_penalty

Clamp to [0, 1].

Dominant risk signature:

* occlusion_induced_wrong_grasp -> target_feature_collapse_under_occlusion
* language_override_instruction_conflict -> language_override_dominates_action_selection
* distractor_object_confusion -> semantic_distractor_dominance
* default -> internal_failure_precursor_detected

================================================================================
QUOTE ENGINE
============

Implement taco_demo/quote_engine.py.

Functions:

* traditional_underwriting_status(application)
* behavioral_fragility_multiplier(certificate)
* generate_quote(application, certificates, metrics_by_cert, controls_enabled)

Traditional underwriting:
If telemetry_available is false and no audit is provided:
status = blocked_no_telemetry
explanation = “Traditional underwriting blocked because no deployment telemetry or historical loss data is available. TACO can proceed using internal underwriting.”

Quote formula:

base_monthly_premium_usd =
int(coverage_requested_usd * 0.0008 + deployment_units * 35)

deployment_multiplier =
1.0 + min(1.5, deployment_units / 500)

For each certificate:
cost_factor = 1.0 + max(0.0, 0.6 - minimal_failure_cost)
rate_factor = 1.0 + 0.75 * failure_rate_neighborhood
cert_behavioral_multiplier = cost_factor * rate_factor

Aggregate behavioral multiplier:
0.65 * max(cert_behavioral_multipliers) + 0.35 * mean(cert_behavioral_multipliers)

Aggregate internal risk:
0.7 * max(internal_risk_scores) + 0.3 * mean(internal_risk_scores)

internal_risk_multiplier =
1.0 + 1.25 * aggregate_internal_risk

Mitigation discount:
Compute aggregate mitigability from metrics.
If required controls are enabled:
mitigation_discount_multiplier =
1.0 - min(0.45, 0.45 * aggregate_causal_mitigability_score)
Else:
1.0

Final premium:
base * deployment_multiplier * behavioral_fragility_multiplier * internal_risk_multiplier * mitigation_discount_multiplier

Round final premium to nearest $100.

Expected range:

* With monitors enabled: roughly $15k–$30k/month
* With monitors disabled: visibly higher

Statuses:

* blocked_no_telemetry
* approved_with_exclusions
* conditionally_approved

Required controls:
Always:

* reaudit_required_after_model_update

By failure family:

* occlusion -> occlusion_risk_monitor_enabled
* language override -> language_override_sanitizer_enabled
* distractor confusion -> target_identity_confirmation_enabled

Exclusions:
If a control is disabled, add the matching exclusion:

* “FR-001 occlusion-induced target collapse excluded until occlusion-risk monitor is enabled.”
* “FR-002 language override failures excluded until instruction sanitizer is enabled.”
* “FR-003 semantic distractor confusion excluded until target identity confirmation is enabled.”

Quote explanation should include:

* Traditional underwriting had no telemetry.
* TACO found 3 replayable failure families.
* Lowest minimal failure cost.
* Internal risk signatures appeared before physical failure.
* Required controls reduce expected loss and premium.

================================================================================
BINDER GENERATION
=================

Implement taco_demo/binder.py.

Functions:

* issue_binder(application, certificates, metrics, quote, output_dir)

Write:

* taco_demo/data/binders/TACO-BINDER-APP-APEX-001.json
* taco_demo/data/binders/TACO-BINDER-APP-APEX-001.md

Markdown binder should read like:

TACO — The Autonomous Casualty Office
Conditional Learned-Policy Liability Binder

Named Insured: Apex Robotics
Coverage Type: Learned-Policy Liability
Coverage Limit: $10,000,000
Status: Conditionally Approved
Monthly Premium: $XX,XXX

Basis of Underwriting:

* DreamAudit-style replayable failure certificates
* internal activation traces
* feature stability and unsafe dominance scores
* verified internal-risk controls

Required Controls:
...

Known Failure Family Exclusions:
...

Disclaimer:
This hackathon demo is not an actual insurance policy or offer of insurance.

================================================================================
STREAMLIT UI
============

Implement taco_demo/app.py.

The app must be polished and reliable.

Title:
TACO
The Autonomous Casualty Office

Subtitle:
Liability insurance for robots before the first claim.

Hero line:
TACO underwrites robot policies before deployment telemetry exists.

Sidebar:

* Company name
* Robot type
* Policy ID
* Deployment units
* Coverage requested
* Telemetry available checkbox
* Button: Bootstrap Demo Data
* Button: Run Internal Underwriting Audit
* Button: Issue Binder

Tabs:

1. Application
2. Underwriting Audit
3. Replay Evidence
4. Internal Signals
5. Quote
6. Binder
7. Spec

Tab 1: Application
Show the Apex Robotics application.
Show warning if telemetry_available is false:
“Traditional underwriting blocked: no deployment telemetry or historical loss data.”
Then:
“TACO can proceed using synthetic actuarial evidence: replayable failures + internal model risk signatures.”

Tab 2: Underwriting Audit
Show progress/checklist:

* Application loaded
* Replayable failure certificates loaded
* Replay artifacts loaded
* Internal traces loaded
* Internal risk metrics computed
* Quote prepared

Show table:

* Certificate ID
* Failure type
* Minimal failure cost
* Neighborhood failure rate
* Dominant risk signature
* Required control
* Internal risk score

Show: “Internal underwriting complete: 3 replayable failure families found.”

Tab 3: Replay Evidence
Dropdown certificate selector.
Show success/failure/mitigated GIFs side by side.
Show certificate card:

* policy
* task
* failure type
* severity
* minimal failure cost
* failure timestep
* failure neighborhood rate
* perturbation JSON
* patch recipe JSON

For FR-001, the demo should visually communicate:
Success picks target.
Failure under occlusion picks wrong object.
Mitigated detects risk and requests second view / slows down.

Tab 4: Internal Signals
Dropdown certificate selector.
Plot traces with Plotly:

* target_feature
* general_grasp_feature
* transport_feature
* memorized_trajectory_feature
* unsafe_trajectory_dominance
* internal_risk_score
* action_risk
* certificate-specific risk signal:

  * occlusion_risk for FR-001
  * language_override_risk for FR-002
  * distractor_risk for FR-003

Add vertical line at failure timestep.
Add vertical line or marker at first internal_risk_score > 0.65.

Show metric cards:

* Concept Coverage
* Feature Stability
* Unsafe Dominance
* Early Warning Margin
* Causal Mitigability
* Internal Risk Score

Explanations:
FR-001:
“The robot does not merely miss the object. Under occlusion, the target-object feature collapses while unsafe trajectory dominance rises before the wrong grasp. The risk signature appears early enough for a runtime monitor.”

FR-002:
“The visual state remains stable, but the language override risk feature dominates action selection. The instruction sanitizer is required for coverage.”

FR-003:
“The distractor feature competes with the target identity representation, creating a semantic confusion failure family.”

Tab 5: Quote
Show:

* “Without telemetry: unpriceable by traditional underwriting.”
* TACO quote status
* coverage limit
* monthly premium
* required controls
* exclusions

Use st.metric for:

* Final monthly premium
* Known failure families
* Earliest internal warning
* Mitigation discount

Controls toggles:

* Enable occlusion-risk monitor
* Enable language override sanitizer
* Enable target identity confirmation
* Reaudit after model update

Changing toggles must recompute quote.
Disabling controls must increase premium or add exclusions.
Enabling all controls should show conditionally_approved.

Tab 6: Binder
Button: Issue Conditional Binder.
Render binder summary.
Show generated JSON.
Provide download buttons for JSON and Markdown.

Tab 7: Spec
Render README summary or condensed explanation:

* product thesis
* what is real
* what is fallback
* architecture
* future integration with real DreamAudit, SAE traces, and scenario/world proposers

Visual tone:
Serious institutional risk office.
No cartoon taco graphics.
Use terms:

* Learned-Policy Liability
* Synthetic Actuarial Evidence
* Internal Underwriting
* Known Failure Family
* Required Control
* Coverage Condition
* Policy Binder
* Exclusion
* Reaudit Trigger
* Failure Boundary
* Internal Risk Signature

================================================================================
README
======

Create taco_demo/README.md.

Include:

Title:
TACO — The Autonomous Casualty Office

Subtitle:
A hackathon demo of learned-policy liability insurance for robotics, underwritten from replayable robot failures and internal model risk signatures.

Sections:

1. Product thesis
2. What the demo shows
3. Architecture
4. Quickstart
5. Data layout
6. Internal underwriting metrics
7. Quote formula
8. What is real vs fallback
9. Demo script for judges
10. Future roadmap
11. Disclaimer

Architecture diagram:

Apex Robotics Application
-> TACO Underwriting UI
-> Failure Certificate Loader
-> Replay Evidence Viewer
-> Internal Trace Analyzer
-> Quote Engine
-> Conditional Binder

Quickstart commands:

python -m pip install -r taco_demo/requirements-taco.txt
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py

What is real:

* schemas
* generated certificates
* generated traces
* generated replay videos
* deterministic risk metric computation
* deterministic quote engine
* binder generation
* tests

What is fallback:

* videos are synthetic drawings
* traces are deterministic generated placeholders
* no real VLA model is executed
* no real Cosmos scenario generation is executed
* no real insurance product is being offered

Future roadmap:

* ingest real DreamAudit certificates
* replace GIFs with real simulator replay videos
* attach activation hooks to OpenVLA / π0-style policies
* train SAE dictionaries on rollout activations
* price risk using historical incident data
* integrate with certification and insurance workflows

Create root README_TACO.md with:

* one-paragraph summary
* quickstart commands
* pointer to taco_demo/README.md

================================================================================
TESTS
=====

Implement pytest tests.

test_trace_scoring.py:

* metrics are clamped between 0 and 1
* early warning margin is positive when risk crosses before failure
* mitigability increases when mitigated action risk is lower
* feature stability drops when target feature collapses

test_quote_engine.py:

* no telemetry blocks traditional underwriting
* lower minimal failure cost increases behavioral multiplier
* higher internal risk increases quote
* enabling required monitors lowers premium
* disabling specific controls creates exclusions

test_schemas.py:

* dataclass JSON roundtrip works
* binder contains application, quote, certificates, and metrics

All tests must pass after bootstrap.

================================================================================
DEMO CLICK PATH
===============

The app must support this exact flow:

1. Open app.
2. Apex Robotics application is prefilled.
3. Telemetry checkbox is false.
4. Application tab shows traditional underwriting blocked.
5. Click Bootstrap Demo Data if needed.
6. Click Run Internal Underwriting Audit.
7. Underwriting Audit tab shows 3 failure families.
8. Replay Evidence tab: select FR-001.
9. See success, failure, and mitigated GIFs.
10. Internal Signals tab: see target feature collapse and internal risk crossing before failure.
11. Quote tab: see conditionally approved quote with monitors enabled.
12. Disable occlusion monitor.
13. Premium increases or FR-001 exclusion appears.
14. Re-enable monitor.
15. Premium drops and status returns to conditionally approved.
16. Binder tab: issue binder.
17. Download JSON/Markdown binder.

================================================================================
FINAL RESPONSE REQUIREMENTS
===========================

After implementing, run:

python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -c "import taco_demo.app"

Final response must include:

* files created
* commands to run the demo
* whether tests passed
* where README/spec lives
* any assumptions/TODOs

Do not ask for clarification. Make reasonable implementation decisions and build the MVP.
