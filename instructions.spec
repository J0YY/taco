You are working adjacent to an existing robotics auditing repository called DreamAudit, cd .. and go under Projects/dreamaudit to see what I mean. Your task is to scaffold a technically functional hackathon demo product called:

TACO — The Autonomous Casualty Office

TACO is an insurance demo for robotics. It sells conditional learned-policy liability insurance for robots, priced using synthetic actuarial evidence from DreamAudit replayable failures plus internal model risk signatures.

This is not just a dashboard. The core thesis is:

“Robotics insurers normally need deployment telemetry and claims history. For frontier robot policies, that data often does not exist yet. TACO underwrites earlier by stress-testing robot policies in simulation, recording internal activations during success/failure/mitigated rollouts, computing internal risk metrics, and issuing a conditional insurance quote whose premium, exclusions, and required controls depend on those internal metrics.”

Your job is to scaffold this as a working local demo that can run tomorrow.

Important constraints:
- Do NOT break the existing DreamAudit repo.
- Do NOT refactor core DreamAudit code unless absolutely necessary.
- Add a new self-contained folder/package called `taco_demo/`.
- Build an offline-first demo that works even if live simulator/model execution is unavailable.
- But also include adapter code that can ingest real DreamAudit certificates and, where possible, real DreamAudit replay artifacts.
- The demo must be technically real enough: real JSON contracts, real quote computation, real metric computation from trace arrays, real certificate generation, real UI.
- The insurance logic can be a transparent demo formula, but it must be coherent and deterministic.
- The UI must center the insurance product, not just robot QA.
- The final scaffold must include a README containing the full product/technical spec, architecture, quickstart, data contracts, and demo script.
- Add tests for the important core logic.
- Keep dependencies lightweight and local.
- Use Python. Prefer Streamlit for the demo UI unless the repo already has an obvious frontend framework.
- Do not require external services, OpenAI APIs, cloud accounts, web access, databases, or GPUs for the fallback demo.
- If the real DreamAudit integration cannot be fully wired automatically, implement robust stubs/adapters and clearly document where to plug in the real replay commands.
- The fallback data must be explicitly labeled as demo-generated placeholder data, while the architecture should support replacing it with real DreamAudit outputs.

The user is preparing for a hackathon tomorrow and needs a demoable scaffold fast. Prioritize robustness and demo clarity.

================================================================================
PRODUCT CONTEXT
================================================================================

Product name:
TACO — The Autonomous Casualty Office

Product category:
AI-native robotics insurer / MGA-style insurance underwriting demo.

Core product:
Conditional learned-policy liability insurance for robotics, priced using:
1. DreamAudit behavioral failure certificates
2. internal model activation traces
3. feature/probe-based internal risk metrics
4. verified runtime monitors / mitigations
5. policy clauses, exclusions, and premium discounts

The product must feel like an insurance office, not generic SaaS.

Suggested tagline:
“Liability insurance for robots before the first claim.”

Secondary tagline:
“Underwriting robot losses before they become real.”

Demo customer:
Apex Robotics

Demo scenario:
Apex Robotics wants liability insurance for 200 warehouse manipulation robots. They request $10M learned-policy liability coverage. They have no deployment telemetry because this is a pre-deployment rollout. Traditional underwriting is blocked. TACO offers internal underwriting instead.

Demo story:
1. Apex Robotics applies for $10M learned-policy liability coverage.
2. Traditional underwriting is blocked because there is no fleet telemetry or claims history.
3. TACO runs an internal underwriting audit.
4. DreamAudit discovers replayable robot failure certificates.
5. TACO records hidden-state traces during nominal success, counterfactual failure, and mitigated replay.
6. TACO computes internal risk metrics:
   - Concept Coverage Score
   - Feature Stability Score
   - Unsafe Dominance Score
   - Early Warning Margin
   - Causal Mitigability Score
7. TACO generates an insurance quote.
8. The quote changes when required internal-risk monitors are enabled or disabled.
9. TACO issues a conditional Learned-Policy Liability Binder and Internal Underwriting Certificate.

The demo must make this obvious:
The quote is not based only on external pass/fail. The quote depends on robot internals.

================================================================================
TECHNICAL OUTPUTS TO CREATE
================================================================================

Create this new directory structure:

taco_demo/
  __init__.py
  app.py
  config.py
  schemas.py
  dreamaudit_adapter.py
  activation_recorder.py
  feature_scoring.py
  quote_engine.py
  policy_issuer.py
  video_utils.py
  sample_data.py
  README.md
  requirements-taco.txt
  scripts/
    __init__.py
    bootstrap_demo_data.py
    normalize_existing_certs.py
    record_replay_video.py
    precompute_demo.py
  tests/
    __init__.py
    test_quote_engine.py
    test_feature_scoring.py
    test_certificate_schema.py
    test_dreamaudit_adapter.py
  data/
    applications/
      .gitkeep
    dreamaudit_certs/
      .gitkeep
    traces/
      .gitkeep
    videos/
      .gitkeep
    quotes/
      .gitkeep

Also create a root-level convenience file if appropriate:
README_TACO.md

The root-level README_TACO.md can point to taco_demo/README.md and give quickstart commands. Do not overwrite the existing root README unless it is safe to append a tiny section.

