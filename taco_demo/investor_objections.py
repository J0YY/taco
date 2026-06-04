"""Investor and carrier objection register for TACO diligence."""

from __future__ import annotations

from typing import Any


def build_investor_objection_register(
    readiness: dict[str, Any],
    methodology_map: dict[str, Any],
    pricing_diligence: dict[str, Any],
    design_partner_plan: dict[str, Any],
    seed_financing_plan: dict[str, Any],
) -> dict[str, Any]:
    """Return evidence-linked answers to likely investor and carrier objections."""

    readiness_score = int(readiness.get("score", 0) or 0)
    methodology_score = int(methodology_map.get("score", 0) or 0)
    pricing_delta = int(pricing_diligence.get("aggregate_control_delta_usd", 0) or 0)
    design_status = str(design_partner_plan.get("status", "unknown"))
    objections = [
        _objection(
            "is_this_real_or_demo_theater",
            "Is this only a polished deterministic demo?",
            _strength(methodology_score >= 75 and readiness_score >= 75, needs_external=True),
            [
                f"VC readiness score {readiness_score}/100 with named gates.",
                f"Methodology evidence score {methodology_score}/100 with claim-level boundaries.",
                "Data-room packet includes manifest, checksum index, certificates, metrics, videos, workflow examples, and verifier.",
            ],
            [
                "Run a live DreamAudit scan in front of reviewers.",
                "Attach partner-specific recorded activation traces for the same certificates.",
            ],
            "Position as an auditable proof of concept plus live-evidence path, not a claim that all evidence is production-sourced.",
        ),
        _objection(
            "where_is_the_buyer_pull",
            "Who urgently needs this, and what validates willingness to engage?",
            _strength(design_status != "not_attached", needs_external=True),
            [
                f"Design-partner plan status: {design_status}.",
                f"{len(design_partner_plan.get('tracks', []))} target tracks: OEM, broker/MGA, carrier/reinsurer.",
                "Seed plan allocates budget to broker, carrier, OEM, and enterprise risk-team pilots.",
            ],
            [
                "Collect signed pilot scopes, reviewer memos, or LOIs.",
                "Record whether each external reviewer would use TACO artifacts in procurement, bind/no-bind, or risk-capital review.",
            ],
            "Use the register to separate planned validation from signed customer demand.",
        ),
        _objection(
            "is_pricing_actuarially_valid",
            "Can this pricing be trusted by a carrier?",
            "artifact_backed_with_actuarial_gap" if pricing_delta > 0 else "needs_work",
            [
                f"Pricing diligence shows ${pricing_delta:,.0f}/mo aggregate control delta.",
                "Disabled controls generate exclusions and changed quote status.",
                pricing_diligence.get("boundary", "Pricing boundary not attached."),
            ],
            [
                "Commission actuarial review for frequency/severity assumptions.",
                "Validate control effectiveness with partner replay and staged-deployment evidence.",
                "Define filed product, MGA, carrier, reinsurer, or referral-path structure.",
            ],
            "Present current pricing as transparent quote-engine sensitivity, not a filed rate or insurance offer.",
        ),
        _objection(
            "why_is_this_venture_scale",
            "Why can this become a venture-scale company rather than a robotics QA tool?",
            _strength(bool(seed_financing_plan.get("milestone_gates")), needs_external=True),
            [
                "Evidence objects can compound across replay certificates, traces, mitigations, exclusions, claims, and renewals.",
                f"Seed plan targets ${int(seed_financing_plan.get('target_raise_usd', 0) or 0):,.0f} across internals integration, evidence generation, design partners, compliance, and GTM.",
                "Workflow can serve OEMs, enterprise buyers, brokers, MGAs, carriers, reinsurers, and certification partners.",
            ],
            [
                "Prove repeated external reviewer usage across at least two buyer categories.",
                "Show evidence reuse across multiple robot task families or policy families.",
            ],
            "Use evidence-network language, but avoid claiming scale until external workflow pull is documented.",
        ),
        _objection(
            "will_simulation_transfer",
            "Will simulator and DreamAudit evidence transfer to real deployments?",
            _simulation_transfer_strength(methodology_map),
            [
                "Methodology map separates simulation evidence from live-field assumptions.",
                "DreamAudit readiness ladder can show when a broader corpus becomes carrier-review-ready.",
                "Replay certificates preserve source paths, validation status, perturbation, minimality, and patch recipes.",
            ],
            [
                "Run partner-specific simulator-to-staged-deployment checks.",
                "Track runtime monitor compliance and renewal deltas after staged deployment.",
            ],
            "Treat simulation as pre-deployment evidence, not proof of live loss frequency.",
        ),
        _objection(
            "is_the_internals_path_real",
            "Is this actually internals-based or just output scoring?",
            _internals_strength(methodology_map),
            [
                "Activation recorder can persist hook-captured NPZ traces without making torch required for local demo.",
                "Methodology map explicitly checks whether primary metrics come from real activation sources.",
                "Internal-risk metrics are tied to certificate IDs in the data room.",
            ],
            [
                "Attach real activation traces for every primary partner certificate.",
                "Calibrate layer-to-signal mappings and document which layers produce underwriting signals.",
            ],
            "Do not upgrade this answer to fully backed unless every primary certificate has real activation metrics.",
        ),
    ]
    return {
        "register_id": "OBJ-TACO-SEED-DILIGENCE",
        "status": _register_status(objections),
        "boundary": "This register is an evidence-linked diligence aid, not proof of signed customers, committed capital, insurance capacity, or actuarial approval.",
        "readiness_score": readiness_score,
        "methodology_score": methodology_score,
        "objections": objections,
    }


