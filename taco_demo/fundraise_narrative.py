"""Concise seed-fundraise narrative memo for TACO."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_fundraise_narrative_memo(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    investor_summary: dict[str, Any],
    fundraise_readiness: dict[str, Any],
    seed_financing_plan: dict[str, Any],
    seed_round_close_plan: dict[str, Any],
    commercial_traction_plan: dict[str, Any],
    dreamaudit_reconciliation: dict[str, Any],
    activation_evidence_contract: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
) -> dict[str, Any]:
    """Return a compact seed narrative without upgrading unproven claims."""

    readiness_score = int(fundraise_readiness.get("score", 0) or 0)
    close_status = str(seed_round_close_plan.get("status", "unknown"))
    dreamaudit_status = str(dreamaudit_reconciliation.get("status", "not_scanned"))
    activation_status = str(activation_evidence_contract.get("status", "unknown"))
    safe_claim_count = int(seed_round_close_plan.get("current_signal_stack", {}).get("safe_claim_count", 0) or 0)
    status = (
        "seed_narrative_ready_external_proof_pending"
        if readiness_score >= 85 and safe_claim_count >= 8 and "ready" in close_status
        else "seed_narrative_needs_more_evidence"
    )
    return {
        "memo_id": f"NARRATIVE-{application.application_id}",
        "status": status,
        "boundary": (
            "This memo is a seed-fundraise narrative compiler, not evidence of committed financing, signed "
            "customers, carrier capacity, actuarial approval, external validation, or guaranteed demand."
        ),
        "one_liner": investor_summary.get(
            "fundraise_thesis",
            "TACO is the evidence layer that can make learned robot policies insurable before claims history exists.",
        ),
        "target_customer": {
            "company_name": application.company_name,
            "robot_type": application.robot_type,
            "deployment_units": application.deployment_units,
            "coverage_requested_usd": application.coverage_requested_usd,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
        },
        "fundraise_ask": {
            "target_raise_usd": int(seed_financing_plan.get("target_raise_usd", 0) or 0),
            "runway_months": int(seed_financing_plan.get("estimated_runway_months", 0) or 0),
            "capital_thesis": _capital_thesis(seed_financing_plan),
            "milestone_to_unlock_next_round": _next_round_milestone(seed_financing_plan),
        },
        "narrative_arc": _narrative_arc(application, quote),
        "seven_minute_demo": _seven_minute_demo(),
        "proof_stack": _proof_stack(
            fundraise_readiness,
            dreamaudit_reconciliation,
            activation_evidence_contract,
            commercial_traction_plan,
            claim_validation_ledger,
        ),
        "investor_questions": _investor_questions(seed_round_close_plan),
        "thirty_day_close_workflow": _thirty_day_close_workflow(seed_round_close_plan, commercial_traction_plan),
        "killer_risks": _killer_risks(dreamaudit_status, activation_status),
        "safe_claims": [
            "TACO has a working local evidence workflow for learned-policy liability underwriting.",
            "The packet includes replay certificates, trace metrics, conditional quote terms, binders, and verifier checksums.",
            "The current repo exposes live DreamAudit and activation-recording paths while keeping external-proof gaps explicit.",
        ],
        "do_not_claim": [
            "Do not say TACO has signed customers, revenue, carrier capacity, or committed seed financing.",
            "Do not say simulator evidence proves live loss frequency or actuarial rate adequacy.",
            "Do not say activations causally explain failures until the validation protocol passes.",
            "Do not describe reviewer meetings as traction unless the proof registry has written, permissioned artifacts.",
        ],
    }


def fundraise_demo_rows(memo: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly rows for the seven-minute demo."""

    return [
        {
            "Minute": item["minute"],
            "Screen": item["screen"],
            "Say": item["say"],
            "Proof Artifact": item["proof_artifact"],
            "Avoid": item["avoid"],
        }
        for item in memo["seven_minute_demo"]
    ]


