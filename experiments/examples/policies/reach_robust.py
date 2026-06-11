"""A robust reach policy: locks the target's identity at t0, then tracks it.

Submitted as the "policy under audit" for demos where the audit should PASS or
come back CONDITIONAL. At the first step it commits to the detection that best
matches the instruction (semantic identity, not raw salience), then *tracks that
object by position* and ignores later instruction edits. That makes it robust to:
  * occlusion (uses match-score, not salience),
  * language override (locked at t0, ignores "...pick the other one").
It remains exposed only to an extreme look-alike distractor, where the match
scores genuinely collide — a real residual failure family the audit should
surface as a required control rather than a hard block.
"""

import numpy as np


class Policy:
    name = "identity_locked_servo"

    def reset(self):
        self.locked = None

    def act(self, obs):
        dets = obs["detections"]
        g = np.asarray(obs["gripper"], dtype=float)

        if self.locked is None:
            best = max(dets, key=lambda d: d["match_score"])   # semantic identity
            self.locked = np.asarray(best["pos"], dtype=float)
        else:
            # track the locked object: snap to the nearest detection, smoothed
            nearest = min(dets, key=lambda d: np.linalg.norm(np.asarray(d["pos"]) - self.locked))
            self.locked = 0.7 * self.locked + 0.3 * np.asarray(nearest["pos"], dtype=float)

        direction = self.locked - g
        dist = float(np.linalg.norm(direction))
        v = direction / (dist + 1e-8)
        if dist < 0.08:
            v *= 0.2
        return v
