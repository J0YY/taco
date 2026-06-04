"""Summaries for live DreamAudit certificate intake."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .dreamaudit_adapter import adapt_dreamaudit_certificates, summarize_adapted_certificates
from .schemas import FailureCertificate


DEFAULT_DREAMAUDIT_ARTIFACTS = Path("/Users/joyyang/Projects/dreamaudit/artifacts")


def certificate_rows(certificates: list[FailureCertificate], max_rows: int = 25) -> list[dict[str, Any]]:
    """Return UI-friendly rows for adapted DreamAudit certificates."""

    rows = []
    for cert in certificates[:max_rows]:
        rows.append(
            {
                "Certificate ID": cert.certificate_id,
                "Policy": cert.policy_id,
                "Failure family": cert.failure_type,
                "Severity": cert.severity,
                "Minimal cost": cert.minimal_failure_cost,
                "Neighborhood failure rate": cert.failure_rate_neighborhood,
                "Task": cert.task_id,
                "Source": cert.source.replace("dreamaudit:", ""),
            }
        )
    return rows


def build_dreamaudit_intake_summary(
    root: Path | str = DEFAULT_DREAMAUDIT_ARTIFACTS,
    *,
    limit: int = 250,
    max_rows: int = 25,
) -> dict[str, Any]:
    """Scan a DreamAudit artifact directory and summarize adapted evidence."""

    root_path = Path(root)
    if not root_path.exists():
        return {
            "root": str(root_path),
            "root_exists": False,
            "summary": summarize_adapted_certificates([]),
            "failure_counts": {},
            "schema_counts": {},
            "backend_counts": {},
            "rows": [],
        }
    certs = adapt_dreamaudit_certificates(root_path, limit=limit)
    failure_counts = Counter(cert.failure_type for cert in certs)
    schema_counts = Counter(str(cert.metadata.get("dreamaudit_schema", "unknown")) for cert in certs)
    backend_counts = Counter(str(cert.metadata.get("backend") or "unknown") for cert in certs)
    return {
        "root": str(root_path),
        "root_exists": True,
        "summary": summarize_adapted_certificates(certs),
        "failure_counts": dict(sorted(failure_counts.items())),
        "schema_counts": dict(sorted(schema_counts.items())),
        "backend_counts": dict(sorted(backend_counts.items())),
        "rows": certificate_rows(certs, max_rows=max_rows),
    }
