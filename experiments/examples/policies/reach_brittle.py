"""A brittle reach policy: a visual-salience follower that re-reads the instruction.

Submitted as the "policy under audit" for demos where the audit should FAIL or
come back CONDITIONAL. It picks whichever detection looks most visually prominent
(salience) and obeys the latest instruction text. That makes it fragile to:
  * occlusion (which suppresses the true target's salience and boosts clutter),
  * a conflicting language override ("...actually pick the other one"),
  * and, weakly, look-alike distractors.

Policy contract (any one of these is accepted by the loader):
  * a module-level ``policy(obs) -> action``
  * a ``Policy`` class with ``act(obs)`` (+ optional ``reset()``)
  * a ``build_policy() -> callable``
"""

import numpy as np


class Policy:
    name = "salience_follower"

    def reset(self):
        pass

    def act(self, obs):
        dets = obs["detections"]
        g = np.asarray(obs["gripper"], dtype=float)

        # follow the most visually salient detection
        target = max(dets, key=lambda d: d["salience"])

        # naively obey a conflicting instruction: jump to "the other one"
        if "actually pick the other one" in obs.get("instruction", "") and len(dets) > 1:
            others = [d for d in dets if d is not target]
            target = others[0]

        direction = np.asarray(target["pos"], dtype=float) - g
        dist = float(np.linalg.norm(direction))
        v = direction / (dist + 1e-8)
        if dist < 0.08:          # ease in for a clean grasp
            v *= 0.2
        return v
