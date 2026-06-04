"""Mechanistic-interpretation basis + an annotated flow chart for TACO.

The core argument TACO needs to make is: *we can mechanistically interpret robot
policies well enough to locate failure modes before deployment.* That claim is
grounded in published work, most directly:

  Swann, McGranahan, Buurmeijer, Kennedy III, Schwager. "Sparse Autoencoders
  Reveal Interpretable and Steerable Features in VLA Models." Stanford, 2026.
  arXiv:2603.19183 · project: drvla.github.io ("Dr. VLA").

That paper's pipeline is exactly what produces TACO's FR-004 evidence: train a
Sparse Autoencoder (SAE) on a VLA's residual-stream activations, obtain sparse
*interpretable* features (grasp, carry, task-progress, language), classify them
as general vs memorized, and *steer* them to causally confirm they drive
behavior. We reuse that to build a runtime monitor whose activation precedes the
physical failure.
"""

from __future__ import annotations

from typing import Any

# Citable claims that back "we can interpret robots and find failure modes".
MECH_SOURCES: list[dict[str, str]] = [
    {
        "claim": "SAEs decompose a VLA's residual stream into interpretable, steerable features.",
        "evidence": "SAEs on VLA residual streams yield features for grasping, carrying, task "
                    "completion and language semantics; steering a feature (y' = y + a*v) causally "
                    "and predictably changes robot behavior.",
        "source": "Swann et al. 2026, 'SAEs Reveal Interpretable and Steerable Features in VLA Models' (Stanford)",
        "url": "https://arxiv.org/abs/2603.19183",
    },
    {
        "claim": "Internal states are linearly decodable, so failure-relevant variables can be probed.",
        "evidence": "Linear probes on OpenVLA activations decode object positions and actions with "
                    ">90% accuracy on most layers.",
        "source": "Lu et al. (probing OpenVLA activations), cited in Swann et al. 2026",
        "url": "https://arxiv.org/abs/2603.19183",
    },
    {
        "claim": "Benchmark success hides brittleness that perturbations expose — a failure mode interpretation explains.",
        "evidence": "Policies above 90% LIBERO success collapse toward zero under systematic "
                    "perturbations (LIBERO-PRO), consistent with memorized rather than general features.",
        "source": "LIBERO-PRO; memorization analysis in Swann et al. 2026",
        "url": "https://arxiv.org/abs/2603.19183",
    },
]

# The four-component method from the paper, in TACO terms.
MECH_STEPS: list[dict[str, str]] = [
    {"step": "Record", "what": "Capture residual-stream activations at several layers during the rollout."},
    {"step": "Decompose", "what": "Train a TopK SAE; activations become sparse, interpretable features."},
    {"step": "Classify", "what": "Score features general vs memorized (coverage, onset, magnitude, run-length)."},
    {"step": "Steer / probe", "what": "Add a feature's decoder vector to causally confirm it drives behavior."},
]


def mechanism_flowchart_dot() -> str:
    """Annotated Graphviz flow chart of the mechanistic-to-insurance pipeline."""
    return r"""
digraph mechanism {
  rankdir=LR;
  bgcolor="white";
  node [shape=box style="rounded,filled" fontname="Helvetica" fontsize=11 color="#1f2937" fillcolor="#eef2ff"];
  edge [fontname="Helvetica" fontsize=9 color="#6b7280"];

  subgraph cluster_policy {
    label="1 · Robot policy (what we analyze)"; style="rounded"; color="#cbd5e1"; fontsize=11;
    rollout [label="Rollout frames\n(camera + state)" fillcolor="#e0f2fe"];
    vla [label="VLA policy\nVLM backbone + action head"];
  }

  subgraph cluster_interp {
    label="2 · Mechanistic interpretation (Swann et al. 2026)"; style="rounded"; color="#cbd5e1";
    acts [label="Residual-stream\nactivations\n(layers 0/5/11/17)" fillcolor="#fef9c3"];
    sae [label="Sparse Autoencoder\n(TopK)"];
    feats [label="Sparse features\ngrasp · carry · task-progress\nlanguage · memorized" fillcolor="#dcfce7"];
    monitor [label="Internal risk monitor\n(probe / general-vs-memorized)" fillcolor="#fee2e2"];
  }

  subgraph cluster_audit {
    label="3 · DreamAudit (force + confirm)"; style="rounded"; color="#cbd5e1";
    perturb [label="Minimal perturbation\nocclusion · language · push" fillcolor="#ffedd5"];
    steer [label="Feature steering\ny' = y + a*v\n(causal check)"];
  }

  subgraph cluster_ins {
    label="4 · Insurance (TACO)"; style="rounded"; color="#cbd5e1";
    price [label="Price\npremium · controls · exclusions" fillcolor="#ede9fe"];
  }

  rollout -> vla;
  vla -> acts [label="record"];
  acts -> sae [label="decompose"];
  sae -> feats;
  feats -> monitor [label="classify / probe"];
  perturb -> vla [label="inject" color="#dc2626" fontcolor="#b91c1c"];
  monitor -> price [label="early-warning lead\n+ mitigability"];
  steer -> feats [label="validate" style=dashed];
  monitor -> steer [style=dashed];
  perturb -> price [label="minimal cost\n+ neighborhood rate" style=dashed];
}
""".strip()


def mechanism_caption() -> str:
    return ("We record the policy's internal activations, decompose them into interpretable features with a "
            "Sparse Autoencoder, and watch the failure-relevant feature rise. A minimal DreamAudit perturbation "
            "forces the failure; the internal signature appears before the physical failure, so a monitor can "
            "catch it — and that detectability is what makes the risk insurable.")


def mechanism_payload() -> dict[str, Any]:
    return {"sources": MECH_SOURCES, "steps": MECH_STEPS, "caption": mechanism_caption()}
