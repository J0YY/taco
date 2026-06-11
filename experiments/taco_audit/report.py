"""Render an audit Verdict to JSON + Markdown."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .types import AuditScope, Verdict

_BADGE = {"PASS": "🟢 PASS", "CONDITIONAL PASS": "🟠 CONDITIONAL PASS", "FAIL": "🔴 FAIL"}


def verdict_to_dict(verdict: Verdict, scope: AuditScope) -> dict[str, Any]:
    return {
        "status": verdict.status,
        "headline": verdict.headline,
        "scope": asdict(scope),
        "required_controls": verdict.required_controls,
        "exclusions": verdict.exclusions,
        "explanation": verdict.explanation,
        "certificates": [asdict(c) for c in verdict.certificates],
        "metrics": verdict.metrics,
        "metadata": verdict.metadata,
    }


def to_markdown(verdict: Verdict, scope: AuditScope) -> str:
    L = []
    L.append("# TACO mechanistic audit — verdict\n")
    L.append(f"## {_BADGE.get(verdict.status, verdict.status)}\n")
    L.append(f"**{verdict.headline}**\n")
    L.append(f"- Policy: `{scope.policy_id}`")
    L.append(f"- Robot / task: {scope.robot_type} — {scope.task_description}")
    L.append(f"- Context: {scope.environment} · {scope.human_proximity} · "
             f"criticality {scope.criticality} · {scope.deployment_units} unit(s)")
    L.append(f"- Engine: {verdict.metadata.get('sim','?')} sim · "
             f"{verdict.metadata.get('proposer','?')} proposer · "
             f"{verdict.metadata.get('total_rollouts','?')} rollouts\n")

    L.append("### Why\n")
    for line in verdict.explanation:
        L.append(f"- {line}")
    L.append("")

    if verdict.required_controls:
        L.append("### Required controls\n")
        for c in verdict.required_controls:
            L.append(f"- `{c}`")
        L.append("")
    if verdict.exclusions:
        L.append("### Exclusions (apply until each control is verified)\n")
        for e in verdict.exclusions:
            L.append(f"- {e}")
        L.append("")

    if verdict.certificates:
        L.append("### Failure certificates\n")
        L.append("| ID | family | type | severity | min cost | nbhd rate | monitorable | patch verified |")
        L.append("|---|---|---|---|---|---|---|---|")
        for c in verdict.certificates:
            md = c.metadata
            L.append(f"| {c.certificate_id} | {c.metadata.get('dominant_risk_signature','')[:24]} "
                     f"| {c.failure_type} | {c.severity} | {c.minimal_failure_cost:.3f} "
                     f"| {c.failure_rate_neighborhood:.3f} | {md.get('monitorable')} "
                     f"| {md.get('verified_patch')} |")
        L.append("")

    if verdict.metrics:
        L.append("### Mechanistic detail (per family)\n")
        for m in verdict.metrics:
            L.append(f"- **{m.get('family')}** — early-warning margin "
                     f"{m.get('early_warning_margin_seconds','?')}s, internal-risk "
                     f"{m.get('internal_risk_score','?')}, feature-stability "
                     f"{m.get('feature_stability_score','?')}, mitigability "
                     f"{m.get('causal_mitigability_score','?')}, tier {m.get('tier','?')}"
                     + (" (tolerable residual)" if m.get('tolerable') else ""))
        L.append("")

    L.append("---")
    L.append("_TACO is a pre-deployment certifier prototype, not an insurance product "
             "or a safety guarantee. Findings are bounded by the simulator and search budget._")
    return "\n".join(L) + "\n"


def save_report(verdict: Verdict, scope: AuditScope, out_dir: str | Path) -> dict[str, str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    j = out / "verdict.json"
    m = out / "verdict.md"
    j.write_text(json.dumps(verdict_to_dict(verdict, scope), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    m.write_text(to_markdown(verdict, scope), encoding="utf-8")
    return {"json": str(j), "markdown": str(m)}
