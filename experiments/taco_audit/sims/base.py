"""Simulator interface.

A Simulator knows how to take a (nominal scenario + Perturbation), roll a policy
out, and return a RolloutResult whose `trace` contains the per-timestep internal
signals the scoring layer expects. Concrete sims: the dependency-free
`ReachWorld` (default), and optional adapters (gymnasium/MuJoCo, Cosmos rollout).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..types import Perturbation, PolicyFn, RolloutResult


class Simulator(ABC):
    #: knob names this sim actually responds to (subset of PERTURBATION_SPACE)
    supported_knobs: list[str] = []

    @abstractmethod
    def rollout(
        self,
        policy: PolicyFn,
        perturbation: Perturbation,
        seed: int = 0,
        control: dict[str, Any] | None = None,
    ) -> RolloutResult:
        """Roll `policy` out once under `perturbation`.

        `control` optionally enables runtime mitigations (e.g. an occlusion
        monitor) so the engine can test whether a control restores success.
        """
        raise NotImplementedError

    @property
    def name(self) -> str:
        return type(self).__name__
