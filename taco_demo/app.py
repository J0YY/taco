"""TACO — pre-deployment certification for learned robot policies.

A single guided flow: pick an analyzed policy, watch a minimal perturbation cause
a real failure, see what we found in the model internals, and get a certification
tier with the recommended patch. (TACO certifies robotics labs pre-deployment.)
"""

from __future__ import annotations

import streamlit as st

from taco_demo.guided_flow import render_guided_flow

st.set_page_config(page_title="TACO", page_icon="T", layout="wide")

st.title("TACO — The Autonomous Casualty Office")
st.caption("Pre-deployment certification for learned robot policies: "
           "stress-test → mechanistic finding → patch → certification tier.")

render_guided_flow()
