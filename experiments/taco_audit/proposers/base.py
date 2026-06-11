"""Proposer interface — the perturbation-sampling strategy.

The engine owns the falsification loop; a Proposer decides *which* perturbation to
try next given what has been seen so far. Swapping the proposer is how we switch
between Monte-Carlo / cross-entropy search (heuristic), an LLM that "guesses" the
next stress (llm), or a Cosmos-driven visual perturbation (cosmos).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..types import Perturbation, RolloutResult

History = list[tuple[Perturbation, RolloutResult]]


class Proposer(ABC):
    name: str = "proposer"

    @abstractmethod
    def propose(self, family: str, history: History) -> Perturbation:
        """Return the next perturbation to evaluate for `family`."""
        raise NotImplementedError
