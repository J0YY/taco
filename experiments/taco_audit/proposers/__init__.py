from .base import Proposer
from .heuristic import HeuristicProposer


def make_proposer(kind: str = "heuristic", *, scope_summary: str = "", seed: int = 0) -> Proposer:
    """Build a proposer by name, importing heavy backends lazily.

    Falls back to the heuristic proposer (with a printed note) if the requested
    backend can't initialize — a missing API key for `llm`, or no GPU/diffusers
    for `cosmos`. The audit always runs.
    """
    kind = (kind or "heuristic").lower()
    if kind == "heuristic":
        return HeuristicProposer(seed=seed)
    if kind == "llm":
        from .llm import LLMProposer
        try:
            return LLMProposer(scope_summary=scope_summary, seed=seed)
        except Exception as e:
            print(f"[proposer] llm unavailable ({e}); using heuristic.")
            return HeuristicProposer(seed=seed)
    if kind == "cosmos":
        from .cosmos import CosmosProposer
        return CosmosProposer(seed=seed)
    raise ValueError(f"unknown proposer: {kind!r} (choose heuristic|llm|cosmos)")


__all__ = ["Proposer", "HeuristicProposer", "make_proposer"]
