"""Issue TACO internal underwriting certificates and binder markdown."""

from __future__ import annotations

from pathlib import Path

from .schemas import (
    InsuranceApplication,
    InternalRiskMetrics,
    InternalUnderwritingCertificate,
    NormalizedDreamAuditCertificate,
    QuoteBreakdown,
    ReplayArtifacts,
    dataclass_to_dict,
    now_iso,
    write_json,
)


DISCLAIMER = (
    "This hackathon demo is not an actual insurance policy or offer of insurance. "
    "It demonstrates how learned-policy liability underwriting could be tied to DreamAudit replayable failures and internal model risk signatures."
)


def build_internal_underwriting_certificate(
    application: InsuranceApplication,
    source_cert: NormalizedDreamAuditCertificate,
    metrics: InternalRiskMetrics,
    quote: QuoteBreakdown,
    artifacts: ReplayArtifacts,
) -> InternalUnderwritingCertificate:
    return InternalUnderwritingCertificate(
        certificate_id=f"TACO-IUC-{application.application_id}-{source_cert.certificate_id}",
        source_dreamaudit_certificate_id=source_cert.certificate_id,
        application=application,
        robot_policy={"policy_id": source_cert.policy_id, "robot_type": application.robot_type},
        behavioral_evidence=dataclass_to_dict(source_cert),
        internal_evidence=metrics,
        mitigation_evidence={"patch_recipe": source_cert.patch_recipe, "artifacts": dataclass_to_dict(artifacts)},
        insurance_decision=quote,
        created_at=now_iso(),
        disclaimer=DISCLAIMER,
    )


def _binder_markdown(application: InsuranceApplication, certificates: list[NormalizedDreamAuditCertificate], quote: QuoteBreakdown) -> str:
    controls = "\n".join(f"- {item}" for item in quote.required_controls) or "- None"
    exclusions = "\n".join(f"- {item}" for item in quote.exclusions) or "- None while required controls remain enabled"
    certs = "\n".join(f"- {c.certificate_id}: {c.failure_type}, minimal cost {c.minimal_failure_cost:.2f}" for c in certificates)
    return f"""# TACO - The Autonomous Casualty Office

## Conditional Learned-Policy Liability Binder

Named Insured: {application.company_name}
Coverage Type: {quote.coverage_type}
Coverage Limit: ${quote.coverage_limit_usd:,.0f}
Status: {quote.status.replace("_", " ").title()}
Monthly Premium: ${quote.final_monthly_premium_usd:,.0f}

## Basis of Underwriting
- DreamAudit replayable failure certificates
- internal activation traces
- feature stability and unsafe dominance scores
- verified internal-risk monitors

## Known Failure Families
{certs}

## Required Controls
{controls}

## Known Failure Family Exclusions
{exclusions}

## Reaudit Trigger
- Reaudit is required after any learned-policy model update, material prompt/schema change, or monitor deactivation.

{DISCLAIMER}
"""


def issue_policy_bundle(
    application: InsuranceApplication,
    certificates: list[NormalizedDreamAuditCertificate],
    metrics_by_cert: dict[str, InternalRiskMetrics],
    quote: QuoteBreakdown,
    artifacts_by_cert: dict[str, ReplayArtifacts],
    output_dir: Path,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    representative = certificates[0]
    cert = build_internal_underwriting_certificate(
        application,
        representative,
        metrics_by_cert[representative.certificate_id],
        quote,
        artifacts_by_cert[representative.certificate_id],
    )
    json_path = output_dir / f"TACO-BINDER-{application.application_id}.json"
    md_path = output_dir / f"TACO-BINDER-{application.application_id}.md"
    write_json({"branding": "TACO - The Autonomous Casualty Office", "bundle": dataclass_to_dict(cert), "all_certificates": [dataclass_to_dict(c) for c in certificates]}, json_path)
    md_path.write_text(_binder_markdown(application, certificates, quote), encoding="utf-8")
    return json_path

