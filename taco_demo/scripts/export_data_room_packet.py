"""Export and verify the TACO data-room packet from the command line."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from taco_demo.data_room import build_data_room_bundle, build_data_room_manifest, data_room_bundle_summary, verify_data_room_bundle
from taco_demo.diligence_memo import build_diligence_memo
from taco_demo.dreamaudit_intake import build_dreamaudit_intake_summary
from taco_demo.maniskill_suite import load_maniskill_suite
from taco_demo.quote_engine import generate_quote
from taco_demo.schemas import FailureCertificate, InsuranceApplication, read_json
from taco_demo.scripts.bootstrap_demo_data import bootstrap
from taco_demo.trace_scoring import compute_internal_metrics, load_trace


DEFAULT_DATA_ROOT = Path(__file__).resolve().parents[1] / "data"
DEFAULT_OUTPUT_PATH = DEFAULT_DATA_ROOT / "data_room" / "TACO-DATAROOM-APP-APEX-001.zip"
DEFAULT_CONTROLS = {
    "reaudit_required_after_model_update": True,
    "occlusion_risk_monitor_enabled": True,
    "language_override_sanitizer_enabled": True,
    "target_identity_confirmation_enabled": True,
}


def export_data_room_packet(
    output_path: Path | str = DEFAULT_OUTPUT_PATH,
    *,
    data_root: Path | str = DEFAULT_DATA_ROOT,
    force_bootstrap: bool = False,
    manifest_output: Path | str | None = None,
    memo_output: Path | str | None = None,
    dreamaudit_root: Path | str | None = None,
    dreamaudit_limit: int = 250,
) -> dict[str, Any]:
    """Build the offline diligence packet and return a verifier summary."""

    root = Path(data_root)
    _ensure_fixture_evidence(root, force_bootstrap=force_bootstrap)
    application = _load_application(root)
    certificates = _load_certificates(root)
    metrics = [_compute_metrics(root, certificate) for certificate in certificates]
    metrics_by_id = {metric.certificate_id: metric for metric in metrics}
    quote = generate_quote(application, certificates, metrics_by_id, DEFAULT_CONTROLS)
    suite_manifest = load_maniskill_suite(root)
    dreamaudit_intake = (
        build_dreamaudit_intake_summary(str(dreamaudit_root), limit=dreamaudit_limit)
        if dreamaudit_root is not None
        else None
    )
    manifest = build_data_room_manifest(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        dreamaudit_intake,
    )
    memo = build_diligence_memo(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        dreamaudit_intake,
    )
    bundle = build_data_room_bundle(
        application,
        certificates,
        metrics,
        quote,
        suite_manifest,
        memo,
        dreamaudit_intake,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(bundle)
    if manifest_output is not None:
        _write_json(Path(manifest_output), manifest)
    if memo_output is not None:
        memo_path = Path(memo_output)
        memo_path.parent.mkdir(parents=True, exist_ok=True)
        memo_path.write_text(memo, encoding="utf-8")
    verification = verify_data_room_bundle(bundle)
    summary = data_room_bundle_summary(bundle)
    return {
        "valid": verification["valid"],
        "issues": verification["issues"],
        "output_path": str(output),
        "packet_sha256": verification["packet_sha256"],
        "file_count": verification["file_count"],
        "indexed_file_count": verification["indexed_file_count"],
        "manifest_id": manifest["manifest_id"],
        "packet_format": _packet_format_from_manifest_bundle(bundle),
        "bundle_file_count": summary["file_count"],
        "application_id": application.application_id,
        "quote_id": quote.quote_id,
        "final_monthly_premium_usd": quote.final_monthly_premium_usd,
        "certificate_count": len(certificates),
        "metric_count": len(metrics),
        "suite_size": int(suite_manifest.get("suite_size", 0) or 0),
        "dreamaudit_attached": dreamaudit_intake is not None,
    }


def _ensure_fixture_evidence(root: Path, *, force_bootstrap: bool) -> None:
    required = [
        root / "applications" / "APP-APEX-001.json",
        root / "certificates" / "FR-001.json",
        root / "traces" / "FR-001_success.npz",
        root / "traces" / "FR-001_failure.npz",
        root / "traces" / "FR-001_mitigated.npz",
        root / "maniskill_suite" / "manifest.json",
    ]
    if force_bootstrap or any(not path.exists() for path in required):
        bootstrap(root, force=force_bootstrap)


def _load_application(root: Path) -> InsuranceApplication:
    path = root / "applications" / "APP-APEX-001.json"
    if not path.exists():
        raise FileNotFoundError(f"Missing application JSON: {path}")
    return InsuranceApplication(**read_json(path))


def _load_certificates(root: Path) -> list[FailureCertificate]:
    certificates = [FailureCertificate(**read_json(path)) for path in sorted((root / "certificates").glob("FR-*.json"))]
    if not certificates:
        raise FileNotFoundError(f"No FR-*.json certificates found under {root / 'certificates'}")
    return certificates


def _compute_metrics(root: Path, certificate: FailureCertificate):
    trace_root = root / "traces"
    return compute_internal_metrics(
        certificate,
        load_trace(trace_root / f"{certificate.certificate_id}_success.npz"),
        load_trace(trace_root / f"{certificate.certificate_id}_failure.npz"),
        load_trace(trace_root / f"{certificate.certificate_id}_mitigated.npz"),
    )


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _packet_format_from_manifest_bundle(bundle: bytes) -> str:
    import io
    import zipfile

    with zipfile.ZipFile(io.BytesIO(bundle), mode="r") as archive:
        index = json.loads(archive.read("packet/index.json"))
    return str(index.get("packet_format", "unknown"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Export and verify the TACO data-room ZIP packet.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--force-bootstrap", action="store_true")
    parser.add_argument("--manifest-output", type=Path, default=None)
    parser.add_argument("--memo-output", type=Path, default=None)
    parser.add_argument("--dreamaudit-root", type=Path, default=None)
    parser.add_argument("--dreamaudit-limit", type=int, default=250)
    args = parser.parse_args()
    summary = export_data_room_packet(
        args.output,
        data_root=args.data_root,
        force_bootstrap=args.force_bootstrap,
        manifest_output=args.manifest_output,
        memo_output=args.memo_output,
        dreamaudit_root=args.dreamaudit_root,
        dreamaudit_limit=args.dreamaudit_limit,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if not summary["valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
