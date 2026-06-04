"""Investor and research-case helpers for the TACO demo."""

from __future__ import annotations

from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown


RESEARCH_FOUNDATIONS = [
    {
        "claim": "Simulation can be a scalable, reproducible evaluation layer for robot policy behavior.",
        "evidence": "SIMPLER reports paired simulation and real-world robot manipulation evaluations and argues simulation can reflect real policy behavior modes under distribution shift.",
        "source": "SIMPLER / CoRL 2024",
        "url": "https://www.oiermees.com/publication/simpler/",
        "taco_translation": "TACO treats simulation replay as pre-deployment actuarial evidence, not as a replacement for field telemetry.",
    },
    {
        "claim": "Robot policy search in simulation needs explicit transfer and robustness controls.",
        "evidence": "Domain randomization work highlights simulation optimization bias and motivates perturbing simulator parameters to learn robust policies.",
        "source": "Muratore et al., CoRL 2018",
        "url": "https://proceedings.mlr.press/v87/muratore18a.html",
        "taco_translation": "TACO prices low-cost failure boundaries and requires controls before coverage attaches.",
    },
    {
        "claim": "Internal activations can expose behavior-relevant concepts that are not visible from outputs alone.",
        "evidence": "Sparse autoencoder research shows internal activations can be decomposed into more interpretable features and linked to counterfactual behavior.",
        "source": "Sparse Autoencoders Find Highly Interpretable Features, ICLR 2024",
        "url": "https://proceedings.iclr.cc/paper_files/paper/2024/hash/1fa1ab11f4bd5f94b2ec20e794dbfa3b-Abstract-Conference.html",
        "taco_translation": "TACO's trace metrics are a lightweight proxy for the future SAE/VLA feature layer.",
    },
    {
        "claim": "Feature-level interpretability can become an operational safety monitor.",
        "evidence": "Anthropic's interpretability work describes dictionary-learning features and notes such techniques may support monitoring dangerous behaviors.",
        "source": "Anthropic, Mapping the Mind of a Large Language Model, 2024",
        "url": "https://www.anthropic.com/research/mapping-mind-language-model",
        "taco_translation": "TACO converts internal risk signatures into insurance controls, exclusions, and re-audit triggers.",
    },
]


UNDERWRITING_WORKFLOW = [
    {
        "step": "1. Pre-telemetry application",
        "operator": "Robot OEM or enterprise buyer",
        "artifact": "InsuranceApplication JSON",
        "investor_point": "TACO starts where traditional loss-history underwriting stalls.",
    },
    {
        "step": "2. Failure boundary discovery",
        "operator": "DreamAudit-style simulator audit",
        "artifact": "FailureCertificate JSON + replay GIF/video",
        "investor_point": "Replayable counterexamples become underwriting evidence objects.",
    },
    {
        "step": "3. Internal risk trace analysis",
        "operator": "Trace analyzer / future SAE feature stack",
        "artifact": "NPZ traces + InternalRiskMetrics",
        "investor_point": "The product prices why the policy failed, not just that it failed.",
    },
    {
        "step": "4. Conditional quote",
        "operator": "Quote engine",
        "artifact": "QuoteBreakdown JSON",
        "investor_point": "Controls and exclusions create a commercial path to deploy risky autonomy.",
    },
    {
        "step": "5. Binder and compliance loop",
        "operator": "Insurer, MGA, broker, or certification partner",
        "artifact": "PolicyBinder JSON/Markdown",
        "investor_point": "The evidence layer can attach to re-audits, renewals, and runtime compliance logs.",
    },
]


MOAT_HYPOTHESES = [
    "Evidence graph: replay certificates, trace metrics, mitigations, exclusions, and claims outcomes compound into proprietary underwriting data.",
    "Workflow lock-in: brokers, carriers, robotics OEMs, and enterprise risk teams need a shared artifact format for autonomy risk.",
    "Model-risk taxonomy: repeated failure families become a defensible schema for learned-policy liability.",
    "Control marketplace: required monitors can become insurability prerequisites for robot deployments.",
]


FUNDRAISE_MILESTONES = [
    "Convert 3 fallback certificates into 30+ real DreamAudit simulator certificates across LIBERO, ManiSkill, and RoboCasa-style tasks.",
    "Replace heuristic trace probes with recorded VLA activations and SAE feature dictionaries for at least one open policy.",
    "Run 2-3 design-partner underwriting reviews with robotics OEMs, specialty brokers, or autonomy insurers.",
    "Produce a reinsurer-facing loss-evidence memo linking failure families to control effectiveness and premium deltas.",
    "Log monitor compliance over replay and staged deployment runs to show a renewal data loop.",
]


def investor_summary(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
) -> dict[str, object]:
    margins = [metric.early_warning_margin_seconds for metric in metrics]
    risks = [metric.internal_risk_score for metric in metrics]
    mitigability = [metric.causal_mitigability_score for metric in metrics]
    return {
        "fundraise_thesis": "TACO is the evidence layer that can make frontier robot autonomy insurable before claims history exists.",
        "wedge_customer": application.company_name,
        "initial_buyer": "robotics OEM risk team, enterprise insurance buyer, specialty broker, or MGA underwriting desk",
        "proof_points": [
            f"{len(certificates)} replayable known failure families generated",
            f"earliest internal warning: {max(margins) if margins else 0:.2f}s before failure",
            f"mean mitigability score: {sum(mitigability) / len(mitigability) if mitigability else 0:.2f}",
            f"conditional premium: ${quote.final_monthly_premium_usd:,.0f}/month",
        ],
        "research_backed_method": [
            "simulation replay for scalable and reproducible pre-deployment evidence",
            "perturbation-based failure boundary search",
            "internal activation features as risk signatures",
            "controls and exclusions as the bridge from safety engineering to insurance terms",
        ],
        "investor_risk": [
            "Fallback traces are synthetic until replaced by real VLA activations.",
            "Quote formula is a transparent demo formula, not filed actuarial pricing.",
            "Carrier adoption requires compliance, capital, and regulatory partnerships.",
        ],
        "next_derisking_step": FUNDRAISE_MILESTONES[0],
        "aggregate_internal_risk": round(sum(risks) / len(risks), 3) if risks else 0.0,
    }
