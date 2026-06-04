"""Summaries for live DreamAudit certificate intake."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .dreamaudit_adapter import adapt_dreamaudit_certificates, summarize_adapted_certificates
from .quote_engine import behavioral_fragility_multiplier, required_control_for_failure
from .schemas import FailureCertificate


DEFAULT_DREAMAUDIT_ARTIFACTS = Path("/Users/joyyang/Projects/dreamaudit/artifacts")
DEFAULT_READINESS_LADDER_LIMITS = (250, 1000, 5000)


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


def _has_completed_minimality_report(cert: FailureCertificate) -> bool:
    minimality = cert.metadata.get("minimality")
    if not isinstance(minimality, dict) or not minimality:
        return False
    method = str(minimality.get("method", "")).lower()
    status = str(minimality.get("status", "")).lower()
    if method in {"not_run", "none", "todo"} or status in {"not_run", "not_started", "pending", "in_progress"}:
        return False
    evidence_keys = {
        "smallest_failing_cost_found",
        "failure_rate_at_0_75_cost",
        "smallest_failing_sigma",
        "evaluated_grid",
        "local_shrink_trials",
    }
    return any(key in minimality and minimality[key] not in (None, "", [], {}) for key in evidence_keys)


def underwriting_readiness(certificates: list[FailureCertificate]) -> dict[str, Any]:
    """Summarize whether imported DreamAudit evidence is ready for underwriting review."""

    if not certificates:
        return {
            "readiness_score": 0,
            "status": "no_evidence",
            "required_controls": [],
            "unmapped_failure_families": [],
            "minimality_reports": 0,
            "replay_commands": 0,
            "mean_behavioral_fragility_multiplier": 0.0,
            "gaps": ["No DreamAudit certificates were adapted."],
        }
    failure_families = sorted({cert.failure_type for cert in certificates})
    controls = sorted({control for cert in certificates if (control := required_control_for_failure(cert.failure_type))})
    unmapped = sorted({cert.failure_type for cert in certificates if required_control_for_failure(cert.failure_type) is None})
    minimality_reports = sum(1 for cert in certificates if _has_completed_minimality_report(cert))
    replay_commands = sum(1 for cert in certificates if cert.replay_command)
    source_dirs = {
        str(Path(str(cert.metadata.get("original_path") or "")).parent)
        for cert in certificates
        if cert.metadata.get("original_path")
    }
    mean_behavioral = sum(behavioral_fragility_multiplier(cert) for cert in certificates) / len(certificates)
    gaps = []
    if len(certificates) < 30:
        gaps.append("Fewer than 30 certificates imported; broaden the scan before carrier review.")
    if len(failure_families) < 3:
        gaps.append("Fewer than three failure families represented.")
    if unmapped:
        gaps.append("Some failure families do not yet map to named required controls.")
    if minimality_reports / len(certificates) < 0.5:
        gaps.append("Less than half of certificates include minimality reports.")
    if replay_commands / len(certificates) < 0.8:
        gaps.append("Most certificates need replay or certificate-inspection commands.")
    if len(source_dirs) < 2 and len(certificates) >= 30:
        gaps.append("Evidence comes from one artifact directory; add another suite or seed for source diversity.")
    score = 100
    score -= 25 if len(certificates) < 30 else 0
    score -= 15 if len(failure_families) < 3 else 0
    score -= 20 if unmapped else 0
    score -= 15 if minimality_reports / len(certificates) < 0.5 else 0
    score -= 10 if replay_commands / len(certificates) < 0.8 else 0
    score -= 10 if len(source_dirs) < 2 and len(certificates) >= 30 else 0
    score = max(0, score)
    status = "carrier_review_ready" if score >= 80 and not gaps else "needs_more_evidence" if score >= 50 else "early_evidence"
    return {
        "readiness_score": score,
        "status": status,
        "required_controls": controls,
        "unmapped_failure_families": unmapped,
        "minimality_reports": minimality_reports,
        "replay_commands": replay_commands,
        "mean_behavioral_fragility_multiplier": round(mean_behavioral, 3),
        "source_directories": len(source_dirs),
        "gaps": gaps,
    }


def evidence_depth_ladder(certificates: list[FailureCertificate], limits: tuple[int, ...]) -> list[dict[str, Any]]:
    """Return readiness snapshots for progressively deeper DreamAudit scans."""

    rows = []
    for scan_limit in sorted({limit for limit in limits if limit > 0}):
        subset = certificates[:scan_limit]
        readiness = underwriting_readiness(subset)
        rows.append(
            {
                "scan_limit": scan_limit,
                "certificates": len(subset),
                "readiness_score": readiness["readiness_score"],
                "status": readiness["status"],
                "failure_families": len({cert.failure_type for cert in subset}),
                "minimality_reports": readiness["minimality_reports"],
                "replay_commands": readiness["replay_commands"],
                "source_directories": readiness.get("source_directories", 0),
                "gaps": readiness["gaps"],
            }
        )
    return rows


def recommended_scan_limit(ladder: list[dict[str, Any]]) -> int | None:
    """Return the first scan depth that is carrier-review-ready, if any."""

    for row in ladder:
        if row["status"] == "carrier_review_ready":
            return int(row["scan_limit"])
    return None


def build_dreamaudit_intake_summary(
    root: Path | str = DEFAULT_DREAMAUDIT_ARTIFACTS,
    *,
    limit: int | None = 250,
    max_rows: int = 25,
    readiness_ladder_limits: tuple[int, ...] = DEFAULT_READINESS_LADDER_LIMITS,
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
            "readiness": underwriting_readiness([]),
            "evidence_depth_ladder": [],
            "recommended_scan_limit": None,
            "rows": [],
        }
    ladder_limits = tuple(limit for limit in readiness_ladder_limits if limit > 0)
    if limit is not None and limit > 0:
        ladder_limits = tuple(sorted(set((*ladder_limits, limit))))
    scan_limit = None
    if limit is not None:
        scan_limit = max((*ladder_limits, limit), default=limit)
    all_certs = adapt_dreamaudit_certificates(root_path, limit=scan_limit)
    certs = all_certs if limit is None else all_certs[:limit]
    ladder = evidence_depth_ladder(all_certs, ladder_limits)
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
        "readiness": underwriting_readiness(certs),
        "evidence_depth_ladder": ladder,
        "recommended_scan_limit": recommended_scan_limit(ladder),
        "rows": certificate_rows(certs, max_rows=max_rows),
    }
