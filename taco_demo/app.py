"""Streamlit UI for TACO - The Autonomous Casualty Office."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from taco_demo.binder import issue_binder
from taco_demo.investor_case import FUNDRAISE_MILESTONES, MOAT_HYPOTHESES, RESEARCH_FOUNDATIONS, UNDERWRITING_WORKFLOW, investor_summary
from taco_demo.maniskill_suite import load_maniskill_suite
from taco_demo.quote_engine import generate_quote, required_control_for_failure, traditional_underwriting_status
from taco_demo.schemas import FailureCertificate, InsuranceApplication, ReplayArtifacts, dataclass_to_dict, default_application, read_json
from taco_demo.scripts.bootstrap_demo_data import bootstrap
from taco_demo.trace_scoring import compute_internal_metrics, load_trace


DATA_ROOT = Path(__file__).resolve().parent / "data"


def _money(value: int | float) -> str:
    return f"${value:,.0f}"


def _load_application() -> InsuranceApplication:
    path = DATA_ROOT / "applications" / "APP-APEX-001.json"
    if path.exists():
        return InsuranceApplication(**read_json(path))
    return default_application()


def _load_certificates() -> list[FailureCertificate]:
    certs = []
    for path in sorted((DATA_ROOT / "certificates").glob("FR-*.json")):
        certs.append(FailureCertificate(**read_json(path)))
    return certs


def _artifacts(certificate_id: str) -> ReplayArtifacts:
    return ReplayArtifacts(
        certificate_id=certificate_id,
        success_video_path=str(DATA_ROOT / "videos" / f"{certificate_id}_success.gif"),
        failure_video_path=str(DATA_ROOT / "videos" / f"{certificate_id}_failure.gif"),
        mitigated_video_path=str(DATA_ROOT / "videos" / f"{certificate_id}_mitigated.gif"),
        success_trace_path=str(DATA_ROOT / "traces" / f"{certificate_id}_success.npz"),
        failure_trace_path=str(DATA_ROOT / "traces" / f"{certificate_id}_failure.npz"),
        mitigated_trace_path=str(DATA_ROOT / "traces" / f"{certificate_id}_mitigated.npz"),
        artifact_source="demo_generated_placeholder_data",
        metadata={},
    )


def _run_audit(application: InsuranceApplication) -> None:
    if not (DATA_ROOT / "certificates").exists() or not list((DATA_ROOT / "certificates").glob("FR-*.json")):
        bootstrap(DATA_ROOT, force=False)
    certs = _load_certificates()
    metrics = {}
    artifacts = {}
    for cert in certs:
        art = _artifacts(cert.certificate_id)
        artifacts[cert.certificate_id] = art
        metrics[cert.certificate_id] = compute_internal_metrics(
            cert,
            load_trace(Path(art.success_trace_path)),
            load_trace(Path(art.failure_trace_path)),
            load_trace(Path(art.mitigated_trace_path)),
        )
    controls = {
        "reaudit_required_after_model_update": True,
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
    }
    st.session_state.audit = {
        "certificates": certs,
        "metrics": metrics,
        "artifacts": artifacts,
        "controls": controls,
        "quote": generate_quote(application, certs, metrics, controls),
    }


def _selected_certificate(certs: list[FailureCertificate], key: str) -> FailureCertificate:
    by_id = {cert.certificate_id: cert for cert in certs}
    selected = st.selectbox("Failure certificate", list(by_id), key=key)
    return by_id[selected]


def _show_gif(path: str | None) -> None:
    if path and Path(path).exists():
        st.image(path)
    else:
        st.info("GIF missing. Click Bootstrap Demo Data.")


def _load_maniskill_manifest() -> dict[str, object]:
    return load_maniskill_suite(DATA_ROOT)


st.set_page_config(page_title="TACO", page_icon="T", layout="wide")

if "application" not in st.session_state:
    st.session_state.application = _load_application()
if "audit" not in st.session_state:
    st.session_state.audit = None

st.title("TACO")
st.subheader("The Autonomous Casualty Office")
st.caption("Liability insurance for robots before the first claim.")
st.markdown("### TACO underwrites robot policies before deployment telemetry exists.")

with st.sidebar:
    st.header("Application")
    app = st.session_state.application
    company_name = st.text_input("Company name", app.company_name)
    robot_type = st.text_input("Robot type", app.robot_type)
    policy_id = st.text_input("Policy ID", app.policy_id)
    deployment_units = st.number_input("Deployment units", min_value=1, value=app.deployment_units, step=10)
    coverage_requested = st.number_input("Coverage requested", min_value=100_000, value=app.coverage_requested_usd, step=100_000)
    telemetry_available = st.checkbox("Telemetry available", value=app.telemetry_available)
    st.session_state.application = InsuranceApplication(
        application_id=app.application_id,
        company_name=company_name,
        robot_type=robot_type,
        policy_id=policy_id,
        deployment_units=int(deployment_units),
        coverage_requested_usd=int(coverage_requested),
        deployment_stage=app.deployment_stage,
        telemetry_available=telemetry_available,
        created_at=app.created_at,
        metadata=app.metadata,
    )
    if st.button("Bootstrap Demo Data", use_container_width=True):
        bootstrap(DATA_ROOT, force=True)
        st.success("Demo data bootstrapped.")
    if st.button("Run Internal Underwriting Audit", type="primary", use_container_width=True):
        _run_audit(st.session_state.application)
        st.success("Internal underwriting audit complete.")
    if st.button("Issue Binder", use_container_width=True):
        if st.session_state.audit:
            audit = st.session_state.audit
            path = issue_binder(
                st.session_state.application,
                audit["certificates"],
                list(audit["metrics"].values()),
                audit["quote"],
                DATA_ROOT / "binders",
            )
            st.session_state.binder_path = str(path)
            st.success(f"Issued {path.name}")
        else:
            st.warning("Run the audit first.")

tabs = st.tabs(
    [
        "Application",
        "Underwriting Audit",
        "Replay Evidence",
        "Internal Signals",
        "Quote",
        "Binder",
        "ManiSkill Suite",
        "Investor Case",
        "Spec",
    ]
)
application = st.session_state.application
audit = st.session_state.audit

with tabs[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Named insured", application.company_name)
    c2.metric("Robot type", application.robot_type)
    c3.metric("Fleet size", f"{application.deployment_units:,}")
    c4.metric("Coverage requested", _money(application.coverage_requested_usd))
    status = traditional_underwriting_status(application)
    if status["status"] == "blocked_no_telemetry":
        st.warning("Traditional underwriting blocked: no deployment telemetry or historical loss data.")
        st.info("TACO can proceed using synthetic actuarial evidence: replayable failures + internal model risk signatures.")
    else:
        st.success(status["explanation"])
    st.json(dataclass_to_dict(application))

with tabs[1]:
    if not audit:
        st.info("Click Run Internal Underwriting Audit to load replayable failure families.")
    else:
        st.success("Internal underwriting complete: 3 replayable failure families found.")
        for item in [
            "Application loaded",
            "Replayable failure certificates loaded",
            "Replay artifacts loaded",
            "Internal traces loaded",
            "Internal risk metrics computed",
            "Quote prepared",
        ]:
            st.checkbox(item, value=True, disabled=True)
        rows = []
        for cert in audit["certificates"]:
            metric = audit["metrics"][cert.certificate_id]
            rows.append(
                {
                    "Certificate ID": cert.certificate_id,
                    "Failure type": cert.failure_type,
                    "Minimal failure cost": cert.minimal_failure_cost,
                    "Neighborhood failure rate": cert.failure_rate_neighborhood,
                    "Dominant risk signature": metric.dominant_risk_signature,
                    "Required control": required_control_for_failure(cert.failure_type),
                    "Internal risk score": round(metric.internal_risk_score, 3),
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
        with st.expander("Research-backed methodology"):
            for foundation in RESEARCH_FOUNDATIONS:
                st.markdown(f"**{foundation['claim']}**")
                st.caption(f"{foundation['source']} - {foundation['evidence']}")
                st.markdown(f"TACO translation: {foundation['taco_translation']} [source]({foundation['url']})")

with tabs[2]:
    if not audit:
        st.info("Run the audit first.")
    else:
        cert = _selected_certificate(audit["certificates"], "replay_cert")
        art = audit["artifacts"][cert.certificate_id]
        cols = st.columns(3)
        with cols[0]:
            st.markdown("**Nominal Success**")
            _show_gif(art.success_video_path)
        with cols[1]:
            st.markdown("**Counterfactual Failure**")
            _show_gif(art.failure_video_path)
        with cols[2]:
            st.markdown("**Mitigated Replay**")
            _show_gif(art.mitigated_video_path)
        st.markdown("#### Certificate Card")
        st.json(
            {
                "policy": cert.policy_id,
                "task": cert.task_id,
                "failure_type": cert.failure_type,
                "severity": cert.severity,
                "minimal_failure_cost": cert.minimal_failure_cost,
                "failure_timestep": cert.failure_timestep,
                "failure_neighborhood_rate": cert.failure_rate_neighborhood,
                "perturbation": cert.perturbation,
                "patch_recipe": cert.patch_recipe,
            }
        )

with tabs[3]:
    if not audit:
        st.info("Run the audit first.")
    else:
        cert = _selected_certificate(audit["certificates"], "signals_cert")
        trace = load_trace(DATA_ROOT / "traces" / f"{cert.certificate_id}_failure.npz")
        risk_signal = {
            "FR-001": "occlusion_risk",
            "FR-002": "language_override_risk",
            "FR-003": "distractor_risk",
        }.get(cert.certificate_id, "internal_risk_score")
        keys = [
            "target_feature",
            "general_grasp_feature",
            "transport_feature",
            "memorized_trajectory_feature",
            "unsafe_trajectory_dominance",
            "internal_risk_score",
            "action_risk",
            risk_signal,
        ]
        fig = go.Figure()
        for key in dict.fromkeys(keys):
            fig.add_trace(go.Scatter(x=trace["time_s"], y=trace[key], name=key))
        failure_x = trace["time_s"][min(cert.failure_timestep, len(trace["time_s"]) - 1)]
        fig.add_vline(x=float(failure_x), line_dash="dash", line_color="#b91c1c", annotation_text="failure")
        crossings = [i for i, value in enumerate(trace["internal_risk_score"][: cert.failure_timestep]) if value > 0.65]
        if crossings:
            fig.add_vline(x=float(trace["time_s"][crossings[0]]), line_dash="dot", line_color="#166534", annotation_text="risk crossing")
        fig.update_layout(height=500, yaxis_range=[0, 1], title="Internal Risk Signature")
        st.plotly_chart(fig, use_container_width=True)
        metric = audit["metrics"][cert.certificate_id]
        cols = st.columns(6)
        cols[0].metric("Concept Coverage", f"{metric.concept_coverage_score:.2f}")
        cols[1].metric("Feature Stability", f"{metric.feature_stability_score:.2f}")
        cols[2].metric("Unsafe Dominance", f"{metric.unsafe_dominance_score:.2f}")
        cols[3].metric("Early Warning Margin", f"{metric.early_warning_margin_seconds:.2f}s")
        cols[4].metric("Causal Mitigability", f"{metric.causal_mitigability_score:.2f}")
        cols[5].metric("Internal Risk Score", f"{metric.internal_risk_score:.2f}")
        explanations = {
            "FR-001": "The robot does not merely miss the object. Under occlusion, the target-object feature collapses while unsafe trajectory dominance rises before the wrong grasp. The risk signature appears early enough for a runtime monitor.",
            "FR-002": "The visual state remains stable, but the language override risk feature dominates action selection. The instruction sanitizer is required for coverage.",
            "FR-003": "The distractor feature competes with the target identity representation, creating a semantic confusion failure family.",
        }
        st.info(explanations.get(cert.certificate_id, "Internal risk signature detected before physical failure."))

with tabs[4]:
    if not audit:
        st.info("Without telemetry: unpriceable by traditional underwriting.")
    else:
        st.caption("Without telemetry: unpriceable by traditional underwriting.")
        controls = {
            "occlusion_risk_monitor_enabled": st.toggle("Enable occlusion-risk monitor", True),
            "language_override_sanitizer_enabled": st.toggle("Enable language override sanitizer", True),
            "target_identity_confirmation_enabled": st.toggle("Enable target identity confirmation", True),
            "reaudit_required_after_model_update": st.toggle("Reaudit after model update", True),
        }
        quote = generate_quote(application, audit["certificates"], audit["metrics"], controls)
        audit["quote"] = quote
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Final monthly premium", _money(quote.final_monthly_premium_usd))
        c2.metric("Known failure families", len(audit["certificates"]))
        c3.metric("Earliest internal warning", f"{max(m.early_warning_margin_seconds for m in audit['metrics'].values()):.2f}s")
        c4.metric("Mitigation discount", f"{(1 - quote.mitigation_discount_multiplier) * 100:.0f}%")
        st.markdown(f"**Status:** {quote.status.replace('_', ' ').title()}")
        st.markdown(f"**Coverage limit:** {_money(quote.coverage_limit_usd)}")
        st.markdown("**Required controls**")
        st.write(quote.required_controls)
        st.markdown("**Exclusions**")
        st.write(quote.exclusions or ["None while required controls remain enabled"])
        with st.expander("Underwriter workflow explanation"):
            workflow_rows = [
                {
                    "Step": item["step"],
                    "Operator": item["operator"],
                    "Artifact": item["artifact"],
                    "Investor point": item["investor_point"],
                }
                for item in UNDERWRITING_WORKFLOW
            ]
            st.dataframe(pd.DataFrame(workflow_rows), use_container_width=True)
        st.json(dataclass_to_dict(quote))

with tabs[5]:
    if not audit:
        st.info("Run the audit before issuing a binder.")
    else:
        if st.button("Issue Conditional Binder", type="primary"):
            path = issue_binder(application, audit["certificates"], list(audit["metrics"].values()), audit["quote"], DATA_ROOT / "binders")
            st.session_state.binder_path = str(path)
        binder_path = Path(st.session_state.get("binder_path", DATA_ROOT / "binders" / f"TACO-BINDER-{application.application_id}.json"))
        st.markdown("### TACO Conditional Learned-Policy Liability Binder")
        st.write(f"Named Insured: **{application.company_name}**")
        st.write(f"Coverage limit: **{_money(audit['quote'].coverage_limit_usd)}**")
        st.write(f"Monthly premium: **{_money(audit['quote'].final_monthly_premium_usd)}**")
        st.write("Coverage is conditioned on required controls, exclusions, and re-audit triggers.")
        if binder_path.exists():
            st.json(read_json(binder_path))
            st.download_button("Download JSON Binder", binder_path.read_bytes(), file_name=binder_path.name)
            markdown_path = binder_path.with_suffix(".md")
            if markdown_path.exists():
                st.download_button("Download Markdown Binder", markdown_path.read_bytes(), file_name=markdown_path.name)

with tabs[6]:
    manifest = _load_maniskill_manifest()
    cases = list(manifest["cases"])
    st.markdown("### ManiSkill/RMA Failure Evidence Suite")
    st.caption("Forty supplemental replays showing how TACO turns varied simulator failures into underwriting signals and required controls.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Replay videos", manifest["suite_size"])
    c2.metric("Failure families", len({case["failure_family"] for case in cases}))
    c3.metric("ManiSkill envs", len({case["env_id"] for case in cases}))
    c4.metric("Cluster status", "reproducible")
    rows = [
        {
            "Video": case["video_id"],
            "Env": case["env_id"],
            "Task": case["task"],
            "Failure": case["failure_family"],
            "Identified signal": case["identified_signal"],
            "Required control": case["required_control"],
            "Severity": case["severity"],
        }
        for case in cases
    ]
    st.dataframe(pd.DataFrame(rows), use_container_width=True)
    selected_id = st.selectbox("Evidence replay", [case["video_id"] for case in cases], key="maniskill_suite_case")
    selected = next(case for case in cases if case["video_id"] == selected_id)
    cols = st.columns([1, 1])
    with cols[0]:
        st.image(DATA_ROOT / "maniskill_suite" / "videos" / str(selected["video_path"]))
    with cols[1]:
        st.markdown("**What TACO identifies**")
        st.write(selected["identified_signal"])
        st.markdown("**Underwriting interpretation**")
        st.write(selected["underwriting_readout"])
        st.markdown("**Required control**")
        st.write(selected["required_control"])
        st.json(selected)

with tabs[7]:
    st.markdown("### Investor Case")
    st.caption("Why this could plausibly support a venture-scale seed story if the fallback evidence is replaced with real DreamAudit and VLA traces.")
    if audit:
        summary = investor_summary(application, audit["certificates"], list(audit["metrics"].values()), audit["quote"])
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Wedge customer", summary["wedge_customer"])
        c2.metric("Evidence objects", len(audit["certificates"]))
        c3.metric("Aggregate internal risk", f"{summary['aggregate_internal_risk']:.2f}")
        c4.metric("Conditional premium", _money(audit["quote"].final_monthly_premium_usd))
        st.markdown(f"**Fundraise thesis:** {summary['fundraise_thesis']}")
        st.markdown("**Proof points**")
        st.write(summary["proof_points"])
        st.markdown("**Methodology spine**")
        st.write(summary["research_backed_method"])
        st.markdown("**Known investor risks**")
        st.write(summary["investor_risk"])
    else:
        st.info("Run the audit to populate the investor proof-point metrics.")

    st.markdown("#### Why This Can Be A Venture-Scale Evidence Layer")
    st.write(
        "TACO is not trying to be a generic robotics dashboard. The wedge is a structured evidence layer for brokers, carriers, "
        "robotics OEMs, and enterprise buyers who need to decide whether learned robot policies are deployable before claims history exists."
    )
    cols = st.columns(2)
    with cols[0]:
        st.markdown("**Moat hypotheses**")
        for item in MOAT_HYPOTHESES:
            st.markdown(f"* {item}")
    with cols[1]:
        st.markdown("**Seed-stage derisking milestones**")
        for item in FUNDRAISE_MILESTONES:
            st.markdown(f"* {item}")

    st.markdown("#### Research Anchors")
    for foundation in RESEARCH_FOUNDATIONS:
        st.markdown(f"* **{foundation['source']}**: {foundation['taco_translation']} [link]({foundation['url']})")

with tabs[8]:
    readme = Path(__file__).with_name("README.md")
    if readme.exists():
        st.markdown(readme.read_text(encoding="utf-8"))
    else:
        st.markdown("TACO is a local MVP for learned-policy liability underwriting from replayable failures and internal risk signatures.")