================================================================================
COMMANDS THAT MUST WORK
================================================================================

After scaffolding, these commands should work from repo root:

1. Install dependencies:
   python -m pip install -r taco_demo/requirements-taco.txt

2. Bootstrap fallback demo data:
   python -m taco_demo.scripts.bootstrap_demo_data --force

3. Run tests:
   python -m pytest taco_demo/tests

4. Launch demo:
   python -m streamlit run taco_demo/app.py

The app must run successfully after bootstrapping, even without real DreamAudit outputs.

================================================================================
DEPENDENCIES
================================================================================

Use lightweight dependencies in taco_demo/requirements-taco.txt:

streamlit
numpy
pandas
plotly
imageio
pillow
pytest

Optional:
torch should NOT be required for fallback demo.
If torch is available because DreamAudit uses it, activation_recorder.py can support PyTorch hooks. But do not make torch a hard dependency for the demo UI.

Avoid scikit-learn unless absolutely necessary. Implement simple vector/probe computations with numpy.

================================================================================
DREAMAUDIT INTEGRATION REQUIREMENTS
================================================================================

You need to inspect the existing repo before writing the adapter.

Search the repo for:
- “certificate_id”
- “patch_recipe”
- “replay_command”
- “minimality”
- “minimal_cost”
- “failure_type”
- “replay”
- “rollout”
- “libero”
- “openvla”
- “video”
- “render”
- “activation”
- “policy_id”
- “task_id”

Use this inspection to make the adapter compatible with existing DreamAudit artifacts where possible.

The adapter must support two modes:

Mode A: real artifact mode
- Load real DreamAudit JSON certificates from one or more directories.
- Normalize them into TACO’s canonical schema.
- If video paths already exist, use them.
- If traces already exist, use them.
- If replay command exists, expose it in UI/certificate.
- Do not assume a single exact DreamAudit schema; implement robust key fallbacks.

Mode B: fallback demo mode
- Load or generate deterministic placeholder DreamAudit-like certificates.
- Generate synthetic videos and traces.
- Make the whole demo functional without real simulator execution.

Implement `taco_demo/dreamaudit_adapter.py` with a class like:

class DreamAuditAdapter:
    def __init__(self, repo_root: Path | None = None, data_root: Path | None = None):
        ...

    def discover_certificate_files(self, extra_dirs: list[Path] | None = None) -> list[Path]:
        ...

    def load_certificates(self, cert_dir: Path | None = None) -> list[NormalizedDreamAuditCertificate]:
        ...

    def normalize_certificate(self, raw: dict, source_path: Path | None = None) -> NormalizedDreamAuditCertificate:
        ...

    def get_replay_artifacts(self, certificate_id: str) -> ReplayArtifacts:
        ...

    def has_real_dreamaudit_artifacts(self) -> bool:
        ...

The adapter should search likely locations:
- taco_demo/data/dreamaudit_certs/
- outputs/
- artifacts/
- results/
- runs/
- any JSON file under repo root containing “certificate_id” or “patch_recipe”, but avoid scanning enormous hidden dirs like .git, venv, node_modules, .venv.

The normalizer should handle possible raw keys:
- certificate_id / id / cert_id
- policy_id / policy / model / robot_policy
- task_id / task / environment / env
- failure_type / observed_failure_mode / vulnerability_type / failure_mode
- perturbation / perturbations / decoded_values
- minimal_failure_cost / minimal_cost / normalized_cost / perturbation.normalized_cost / minimality.minimal_failure_cost
- replay_command / replay.cmd / command
- patch_recipe / patch / mitigation / intervention

If fields are missing, fill deterministic sensible defaults and mark `"source": "normalized_missing_fields"` in metadata.

================================================================================
CANONICAL DATA SCHEMAS
================================================================================

Implement typed dataclasses in `taco_demo/schemas.py`. Use dataclasses and standard library JSON serialization helpers. Do not require pydantic.

Create these dataclasses:

1. InsuranceApplication

Fields:
- application_id: str
- company_name: str
- robot_type: str
- policy_id: str
- deployment_units: int
- coverage_requested_usd: int
- deployment_stage: str
- telemetry_available: bool
- created_at: str
- metadata: dict[str, Any]

Default demo application:
{
  "application_id": "APP-APEX-001",
  "company_name": "Apex Robotics",
  "robot_type": "warehouse_manipulation_arm",
  "policy_id": "openvla_warehouse_v3",
  "deployment_units": 200,
  "coverage_requested_usd": 10000000,
  "deployment_stage": "pre_deployment",
  "telemetry_available": false
}

2. NormalizedDreamAuditCertificate

Fields:
- certificate_id: str
- policy_id: str
- task_id: str
- failure_type: str
- severity: str
- perturbation: dict[str, Any]
- minimal_failure_cost: float
- failure_rate_neighborhood: float
- failure_timestep: int
- replay_command: str
- patch_recipe: dict[str, Any]
- source_path: str | None
- source: str
- metadata: dict[str, Any]

3. ReplayArtifacts

Fields:
- certificate_id: str
- success_video_path: str | None
- failure_video_path: str | None
- mitigated_video_path: str | None
- success_trace_path: str | None
- failure_trace_path: str | None
- mitigated_trace_path: str | None
- artifact_source: str
- metadata: dict[str, Any]

