"""Streamlit app for TACO - The Autonomous Casualty Office."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from taco_demo.config import data_root, ensure_data_dirs
from taco_demo.dreamaudit_adapter import DreamAuditAdapter
from taco_demo.feature_scoring import compute_internal_metrics, load_trace
from taco_demo.maniskill_gallery import build_maniskill_gallery
from taco_demo.policy_issuer import issue_policy_bundle
from taco_demo.quote_engine import generate_quote, required_control_for_failure, traditional_underwriting_status
from taco_demo.schemas import InsuranceApplication, dataclass_to_dict, default_application, read_json, write_json
from taco_demo.scripts.bootstrap_demo_data import bootstrap


st.set_page_config(page_title="TACO", page_icon="T", layout="wide")


def load_application(root: Path) -> InsuranceApplication:
    path = root / "applications" / "APP-APEX-001.json"
    if path.exists():
        return InsuranceApplication(**read_json(path))
    return default_application()


def save_application(root: Path, app: InsuranceApplication) -> None:
    write_json(app, root / "applications" / f"{app.application_id}.json")


def run_audit(root: Path, app: InsuranceApplication):
    adapter = DreamAuditAdapter(data_root=root)
    certs = adapter.load_certificates(root / "dreamaudit_certs")
    if not certs:
        bootstrap(root, force=False)
        certs = adapter.load_certificates(root / "dreamaudit_certs")
    artifacts = {cert.certificate_id: adapter.get_replay_artifacts(cert.certificate_id) for cert in certs}
    metrics = {}
    for cert in certs:
        try:
            metrics[cert.certificate_id] = compute_internal_metrics(
                cert,
                load_trace(root / "traces" / f"{cert.certificate_id}_success.npz"),
                load_trace(root / "traces" / f"{cert.certificate_id}_failure.npz"),
                load_trace(root / "traces" / f"{cert.certificate_id}_mitigated.npz"),
            )
        except Exception:
            continue
    controls = {
        "occlusion_risk_monitor_enabled": True,
        "language_override_sanitizer_enabled": True,
        "target_identity_confirmation_enabled": True,
    }
    quote = generate_quote(app, certs, metrics, monitor_enabled=True, controls_enabled=controls)
    st.session_state.audit = {"certs": certs, "artifacts": artifacts, "metrics": metrics, "quote": quote}


def money(value: int | float) -> str:
    return f"${value:,.0f}"


def show_video(path: str | None):
    if not path:
        st.info("Replay media missing. Run `python -m taco_demo.scripts.bootstrap_demo_data --force`.")
        return
    if path.endswith(".gif"):
        st.image(path)
    else:
        st.video(path)


def selected_cert(certs):
    ids = [cert.certificate_id for cert in certs]
    chosen = st.selectbox("Known Failure Family", ids)
    return next(cert for cert in certs if cert.certificate_id == chosen)


root = ensure_data_dirs(data_root())
if "application" not in st.session_state:
    st.session_state.application = load_application(root)
if "audit" not in st.session_state:
    st.session_state.audit = None

st.title("TACO")
st.subheader("The Autonomous Casualty Office")
st.caption("Liability insurance for robots before the first claim.")

app = st.session_state.application
with st.sidebar:
    st.header("Application")
    company_name = st.text_input("Company name", app.company_name)
    robot_type = st.text_input("Robot type", app.robot_type)
    policy_id = st.text_input("Policy ID", app.policy_id)
    deployment_units = st.number_input("Deployment units", min_value=1, value=int(app.deployment_units), step=10)
    coverage_requested = st.number_input("Coverage requested", min_value=100000, value=int(app.coverage_requested_usd), step=100000)
    deployment_stage = st.text_input("Deployment stage", app.deployment_stage)
    telemetry_available = st.checkbox("Telemetry available", value=bool(app.telemetry_available))
    st.session_state.application = InsuranceApplication(
        application_id=app.application_id,
        company_name=company_name,
        robot_type=robot_type,
        policy_id=policy_id,
        deployment_units=int(deployment_units),
        coverage_requested_usd=int(coverage_requested),
        deployment_stage=deployment_stage,
        telemetry_available=telemetry_available,
        created_at=app.created_at,
        metadata=app.metadata,
    )
    if st.button("Save Application", use_container_width=True):
        save_application(root, st.session_state.application)
        st.success("Application saved.")
    if st.button("Bootstrap Demo Data", use_container_width=True):
        bootstrap(root, force=True)
        st.success("Demo data bootstrapped.")
    if st.button("Run Internal Underwriting Audit", type="primary", use_container_width=True):
        run_audit(root, st.session_state.application)
        st.success("Internal underwriting complete.")
    if st.button("Issue Binder", use_container_width=True):
        if st.session_state.audit:
            audit = st.session_state.audit
            out = issue_policy_bundle(st.session_state.application, audit["certs"], audit["metrics"], audit["quote"], audit["artifacts"], root / "quotes")
            st.success(f"Issued {out.name}")
        else:
            st.warning("Run the audit first.")

tabs = st.tabs(["Application", "Underwriting Audit", "Replay Evidence", "Internal Signals", "Quote", "Binder / Certificate", "Spec / README"])

with tabs[0]:
    st.markdown("### TACO underwrites robot policies before deployment telemetry exists.")
    current = st.session_state.application
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Named insured", current.company_name)
    c2.metric("Fleet units", f"{current.deployment_units:,}")
    c3.metric("Coverage", money(current.coverage_requested_usd))
    c4.metric("Telemetry", "Available" if current.telemetry_available else "None")
    status = traditional_underwriting_status(current)
    if status["status"] == "blocked_no_telemetry":
        st.warning("Traditional underwriting blocked: no deployment telemetry or historical loss data.")
        st.info("TACO can underwrite from synthetic actuarial evidence: DreamAudit failures + internal model risk signatures.")
    else:
        st.success(status["explanation"])
    st.json(dataclass_to_dict(current))

audit = st.session_state.audit
with tabs[1]:
    if not audit:
        st.info("Run Internal Underwriting Audit to load known failure families.")
    else:
        certs = audit["certs"]
        metrics = audit["metrics"]
        st.success(f"Internal underwriting complete: {len(certs)} replayable failure families found.")
        steps = ["Load policy/application", "Load DreamAudit certificates", "Load replay artifacts", "Load activation traces", "Compute internal risk metrics", "Calculate quote", "Prepare binder"]
        for step in steps:
            st.checkbox(step, value=True, disabled=True)
        rows = []
        for cert in certs:
            metric = metrics.get(cert.certificate_id)
            rows.append(
                {
                    "Certificate ID": cert.certificate_id,
                    "Failure type": cert.failure_type,
                    "Minimal cost": cert.minimal_failure_cost,
                    "Failure rate neighborhood": cert.failure_rate_neighborhood,
                    "Dominant internal risk signature": metric.dominant_risk_signature if metric else "missing trace",
                    "Required control": required_control_for_failure(cert.failure_type),
                    "Premium impact estimate": "high" if cert.minimal_failure_cost < 0.35 else "medium",
                }
            )
        st.dataframe(pd.DataFrame(rows), use_container_width=True)

with tabs[2]:
    if not audit:
        st.info("Run the audit first.")
    else:
        cert = selected_cert(audit["certs"])
        art = audit["artifacts"][cert.certificate_id]
        cols = st.columns(3)
        with cols[0]:
            st.markdown("**Nominal success**")
            show_video(art.success_video_path)
        with cols[1]:
            st.markdown("**Counterfactual failure**")
            show_video(art.failure_video_path)
        with cols[2]:
            st.markdown("**Mitigated replay**")
            show_video(art.mitigated_video_path)
        st.code(cert.replay_command or "No replay command supplied by certificate.")
        st.json({"perturbation": cert.perturbation, "patch_recipe": cert.patch_recipe})
        st.json(
            {
                "minimal_failure_cost": cert.minimal_failure_cost,
                "failure_timestep": cert.failure_timestep,
                "failure_rate_neighborhood": cert.failure_rate_neighborhood,
                "severity": cert.severity,
            }
        )
        st.markdown("### ManiSkill/RMA Pipeline Examples")
        manifest = root / "maniskill_gallery.json"
        if not manifest.exists():
            build_maniskill_gallery(root, Path("/Users/joyyang/Projects/dreamaudit"), force=False)
        if manifest.exists():
            gallery = read_json(manifest).get("examples", [])
            options = {f"{item['example_id']} - {item['failure_family']}": item for item in gallery}
            chosen = st.selectbox("ManiSkill example", list(options), key="maniskill_gallery_select")
            item = options[chosen]
            left, right = st.columns([1.2, 1])
            with left:
                show_video(str(root / item["video_path"]))
            with right:
                st.json(item)

with tabs[3]:
    if not audit:
        st.info("Run the audit first.")
    else:
        cert = selected_cert(audit["certs"])
        trace_path = root / "traces" / f"{cert.certificate_id}_failure.npz"
        if not trace_path.exists():
            st.info("Trace missing. Bootstrap demo data to generate fallback NPZ traces.")
        else:
            trace = load_trace(trace_path)
            fig = go.Figure()
            for key in ["target_feature", "occlusion_risk", "language_override_risk", "unsafe_trajectory_dominance", "internal_risk_score", "action_risk"]:
                fig.add_trace(go.Scatter(x=trace["time_s"], y=trace[key], name=key))
            failure_x = trace["time_s"][min(cert.failure_timestep, len(trace["time_s"]) - 1)]
            fig.add_vline(x=float(failure_x), line_dash="dash", line_color="red")
            fig.update_layout(height=500, yaxis_range=[0, 1], title="Internal Risk Signature Curves")
            st.plotly_chart(fig, use_container_width=True)
            metric = audit["metrics"][cert.certificate_id]
            cards = st.columns(6)
            cards[0].metric("Concept Coverage", f"{metric.concept_coverage_score:.2f}")
            cards[1].metric("Feature Stability", f"{metric.feature_stability_score:.2f}")
            cards[2].metric("Unsafe Dominance", f"{metric.unsafe_dominance_score:.2f}")
            cards[3].metric("Early Warning", f"{metric.early_warning_margin_seconds:.2f}s")
            cards[4].metric("Mitigability", f"{metric.causal_mitigability_score:.2f}")
            cards[5].metric("Internal Risk", f"{metric.internal_risk_score:.2f}")
            copy = {
                "FR-001": "The robot does not merely miss the object. Under occlusion, the target-object feature collapses while unsafe trajectory dominance rises before the wrong grasp. The risk signature appears early enough for a runtime monitor to intervene.",
                "FR-002": "The visual state remains stable, but the language override risk feature dominates action selection. The instruction sanitizer is therefore required for coverage.",
                "FR-003": "The distractor feature competes with the target identity representation, creating a known semantic confusion family.",
            }
            st.info(copy.get(cert.certificate_id, "Risk signature detected before physical failure."))

with tabs[4]:
    if not audit:
        st.info("Without telemetry: unpriceable by traditional underwriting. Run the audit to generate a TACO quote.")
    else:
        st.markdown("### Conditionally approved with required internal-risk controls.")
        st.caption("Without telemetry: unpriceable by traditional underwriting.")
        controls = {
            "occlusion_risk_monitor_enabled": st.toggle("Enable occlusion-risk monitor", True),
            "language_override_sanitizer_enabled": st.toggle("Enable language override sanitizer", True),
            "target_identity_confirmation_enabled": st.toggle("Enable target identity confirmation", True),
            "reaudit_required_after_model_update": st.toggle("Reaudit after model update", True),
        }
        quote = generate_quote(st.session_state.application, audit["certs"], audit["metrics"], all(controls.values()), controls)
        enabled_quote = generate_quote(st.session_state.application, audit["certs"], audit["metrics"], True, {k: True for k in controls})
        savings = max(0, quote.final_monthly_premium_usd - enabled_quote.final_monthly_premium_usd)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Final monthly premium", money(quote.final_monthly_premium_usd))
        c2.metric("Savings from required monitors", money(savings))
        c3.metric("Known failure families", len(audit["certs"]))
        c4.metric("Earliest internal warning", f"{max(m.early_warning_margin_seconds for m in audit['metrics'].values()):.2f}s")
        st.json(dataclass_to_dict(quote))
        audit["quote"] = quote

with tabs[5]:
    if not audit:
        st.info("Run the audit before issuing a binder.")
    else:
        if st.button("Issue Conditional Binder", type="primary"):
            out = issue_policy_bundle(st.session_state.application, audit["certs"], audit["metrics"], audit["quote"], audit["artifacts"], root / "quotes")
            st.session_state.binder_path = str(out)
        out = Path(st.session_state.get("binder_path", root / "quotes" / f"TACO-BINDER-{st.session_state.application.application_id}.json"))
        st.markdown("### TACO Conditional Learned-Policy Liability Binder")
        st.write(f"Named Insured: **{st.session_state.application.company_name}**")
        st.write(f"Coverage limit: **{money(st.session_state.application.coverage_requested_usd)}**")
        st.write(f"Premium: **{money(audit['quote'].final_monthly_premium_usd)} / month**")
        st.write("This binder is conditioned on monitor compliance and re-audit after model updates.")
        if out.exists():
            st.json(read_json(out))
            st.download_button("Download JSON binder", out.read_bytes(), file_name=out.name)
            md = out.with_suffix(".md")
            if md.exists():
                st.download_button("Download markdown binder", md.read_bytes(), file_name=md.name)

with tabs[6]:
    readme = Path(__file__).with_name("README.md")
    st.markdown(readme.read_text(encoding="utf-8") if readme.exists() else "README missing.")