def investor_objection_rows(register: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly objection rows."""

    return [
        {
            "Objection": item["objection_id"],
            "Question": item["question"],
            "Answer Strength": item["answer_strength"].replace("_", " ").title(),
            "Current Evidence": "; ".join(item["current_evidence"]),
            "Next Proof": "; ".join(item["next_proof_to_collect"]),
            "Boundary": item["boundary"],
        }
        for item in register["objections"]
    ]


def _objection(
    objection_id: str,
    question: str,
    answer_strength: str,
    current_evidence: list[str],
    next_proof_to_collect: list[str],
    boundary: str,
) -> dict[str, Any]:
    return {
        "objection_id": objection_id,
        "question": question,
        "answer_strength": answer_strength,
        "current_evidence": current_evidence,
        "next_proof_to_collect": next_proof_to_collect,
        "boundary": boundary,
    }


def _strength(condition: bool, *, needs_external: bool) -> str:
    if condition and needs_external:
        return "artifact_backed_needs_external_validation"
    if condition:
        return "artifact_backed"
    return "needs_work"


def _simulation_transfer_strength(methodology_map: dict[str, Any]) -> str:
    claims = {claim["claim_id"]: claim for claim in methodology_map.get("claims", [])}
    status = claims.get("live_corpus_transfer", {}).get("status")
    if status == "research_and_artifact_backed":
        return "artifact_backed_needs_external_validation"
    if status == "demo_backed_needs_live_evidence":
        return "demo_backed_needs_live_evidence"
    return "needs_work"


def _internals_strength(methodology_map: dict[str, Any]) -> str:
    claims = {claim["claim_id"]: claim for claim in methodology_map.get("claims", [])}
    status = claims.get("internal_activation_risk_path", {}).get("status")
    if status == "research_and_artifact_backed":
        return "artifact_backed"
    if status == "demo_backed_needs_live_evidence":
        return "demo_backed_needs_live_evidence"
    return "needs_work"


def _register_status(objections: list[dict[str, Any]]) -> str:
    if all(item["answer_strength"] not in {"needs_work"} for item in objections):
        return "seed_diligence_objections_answered_with_boundaries"
    if any(item["answer_strength"] == "needs_work" for item in objections):
        return "objection_register_needs_more_evidence"
    return "objection_register_ready"
