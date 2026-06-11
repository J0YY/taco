"""HeuristicProposer — Monte-Carlo cross-entropy falsification search.

This is the default, dependency-free proposer. It searches each failure family's
knob subspace for the perturbation that pushes the policy closest to (and then
over) the failure boundary:

  * Warm-up: random Monte-Carlo samples of small perturbations.
  * Cross-entropy refinement: fit a Gaussian to the *elite* (highest
    failure-proximity) samples and resample, concentrating around the boundary.
  * An explore fraction keeps widening so the search does not collapse early.

Because `RolloutResult.failure_proximity` is continuous (not just pass/fail), the
search gets gradient information even before it trips the first real failure —
which is what makes it find *minimal* failures, not just any failure.
"""

from __future__ import annotations

import numpy as np

from ..types import FAMILY_KNOBS, PERTURBATION_SPACE, Perturbation
from .base import History, Proposer


class HeuristicProposer(Proposer):
    name = "heuristic"

    def __init__(self, warmup: int = 5, elite_frac: float = 0.3,
                 explore: float = 0.30, seed: int = 0):
        self.warmup = warmup
        self.elite_frac = elite_frac
        self.explore = explore
        self.rng = np.random.default_rng(seed)

    def _sample_random(self, knobs: list[str], scale: float) -> dict[str, float]:
        out = {}
        for k in knobs:
            lo, hi = PERTURBATION_SPACE[k]
            if k == "camera_yaw_deg":
                out[k] = float(self.rng.uniform(-1, 1) * (hi) * scale)
            else:
                out[k] = float(lo + self.rng.uniform(0, 1) * (hi - lo) * scale)
        return out

    def propose(self, family: str, history: History) -> Perturbation:
        knobs = FAMILY_KNOBS.get(family, list(PERTURBATION_SPACE))
        fam = [(p, r) for (p, r) in history if p.family == family]

        # Warm-up: random Monte-Carlo, growing in scale so we bracket the boundary.
        if len(fam) < self.warmup:
            scale = 0.25 + 0.6 * (len(fam) / max(1, self.warmup))
            return Perturbation(knobs=self._sample_random(knobs, scale), family=family,
                                source="heuristic")

        # Cross-entropy: rank by proximity, fit Gaussian to elites, resample.
        ranked = sorted(fam, key=lambda pr: pr[1].failure_proximity, reverse=True)
        n_elite = max(2, int(len(ranked) * self.elite_frac))
        elites = ranked[:n_elite]

        out: dict[str, float] = {}
        for k in knobs:
            lo, hi = PERTURBATION_SPACE[k]
            vals = np.array([p.knobs.get(k, lo) for p, _ in elites], dtype=float)
            mean = float(vals.mean())
            std = float(vals.std())
            span = hi - lo
            std = max(std, 0.06 * span)            # floor so we keep moving
            if self.rng.uniform() < self.explore:  # occasional widening
                std *= 2.5
            sample = float(self.rng.normal(mean, std))
            out[k] = sample
        return Perturbation(knobs=out, family=family, source="heuristic")
