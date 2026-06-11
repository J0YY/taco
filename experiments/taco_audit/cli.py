"""Command-line entrypoint for the TACO audit engine.

    python -m taco_audit.cli audit <policy.py> \
        --robot-type "tabletop arm" --environment cluttered \
        --proximity shared_space --criticality high --out runs/my_audit

Run from inside ``experiments/`` (so ``taco_audit`` is importable), or invoke the
file directly: ``python experiments/taco_audit/cli.py audit <policy.py>``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):  # allow direct-file invocation
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from taco_audit.engine import AuditEngine
from taco_audit.policy_loader import load_policy
from taco_audit.proposers.heuristic import HeuristicProposer
from taco_audit.report import save_report, to_markdown
from taco_audit.scope import gather_scope, interactive_scope

_BADGE = {"PASS": "🟢 PASS", "CONDITIONAL PASS": "🟠 CONDITIONAL PASS", "FAIL": "🔴 FAIL"}


def _event_printer(verbose: bool):
    def emit(kind, **kw):
        if not verbose:
            return
        if kind == "nominal":
            print(f"  · nominal task: {'ok' if kw.get('success') else 'FAILED'}")
        elif kind == "family_search":
            tag = "broke it" if kw.get("found") else "robust"
            print(f"  · search [{kw['family']:<18}] {tag} "
                  f"(best proximity {kw['best_proximity']}, {kw['rollouts']} rollouts)")
        elif kind == "family_done":
            print(f"      ↳ minimal cost {kw['minimal_cost']}, nbhd rate "
                  f"{kw['neighborhood_rate']}, monitorable={kw['monitorable']}, "
                  f"patch_verified={kw['verified_patch']}, severity={kw['severity']}")
    return emit


def cmd_audit(args: argparse.Namespace) -> int:
    policy = load_policy(args.policy, policy_id=args.policy_id)
    if args.interactive:
        scope = interactive_scope(policy_id=policy.policy_id)
    else:
        scope = gather_scope(
            policy_id=args.policy_id or policy.policy_id,
            robot_type=args.robot_type, task_description=args.task,
            environment=args.environment, human_proximity=args.proximity,
            criticality=args.criticality, deployment_units=args.units,
            notes=args.notes or "",
        )

    engine = AuditEngine(search_budget=args.budget, seed=args.seed,
                         on_event=_event_printer(not args.quiet))
    print(f"\nAuditing `{policy.policy_id}` from {policy.source_path}")
    print(f"Scope: {scope.robot_type} · {scope.environment} · {scope.human_proximity} "
          f"· criticality {scope.criticality} (risk tolerance {scope.risk_tolerance():.3f})\n")

    verdict = engine.audit(policy, scope)

    print("\n" + "=" * 62)
    print(f"  VERDICT: {_BADGE.get(verdict.status, verdict.status)}")
    print(f"  {verdict.headline}")
    print("=" * 62)
    if verdict.required_controls:
        print("  Required controls:")
        for c in verdict.required_controls:
            print(f"    - {c}")
    if verdict.exclusions:
        print("  Exclusions:")
        for e in verdict.exclusions:
            print(f"    - {e}")
    print(f"  Failure certificates: {len(verdict.certificates)} "
          f"· rollouts: {verdict.metadata.get('total_rollouts')}")

    if args.out:
        paths = save_report(verdict, scope, args.out)
        print(f"\n  Report written: {paths['markdown']}")
    if args.print_report:
        print("\n" + to_markdown(verdict, scope))

    return 0 if verdict.status != "FAIL" else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="taco_audit", description="TACO mechanistic audit engine")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("audit", help="audit a submitted policy file")
    a.add_argument("policy", help="path to the policy .py file")
    a.add_argument("--policy-id", default=None)
    a.add_argument("--robot-type", dest="robot_type", default="tabletop manipulation arm")
    a.add_argument("--task", default="pick the instructed object")
    a.add_argument("--environment", default="structured indoor",
                   choices=["structured indoor", "cluttered", "public", "outdoor"])
    a.add_argument("--proximity", default="supervised",
                   choices=["isolated", "supervised", "shared_space", "direct_contact"])
    a.add_argument("--criticality", default="medium",
                   choices=["low", "medium", "high", "safety_critical"])
    a.add_argument("--units", type=int, default=1)
    a.add_argument("--notes", default=None)
    a.add_argument("--budget", type=int, default=40, help="search rollouts per family")
    a.add_argument("--seed", type=int, default=0)
    a.add_argument("--out", default=None, help="directory to write verdict.json/.md")
    a.add_argument("--interactive", action="store_true", help="prompt for deployment scope")
    a.add_argument("--print-report", action="store_true")
    a.add_argument("--quiet", action="store_true")
    a.set_defaults(func=cmd_audit)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
