"""Run the audit on all three example policies and print a one-line summary each.

    python examples/run_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from taco_audit.engine import AuditEngine
from taco_audit.policy_loader import load_policy
from taco_audit.scope import gather_scope

POLICIES = [
    ("reach_robust", "expect PASS"),
    ("reach_brittle", "expect CONDITIONAL PASS"),
    ("reach_blind", "expect FAIL"),
]
HERE = Path(__file__).resolve().parent


def main() -> None:
    scope_kwargs = dict(robot_type="tabletop manipulation arm", environment="cluttered",
                        human_proximity="shared_space", criticality="high")
    print(f"\n{'policy':<22}{'verdict':<20}{'certs':<7}{'controls':<9}rollouts")
    print("-" * 70)
    for name, _ in POLICIES:
        policy = load_policy(HERE / "policies" / f"{name}.py")
        scope = gather_scope(policy_id=policy.policy_id, **scope_kwargs)
        verdict = AuditEngine(seed=0).audit(policy, scope)
        print(f"{name:<22}{verdict.status:<20}{len(verdict.certificates):<7}"
              f"{len(verdict.required_controls):<9}{verdict.metadata.get('total_rollouts')}")
    print()


if __name__ == "__main__":
    main()
