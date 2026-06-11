"""LLMProposer — Claude proposes the next perturbation as a validated JSON spec.

This is the "a language model outputs a sim state, feed it into the sim" route.
Instead of sampling blindly, Claude reads the deployment intent and the search
history (which perturbations the policy survived, which it failed, and how close
each came) and *reasons* about the next stress most likely to expose a minimal
failure — then emits it as a bounded, schema-validated JSON object.

Activates only when the `anthropic` SDK is installed and `ANTHROPIC_API_KEY` is
set; otherwise the engine falls back to the heuristic proposer. The model defaults
to Claude Opus 4.8 (`claude-opus-4-8`) and can be overridden with the
`TACO_LLM_MODEL` env var.
"""

from __future__ import annotations

import json
import os

from ..types import FAMILY_KNOBS, PERTURBATION_SPACE, Perturbation
from .base import History, Proposer
from .heuristic import HeuristicProposer

DEFAULT_MODEL = "claude-opus-4-8"  # per the Anthropic model catalog; override via env

SYSTEM = (
    "You are a red-team adversary auditing a learned robot policy in simulation. "
    "Your job is to find the SMALLEST, most plausible perturbation of the robot's "
    "situation that makes the policy fail its task. You propose perturbations as "
    "bounded numeric knobs; a separate simulator rolls the policy out and reports "
    "how close it came to failing. Prefer minimal, in-distribution stresses over "
    "extreme ones — a small perturbation that breaks the policy is a stronger "
    "finding. Use the history to climb toward the failure boundary."
)


class LLMProposer(Proposer):
    name = "llm"

    def __init__(self, scope_summary: str = "", model: str | None = None, seed: int = 0):
        self.model = model or os.environ.get("TACO_LLM_MODEL", DEFAULT_MODEL)
        self.scope_summary = scope_summary
        self._fallback = HeuristicProposer(seed=seed)
        try:
            import anthropic  # noqa: F401
        except ImportError as e:  # pragma: no cover - depends on environment
            raise RuntimeError(
                "LLMProposer needs the anthropic SDK: pip install anthropic"
            ) from e
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            raise RuntimeError("LLMProposer needs ANTHROPIC_API_KEY to be set")
        import anthropic
        self._client = anthropic.Anthropic()

    def _schema(self, knobs: list[str]) -> dict:
        # numeric constraints aren't supported by structured outputs; we clamp.
        props = {k: {"type": "number"} for k in knobs}
        props["rationale"] = {"type": "string"}
        return {
            "type": "object",
            "properties": props,
            "required": knobs + ["rationale"],
            "additionalProperties": False,
        }

    def _history_text(self, family: str, history: History) -> str:
        rows = []
        for p, r in history[-12:]:
            if p.family != family:
                continue
            knobs = {k: round(v, 3) for k, v in p.knobs.items()}
            rows.append(f"  knobs={knobs} -> "
                        f"{'FAIL' if not r.success else 'survived'} "
                        f"(failure_proximity={r.failure_proximity:.2f})")
        return "\n".join(rows) if rows else "  (no attempts yet)"

    def propose(self, family: str, history: History) -> Perturbation:
        knobs = FAMILY_KNOBS.get(family, list(PERTURBATION_SPACE))
        ranges = {k: list(PERTURBATION_SPACE[k]) for k in knobs}
        user = (
            f"Deployment: {self.scope_summary or 'tabletop manipulation, pick the instructed object'}.\n"
            f"Failure family under test: {family}.\n"
            f"Tunable knobs and their [min,max] ranges:\n{json.dumps(ranges, indent=2)}\n\n"
            f"Attempts so far (proximity 1.0 = clear failure, lower = robust):\n"
            f"{self._history_text(family, history)}\n\n"
            "Propose the next knob values to try. Aim to just cross the failure "
            "boundary with the smallest perturbation. Return only the JSON object."
        )
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=1024,
                system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": self._schema(knobs)}},
                messages=[{"role": "user", "content": user}],
            )
            if resp.stop_reason == "refusal":  # safety classifier declined; fall back
                return self._fallback.propose(family, history)
            text = next(b.text for b in resp.content if b.type == "text")
            data = json.loads(text)
        except Exception:  # network/parse/SDK error -> never break the audit
            return self._fallback.propose(family, history)

        out = {k: float(data[k]) for k in knobs if k in data}
        if not out:
            return self._fallback.propose(family, history)
        return Perturbation(knobs=out, family=family, source="llm")
