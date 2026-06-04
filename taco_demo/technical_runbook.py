"""Technical diligence runbook for reproducing TACO evidence artifacts."""

from __future__ import annotations

from typing import Any

from .schemas import InsuranceApplication, QuoteBreakdown


def build_technical_diligence_runbook(
    application: InsuranceApplication,
    quote: QuoteBreakdown,
    suite_manifest: dict[str, Any],
    dreamaudit_summary: dict[str, Any],
    security_plan: dict[str, Any],
) -> dict[str, Any]:
    """Return a reviewer-facing runbook for local and live-evidence verification."""

    suite_size = int(suite_manifest.get("suite_size", len(suite_manifest.get("cases", []))) or 0)
    return {
        "runbook_id": f"TECH-{application.application_id}",
        "status": "local_reproducibility_defined_live_evidence_optional",
        "boundary": "This runbook proves local reproducibility and integration paths; it is not proof of live customer deployment, signed external validation, production security controls, or actuarial approval.",
        "target_customer_context": {
            "company_name": application.company_name,
            "policy_id": application.policy_id,
            "conditional_monthly_premium_usd": quote.final_monthly_premium_usd,
            "required_controls": list(quote.required_controls),
        },
        "reviewer_prerequisites": [
            "macOS or Linux shell with Python 3.14-compatible virtualenv support.",
            "Repository cloned from https://github.com/J0YY/taco.git on main.",
            "Local .venv installed from taco_demo/requirements-taco.txt.",
            "Optional DreamAudit artifact directory for live certificate intake.",
            "Optional torch runtime and robot policy model for activation recording.",
        ],
        "local_repro_steps": [
            _step(
                "sync_main",
                "Confirm the reviewer is on pushed main.",
                "git pull --ff-only origin main && git rev-parse HEAD",
                "Command exits 0 and printed HEAD matches origin/main.",
                ["README.md", "bitacora.md"],
            ),
            _step(
                "install_dependencies",
                "Create or refresh the local test environment.",
                "python3 -m venv .venv && .venv/bin/python -m pip install --upgrade pip && .venv/bin/python -m pip install -r taco_demo/requirements-taco.txt",
                "Dependencies install without writing .venv into Git.",
                ["taco_demo/requirements-taco.txt"],
            ),
            _step(
                "bootstrap_fixture_evidence",
                "Regenerate local applications, certificates, traces, videos, and binders.",
                ".venv/bin/python -m taco_demo.scripts.bootstrap_demo_data --force",
                "Command exits 0 and fixture outputs remain reproducible for local regression tests.",
                ["taco_demo/data/applications/APP-APEX-001.json", "taco_demo/data/certificates/FR-001.json"],
            ),
            _step(
                "run_full_test_suite",
                "Verify all local schemas, quote logic, adapters, packet verifier, security artifacts, and UI imports covered by tests.",
                ".venv/bin/python -m pytest taco_demo/tests",
                "All tests pass.",
                ["taco_demo/tests"],
            ),
            _step(
                "import_streamlit_app",
                "Verify the Streamlit app imports in bare mode.",
                ".venv/bin/python -c \"import taco_demo.app\"",
                "Command exits 0; Streamlit bare-mode warnings are expected.",
                ["taco_demo/app.py"],
            ),
            _step(
                "launch_local_app",
                "Run the investor/demo workflow locally.",
                ".venv/bin/python -m streamlit run taco_demo/app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true",
                "App serves http://127.0.0.1:8501 and shows Investor Case plus DreamAudit Intake tabs.",
                ["taco_demo/app.py"],
            ),
            _step(
                "verify_data_room_packet",
                "Download or build a data-room ZIP and verify packet/index.json checksums.",
                "Use the Investor Case tab's Data Room Packet download, then upload it under Verify Transferred Data Room Packet.",
                "Verifier reports valid, indexed file count, and SHA-256 fingerprint.",
                ["packet/index.json", "commercial/enterprise_security_plan.json"],
            ),
        ],
        "live_evidence_steps": [
            _step(
                "dreamaudit_certificate_intake",
                "Scan real DreamAudit artifacts and attach readiness ladder to investor gates.",
                "Use the DreamAudit Intake tab with /Users/joyyang/Projects/dreamaudit/artifacts or run adapt_dreamaudit_certificates(path, limit=250).",
                "Summary reports adapted certificates, failure families, source paths, minimality coverage, and readiness gaps.",
                ["taco_demo/dreamaudit_adapter.py", "taco_demo/dreamaudit_intake.py"],
            ),
            _step(
                "activation_recorder_trace_export",
                "Record torch forward-hook activations for a real policy rollout bundle.",
                "Use ActivationRecorder or record_taco_trace_bundle with explicit layer_names and signal_map.",
                "NPZ traces contain calibrated signal arrays that feed compute_internal_metrics.",
                ["taco_demo/activation_recorder.py", "taco_demo/trace_scoring.py"],
            ),
            _step(
                "maniskill_cluster_suite",
                "Rebuild the 40-video ManiSkill/RMA-style evidence suite locally or on cluster.",
                ".venv/bin/python -m taco_demo.scripts.generate_maniskill_video_suite --force",
                f"Manifest reports at least {max(40, suite_size)} replay cases and generated video files.",
                ["taco_demo/maniskill_suite.py", "taco_demo/data/maniskill_suite/manifest.json"],
            ),
        ],
        "pass_fail_gates": [
            {
                "gate": "local_tests_green",
                "pass_condition": "Full pytest suite exits 0.",
                "fail_condition": "Any schema, packet, adapter, quote, or UI import test fails.",
            },
            {
                "gate": "packet_verifier_valid",
                "pass_condition": "verify_data_room_bundle returns valid true and packet SHA-256 is shown.",
                "fail_condition": "Missing required files, unsafe ZIP paths, checksum mismatches, or unsupported packet format.",
            },
            {
                "gate": "not_fixture_only_for_live_claims",
                "pass_condition": "Any claim of live evidence points to DreamAudit source paths or recorded activation traces.",
                "fail_condition": "Demo fixtures are presented as production customer deployment evidence.",
            },
            {
                "gate": "security_boundaries_visible",
                "pass_condition": "Enterprise security plan boundary states no SOC 2, pen test, customer approval, or production attestation is claimed.",
                "fail_condition": "Reviewer is asked to accept local packet verification as production security certification.",
            },
        ],
        "expected_current_counts": {
            "maniskill_suite_size": suite_size,
            "dreamaudit_attached": bool(dreamaudit_summary.get("attached")),
            "security_control_backlog": len(security_plan.get("control_backlog", [])),
        },
        "source_material": [
            "README.md",
            "bitacora.md",
            "taco_demo/tests",
            "taco_demo/data_room.py",
            "taco_demo/dreamaudit_adapter.py",
            "taco_demo/activation_recorder.py",
            "taco_demo/maniskill_suite.py",
        ],
        "open_reproducibility_risks": [
            "Local replay GIFs and traces are test fixtures unless replaced with DreamAudit and recorded activation evidence.",
            "Cluster video generation depends on the cluster environment and repository checkout state.",
            "Torch activation recording requires a real model runtime and calibrated layer-to-signal mapping.",
            "Passing local tests does not prove production security controls, insurance capacity, or actuarial approval.",
        ],
    }


def technical_step_rows(runbook: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly reproducibility step rows."""

    rows = []
    for group_name in ["local_repro_steps", "live_evidence_steps"]:
        for item in runbook[group_name]:
            rows.append(
                {
                    "Group": group_name,
                    "Step": item["step_id"],
                    "Purpose": item["purpose"],
                    "Command": item["command"],
                    "Expected Result": item["expected_result"],
                    "Artifacts": "; ".join(item["artifacts"]),
                }
            )
    return rows


def technical_gate_rows(runbook: dict[str, Any]) -> list[dict[str, str]]:
    """Return Streamlit-friendly technical pass/fail gates."""

    return [
        {
            "Gate": item["gate"],
            "Pass Condition": item["pass_condition"],
            "Fail Condition": item["fail_condition"],
        }
        for item in runbook["pass_fail_gates"]
    ]


def _step(
    step_id: str,
    purpose: str,
    command: str,
    expected_result: str,
    artifacts: list[str],
) -> dict[str, Any]:
    return {
        "step_id": step_id,
        "purpose": purpose,
        "command": command,
        "expected_result": expected_result,
        "artifacts": artifacts,
    }
