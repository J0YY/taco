"""VC data-room checklist generation for TACO diligence."""

from __future__ import annotations

import io
import hashlib
import json
import re
from typing import Any
import zipfile

from .insurance_scenarios import INSURANCE_SCENARIOS
from .investor_case import RESEARCH_FOUNDATIONS
from .schemas import FailureCertificate, InsuranceApplication, InternalRiskMetrics, QuoteBreakdown, dataclass_to_dict


ZIP_TIMESTAMP = (2026, 6, 4, 0, 0, 0)
PACKET_INDEX_PATH = "packet/index.json"
REQUIRED_BUNDLE_FILES = {
    "README.md",
    "manifest.json",
    "application.json",
    "quote.json",
    "checklist.json",
    "diligence_memo.md",
    "insurance/workflow_examples.json",
    "research/sources.json",
    "suite/video_index.json",
    "dreamaudit/summary.json",
}


def build_data_room_checklist(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return diligence packet items investors and carriers will ask to inspect."""

    suite_cases = list(suite_manifest.get("cases", []))
    suite_size = int(suite_manifest.get("suite_size", len(suite_cases)) or 0)
    suite_families = {str(case.get("failure_family", "unknown")) for case in suite_cases}
    metric_ids = {metric.certificate_id for metric in metrics}
    covered_metrics = sum(1 for cert in certificates if cert.certificate_id in metric_ids)
    metric_sources = sorted({metric.metrics_source for metric in metrics})
    metric_source_text = ", ".join(metric_sources) if metric_sources else "none"
    dreamaudit = _dreamaudit_status(dreamaudit_intake)
    items = [
        _item(
            "Application And Coverage File",
            "ready" if application.application_id and quote.quote_id else "needs_work",
            f"{application.application_id}; ${application.coverage_requested_usd:,.0f} requested coverage; quote {quote.quote_id}.",
            "Keep the application JSON, quote breakdown, and coverage request in the diligence packet.",
        ),
        _item(
            "Replay Failure Certificates",
            "ready" if len(certificates) >= 3 else "needs_work",
            f"{len(certificates)} primary replayable failure certificates attached.",
            "Attach at least three primary certificates with replay commands and required controls.",
        ),
        _item(
            "Internal Risk Trace Coverage",
            "ready" if certificates and covered_metrics == len(certificates) else "needs_work",
            f"{covered_metrics}/{len(certificates)} certificates have internal risk metrics; sources: {metric_source_text}.",
            "Attach activation/trace NPZ evidence for every primary certificate.",
        ),
        _item(
            "ManiSkill/RMA Video Suite",
            "ready" if suite_size >= 40 and len(suite_families) >= 8 else "needs_work",
            f"{suite_size} videos across {len(suite_families)} failure families.",
            "Keep the 40-video replay suite and manifest in the data room.",
        ),
        _item(
            "Insurance Workflow And Pricing Examples",
            "ready" if len(INSURANCE_SCENARIOS) >= 10 else "needs_work",
            f"{len(INSURANCE_SCENARIOS)} priced end-to-end insurance workflows.",
            "Include 10+ workflows with controls, exclusions, and premium deltas.",
        ),
        _item(
            "Live DreamAudit Corpus",
            dreamaudit["status"],
            dreamaudit["evidence"],
            dreamaudit["next_action"],
        ),
        _item(
            "Research And Methodology Sources",
            "ready" if len(RESEARCH_FOUNDATIONS) >= 4 else "needs_work",
            f"{len(RESEARCH_FOUNDATIONS)} linked research anchors.",
            "Attach primary-source references for simulation, perturbation, interpretability, and monitoring claims.",
        ),
        _item(
            "Design-Partner References",
            "external_pending",
            "Signed broker/carrier/OEM design-partner reviews are not represented in local demo artifacts.",
            "Secure 2-3 design-partner reviews and add written feedback or LOIs to the data room.",
        ),
    ]
    ready_items = sum(1 for item in items if item["status"] == "ready")
    internal_items = [item for item in items if item["status"] != "external_pending"]
    internal_ready = sum(1 for item in internal_items if item["status"] == "ready")
    return {
        "ready_items": ready_items,
        "total_items": len(items),
        "internal_ready_items": internal_ready,
        "internal_total_items": len(internal_items),
        "internal_packet_score": round(100 * internal_ready / len(internal_items)) if internal_items else 0,
        "external_pending_items": sum(1 for item in items if item["status"] == "external_pending"),
        "items": items,
    }


def data_room_rows(checklist: dict[str, Any]) -> list[dict[str, Any]]:
    """Return table rows for the Streamlit UI and Markdown memo."""

    return [
        {
            "Artifact": item["artifact"],
            "Status": item["status"].replace("_", " ").title(),
            "Evidence": item["evidence"],
            "Next Action": item["next_action"],
        }
        for item in checklist["items"]
    ]


def build_data_room_manifest(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a machine-readable diligence manifest for export."""

    checklist = build_data_room_checklist(application, certificates, metrics, quote, suite_manifest, dreamaudit_intake)
    suite_cases = list(suite_manifest.get("cases", []))
    dreamaudit_summary = _dreamaudit_manifest_summary(dreamaudit_intake)
    return {
        "manifest_id": f"DR-{application.application_id}",
        "purpose": "VC/carrier diligence packet for learned-policy liability underwriting evidence.",
        "application": dataclass_to_dict(application),
        "quote": dataclass_to_dict(quote),
        "checklist": checklist,
        "primary_certificates": [dataclass_to_dict(cert) for cert in certificates],
        "internal_metrics": [dataclass_to_dict(metric) for metric in metrics],
        "suite_summary": {
            "suite_name": suite_manifest.get("suite_name", "unknown"),
            "suite_size": int(suite_manifest.get("suite_size", len(suite_cases)) or 0),
            "failure_families": sorted({str(case.get("failure_family", "unknown")) for case in suite_cases}),
            "video_paths": [str(case.get("video_path", "")) for case in suite_cases if case.get("video_path")],
        },
        "dreamaudit": dreamaudit_summary,
    }


def build_data_room_bundle(
    application: InsuranceApplication,
    certificates: list[FailureCertificate],
    metrics: list[InternalRiskMetrics],
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    diligence_memo: str,
    dreamaudit_intake: dict[str, Any] | None = None,
) -> bytes:
    """Build a ZIP diligence packet with machine-readable contracts and memo."""

    manifest = build_data_room_manifest(application, certificates, metrics, quote, suite_manifest, dreamaudit_intake)
    entries: list[tuple[str, bytes]] = [
        ("README.md", _text_bytes(_bundle_readme(manifest))),
        ("manifest.json", _json_bytes(manifest)),
        ("application.json", _json_bytes(manifest["application"])),
        ("quote.json", _json_bytes(manifest["quote"])),
        ("checklist.json", _json_bytes(manifest["checklist"])),
        ("diligence_memo.md", _text_bytes(diligence_memo)),
        ("insurance/workflow_examples.json", _json_bytes(INSURANCE_SCENARIOS)),
        ("research/sources.json", _json_bytes(RESEARCH_FOUNDATIONS)),
        ("suite/video_index.json", _json_bytes(manifest["suite_summary"])),
        ("dreamaudit/summary.json", _json_bytes(manifest["dreamaudit"])),
    ]
    certificate_names: set[str] = set()
    for cert in certificates:
        name = _safe_zip_stem(cert.certificate_id, certificate_names)
        entries.append((f"certificates/{name}.json", _json_bytes(dataclass_to_dict(cert))))
    metric_names: set[str] = set()
    for metric in metrics:
        name = _safe_zip_stem(metric.certificate_id, metric_names)
        entries.append((f"metrics/{name}.json", _json_bytes(dataclass_to_dict(metric))))
    packet_index = _packet_index(manifest["manifest_id"], entries)
    entries.append((PACKET_INDEX_PATH, _json_bytes(packet_index)))

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries:
            _write_zip_bytes(archive, name, payload)
    return buffer.getvalue()


def data_room_bundle_summary(bundle_bytes: bytes) -> dict[str, Any]:
    """Return lightweight facts about a generated data-room ZIP."""

    with zipfile.ZipFile(io.BytesIO(bundle_bytes), mode="r") as archive:
        names = sorted(archive.namelist())
    return {
        "file_count": len(names),
        "contains_manifest": "manifest.json" in names,
        "contains_memo": "diligence_memo.md" in names,
        "contains_video_index": "suite/video_index.json" in names,
        "contains_packet_index": PACKET_INDEX_PATH in names,
        "files": names,
    }


def verify_data_room_bundle(bundle_bytes: bytes) -> dict[str, Any]:
    """Verify ZIP member safety and packet-index checksums."""

    issues: list[str] = []
    names: list[str] = []
    index: dict[str, Any] | None = None
    indexed_file_count = 0
    try:
        with zipfile.ZipFile(io.BytesIO(bundle_bytes), mode="r") as archive:
            names = sorted(archive.namelist())
            unsafe_names = [name for name in names if _unsafe_zip_name(name)]
            if unsafe_names:
                issues.extend(f"Unsafe ZIP member path: {name}" for name in unsafe_names)
            duplicate_names = sorted({name for name in names if names.count(name) > 1})
            if duplicate_names:
                issues.extend(f"Duplicate ZIP member path: {name}" for name in duplicate_names)
            required_missing = sorted(REQUIRED_BUNDLE_FILES - set(names))
            if required_missing:
                issues.extend(f"Missing required file: {name}" for name in required_missing)
            if PACKET_INDEX_PATH not in names:
                issues.append(f"Missing required file: {PACKET_INDEX_PATH}")
            else:
                raw_index = json.loads(archive.read(PACKET_INDEX_PATH))
                if isinstance(raw_index, dict):
                    index = raw_index
                else:
                    issues.append("Invalid packet index: expected JSON object")
            if index is not None:
                indexed_items = index.get("files")
                if not isinstance(indexed_items, list) or not indexed_items:
                    issues.append("Invalid packet index: files must be a non-empty list")
                    indexed_items = []
                indexed_files = {}
                for item in indexed_items:
                    if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                        issues.append("Invalid packet index: file entries must be objects with string paths")
                        continue
                    indexed_files[item["path"]] = item
                indexed_file_count = len(indexed_files)
                for name, item in indexed_files.items():
                    if name not in names:
                        issues.append(f"Indexed file missing from ZIP: {name}")
                        continue
                    payload = archive.read(name)
                    expected = str(item.get("sha256", ""))
                    actual = hashlib.sha256(payload).hexdigest()
                    if actual != expected:
                        issues.append(f"Checksum mismatch: {name}")
                    if len(payload) != int(item.get("bytes", -1)):
                        issues.append(f"Byte length mismatch: {name}")
                unindexed = sorted(set(names) - set(indexed_files) - {PACKET_INDEX_PATH})
                if unindexed:
                    issues.extend(f"ZIP file missing from packet index: {name}" for name in unindexed)
    except (KeyError, TypeError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        issues.append(f"Invalid data-room packet: {exc}")
    return {
        "valid": not issues,
        "issues": issues,
        "file_count": len(names),
        "indexed_file_count": indexed_file_count,
    }


def _dreamaudit_status(dreamaudit_intake: dict[str, Any] | None) -> dict[str, str]:
    if not dreamaudit_intake:
        return {
            "status": "needs_live_scan",
            "evidence": "No DreamAudit intake scan is attached.",
            "next_action": "Run DreamAudit Intake and attach the carrier-readiness ladder.",
        }
    if not dreamaudit_intake.get("root_exists"):
        return {
            "status": "needs_live_scan",
            "evidence": f"DreamAudit path not found: {dreamaudit_intake.get('root', 'unknown')}.",
            "next_action": "Point DreamAudit Intake at an existing artifact directory.",
        }
    readiness = dreamaudit_intake.get("readiness", {})
    ladder = list(dreamaudit_intake.get("evidence_depth_ladder", []))
    recommended = dreamaudit_intake.get("recommended_scan_limit")
    carrier_ready = readiness.get("status") == "carrier_review_ready" or any(
        row.get("status") == "carrier_review_ready" for row in ladder
    )
    selected_count = int(dreamaudit_intake.get("summary", {}).get("certificates", 0) or 0)
    selected_score = int(readiness.get("readiness_score", 0) or 0)
    status = "ready" if carrier_ready else "needs_live_scan"
    evidence = (
        f"{selected_count} selected DreamAudit certificates; selected readiness {selected_score}/100; "
        f"recommended carrier-ready depth {recommended or 'not found'}."
    )
    next_action = (
        "Attach the carrier-ready ladder and representative source paths to the data room."
        if carrier_ready
        else "Expand the DreamAudit scan until a carrier-ready ladder depth is available."
    )
    return {"status": status, "evidence": evidence, "next_action": next_action}


def _dreamaudit_manifest_summary(dreamaudit_intake: dict[str, Any] | None) -> dict[str, Any]:
    if not dreamaudit_intake:
        return {"attached": False, "status": "not_scanned"}
    readiness = dreamaudit_intake.get("readiness", {})
    return {
        "attached": True,
        "root": dreamaudit_intake.get("root"),
        "root_exists": bool(dreamaudit_intake.get("root_exists")),
        "selected_certificates": int(dreamaudit_intake.get("summary", {}).get("certificates", 0) or 0),
        "readiness_score": int(readiness.get("readiness_score", 0) or 0),
        "readiness_status": readiness.get("status", "unknown"),
        "recommended_scan_limit": dreamaudit_intake.get("recommended_scan_limit"),
        "evidence_depth_ladder": dreamaudit_intake.get("evidence_depth_ladder", []),
        "gaps": readiness.get("gaps", []),
    }


def _item(artifact: str, status: str, evidence: str, next_action: str) -> dict[str, str]:
    return {
        "artifact": artifact,
        "status": status,
        "evidence": evidence,
        "next_action": next_action,
    }


def _json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")


def _text_bytes(payload: str) -> bytes:
    return payload.encode("utf-8")


def _write_zip_bytes(archive: zipfile.ZipFile, name: str, payload: bytes) -> None:
    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    info.compress_type = zipfile.ZIP_DEFLATED
    archive.writestr(info, payload)


def _packet_index(manifest_id: str, entries: list[tuple[str, bytes]]) -> dict[str, Any]:
    return {
        "packet_format": "taco_data_room_zip_v1",
        "manifest_id": manifest_id,
        "checksum_algorithm": "sha256",
        "indexed_file_count": len(entries),
        "required_files": sorted(REQUIRED_BUNDLE_FILES | {PACKET_INDEX_PATH}),
        "files": [
            {
                "path": name,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            for name, payload in sorted(entries)
        ],
    }


def _unsafe_zip_name(name: str) -> bool:
    return name.startswith("/") or name.startswith("../") or "/../" in name or "\\" in name


def _safe_zip_stem(raw_id: str, used: set[str]) -> str:
    stem = re.sub(r"[^0-9A-Za-z._-]+", "_", str(raw_id)).strip("._-")
    if not stem or stem in {".", ".."}:
        stem = "evidence"
    candidate = stem
    counter = 2
    while candidate in used:
        candidate = f"{stem}__{counter}"
        counter += 1
    used.add(candidate)
    return candidate


def _bundle_readme(manifest: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# TACO Data Room Packet",
            "",
            f"Manifest: {manifest['manifest_id']}",
            "",
            "This packet contains the machine-readable underwriting contracts and diligence memo for the TACO learned-policy liability demo.",
            "Replay videos and DreamAudit source artifacts are indexed by path rather than embedded, so reviewers can verify local evidence without treating generated media as opaque marketing collateral.",
            "",
            "Core files:",
            "",
            "* `manifest.json` - full packet index",
            "* `application.json` - insurance application",
            "* `quote.json` - quote breakdown",
            "* `checklist.json` - VC/carrier readiness checklist",
            "* `diligence_memo.md` - investor and underwriting memo",
            "* `packet/index.json` - SHA-256 checksum index for packet verification",
            "* `insurance/workflow_examples.json` - priced workflow examples",
            "* `research/sources.json` - research-methodology anchors",
            "* `certificates/` - primary replay failure certificates",
            "* `metrics/` - internal-risk metric contracts",
            "* `suite/video_index.json` - 40-video ManiSkill/RMA suite index",
            "* `dreamaudit/summary.json` - attached DreamAudit intake summary",
            "",
            "Boundary: this packet is diligence evidence for a local proof of concept, not an insurance offer or filed actuarial product.",
            "",
        ]
    )
