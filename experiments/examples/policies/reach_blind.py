"""An open-loop / memorized-trajectory policy: ignores perception, replays a path.

Submitted as the "policy under audit" for demos where the audit should FAIL. It
uses only proprioception (the gripper position) and drives to the location the
target occupied at training time, ignoring the detections entirely. It succeeds
on the nominal task — and looks fine for almost the whole trajectory — but when
the target's pose shifts it confidently grasps empty space, with the behavioural
risk signal arriving only at the very end (no usable early warning). That makes
the failure *not monitorable*, which the audit treats as a hard block.
"""

import numpy as np

MEMORIZED_TARGET = np.array([0.80, 0.56])   # where the target sat during training


class Policy:
    name = "open_loop_memorizer"

    def reset(self):
        pass

    def act(self, obs):
        g = np.asarray(obs["gripper"], dtype=float)
        direction = MEMORIZED_TARGET - g
        dist = float(np.linalg.norm(direction))
        v = direction / (dist + 1e-8)
        if dist < 0.08:
            v *= 0.2
        return v
