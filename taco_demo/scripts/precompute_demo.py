"""Precompute TACO metrics, quote, and binder."""

from __future__ import annotations

from taco_demo.config import data_root, ensure_data_dirs
from taco_demo.dreamaudit_adapter import DreamAuditAdapter
from taco_demo.feature_scoring import compute_internal_metrics, load_trace
from taco_demo.policy_issuer import issue_policy_bundle
from taco_demo.quote_engine import generate_quote
from taco_demo.schemas import InsuranceApplication, read_json


def main() -> None:
    root = ensure_data_dirs(data_root())
    app = InsuranceApplication(**read_json(root / "applications" / "APP-APEX-001.json"))
    adapter = DreamAuditAdapter(data_root=root)
    certs = adapter.load_certificates(root / "dreamaudit_certs")
    artifacts = {cert.certificate_id: adapter.get_replay_artifacts(cert.certificate_id) for cert in certs}
    metrics = {}
    for cert in certs:
        art = artifacts[cert.certificate_id]
        metrics[cert.certificate_id] = compute_internal_metrics(
            cert,
            load_trace(root / "traces" / f"{cert.certificate_id}_success.npz"),
            load_trace(root / "traces" / f"{cert.certificate_id}_failure.npz"),
            load_trace(root / "traces" / f"{cert.certificate_id}_mitigated.npz"),
        )
    controls = {
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
    }
    quote = generate_quote(app, certs, metrics, monitor_enabled=True, controls_enabled=controls)
    out = issue_policy_bundle(app, certs, metrics, quote, artifacts, root / "quotes")
    print(f"Issued JSON binder: {out}")
    print(f"Issued markdown binder: {out.with_suffix('.md')}")


if __name__ == "__main__":
    main()

