# TACO SAE + DreamAudit Manim Explainer Plan

This folder is for a 3Blue1Brown-style ManimGL explainer of the interpretability
story behind TACO. It is intentionally separate from `taco_demo/` so it does not
touch the Streamlit quote pipeline, certificates, or real replay wiring.

## Research Anchors

- 3b1b ManimGL is the intended engine. The upstream repo says this package is
  installed as `manimgl`, imports from `manimlib`, and runs scenes with commands
  like `manimgl example_scenes.py OpeningManimExample`.
  Source: https://github.com/3b1b/manim
- Sparse autoencoders are used for mechanistic interpretability because they
  decompose dense model activations into a sparse dictionary of more
  interpretable feature directions.
  Source: https://arxiv.org/abs/2309.08600
- Dr. VLA / Swann et al. 2026 applies SAEs to VLA hidden activations, finds
  interpretable and steerable features, separates general motion/semantic
  primitives from memorized episode features, and validates causal influence by
  steering.
  Source: https://arxiv.org/abs/2603.19183 and https://drvla.github.io
- TACO's local data exposes real SAE summary artifacts for Octo-Base: TopK SAE,
  `d_model=256`, `d_sae=4096`, 16x expansion, 1,976 samples, 1,172 alive
  features, 64 median active features, and 99.8% explained variance.
  Source: `taco_demo/data/sae_features/octo/feature_analysis_metrics.json`
- TACO's FR-004 exhibit is real cross-policy evidence from sae-scope:
  failures are detected by an internal monitor with first alert at step 32,
  mean lead of 48 steps, recall 1.0, precision 0.857, and one false handoff
  limitation.
  Source: `taco_demo/data/videos/real_external/saescope/manifest.json`

## Core Explanation

The animation should explain this chain:

1. A robot policy receives pixels and language and outputs actions.
2. Before the visible failure, its internal activations already move into a
   risk-relevant region.
3. A Sparse Autoencoder turns a dense, mixed activation vector into a sparse set
   of feature coordinates.
4. Some features behave like general, transferable primitives; others look like
   memorized episode traces.
5. DreamAudit-style perturbations force and replay the failure, giving a
   certificate: what changed, when it failed, how reproducible it is, and whether
   a monitor can intervene.
6. TACO translates that monitorability into a readiness certificate: identified
   failure family, required runtime control, limitations, and certification tier.

## Animation Sequence

### 1. Opening Claim

Visual:

- Four metric cards: SAE expansion, median active features, FR-004 lead time,
  and monitor precision.
- Source line showing whether the numbers came from local TACO artifacts or the
  documented fallback.

Point:

- The explainer is about how internal structure becomes operational evidence,
  not about adding another dashboard.

### 2. Activation Vocabulary

Visual:

- A small pixel grid and language instruction flow into a drawn neural network.
- Individual nodes and colored weight lines call out "neuron", "weights",
  "activation", and the dense activation vector `h`.
- Plain-text formula: activation = weighted sum + bias, then nonlinearity.

Point:

- A model's internal state is a vector of activation numbers at a moment in the
  rollout.

### 3. What A Feature Is

Visual:

- A 2D slice of activation space with axes labeled as neurons.
- The activation vector appears as a point; a feature is drawn as a direction.
- A projection from `h` onto the feature direction defines the feature score.

Point:

- A feature is a reusable direction or pattern in activation space, not
  necessarily a single neuron. A human label is a description we assign after
  inspecting what activates the feature.

### 4. Why Neurons Are Not Enough

Visual:

- Left: clean human concepts such as object closeness, gripper closing, language
  target, and episode shortcut.
- Right: several concept directions squeezed into two drawn coordinates.

Point:

- Superposition and polysemantic neurons mean one raw coordinate can help
  represent multiple features. Interpretability needs a better basis.

### 5. SAE Mechanics

Visual:

- Dense activation `h` flows through encoder, sparse vector `z`, decoder, and
  reconstruction `h_hat`.
- The sparse vector has only a few lit bars.
- Plain-text reconstruction equation: `h_hat = z_3 d_3 + z_8 d_8 + ...`.

Point:

- A sparse autoencoder learns a dictionary of feature directions. It is trained
  to reconstruct `h` while using a sparse code `z`.

### 6. TopK Definition

Visual:

- Raw feature-score bars on the left.
- After-TopK bars on the right, with only the largest K bars remaining.
- Project-specific callout: about 64 active features out of 4,096 slots for the
  local Octo SAE.

Point:

- TopK is the sparsity rule: keep the K largest feature activations and zero the
  rest. This makes individual feature slots inspectable over time.

### 7. Monitor Definition

Visual:

- Feature activation traces over time.
- A safe rollout stays below threshold; a failure rollout crosses threshold.
- The monitor rule reads sparse features `z(t)` and hands off when a risk feature
  crosses threshold.

Point:

- The certification-relevant object is not just "a feature exists"; it is a
  runtime rule with a threshold, lead time, and false-alert profile.

### 8. The Black Box Is Not Enough

Visual:

- Left: camera frame, instruction label, robot arm, object.
- Center: a black policy box with a few dense "neuron" lights.
- Right: action arrow and task outcome.

Movement:

- Pixels and instruction dots stream into the box.
- Action arrow starts smooth, then bends into a red failed trajectory.

Point:

- The visible replay tells us what happened, but not why it was predictable.

### 9. SAE As A Prism

Visual:

- Encoder wedge from 256 dense activations to 4,096 feature slots.
- Only 64 feature slots light up.
- Feature labels: grasp primitive, task progress, language target, memorized
  episode.

Movement:

- Dense vector enters the SAE.
- Sparse bars fan out; most stay dim.
- A few bars pulse.

Point:

- The SAE gives a sparse coordinate system where individual features can be
  inspected, plotted, and sometimes steered.

### 10. General Versus Memorized Features

Visual:

- Two columns of feature-time traces.
- General feature: appears across several tasks and moves with the same phase.
- Memorized feature: sharp trace tied to one replay.

Movement:

- Multiple faint rollouts align under the general feature.
- The memorized feature only follows one replay and fades under perturbation.

Point:

- TACO should not claim that all features are causal or general. The useful
  certification signal is a feature that appears early, repeatedly, and with
  enough lead to intervene.

### 11. DreamAudit Forces The Boundary

Visual:

- A replay timeline from step 0 to step 80.
- Internal monitor curve crosses threshold at step 32.
- Action diagnostic crosses later at step 56 in one case.
- Physical failure at step 80.

Movement:

- A perturbation slider nudges the rollout.
- Internal risk curve rises before the robot visibly diverges.
- A red bracket labels "48-step lead".

Point:

- DreamAudit-like certificates make the failure replayable and minimal; the SAE
  monitor makes it anticipatable.

### 12. Readiness Certificate

Visual:

- Evidence cards: replay, certificate, SAE monitor, mitigation.
- TACO readiness certificate: identified failure mode, required control,
  limitation, and tier.

Movement:

- Monitorability token moves from the timeline into the certificate.
- Terms update from "unknown readiness" to "certifiable when runtime handoff is
  on and verified".

Point:

- Interpretability matters here because it changes the certification tier and
  required controls, not because it makes a pretty dashboard.

## Deliverable Shape

- One full scene class: `TacoSAEDreamAuditExplainer`.
- Smaller scene aliases for partial rendering can be added later if useful.
- The scene reads local TACO summary numbers at runtime when possible and falls
  back to the documented values above if the package import fails.
- The visuals avoid LaTeX so the first render only needs ManimGL, FFmpeg, and
  OpenGL.
