"""Gather just-enough deployment context to make the verdict meaningful.

The product wants to ask the operator a few questions about *where and how* the
policy will run — enough to set the risk bar, without overwhelming them. Five
fields do the work (everything else has a sane default):

  robot_type · task · environment · human_proximity · criticality

`gather_scope` builds an AuditScope programmatically; `interactive_scope` prompts
for the same fields on the CLI with the defaults pre-filled.
"""

from __future__ import annotations

from .types import AuditScope

ENVIRONMENTS = ["structured indoor", "cluttered", "public", "outdoor"]
PROXIMITY = ["isolated", "supervised", "shared_space", "direct_contact"]
CRITICALITY = ["low", "medium", "high", "safety_critical"]

QUESTIONS = [
    ("robot_type", "Robot / embodiment", "tabletop manipulation arm"),
    ("task_description", "Task the policy performs", "pick the instructed object"),
    ("environment", f"Deployment environment {ENVIRONMENTS}", "structured indoor"),
    ("human_proximity", f"Human proximity {PROXIMITY}", "supervised"),
    ("criticality", f"Failure criticality {CRITICALITY}", "medium"),
    ("deployment_units", "How many units deployed", "1"),
]


def gather_scope(**kwargs) -> AuditScope:
    """Build a scope from keyword overrides, validating the categorical fields."""
    scope = AuditScope()
    for key, value in kwargs.items():
        if value is None or not hasattr(scope, key):
            continue
        if key == "environment" and value not in ENVIRONMENTS:
            raise ValueError(f"environment must be one of {ENVIRONMENTS}")
        if key == "human_proximity" and value not in PROXIMITY:
            raise ValueError(f"human_proximity must be one of {PROXIMITY}")
        if key == "criticality" and value not in CRITICALITY:
            raise ValueError(f"criticality must be one of {CRITICALITY}")
        if key == "deployment_units":
            value = int(value)
        setattr(scope, key, value)
    return scope


def interactive_scope(policy_id: str = "submitted_policy") -> AuditScope:  # pragma: no cover
    print("\nTACO audit — describe the deployment (press Enter to accept the default):\n")
    answers: dict = {"policy_id": policy_id}
    for key, prompt, default in QUESTIONS:
        raw = input(f"  {prompt} [{default}]: ").strip()
        answers[key] = raw or default
    return gather_scope(**answers)
