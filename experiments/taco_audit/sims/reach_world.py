"""ReachWorld — a dependency-free, deterministic tabletop reach-and-grasp sim.

It is small on purpose: a 2-D table, a gripper, a true target, and a distractor.
The policy never sees ground-truth identities — only *perceptual detections*
(position, visual salience, instruction match-score) plus a language instruction.
A Perturbation degrades those perceptions the way a real deployment would
(occlusion, a look-alike distractor, a conflicting instruction, sensor noise,
bad lighting, viewpoint shift). Success = the gripper grasps the *true* target
in time; everything else is a failure.

Crucially, the rollout records the same per-timestep internal signals that
`taco_demo.trace_scoring` consumes (target_feature, occlusion_risk,
internal_risk_score, action_risk, …), computed *behaviourally* from the policy's
own actions — a model-agnostic monitor that needs no access to network weights.
If a policy chooses to expose real internals (by returning `(action, info)` with
an ``internal`` dict), those override the behavioural estimates.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from ..types import Perturbation, PolicyFn, RolloutResult
from .base import Simulator

EPS = 1e-8


def _unit(v: np.ndarray) -> np.ndarray:
    n = float(np.linalg.norm(v))
    return v / n if n > EPS else np.zeros_like(v)


def _ema(prev: float, x: float, alpha: float = 0.25) -> float:
    return (1 - alpha) * prev + alpha * x


class ReachWorld(Simulator):
    """Reach-and-grasp falsification environment."""

    supported_knobs = [
        "occlusion_fraction", "distractor_similarity", "camera_yaw_deg",
        "target_pose_shift", "sensor_noise", "language_override", "lighting",
    ]

    def __init__(self, control_hz: int = 20, max_steps: int = 120, speed: float = 0.25):
        self.control_hz = control_hz
        self.max_steps = max_steps
        self.speed = speed
        self.dt = 1.0 / control_hz
        self.grasp_radius = 0.06

    # -- scenario construction ------------------------------------------------
    def _nominal(self) -> dict[str, Any]:
        return {
            "gripper": np.array([0.12, 0.5]),
            "target_pos": np.array([0.80, 0.56]),
            "distractor_pos": np.array([0.80, 0.34]),
            "instruction": "pick the target cube",
            "target_salience": 0.90,
            "target_match": 0.90,
            "distractor_salience": 0.50,
            "distractor_match": 0.18,
        }

    def _perceive(
        self, scn: dict[str, Any], p: dict[str, float], gripper: np.ndarray,
        rng: np.random.Generator, t: int, control: dict[str, Any],
    ) -> dict[str, Any]:
        """Build the observation the policy sees this step (perception layer)."""
        occ = p.get("occlusion_fraction", 0.0)
        sim = p.get("distractor_similarity", 0.0)
        yaw = np.deg2rad(p.get("camera_yaw_deg", 0.0))
        noise = p.get("sensor_noise", 0.0)
        lang = p.get("language_override", 0.0)
        light = p.get("lighting", 0.0)

        # occlusion monitor (runtime control): a "second view" halves occlusion.
        if control.get("occlusion_monitor") and t > 6:
            occ *= 0.4

        yawn = float(min(1.0, abs(yaw) / np.deg2rad(25)))  # normalised viewpoint shift
        t_sal = scn["target_salience"] - 0.70 * occ - 0.25 * light - 0.20 * yawn
        t_match = scn["target_match"] - 0.50 * occ - 0.12 * yawn
        d_sal = scn["distractor_salience"] + 0.40 * occ + 0.50 * sim + 0.15 * light
        # a look-alike distractor raises the distractor's match-score but stays
        # *below* the true target's — a semantic policy that uses match-score is
        # robust to it, while a salience follower is fooled by the salience bump.
        d_match = min(0.72, scn["distractor_match"] + 0.55 * sim)

        # language override: a conflicting suffix re-points the *instruction text*
        # at the distractor. It does NOT change visual identity (match_score), so a
        # policy that locks its target at t0 is immune; one that re-reads the
        # instruction each step is redirected. A runtime sanitizer strips it.
        conflict = 0.0 if control.get("language_sanitizer") else lang

        def jitter(pos: np.ndarray) -> np.ndarray:
            # mild viewpoint shear (does NOT teleport into an unservoable frame) +
            # sensor wobble — keeps yaw a perception *degrader*, not a calibration bug.
            ap = pos + np.array([0.0, 1.0]) * (yaw * 0.05)
            if noise > 0:
                ap = ap + rng.normal(0, noise * 0.15, size=2)
            return ap

        dets = [
            {"pos": jitter(scn["target_pos"]), "salience": float(np.clip(t_sal, 0, 1)),
             "match_score": float(np.clip(t_match, 0, 1)), "_truth": "target"},
            {"pos": jitter(scn["distractor_pos"]), "salience": float(np.clip(d_sal, 0, 1)),
             "match_score": float(np.clip(d_match, 0, 1)), "_truth": "distractor"},
        ]
        # randomise order so a policy can't cheat by list index
        order = rng.permutation(2)
        dets = [dets[i] for i in order]
        instruction = scn["instruction"]
        if conflict > 0.5:
            instruction = scn["instruction"] + " — actually pick the other one"
        return {
            "t": t,
            "gripper": gripper.copy(),
            "instruction": instruction,
            "instruction_conflict": float(conflict),
            "detections": dets,
            "time_left": (self.max_steps - t) / self.max_steps,
        }

    # -- rollout --------------------------------------------------------------
    def rollout(
        self, policy: PolicyFn, perturbation: Perturbation, seed: int = 0,
        control: dict[str, Any] | None = None,
    ) -> RolloutResult:
        control = control or {}
        p = perturbation.clamped().knobs
        scn = self._nominal()
        scn["target_pos"] = scn["target_pos"] + np.array([0.0, 1.0]) * p.get("target_pose_shift", 0.0)
        rng = np.random.default_rng(seed)

        gripper = scn["target_pos"] * 0 + scn["gripper"]
        truth_target = scn["target_pos"]
        truth_distractor = scn["distractor_pos"]

        T = self.max_steps
        sig = {k: np.zeros(T, dtype=float) for k in [
            "time_s", "target_feature", "general_grasp_feature", "transport_feature",
            "memorized_trajectory_feature", "unsafe_trajectory_dominance", "action_risk",
            "internal_risk_score", "occlusion_risk", "language_override_risk", "distractor_risk",
        ]}
        ema = {"target": 0.5, "distractor": 0.0, "unsafe": 0.0, "memorized": 0.0}
        settle = 0
        grasped: str | None = None
        failure_timestep: int | None = None
        peak_distractor = 0.0
        peak_action_risk = 0.0
        min_target_feat = 1.0
        steps_used = T

        for t in range(T):
            obs = self._perceive(scn, p, gripper, rng, t, control)
            raw = policy(obs)
            info: dict[str, Any] = {}
            if isinstance(raw, tuple):
                action, info = raw[0], (raw[1] if len(raw) > 1 else {})
            else:
                action = raw
            action = np.asarray(action, dtype=float).reshape(-1)[:2]
            if action.shape[0] < 2:
                action = np.pad(action, (0, 2 - action.shape[0]))
            action = np.clip(action, -1.0, 1.0)

            dir_t = _unit(truth_target - gripper)
            dir_d = _unit(truth_distractor - gripper)
            an = _unit(action)
            speed = float(min(1.0, np.linalg.norm(action)))
            target_align = float(np.clip((np.dot(an, dir_t) + 1) / 2, 0, 1))
            distractor_align = float(np.clip((np.dot(an, dir_d) + 1) / 2, 0, 1))

            # distractor monitor (runtime control): damp motion toward the distractor
            if control.get("distractor_confirmation") and distractor_align > 0.7 and target_align < 0.6:
                action = action * 0.25
                speed *= 0.25

            occ_risk = float(np.clip(p.get("occlusion_fraction", 0.0) + 0.05 * rng.standard_normal(), 0, 1))
            if control.get("occlusion_monitor") and t > 6:
                occ_risk *= 0.4
            lang_risk = float(np.clip(p.get("language_override", 0.0) * (0.0 if control.get("language_sanitizer") else 1.0), 0, 1))

            ema["target"] = _ema(ema["target"], target_align)
            ema["distractor"] = _ema(ema["distractor"], distractor_align * speed)
            wrong = max(distractor_align, 1.0 - target_align)
            ema["unsafe"] = _ema(ema["unsafe"], 1.0 if wrong > 0.55 else 0.0)
            ema["memorized"] = _ema(ema["memorized"], speed * (1.0 - target_align))

            dist_to_target = float(np.linalg.norm(truth_target - gripper))
            dist_nearest = min(dist_to_target, float(np.linalg.norm(truth_distractor - gripper)))
            action_risk = float(np.clip(speed * max(distractor_align, occ_risk, lang_risk, 1 - target_align), 0, 1))

            sig["time_s"][t] = t * self.dt
            sig["target_feature"][t] = ema["target"]
            sig["distractor_risk"][t] = ema["distractor"]
            sig["general_grasp_feature"][t] = float(np.clip(1.0 - dist_nearest, 0, 1))
            sig["transport_feature"][t] = float(np.clip(1.0 - dist_to_target, 0, 1))
            sig["memorized_trajectory_feature"][t] = float(np.clip(ema["memorized"], 0, 1))
            sig["unsafe_trajectory_dominance"][t] = float(np.clip(ema["unsafe"], 0, 1))
            sig["action_risk"][t] = action_risk
            sig["occlusion_risk"][t] = occ_risk
            sig["language_override_risk"][t] = lang_risk
            irs = float(np.clip(
                0.30 * action_risk + 0.22 * ema["unsafe"] + 0.20 * occ_risk
                + 0.18 * lang_risk + 0.20 * ema["distractor"] + 0.15 * (1 - ema["target"]) - 0.10, 0, 1))
            sig["internal_risk_score"][t] = irs

            # allow a policy to override behavioural signals with real internals
            for key, val in (info.get("internal") or {}).items():
                if key in sig:
                    sig[key][t] = float(val)

            peak_distractor = max(peak_distractor, ema["distractor"])
            peak_action_risk = max(peak_action_risk, action_risk)
            min_target_feat = min(min_target_feat, ema["target"])

            # integrate motion
            gripper = np.clip(gripper + action * self.dt * self.speed * 2.5, 0.0, 1.0)

            # grasp commitment: settle near an object
            near_t = float(np.linalg.norm(truth_target - gripper)) < self.grasp_radius
            near_d = float(np.linalg.norm(truth_distractor - gripper)) < self.grasp_radius
            if (near_t or near_d) and speed < 0.25:
                settle += 1
            else:
                settle = max(0, settle - 1)
            if settle >= 3 and (near_t or near_d):
                grasped = "target" if near_t and (not near_d or
                          np.linalg.norm(truth_target - gripper) <= np.linalg.norm(truth_distractor - gripper)) else "distractor"
                steps_used = t + 1
                if grasped == "distractor":
                    failure_timestep = t
                break

        # outcome
        success = grasped == "target"
        if not success and failure_timestep is None:
            # timeout / miss: blame the step where risk first dominated, else last step
            crossings = np.where(sig["internal_risk_score"][:steps_used] > 0.6)[0]
            failure_timestep = int(crossings[0]) if len(crossings) else max(1, steps_used - 1)

        # truncate signals to used length
        for k in sig:
            sig[k] = sig[k][:steps_used]
        sig["trace_source"] = np.array(["reachworld_behavioural_monitor"])
        sig["recorded_required_signal_count"] = np.array([6])

        # continuous failure-proximity: drives the heuristic search even on success
        if success:
            proximity = float(np.clip(0.6 * max(peak_distractor, 1 - min_target_feat, peak_action_risk), 0, 0.59))
        else:
            sev = 1.0 if grasped == "distractor" else 0.78  # wrong grasp worse than timeout
            proximity = float(np.clip(0.6 + 0.4 * sev, 0.6, 1.0))

        return RolloutResult(
            success=success,
            failure_proximity=proximity,
            failure_timestep=int(failure_timestep) if failure_timestep is not None else None,
            trace=sig,
            info={
                "grasped": grasped, "steps_used": steps_used,
                "peak_distractor_risk": peak_distractor, "min_target_feature": min_target_feat,
                "outcome": "success" if success else ("wrong_grasp" if grasped == "distractor" else "timeout"),
            },
        )
