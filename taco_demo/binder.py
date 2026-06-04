"""Policy binder generation for the TACO MVP."""

from __future__ import annotations

from pathlib import Path

from .schemas import (
    FailureCertificate,
    InsuranceApplication,
    InternalRiskMetrics,
    PolicyBinder,
    QuoteBreakdown,
    dataclass_to_dict,
    now_iso,
    write_json,
)


DISCLAIMER = "This hackathon demo is not an actual insurance policy or offer of insurance."


def _money(value: int) -> str:
    return f"${value:,.0f}"


def _markdown_binder(binder: PolicyBinder) -> str:
    quote = binder.quote
    app = binder.application
    controls = "\n".join(f"* {control}" for control in quote.required_controls) or "* None"
    exclusions = "\n".join(f"* {exclusion}" for exclusion in quote.exclusions) or "* None while required controls remain enabled"
    certs = "\n".join(
        f"* {cert.certificate_id}: {cert.failure_type}, minimal failure cost {cert.minimal_failure_cost:.2f}"
        for cert in binder.certificates
    )
    return f"""# TACO - The Autonomous Casualty Office

## Conditional Learned-Policy Liability Binder

Named Insured: {app.company_name}
Coverage Type: {quote.coverage_type}
Coverage Limit: {_money(quote.coverage_limit_usd)}
Status: {quote.status.replace("_", " ").title()}
Monthly Premium: {_money(quote.final_monthly_premium_usd)}

## Basis of Underwriting

* DreamAudit-style replayable failure certificates
* internal activation traces
* feature stability and unsafe dominance scores
* verified internal-risk controls

## Known Failure Families

{certs}

## Required Controls

{controls}

## Known Failure Family Exclusions

{exclusions}

## Disclaimer

{binder.disclaimer}
"""


def issue_binder(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    output_dir: Path,
) -> Path:
    binder = PolicyBinder(
        binder_id=f"TACO-BINDER-{application.application_id}",
        application=application,
        quote=quote,
        certificates=certificates,
        internal_metrics=metrics,
        created_at=now_iso(),
        disclaimer=DISCLAIMER,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{binder.binder_id}.json"
    md_path = output_dir / f"{binder.binder_id}.md"
    write_json(binder, json_path)
    md_path.write_text(_markdown_binder(binder), encoding="utf-8")
    return json_path
