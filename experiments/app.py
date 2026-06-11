"""TACO mechanistic audit — web interface.

Submit one policy file, answer a few questions about the deployment, and get a
PASS / CONDITIONAL PASS / FAIL verdict with the failure certificates and the
runtime controls that would make the policy deployable.

    cd experiments && streamlit run app.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from taco_audit.engine import AuditEngine
from taco_audit.policy_loader import load_policy
from taco_audit.proposers import make_proposer
from taco_audit.proposers.cosmos import status as cosmos_status
from taco_audit.report import to_markdown, verdict_to_dict
from taco_audit.scope import CRITICALITY, ENVIRONMENTS, PROXIMITY, gather_scope

import json

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE / "examples" / "policies"
BADGE = {"PASS": ("🟢", "#1a7f37"), "CONDITIONAL PASS": ("🟠", "#b35900"), "FAIL": ("🔴", "#c81e1e")}

st.set_page_config(page_title="TACO — mechanistic audit", page_icon="🛡️", layout="wide")
st.title("TACO — mechanistic policy audit")
st.caption("Submit one robot policy. We stress-test it in simulation until it breaks, "
           "then issue a PASS / CONDITIONAL PASS / FAIL certification.")

# ---- 1. the policy -------------------------------------------------------
left, right = st.columns([1, 1])
with left:
    st.subheader("1 · Policy under audit")
    source = st.radio("Policy source", ["Example policy", "Upload a .py file"], horizontal=True)
    policy_path = None
    if source == "Example policy":
        examples = sorted(p.name for p in EXAMPLES.glob("*.py"))
        choice = st.selectbox("Example", examples, index=examples.index("reach_brittle.py")
                              if "reach_brittle.py" in examples else 0)
        policy_path = EXAMPLES / choice
        st.code((EXAMPLES / choice).read_text()[:1200], language="python")
    else:
        up = st.file_uploader("Policy file (defines a `Policy` class, `policy(obs)`, "
                              "or `build_policy()`)", type=["py"])
        if up is not None:
            tmp = Path(tempfile.gettempdir()) / f"taco_policy_{up.name}"
            tmp.write_bytes(up.getvalue())
            policy_path = tmp
            st.code(up.getvalue().decode("utf-8", "replace")[:1200], language="python")

# ---- 2. the deployment scope --------------------------------------------
with right:
    st.subheader("2 · Where will it run?")
    robot_type = st.text_input("Robot / embodiment", "tabletop manipulation arm")
    task = st.text_input("Task", "pick the instructed object")
    environment = st.selectbox("Environment", ENVIRONMENTS, index=1)
    proximity = st.selectbox("Human proximity", PROXIMITY, index=2)
    criticality = st.selectbox("Failure criticality", CRITICALITY, index=2)
    units = st.number_input("Deployment units", 1, 100000, 1)
    with st.expander("Advanced"):
        proposer_kind = st.selectbox(
            "Perturbation proposer", ["heuristic", "llm", "cosmos"],
            help="heuristic = Monte-Carlo search (no deps); llm = Claude proposes "
                 "(needs ANTHROPIC_API_KEY); cosmos = NVIDIA world model (needs GPU + weights).")
        budget = st.slider("Search budget (rollouts per family)", 12, 120, 40, 4)
        cs = cosmos_status()
        st.caption(f"Cosmos device: {cs.get('device') or 'none'} · diffusers "
                   f"{cs.get('diffusers')} · render-ready: {cs.get('ready')}")

run = st.button("Run audit", type="primary", width="stretch", disabled=policy_path is None)

# ---- 3. run + render -----------------------------------------------------
if run and policy_path is not None:
    scope = gather_scope(policy_id=Path(policy_path).stem, robot_type=robot_type,
                         task_description=task, environment=environment,
                         human_proximity=proximity, criticality=criticality,
                         deployment_units=int(units))
    events: list[str] = []

    def on_event(kind, **kw):
        if kind == "family_search":
            events.append(f"search [{kw['family']}] -> "
                          f"{'broke it' if kw['found'] else 'robust'} "
                          f"(best proximity {kw['best_proximity']})")
        elif kind == "family_done":
            events.append(f"   ↳ minimal cost {kw['minimal_cost']}, nbhd rate "
                          f"{kw['neighborhood_rate']}, monitorable={kw['monitorable']}, "
                          f"patch_verified={kw['verified_patch']}")

    with st.spinner("Falsifying the policy in simulation…"):
        policy = load_policy(policy_path)
        proposer = make_proposer(proposer_kind,
                                 scope_summary=f"{robot_type}, {task}, {environment}")
        engine = AuditEngine(proposer=proposer, search_budget=int(budget), on_event=on_event)
        verdict = engine.audit(policy, scope)
    st.session_state["verdict"] = verdict
    st.session_state["scope"] = scope
    st.session_state["events"] = events

if "verdict" in st.session_state:
    verdict = st.session_state["verdict"]
    scope = st.session_state["scope"]
    icon, color = BADGE.get(verdict.status, ("", "#333"))
    st.markdown("---")
    st.markdown(f"<h2 style='color:{color}'>{icon} {verdict.status}</h2>", unsafe_allow_html=True)
    st.markdown(f"**{verdict.headline}**")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Verdict", verdict.status)
    c2.metric("Failure certificates", len(verdict.certificates))
    c3.metric("Required controls", len(verdict.required_controls))
    c4.metric("Rollouts run", verdict.metadata.get("total_rollouts", "—"))

    for line in verdict.explanation:
        st.write("• " + line)

    if verdict.required_controls:
        st.subheader("Required controls")
        for c in verdict.required_controls:
            st.write(f"- `{c}`")
    if verdict.exclusions:
        st.subheader("Exclusions (until each control is verified)")
        for e in verdict.exclusions:
            st.write(f"- {e}")

    if verdict.certificates:
        st.subheader("Failure certificates")
        st.dataframe([{
            "id": c.certificate_id, "failure_type": c.failure_type, "severity": c.severity,
            "min cost": c.minimal_failure_cost, "nbhd rate": c.failure_rate_neighborhood,
            "monitorable": c.metadata.get("monitorable"),
            "patch verified": c.metadata.get("verified_patch"),
        } for c in verdict.certificates], width="stretch", hide_index=True)

    if verdict.metrics:
        with st.expander("Mechanistic detail (per failure family)"):
            for m in verdict.metrics:
                st.write(f"**{m.get('family')}** — early-warning margin "
                         f"{m.get('early_warning_margin_seconds')}s · internal-risk "
                         f"{m.get('internal_risk_score')} · feature-stability "
                         f"{m.get('feature_stability_score')} · mitigability "
                         f"{m.get('causal_mitigability_score')} · tier {m.get('tier')}"
                         + (" · tolerable residual" if m.get("tolerable") else ""))

    if st.session_state.get("events"):
        with st.expander("Search log"):
            st.code("\n".join(st.session_state["events"]))

    d1, d2 = st.columns(2)
    d1.download_button("Download verdict.json",
                       json.dumps(verdict_to_dict(verdict, scope), indent=2, sort_keys=True),
                       file_name="verdict.json", mime="application/json")
    d2.download_button("Download verdict.md", to_markdown(verdict, scope),
                       file_name="verdict.md", mime="text/markdown")

    st.caption("TACO is a pre-deployment certifier prototype — not insurance or a safety "
               "guarantee. Findings are bounded by the simulator and the search budget.")