4. InternalRiskMetrics

Fields:
- certificate_id: str
- concept_coverage_score: float
- feature_stability_score: float
- unsafe_dominance_score: float
- early_warning_margin_seconds: float
- causal_mitigability_score: float
- internal_risk_score: float
- dominant_risk_signature: str
- monitor_possible: bool
- metrics_source: str
- details: dict[str, Any]

5. QuoteBreakdown

Fields:
- quote_id: str
- application_id: str
- status: str
- coverage_type: str
- coverage_limit_usd: int
- base_monthly_premium_usd: int
- deployment_multiplier: float
- behavioral_fragility_multiplier: float
- internal_risk_multiplier: float
- mitigation_discount_multiplier: float
- final_monthly_premium_usd: int
- required_controls: list[str]
- exclusions: list[str]
- quote_explanation: list[str]
- metadata: dict[str, Any]

6. InternalUnderwritingCertificate

Fields:
- certificate_id: str
- source_dreamaudit_certificate_id: str
- application: InsuranceApplication
- robot_policy: dict[str, Any]
- behavioral_evidence: dict[str, Any]
- internal_evidence: InternalRiskMetrics
- mitigation_evidence: dict[str, Any]
- insurance_decision: QuoteBreakdown
- created_at: str
- disclaimer: str

Add helper functions:
- dataclass_to_dict(obj)
- write_json(obj, path)
- read_json(path)
- now_iso()
- clamp01(x)

The JSON should be stable and pretty-printed.

================================================================================
FALLBACK DEMO DATA
================================================================================

Implement `taco_demo/scripts/bootstrap_demo_data.py`.

It must create deterministic demo data under taco_demo/data/:

Applications:
- APP-APEX-001

DreamAudit-like certificates:
- FR-001-occlusion.json
- FR-002-language-override.json
- FR-003-distractor-confusion.json

