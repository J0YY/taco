"""Adapter that normalizes DreamAudit certificates into TACO contracts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .config import data_root, dreamaudit_root
from .schemas import NormalizedDreamAuditCertificate, ReplayArtifacts, read_json


SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}


def _first(raw: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    for key in keys:
        current: Any = raw
        ok = True
        for part in key.split("."):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                ok = False
                break
        if ok and current not in (None, ""):
            return current
    return default


def _looks_like_certificate(raw: dict[str, Any]) -> bool:
    return any(k in raw for k in ("certificate_id", "cert_id", "patch_recipe", "minimality", "simulator_validation")) or (
        isinstance(raw.get("replay"), dict) and "command" in raw["replay"]
    )


class DreamAuditAdapter:
    def __init__(self, repo_root: Path | None = None, data_root: Path | None = None):
        self.repo_root = (repo_root or dreamaudit_root()).resolve()
        self.data_root = (data_root or globals()["data_root"]()).resolve()

    def discover_certificate_files(self, extra_dirs: list[Path] | None = None) -> list[Path]:
        roots = [
            self.data_root / "dreamaudit_certs",
            self.repo_root / "outputs",
            self.repo_root / "artifacts",
            self.repo_root / "results",
            self.repo_root / "runs",
        ]
        roots.extend(extra_dirs or [])
        found: list[Path] = []
        for root in roots:
            if not root.exists():
                continue
            for path in root.rglob("*.json"):
                if any(part in SKIP_DIRS for part in path.parts):
                    continue
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if isinstance(raw, dict) and _looks_like_certificate(raw):
                    found.append(path)
        return sorted(set(found))

    def load_certificates(self, cert_dir: Path | None = None) -> list[NormalizedDreamAuditCertificate]:
        paths = self._discover_under(cert_dir) if cert_dir else self.discover_certificate_files()
        certs: list[NormalizedDreamAuditCertificate] = []
        for path in paths:
            try:
                raw = read_json(path)
            except Exception:
                continue
            if isinstance(raw, dict):
                certs.append(self.normalize_certificate(raw, path))
        return certs

    def _discover_under(self, root: Path) -> list[Path]:
        if not root.exists():
            return []
        found: list[Path] = []
        for path in root.rglob("*.json"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if isinstance(raw, dict) and _looks_like_certificate(raw):
                found.append(path)
        return sorted(found)

    def normalize_certificate(self, raw: dict[str, Any], source_path: Path | None = None) -> NormalizedDreamAuditCertificate:
        missing: list[str] = []
        cert_id = _first(raw, ["certificate_id", "id", "cert_id"], "CERT-UNKNOWN")
        policy = _first(raw, ["policy_id", "policy.name", "policy", "model", "robot_policy"], "unknown_policy")
        if isinstance(policy, dict):
            policy = policy.get("name") or policy.get("id") or "unknown_policy"
        task = _first(raw, ["task_id", "task.task_id", "task", "environment", "env"], "unknown_task")
        if isinstance(task, dict):
            task = task.get("task_id") or task.get("name") or task.get("suite") or "unknown_task"
        failure_type = _first(
            raw,
            ["failure_type", "observed_failure_mode", "vulnerability_type", "failure_mode", "simulator_validation.failure_mode"],
            "internal_failure_precursor_detected",
        )
        perturbation = _first(raw, ["perturbation", "perturbations", "decoded_values"], {})
        minimal_cost = _first(
            raw,
            [
                "minimal_failure_cost",
                "minimal_cost",
                "normalized_cost",
                "perturbation.normalized_cost",
                "perturbation.perturbation_cost",
                "minimality.minimal_failure_cost",
                "minimality.smallest_failing_cost_found",
            ],
            0.5,
        )
        failure_rate = _first(raw, ["failure_rate_neighborhood", "minimality.failure_rate_at_0_75_cost"], 0.5)
        failure_timestep = _first(raw, ["failure_timestep", "simulator_validation.failure_frame", "failure_frame"], 90)
        replay_command = _first(raw, ["replay_command", "replay.cmd", "replay.command", "command"], "")
        patch_recipe = _first(raw, ["patch_recipe", "patch", "mitigation", "intervention"], {})
        for name, value in {
            "certificate_id": cert_id,
            "policy_id": policy,
            "task_id": task,
            "failure_type": failure_type,
        }.items():
            if value in ("unknown_policy", "unknown_task", "internal_failure_precursor_detected", "CERT-UNKNOWN"):
                missing.append(name)
        metadata = {
            "raw_keys": sorted(raw.keys()),
            "source": "normalized_missing_fields" if missing else "dreamaudit_normalized",
            "missing_fields": missing,
            "replay_video_uri": _first(raw, ["simulator_validation.replay_video_uri", "replay_video_uri"]),
            "rollout_uri": _first(raw, ["world_model_discovery.rollout_uri", "rollout_uri"]),
        }
        return NormalizedDreamAuditCertificate(
            certificate_id=str(cert_id),
            policy_id=str(policy),
            task_id=str(task),
            failure_type=str(failure_type),
            severity=str(_first(raw, ["severity"], "material")),
            perturbation=perturbation if isinstance(perturbation, dict) else {"value": perturbation},
            minimal_failure_cost=float(minimal_cost),
            failure_rate_neighborhood=float(failure_rate),
            failure_timestep=int(failure_timestep),
            replay_command=str(replay_command),
            patch_recipe=patch_recipe if isinstance(patch_recipe, dict) else {"value": patch_recipe},
            source_path=str(source_path) if source_path else None,
            source="dreamaudit_real_artifact" if source_path and "taco_demo" not in str(source_path) else "taco_demo",
            metadata=metadata,
        )

    def get_replay_artifacts(self, certificate_id: str) -> ReplayArtifacts:
        videos = self.data_root / "videos"
        traces = self.data_root / "traces"

        def existing(base: Path, suffixes: list[str]) -> str | None:
            for suffix in suffixes:
                path = base / suffix
                if path.exists():
                    return str(path)
            return None

        return ReplayArtifacts(
            certificate_id=certificate_id,
            success_video_path=existing(videos, [f"{certificate_id}_success.mp4", f"{certificate_id}_success.gif"]),
            failure_video_path=existing(videos, [f"{certificate_id}_failure.mp4", f"{certificate_id}_failure.gif"]),
            mitigated_video_path=existing(videos, [f"{certificate_id}_mitigated.mp4", f"{certificate_id}_mitigated.gif"]),
            success_trace_path=existing(traces, [f"{certificate_id}_success.npz"]),
            failure_trace_path=existing(traces, [f"{certificate_id}_failure.npz"]),
            mitigated_trace_path=existing(traces, [f"{certificate_id}_mitigated.npz"]),
            artifact_source="taco_demo_or_real_paths",
            metadata={},
        )

    def has_real_dreamaudit_artifacts(self) -> bool:
        return any(path.exists() for path in (self.repo_root / "artifacts", self.repo_root / "outputs", self.repo_root / "runs"))
