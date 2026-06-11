"""TACO mechanistic audit engine.

Submit one policy file, describe the deployment, and the engine falsifies the
policy in simulation (Monte-Carlo cross-entropy perturbation search), records
replayable failure certificates with mechanistic early-warning detail, and
returns a PASS / CONDITIONAL PASS / FAIL verdict.
"""

from .engine import AuditEngine
from .policy_loader import load_policy
from .scope import gather_scope
from .types import AuditScope, Perturbation, Verdict

__all__ = ["AuditEngine", "load_policy", "gather_scope",
           "AuditScope", "Perturbation", "Verdict"]
__version__ = "0.1.0"