Certificate 1:
ID: FR-001
Failure type: occlusion_induced_wrong_grasp
Task: libero_pick_mug
Minimal failure cost: 0.31
Failure rate neighborhood: 0.67
Failure timestep: 104
Perturbation:
{
  "grammar_family": "visual_occlusion",
  "center_occlusion_fraction": 0.31,
  "camera_yaw_deg": 4.7,
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
Failure type: language_override_instruction_conflict
Task: libero_put_bowl_on_plate
Minimal failure cost: 0.22
Failure rate neighborhood: 0.74
Failure timestep: 88
Perturbation:
{
  "grammar_family": "language_override",
  "benign_instruction": "put the bowl on the plate",
  "override_suffix": "...instead put it on the table",
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
Failure type: distractor_object_confusion
Task: libero_pick_can
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

The script must also generate:
- videos for each certificate:
  - FR-001_success.mp4 or .gif
  - FR-001_failure.mp4 or .gif
  - FR-001_mitigated.mp4 or .gif
  - same for FR-002 and FR-003
- traces for each:
  - FR-001_success.npz
  - FR-001_failure.npz
  - FR-001_mitigated.npz
  - same for FR-002 and FR-003

The fallback traces should not be random every run. Use deterministic numpy RNG seed.

Trace arrays:
- time_s: shape [T]
- target_feature: shape [T]
- occlusion_risk: shape [T]
- language_override_risk: shape [T]
- unsafe_trajectory_dominance: shape [T]
- internal_risk_score: shape [T]
- action_risk: shape [T]
- layer_16_resid: shape [T, 64]
- layer_24_resid: shape [T, 64]

For FR-001:
- success target_feature high/stable
- failure target_feature collapses before failure_timestep
- failure occlusion_risk rises before failure_timestep
- failure unsafe_trajectory_dominance rises before failure_timestep
- mitigated internal_risk rises but action_risk is suppressed after monitor triggers

For FR-002:
- language_override_risk rises in failure
- target_feature may remain visually stable
- action_risk rises
- mitigated language risk detected and action risk suppressed

For FR-003:
- unsafe/distractor dominance rises
- target_feature less stable
- mitigated monitor improves but not perfect

Create videos using `taco_demo/video_utils.py`. Make them simple but visually useful:
- white/dark background
- text labels: “Nominal success”, “Counterfactual failure”, “Mitigated replay”
- simple 2D robot arm line or gripper
- target object circle/box
- distractor object
- occluder rectangle for FR-001
- overlay risk messages:
  - “Target feature collapse”
  - “Internal risk signature detected”
  - “Monitor: request second view”
  - “Language override blocked”
  - “Target identity confirmation”
The video can be synthetic drawings; the README must state these are fallback placeholders and should be replaced with real DreamAudit renderings for the final hackathon recording.

Use imageio and PIL.
If MP4 writing fails due to missing ffmpeg, fall back to GIF and make the UI handle both.

================================================================================
FEATURE SCORING REQUIREMENTS
================================================================================

Implement `taco_demo/feature_scoring.py`.

It must load `.npz` traces and compute InternalRiskMetrics.

Functions:
- load_trace(path: Path) -> dict[str, np.ndarray]
- compute_internal_metrics(certificate, success_trace, failure_trace, mitigated_trace) -> InternalRiskMetrics
- compute_feature_stability(success_trace, failure_trace, failure_timestep) -> float
- compute_unsafe_dominance(failure_trace, failure_timestep) -> float
- compute_early_warning_margin(failure_trace, failure_timestep, threshold=0.65) -> float
- compute_causal_mitigability(certificate, failure_trace, mitigated_trace) -> float
- compute_concept_coverage(trace_bundle) -> float
- compute_internal_risk_score(...) -> float

Metric definitions:

Concept Coverage Score:
Approximate whether the required hazard concepts are represented by available feature arrays/probe signals. In fallback data, required concepts:
- target_feature
- occlusion_risk
- language_override_risk
- unsafe_trajectory_dominance
- action_risk

Score:
available_nonflat_concept_signals / total_required_signals
with some nuance:
- A signal is “available” if present and has nontrivial variance or meaningful mean.
- Clamp to [0,1].

Feature Stability Score:
Measure how stable the target/safety feature remains between success and failure.
Use the pre-failure window.
For example:
success_mean = mean(success.target_feature[pre_window])
failure_mean = mean(failure.target_feature[pre_window])
collapse = max(0, success_mean - failure_mean)
score = 1 - collapse
Clamp to [0,1].
Low score means fragile.

Unsafe Dominance Score:
Use max or mean of unsafe_trajectory_dominance / action_risk in pre-failure window.
High score means unsafe internal feature dominates.
Clamp to [0,1].

Early Warning Margin:
Find first timestep where internal_risk_score > threshold before failure_timestep.
margin_seconds = time_s[failure_timestep] - time_s[first_risk_timestep]
If never crosses before failure, margin = 0.
Monitor possible if margin >= 0.25 sec.

Causal Mitigability Score:
Compare failure trace risk/action risk to mitigated trace risk/action risk.
Could use:
original = mean(failure.action_risk[post_monitor_window])
mitigated = mean(mitigated.action_risk[post_monitor_window])
score = (original - mitigated) / max(original, 1e-6)
Clamp to [0,1].
This is demo evidence for an insurance discount.

Internal Risk Score:
Weighted score:
internal_risk_score =
  0.25 * (1 - concept_coverage_score)
+ 0.25 * (1 - feature_stability_score)
+ 0.25 * unsafe_dominance_score
+ 0.15 * (1 - causal_mitigability_score)
+ 0.10 * early_warning_penalty

Where:
early_warning_penalty = 0 if early_warning_margin_seconds >= 0.5 else 1 - early_warning_margin_seconds/0.5

Clamp to [0,1].

Dominant risk signature:
Map certificate failure_type to:
- occlusion_induced_wrong_grasp -> target_feature_collapse_under_occlusion
- language_override_instruction_conflict -> language_override_dominates_action_selection
- distractor_object_confusion -> semantic_distractor_dominance
- fallback -> internal_failure_precursor_detected

The function must return deterministic values, not hard-coded magic only. It should compute from arrays.

================================================================================
QUOTE ENGINE REQUIREMENTS
================================================================================

Implement `taco_demo/quote_engine.py`.

The quote engine must make the insurance central.

Functions:
- traditional_underwriting_status(application) -> dict
- behavioral_fragility_multiplier(minimal_failure_cost, failure_rate_neighborhood) -> float
- internal_risk_multiplier(internal_risk_score) -> float
- mitigation_discount(causal_mitigability_score, monitor_enabled) -> float
- generate_quote(application, certificates, metrics_by_cert, monitor_enabled: bool, controls_enabled: dict[str, bool] | None = None) -> QuoteBreakdown

Important:
Before audit, if telemetry_available is false:
status should be:
"blocked_no_telemetry"
with explanation:
"Traditional underwriting blocked because no deployment telemetry or historical loss data is available. TACO can proceed using internal underwriting."

After audit:
The quote should be generated.

Quote formula:
base_monthly_premium_usd =
  int(coverage_requested_usd * 0.0008 + deployment_units * 35)

deployment_multiplier =
  1.0 + min(1.5, deployment_units / 500)

For each cert:
behavioral multiplier increases when:
- minimal_failure_cost is low
- failure_rate_neighborhood is high

Suggested formula:
cost_factor = 1.0 + max(0.0, 0.6 - minimal_failure_cost)
rate_factor = 1.0 + 0.75 * failure_rate_neighborhood
cert_behavioral_multiplier = cost_factor * rate_factor

Aggregate behavioral_fragility_multiplier:
Use mean or max/mean blend across certs:
0.65 * max(cert_mults) + 0.35 * mean(cert_mults)

Internal risk multiplier:
1.0 + 1.25 * aggregate_internal_risk_score

Aggregate internal risk:
Use max/mean blend:
0.7 * max(scores) + 0.3 * mean(scores)

Mitigation discount:
If monitor_enabled:
1.0 - min(0.45, 0.45 * aggregate_causal_mitigability_score)
Else:
1.0

Final:
base * deployment_multiplier * behavioral_fragility_multiplier * internal_risk_multiplier * mitigation_discount_multiplier

Round final monthly premium to nearest $100.

Status:
- If no audit and no telemetry: blocked_no_telemetry
- If audit exists but monitor disabled: approved_with_exclusions
- If audit exists and monitor enabled: conditionally_approved

Required controls:
Always include:
- "reaudit_required_after_model_update"
Based on certificates:
- occlusion failure -> "occlusion_risk_monitor_enabled"
- language override -> "language_override_sanitizer_enabled"
- distractor confusion -> "target_identity_confirmation_enabled"

Exclusions:
If monitor disabled:
- "Known DreamAudit certificate families are excluded until required internal-risk controls are enabled."
If a specific control disabled:
- "FR-001 occlusion-induced target collapse excluded if occlusion-risk monitor is disabled."
- "FR-002 language override failures excluded if instruction sanitizer is disabled."
- etc.

Quote explanation:
Return a list of human-readable bullets:
- “Traditional underwriting had no telemetry to price this robot fleet.”
- “DreamAudit found 3 replayable failure families.”
- “The lowest minimal failure cost was 0.22, indicating fragile failure boundaries.”
- “Internal risk signatures appeared before physical failure, so runtime monitors can reduce expected loss.”
- “Required controls reduce premium by X%.”

Tests must assert:
- Lower minimal_failure_cost increases premium.
- Higher internal_risk_score increases premium.
- Enabling monitor lowers premium when mitigability > 0.
- No telemetry before audit returns blocked_no_telemetry.
- Required controls are present for matching failure types.

================================================================================
POLICY ISSUER REQUIREMENTS
================================================================================

Implement `taco_demo/policy_issuer.py`.

Functions:
- build_internal_underwriting_certificate(application, source_cert, metrics, quote, artifacts) -> InternalUnderwritingCertificate
- issue_policy_bundle(application, certificates, metrics_by_cert, quote, artifacts_by_cert, output_dir) -> Path

The issued certificate JSON should include:
- TACO branding
- application
- robot_policy info
- behavioral evidence from DreamAudit
- internal evidence
- mitigation evidence
- quote/insurance decision
- conditions
- exclusions
- disclaimer

Disclaimer:
“This hackathon demo is not an actual insurance policy or offer of insurance. It demonstrates how learned-policy liability underwriting could be tied to DreamAudit replayable failures and internal model risk signatures.”

But keep the UI phrasing product-like. Do not overdo disclaimers in the main UI.

Output path:
taco_demo/data/quotes/TACO-BINDER-APP-APEX-001.json

Human-readable binder text:
Also write:
taco_demo/data/quotes/TACO-BINDER-APP-APEX-001.md

The markdown binder should read like:

TACO — The Autonomous Casualty Office
Conditional Learned-Policy Liability Binder

Named Insured: Apex Robotics
Coverage Type: Learned-Policy Liability
Coverage Limit: $10,000,000
Status: Conditionally Approved
Monthly Premium: $XX,XXX

Basis of Underwriting:
- DreamAudit replayable failure certificates
- internal activation traces
- feature stability and unsafe dominance scores
- verified internal-risk monitors

Required Controls:
...

Known Failure Family Exclusions:
...

================================================================================
STREAMLIT UI REQUIREMENTS
================================================================================

Implement `taco_demo/app.py`.

The app must be polished enough for a hackathon.

Global title:
TACO
The Autonomous Casualty Office

Subtitle:
Liability insurance for robots before the first claim.

Sidebar:
- Application fields:
  - Company name
  - Robot type
  - Policy ID
  - Deployment units
  - Coverage requested
  - Deployment stage
  - Telemetry available checkbox
- Buttons:
  - “Save Application”
  - “Run Internal Underwriting Audit”
  - “Bootstrap Demo Data”
  - “Issue Binder”

Main navigation:
Use tabs:
1. Application
2. Underwriting Audit
3. Replay Evidence
4. Internal Signals
5. Quote
6. Binder / Certificate
7. Spec / README

Tab 1: Application
Show:
- Insurance application summary
- Traditional underwriting status
If telemetry_available is false:
Display a warning:
“Traditional underwriting blocked: no deployment telemetry or claims history.”
Then:
“TACO can underwrite from synthetic actuarial evidence: DreamAudit failures + internal model risk signatures.”

Tab 2: Underwriting Audit
Show stepper/progress:
- Load policy/application
- Load DreamAudit certificates
- Load replay artifacts
- Load activation traces
- Compute internal risk metrics
- Calculate quote
- Prepare binder

Show count:
“3 replayable failure families loaded.”

Show table with:
- Certificate ID
- Failure type
- Minimal cost
- Failure rate neighborhood
- Dominant internal risk signature
- Required control
- Premium impact estimate

Tab 3: Replay Evidence
For selected certificate:
- Dropdown select cert
- Show success/failure/mitigated videos side by side
- Show replay command
- Show perturbation JSON
- Show patch_recipe JSON
- Show behavioral evidence:
  - minimal failure cost
  - failure timestep
  - failure neighborhood rate
  - severity

If video missing:
- Show a friendly placeholder and command to run bootstrap script.

Tab 4: Internal Signals
For selected certificate:
- Plot feature curves over time using plotly:
  - target_feature
  - occlusion_risk
  - language_override_risk
  - unsafe_trajectory_dominance
  - internal_risk_score
  - action_risk
- Add vertical line for failure timestep.
- Add vertical line or marker for first risk threshold crossing.
- Show metric cards:
  - Concept Coverage
  - Feature Stability
  - Unsafe Dominance
  - Early Warning Margin
  - Causal Mitigability
  - Internal Risk Score
- Human explanation text:
  For FR-001:
  “The robot does not merely miss the object. Under occlusion, the target-object feature collapses while unsafe trajectory dominance rises before the wrong grasp. The risk signature appears early enough for a runtime monitor to intervene.”
  For FR-002:
  “The visual state remains stable, but the language override risk feature dominates action selection. The instruction sanitizer is therefore required for coverage.”
  For FR-003:
  “The distractor feature competes with the target identity representation, creating a known semantic confusion family.”

Tab 5: Quote
Show:
- Initial status:
  “Without telemetry: unpriceable by traditional underwriting.”
- TACO quote:
  - status
  - monthly premium
  - coverage limit
  - required controls
  - exclusions
- Show premium breakdown:
  - base monthly premium
  - deployment multiplier
  - behavioral fragility multiplier
  - internal risk multiplier
  - mitigation discount multiplier
- Controls toggles:
  - Enable occlusion-risk monitor
  - Enable language override sanitizer
  - Enable target identity confirmation
  - Reaudit after model update
Changing toggles must recompute quote.
If controls disabled, premium increases and exclusions appear.
If controls enabled, premium lowers and status becomes conditionally approved.

Important visual:
Use `st.metric` to show:
- “Final monthly premium”
- “Savings from required monitors”
- “Known failure families”
- “Earliest internal warning”

Tab 6: Binder / Certificate
Show:
- Button: “Issue Conditional Binder”
- Render generated JSON
- Provide download button for JSON
- Provide download button for markdown binder
- Show human-readable policy card:
  TACO Conditional Learned-Policy Liability Binder
  Named Insured
  Coverage limit
  Premium
  Required controls
  Exclusions
  Reaudit triggers

Tab 7: Spec / README
Render content from taco_demo/README.md or a condensed version.
This makes the demo self-explaining even if judges ask how it works.

Visual design:
- Serious institutional vibe.
- Avoid overly goofy taco imagery.
- It is okay that TACO acronym is funny, but the UI should feel like an old insurance office for robots.
- Use labels like:
  “Binder”
  “Casualty”
  “Known Failure Family”
  “Required Control”
  “Exclusion”
  “Synthetic Actuarial Evidence”
  “Internal Underwriting”
  “Learned-Policy Liability”

Do not spend time on custom CSS unless simple.

================================================================================
ACTIVATION RECORDER REQUIREMENTS
================================================================================

Implement `taco_demo/activation_recorder.py`.

This module should support optional real model hooks but not be required for fallback.

Design:

class ActivationRecorder:
    def __init__(self, model, layer_name_substrings: list[str]):
        ...
    def attach(self):
        ...
    def detach(self):
        ...
    def clear(self):
        ...
    def export_npz(self, path, certificate_id, rollout_mode):
        ...

If torch is unavailable, importing this module should still work. Use try/except:
try:
    import torch
except ImportError:
    torch = None

If torch is None and user tries to instantiate real recorder, raise a clear error:
“PyTorch is not installed. The fallback demo uses precomputed NPZ traces.”

The README should explain how to use this:
- Attach hooks to OpenVLA/VLA model layers.
- Run nominal, failure, and mitigated replays.
- Save traces to taco_demo/data/traces/.
- The UI will load them automatically.

================================================================================
VIDEO UTILS REQUIREMENTS
================================================================================

Implement `taco_demo/video_utils.py`.

Functions:
- create_demo_video(output_path, certificate_id, mode, failure_type, fps=12, duration_s=5) -> Path
- write_frames(frames, output_path, fps) -> Path
- draw_frame(...) -> PIL.Image.Image
- create_all_demo_videos(data_root)

The videos should be deterministic and simple.

For FR-001:
- success: robot arm reaches target object
- failure: occluder appears; robot reaches wrong object
- mitigated: risk monitor warning; robot pauses; then reaches target or requests second view

For FR-002:
- success: follows instruction
- failure: text override appears; robot places object incorrectly
- mitigated: sanitizer blocks override

For FR-003:
- success: picks target
- failure: picks similar distractor
- mitigated: target confirmation box appears

Use PIL ImageDraw.
Save MP4 if possible, otherwise GIF.
Return actual path.

The UI must handle both .mp4 and .gif:
- st.video for mp4
- st.image for gif

================================================================================
NORMALIZE EXISTING CERTS SCRIPT
================================================================================

Implement `taco_demo/scripts/normalize_existing_certs.py`.

CLI:
python -m taco_demo.scripts.normalize_existing_certs --input-dir path/to/certs --output-dir taco_demo/data/dreamaudit_certs

It should:
- load all JSON files in input-dir recursively
- keep only files that look like DreamAudit certs
- normalize via DreamAuditAdapter
- write normalized JSON files
- print summary

Arguments:
- --input-dir
- --output-dir
- --limit optional
- --overwrite

================================================================================
RECORD REPLAY VIDEO SCRIPT
================================================================================

Implement `taco_demo/scripts/record_replay_video.py`.

This script should be a placeholder integration wrapper because actual DreamAudit replay APIs may vary.

CLI:
python -m taco_demo.scripts.record_replay_video --certificate taco_demo/data/dreamaudit_certs/FR-001-occlusion.json --mode failure --out taco_demo/data/videos/FR-001_failure.mp4

Behavior:
- If a real DreamAudit replay command exists in the certificate and an env var TACO_ALLOW_REAL_REPLAY=1 is set, print the command it would run and try to run it safely.
- Otherwise generate fallback demo video using video_utils.
- Never fail hard just because real replay is unavailable.
- Document this in README.

================================================================================
PRECOMPUTE DEMO SCRIPT
================================================================================

Implement `taco_demo/scripts/precompute_demo.py`.

This should:
- load application
- load certs
- load traces
- compute metrics
- generate quote with controls enabled
- issue binder
- print output paths

CLI:
python -m taco_demo.scripts.precompute_demo

================================================================================
TEST REQUIREMENTS
================================================================================

Use pytest.

test_quote_engine.py:
- test_no_telemetry_blocks_traditional_underwriting
- test_monitor_discount_lowers_premium
- test_lower_minimal_cost_increases_behavioral_multiplier
- test_higher_internal_risk_increases_quote
- test_required_controls_generated_from_failure_types

test_feature_scoring.py:
- test_metrics_are_clamped_between_zero_and_one
- test_early_warning_margin_positive_when_risk_crosses_before_failure
- test_mitigability_higher_when_mitigated_action_risk_lower
- test_feature_stability_drops_when_target_feature_collapses

test_certificate_schema.py:
- test_dataclass_json_roundtrip
- test_internal_underwriting_certificate_contains_application_quote_metrics

test_dreamaudit_adapter.py:
- test_normalize_minimal_raw_certificate
- test_load_bootstrapped_certificates
- test_missing_fields_do_not_crash

All tests must pass after:
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests

================================================================================
README REQUIREMENTS
================================================================================

Create `taco_demo/README.md` containing a complete, polished spec. It should include:

Title:
TACO — The Autonomous Casualty Office

Subtitle:
A hackathon demo of learned-policy liability insurance for robotics, underwritten from DreamAudit failures and internal model risk signatures.

Sections:

1. Product thesis
Explain:
- Robotics insurers normally need deployment history and fleet telemetry.
- Frontier robot policies may not have that data before enterprise deployment.
- TACO creates synthetic actuarial evidence from simulation and internals.
- The quote depends on internal risk signatures, not just benchmark pass/fail.

2. What the demo shows
End-to-end flow:
- insurance application
- traditional underwriting blocked
- DreamAudit certificates loaded
- success/failure/mitigated replay videos
- internal risk metrics
- premium calculation
- policy binder issuance

3. Architecture
Include ASCII diagram:

Apex Robotics Application
  -> TACO Underwriting UI
  -> DreamAudit Adapter
  -> Replay / Certificate Loader
  -> Internal Trace Analyzer
  -> Quote Engine
  -> Conditional Binder

4. Quickstart
Commands:
python -m pip install -r taco_demo/requirements-taco.txt
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py

5. Data layout
Explain taco_demo/data directories.

6. DreamAudit integration
Explain:
- where to put real certificates
- how normalization works
- how to replace fallback videos with real replays
- how to record activation traces
- env vars:
  - DREAMAUDIT_ROOT
  - TACO_DEMO_DATA_ROOT
  - DREAMAUDIT_CERT_DIR
  - TACO_ALLOW_REAL_REPLAY

7. Internal underwriting metrics
Document:
- Concept Coverage Score
- Feature Stability Score
- Unsafe Dominance Score
- Early Warning Margin
- Causal Mitigability Score
- Internal Risk Score
Include formulas.

8. Insurance quote formula
Document:
- base premium
- deployment multiplier
- behavioral fragility multiplier
- internal risk multiplier
- mitigation discount
- statuses
- controls/exclusions

9. Certificate schema
Include example JSON for Internal Underwriting Certificate.

10. Demo script for judges
Give a 2-minute pitch:
“Apex Robotics wants $10M coverage…”
Include exact story.

11. What is real vs fallback
Be honest:
- Real: schema, quote engine, metric computations, UI, artifact generation.
- Fallback: generated videos/traces unless replaced with DreamAudit recordings.
- Integration-ready: adapter for real DreamAudit certs and traces.

12. Future roadmap
- real VLA activation hooks
- SAE feature dictionaries
- event-grounded feature labeling
- carrier/reinsurer integration
- claims triage
- runtime compliance logs
- formal policy wording

13. Disclaimer
“This is a hackathon demo and not an actual offer of insurance.”

Also create README_TACO.md at repo root with:
- one-paragraph summary
- quickstart commands
- pointer to taco_demo/README.md

================================================================================
IMPLEMENTATION DETAILS AND EDGE CASES
================================================================================

Path handling:
- Use pathlib.Path everywhere.
- Data root defaults to taco_demo/data.
- Allow env var TACO_DEMO_DATA_ROOT to override.
- Avoid absolute paths in generated JSON when possible; store relative paths for portability.

Serialization:
- Use UTF-8.
- JSON pretty indent 2.
- Convert dataclasses recursively.
- Convert numpy floats to Python floats before JSON writing.

UI robustness:
- If no data exists, show button to bootstrap demo data.
- Do not crash on missing videos.
- Do not crash on missing traces.
- If missing trace, show explanation and use fallback generated trace only when user clicks bootstrap.
- Use Streamlit session_state for application and audit state.
- Do not require user to type everything manually; prefill Apex Robotics values.

Tests:
- Tests must create temporary data or rely on bootstrap script.
- Avoid tests that require Streamlit launch.

Code quality:
- Type hints where reasonable.
- Docstrings for core modules.
- Clear comments explaining demo formulas.
- Avoid giant monolithic app.py; use backend modules.
- Keep app.py readable.

Do not over-engineer:
- No database.
- No auth.
- No cloud.
- No background jobs.
- No Docker unless trivial.
- No real actuarial compliance.
- No heavy model downloads.

================================================================================
VISUAL / COPY GUIDELINES
================================================================================

Brand:
TACO — The Autonomous Casualty Office

Tone:
Serious institutional risk office with a funny acronym.
Avoid cartoon taco imagery.
The humor is in the acronym, not the UI.

Core phrases to use:
- “Learned-Policy Liability”
- “Synthetic Actuarial Evidence”
- “Internal Underwriting”
- “Known Failure Family”
- “Required Control”
- “Coverage Condition”
- “Policy Binder”
- “Exclusion”
- “Reaudit Trigger”
- “Failure Boundary”
- “Internal Risk Signature”

Main UI hero copy:
“TACO underwrites robot policies before deployment telemetry exists.”

Application warning:
“Traditional underwriting blocked: no deployment telemetry or historical loss data.”

Audit success:
“Internal underwriting complete: 3 replayable failure families found.”

Internal signals:
“Risk signature detected before physical failure.”

Quote:
“Conditionally approved with required internal-risk controls.”

Binder:
“This binder is conditioned on monitor compliance and re-audit after model updates.”

================================================================================
HACKATHON DEMO FLOW TO SUPPORT
================================================================================

The app must support this exact click path:

1. Open app.
2. See TACO landing/application page.
3. The Apex Robotics application is prefilled.
4. Telemetry checkbox is false.
5. App shows traditional underwriting blocked.
6. Click “Run Internal Underwriting Audit.”
7. App loads/generates demo data.
8. App shows 3 DreamAudit failure families.
9. Open Replay Evidence tab.
10. Select FR-001.
11. See success/failure/mitigated videos.
12. Open Internal Signals tab.
13. See risk curves; target feature collapses before failure; internal risk crosses threshold early.
14. Open Quote tab.
15. See final premium with monitors enabled.
16. Disable occlusion monitor.
17. Premium increases and FR-001 exclusion appears.
18. Re-enable monitor.
19. Premium drops and status becomes conditionally approved.
20. Open Binder tab.
21. Click “Issue Conditional Binder.”
22. See JSON/markdown binder and download buttons.

================================================================================
SPECIFIC DEFAULT NUMBERS FOR DEMO
================================================================================

Use these as defaults but compute them from data when possible:

Application:
- Coverage: $10,000,000
- Units: 200
- Telemetry: false

Behavioral:
- FR-001 minimal cost: 0.31, failure rate: 0.67
- FR-002 minimal cost: 0.22, failure rate: 0.74
- FR-003 minimal cost: 0.44, failure rate: 0.52

Internal metrics should roughly come out around:
FR-001:
- concept_coverage_score: 0.8
- feature_stability_score: 0.35 to 0.55
- unsafe_dominance_score: 0.75 to 0.9
- early_warning_margin_seconds: 0.7 to 1.2
- causal_mitigability_score: 0.65 to 0.85
- internal_risk_score: 0.45 to 0.7

FR-002:
- language override risk high
- feature stability can be higher because visual features remain stable
- internal risk moderate/high
- mitigability high due to sanitizer

FR-003:
- moderate fragility
- moderate mitigability

Quote:
Make the final premium believable and visibly variable:
- With required monitors: around $15k–$30k/month
- Without monitors: significantly higher, maybe $30k–$50k/month
The exact formula can produce different values, but the change must be noticeable.

================================================================================
ROOT README_TACO.md
================================================================================

Create root `README_TACO.md`:

Content:
# TACO — The Autonomous Casualty Office

One paragraph:
TACO is a self-contained hackathon demo layered on top of DreamAudit. It demonstrates conditional learned-policy liability insurance for robotics, priced using DreamAudit replayable failure certificates and internal model risk signatures.

Quickstart commands:
python -m pip install -r taco_demo/requirements-taco.txt
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests
python -m streamlit run taco_demo/app.py

Then:
See `taco_demo/README.md` for full PRD, architecture, data contracts, and demo script.

================================================================================
FINAL RESPONSE FROM CODEX
================================================================================

After implementing, run:
python -m taco_demo.scripts.bootstrap_demo_data --force
python -m pytest taco_demo/tests

If streamlit cannot be launched in the environment, at least verify imports:
python -c "import taco_demo.app"

Your final response should include:
- list of files created
- commands to run the demo
- whether tests passed
- where README/spec lives
- any DreamAudit integration assumptions or TODOs

Do not ask for clarification. Make best-effort decisions and implement the scaffold.