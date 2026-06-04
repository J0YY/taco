"""Real cross-policy replay evidence imported from sibling robotics projects.

Unlike the Apex warehouse certificates (FR-001..FR-003), these exhibits are real
rendered rollouts from other policies/simulators, shipped with their original
success/failure metadata:

* FR-004 - a VLA diffusion policy on SimplerEnv ``move_near`` (from the sae-scope
  project) instrumented with an internal SAE monitor. Its manifest records, per
  episode, whether the policy succeeded and the timestep at which the internal
  monitor first alerted - giving a REAL early-warning lead before failure.
* nla4vla breadth - OpenVLA-7B (LIBERO) and SmolVLA (MetaWorld) native rollouts
  plus a destructive-token failure, showing TACO evidence is policy-agnostic.

Everything here is derived from the copied manifest.json files; no numbers are
fabricated. If a manifest is missing the functions degrade to empty results so
the app never crashes.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

EXTERNAL_ROOT = Path(__file__).resolve().parent / "data" / "videos" / "real_external"

# Copied-file -> original curated clip, so we can join back to the real manifest.
SAESCOPE_CLIPS = {
    "FR-004_success_no_alert.mp4": "01_success_clean_orange_no_alert.mp4",
    "FR-004_failure_alert_lead48.mp4": "04_failure_internal_early_no_action_orange.mp4",
    "FR-004_failure_action_late.mp4": "08_failure_internal_early_action_late.mp4",
    "FR-004_false_alert_handoff.mp4": "10_limitation_false_handoff_success.mp4",
}

NLA4VLA_CLIPS = {
    "openvla_libero_success.mp4": "01_native_identity_success.mp4",
    "openvla_libero_failure.mp4": "02_destructive_wrong_token.mp4",
    "smolvla_metaworld_success.mp4": "03_smolvla_metaworld_bin_picking_success.mp4",
}


def _load_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict):
        for key in ("videos", "entries", "clips", "cases"):
            if isinstance(payload.get(key), list):
                return payload[key]
        return []
    return payload if isinstance(payload, list) else []


def load_saescope_manifest(root: Path = EXTERNAL_ROOT) -> list[dict[str, Any]]:
    return _load_manifest(root / "saescope" / "manifest.json")


def _by_selected_name(manifest: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(e.get("selected_name") or Path(str(e.get("video", ""))).name): e for e in manifest}


def saescope_summary(root: Path = EXTERNAL_ROOT) -> dict[str, Any]:
    """Compute REAL internal-monitor statistics from the sae-scope manifest."""
    manifest = load_saescope_manifest(root)
    if not manifest:
        return {"available": False}

    successes = [e for e in manifest if int(e.get("success", 0)) == 1]
    failures = [e for e in manifest if int(e.get("success", 0)) == 0]
    # Failures the internal monitor actually flagged (first_alert is a real timestep).
    flagged_failures = [e for e in failures if e.get("first_alert") is not None]
    # Successes where the monitor alerted anyway (real false positives / limitations).
    false_alerts = [e for e in successes if e.get("first_alert") is not None]

    leads = [int(e["lead"]) for e in flagged_failures if e.get("lead") is not None]
    first_alerts = [int(e["first_alert"]) for e in flagged_failures if e.get("first_alert") is not None]
    reproduced = [e for e in failures if e.get("rerun_success") is False]

    detected = len(flagged_failures)
    precision_den = detected + len(false_alerts)
    return {
        "available": True,
        "total_clips": len(manifest),
        "success_count": len(successes),
        "failure_count": len(failures),
        "neighborhood_failure_rate": round(len(failures) / len(manifest), 3) if manifest else 0.0,
        "failures_detected_by_monitor": detected,
        "false_alert_count": len(false_alerts),
        "recall": round(detected / len(failures), 3) if failures else 0.0,
        "precision": round(detected / precision_den, 3) if precision_den else 0.0,
        "mean_early_warning_lead_steps": round(mean(leads), 1) if leads else 0.0,
        "first_alert_step": min(first_alerts) if first_alerts else None,
        "failure_reproducibility": round(len(reproduced) / len(failures), 3) if failures else 0.0,
        "policy": "VLA diffusion policy",
        "environment": "SimplerEnv move_near (Google robot arm)",
        "source_project": "sae-scope",
    }


def fr004_certificate() -> dict[str, Any]:
    """Real cross-policy certificate descriptor (kept out of the Apex quote pipeline)."""
    summary = saescope_summary()
    lead = summary.get("mean_early_warning_lead_steps", 0.0)
    return {
        "certificate_id": "FR-004",
        "policy_id": "vla_diffusion_move_near",
        "task_id": "simplerenv_move_near",
        "failure_type": "internal_monitor_early_warning_before_task_failure",
        "severity": "high",
        "source": "real_saescope_internal_monitor_evidence",
        "real_internal_evidence": True,
        "dominant_risk_signature": "internal SAE monitor activation rises before action diverges",
        "recommended_control": "internal_risk_monitor_handoff_on_alert",
        "early_warning_lead_steps": lead,
        "provenance": (
            "Real VLA diffusion rollouts on SimplerEnv move_near (sae-scope project). "
            f"Across flagged failures the internal monitor first alerted at step "
            f"{summary.get('first_alert_step')} - a {lead:.0f}-step lead before the episode failed. "
            f"Recall {summary.get('recall')}, precision {summary.get('precision')} on the curated set."
        ),
    }


def _video_rel(subdir: str, filename: str) -> str:
    return str(EXTERNAL_ROOT / subdir / filename)


def saescope_catalog_rows(root: Path = EXTERNAL_ROOT) -> list[dict[str, Any]]:
    index = _by_selected_name(load_saescope_manifest(root))
    rows: list[dict[str, Any]] = []
    for filename, original in SAESCOPE_CLIPS.items():
        entry = index.get(original, {})
        success = int(entry.get("success", 0)) == 1
        rows.append(
            {
                "clip": filename,
                "video_path": _video_rel("saescope", filename),
                "outcome": "success" if success else "FAILURE",
                "internal_alert_step": entry.get("first_alert"),
                "early_warning_lead_steps": entry.get("lead"),
                "monitor_reproduced": entry.get("rerun_success"),
                "case": entry.get("case", ""),
                "note": entry.get("review_note", ""),
            }
        )
    return rows


def nla4vla_catalog(root: Path = EXTERNAL_ROOT) -> list[dict[str, Any]]:
    index = _by_selected_name(_load_manifest(root / "nla4vla" / "manifest.json"))
    rows: list[dict[str, Any]] = []
    for filename, original in NLA4VLA_CLIPS.items():
        entry = index.get(original, {})
        success = entry.get("strict_success")
        rows.append(
            {
                "clip": filename,
                "video_path": _video_rel("nla4vla", filename),
                "policy": entry.get("vla") or entry.get("vla_family") or entry.get("policy") or "VLA",
                "environment": entry.get("suite") or entry.get("env") or entry.get("simulator") or "",
                "task": entry.get("task", ""),
                "outcome": "success" if success else ("FAILURE" if success is False else "unknown"),
                "what_to_watch_for": entry.get("what_to_watch_for", ""),
            }
        )
    return rows


def maniskill_render_summary(root: Path | None = None) -> dict[str, Any]:
    """Summarize the cluster-rendered ManiSkill rope rollout (if pulled back)."""
    base = root or (Path(__file__).resolve().parent / "data" / "videos" / "real_maniskill")
    traj = base / "rope_loop_16env.trajectory.json"
    video = base / "rope_loop_16env.mp4"
    if not traj.exists() or not video.exists():
        return {"available": False}
    payload = json.loads(traj.read_text(encoding="utf-8"))
    episodes = payload.get("episodes", [])
    failures = sum(1 for e in episodes if not e.get("success"))
    return {
        "available": True,
        "video_path": str(video),
        "env_id": payload.get("env_info", {}).get("env_id", "RopeLoopPlacementRMA-v1"),
        "episodes": len(episodes),
        "failures": failures,
        "neighborhood_failure_rate": round(failures / len(episodes), 3) if episodes else 0.0,
        "source_project": "cotracker-rma (rendered on athena cluster)",
    }
