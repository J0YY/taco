# TACO - The Autonomous Casualty Office

## Conditional Learned-Policy Liability Binder

Named Insured: Apex Robotics
Coverage Type: Learned-Policy Liability
Coverage Limit: $10,000,000
Status: Conditionally Approved
Monthly Premium: $49,300

## Basis of Underwriting
- DreamAudit replayable failure certificates
- internal activation traces
- feature stability and unsafe dominance scores
- verified internal-risk monitors

## Known Failure Families
- FR-001: occlusion_induced_wrong_grasp, minimal cost 0.31
- FR-002: language_override_instruction_conflict, minimal cost 0.22
- FR-003: distractor_object_confusion, minimal cost 0.44

## Required Controls
- reaudit_required_after_model_update
- occlusion_risk_monitor_enabled
- language_override_sanitizer_enabled
- target_identity_confirmation_enabled

## Known Failure Family Exclusions
- None while required controls remain enabled

## Reaudit Trigger
- Reaudit is required after any learned-policy model update, material prompt/schema change, or monitor deactivation.

This hackathon demo is not an actual insurance policy or offer of insurance. It demonstrates how learned-policy liability underwriting could be tied to DreamAudit replayable failures and internal model risk signatures.