def fundraise_proof_rows(memo: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for seed proof stack."""

    return [
        {
            "Proof": item["proof"],
            "Current Evidence": item["current_evidence"],
            "Investor Use": item["investor_use"],
            "Upgrade Gate": item["upgrade_gate"],
        }
        for item in memo["proof_stack"]
    ]


def fundraise_question_rows(memo: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for investor questions and answers."""

    return [
        {
            "Question": item["question"],
            "Answer": item["answer"],
            "Evidence": item["evidence"],
            "Boundary": item["boundary"],
        }
        for item in memo["investor_questions"]
    ]


def fundraise_workflow_rows(memo: dict[str, Any]) -> list[dict[str, str]]:
    """Return rows for the 30-day close workflow."""

    return [
        {
            "Week": item["week"],
            "Goal": item["goal"],
            "Output": item["output"],
            "Do Not Count": item["do_not_count"],
        }
        for item in memo["thirty_day_close_workflow"]
    ]


def _capital_thesis(seed_financing_plan: dict[str, Any]) -> str:
    use_of_funds = list(seed_financing_plan.get("use_of_funds", []))
    top = sorted(use_of_funds, key=lambda item: int(item.get("amount_usd", 0) or 0), reverse=True)[:2]
    categories = ", ".join(str(item.get("category", "unknown")) for item in top)
    return f"Fund the two hardest proof bottlenecks first: {categories}."


def _next_round_milestone(seed_financing_plan: dict[str, Any]) -> str:
    gates = list(seed_financing_plan.get("milestone_gates", []))
    for gate in gates:
        if "paid pilot" in str(gate.get("milestone", "")).lower() or "loi" in str(gate.get("milestone", "")).lower():
            return str(gate.get("success_metric", "Signed commercial proof tied to TACO evidence artifacts."))
    return "External reviewer artifacts and one commercial conversion document tied to TACO evidence objects."


def _narrative_arc(application: InsuranceApplication, quote: QuoteBreakdown) -> list[dict[str, str]]:
    return [
        {
            "beat": "blocked_market",
            "message": f"{application.company_name} wants coverage for {application.deployment_units} robots before fleet telemetry exists.",
            "evidence": "InsuranceApplication plus traditional-underwriting block.",
        },
        {
            "beat": "new_evidence_layer",
            "message": "TACO turns simulator counterfactuals and policy internals into reviewer-verifiable underwriting artifacts.",
            "evidence": "Failure certificates, traces, DreamAudit intake, and activation evidence contract.",
        },
        {
            "beat": "commercial_translation",
            "message": f"Controls and exclusions change the conditional premium to ${quote.final_monthly_premium_usd:,.0f}/month.",
            "evidence": "QuoteBreakdown, pricing diligence, binder, and insurance workflow examples.",
        },
        {
            "beat": "venture_scale_path",
            "message": "The wedge can expand from evidence packets into autonomy-risk infrastructure for OEMs, brokers, carriers, and enterprise buyers.",
            "evidence": "Commercial model, traction plan, unit economics, and seed close plan.",
        },
    ]


def _seven_minute_demo() -> list[dict[str, str]]:
    return [
        _demo("0:00-0:45", "Application", "Traditional underwriting blocks pre-deployment robots because loss history is missing.", "application.json", "Do not start with model dashboards."),
        _demo("0:45-1:45", "Replay Evidence", "TACO creates replayable failure certificates that make the risk inspectable.", "certificates/*.json and GIF replays", "Do not imply simulator failures are live claims."),
        _demo("1:45-2:45", "Internal Signals", "The trace path shows early warning and mitigability signals before the physical failure.", "metrics/*.json and activation evidence contract", "Do not claim causal explanation."),
        _demo("2:45-3:45", "Quote", "Controls and exclusions move the price, so this is an insurance workflow, not just safety scoring.", "quote.json and pricing diligence", "Do not call it filed pricing."),
        _demo("3:45-4:45", "DreamAudit Intake", "Real DreamAudit artifacts can enter the same packet, with gates for what is still non-countable.", "dreamaudit/corpus_reconciliation.json", "Do not hide failing gates."),
        _demo("4:45-5:45", "Investor Case", "The packet includes proof, objections, validation protocol, and commercial conversion workflow.", "claim ledger and proof registry", "Do not claim external validation is complete."),
        _demo("5:45-7:00", "Data Room Packet", "The ask is to fund the proof bottlenecks that turn this into the autonomy-risk evidence layer.", "packet/index.json and seed financing plan", "Do not overstate customers or financing."),
    ]


def _demo(minute: str, screen: str, say: str, proof_artifact: str, avoid: str) -> dict[str, str]:
    return {
        "minute": minute,
        "screen": screen,
        "say": say,
        "proof_artifact": proof_artifact,
        "avoid": avoid,
    }


def _proof_stack(
    fundraise_readiness: dict[str, Any],
    dreamaudit_reconciliation: dict[str, Any],
    activation_evidence_contract: dict[str, Any],
    commercial_traction_plan: dict[str, Any],
    claim_validation_ledger: dict[str, Any],
) -> list[dict[str, str]]:
    readiness_score = int(fundraise_readiness.get("score", 0) or 0)
    countable_claims = sum(1 for claim in claim_validation_ledger.get("claims", []) if "local" in str(claim.get("evidence_level", "")) or "artifact" in str(claim.get("evidence_level", "")))
    return [
        _proof("working_product", f"Readiness score {readiness_score}/100 with local tests and packet export.", "Show the demo and packet as real software.", "External reviewer verifies packet SHA-256."),
        _proof("live_dreamaudit_path", str(dreamaudit_reconciliation.get("status", "unknown")), "Show real artifact ingestion without pretending every gate passed.", "Minimality and reviewer acceptance gates pass."),
        _proof("internals_path", str(activation_evidence_contract.get("status", "unknown")), "Answer the biggest technical-depth objection.", "Recorded policy-specific activation bundle is attached."),
        _proof("commercial_path", str(commercial_traction_plan.get("status", "unknown")), "Show how proof becomes paid evidence work.", "Paid scope, LOI, or permissioned reviewer artifact."),
        _proof("claim_control", f"{countable_claims} claims have local or artifact evidence levels.", "Keep the pitch credible under diligence.", "External proof registry upgrades specific claims."),
    ]


def _proof(proof: str, current_evidence: str, investor_use: str, upgrade_gate: str) -> dict[str, str]:
    return {
        "proof": proof,
        "current_evidence": current_evidence,
        "investor_use": investor_use,
        "upgrade_gate": upgrade_gate,
    }


def _investor_questions(seed_round_close_plan: dict[str, Any]) -> list[dict[str, str]]:
    prompts = list(seed_round_close_plan.get("partner_meeting_prompts", []))
    rows = []
    for prompt in prompts:
        rows.append(
            {
                "question": str(prompt.get("question", "")),
                "answer": str(prompt.get("good_answer", "")),
                "evidence": str(prompt.get("prompt", "seed_close_prompt")),
                "boundary": "Use as meeting guidance; do not count the answer until a written artifact is attached.",
            }
        )
    return rows


def _thirty_day_close_workflow(
    seed_round_close_plan: dict[str, Any],
    commercial_traction_plan: dict[str, Any],
) -> list[dict[str, str]]:
    weekly_motion = list(seed_round_close_plan.get("weekly_close_motion", []))[:5]
    reporting_rules = list(commercial_traction_plan.get("investor_reporting", {}).get("do_not_blend", []))
    rows = []
    for index, week in enumerate(weekly_motion):
        rows.append(
            {
                "week": str(week.get("week", f"week_{index}")),
                "goal": str(week.get("objective", "")),
                "output": str(week.get("output", "")),
                "do_not_count": reporting_rules[index % len(reporting_rules)] if reporting_rules else "Do not count meetings without written artifacts.",
            }
        )
    return rows


def _killer_risks(dreamaudit_status: str, activation_status: str) -> list[dict[str, str]]:
    return [
        {
            "risk": "This is demo theater, not a real product.",
            "answer": "Local tests, packet verifier, DreamAudit adapter, and activation recorder make the workflow inspectable.",
            "still_needed": "External reviewer packet run and written artifact.",
        },
        {
            "risk": "The DreamAudit corpus is not carrier-grade yet.",
            "answer": f"Current reconciliation status is {dreamaudit_status}, with failing gates exposed instead of hidden.",
            "still_needed": "Minimality coverage and reviewer acceptance artifacts.",
        },
        {
            "risk": "Internals may not add signal over outputs.",
            "answer": f"Current activation contract status is {activation_status}; validation protocol blocks stronger claims until baselines pass.",
            "still_needed": "Recorded policy-specific activation bundle and incrementality baseline.",
        },
        {
            "risk": "Insurance pricing and capacity are not real yet.",
            "answer": "TACO is positioned as evidence infrastructure first; actuarial and capacity paths are explicitly future gates.",
            "still_needed": "Carrier/reinsurer review, compliance path, and actuarial memo.",
        },
    ]
