"""Record or synthesize a replay video for a DreamAudit certificate."""

from __future__ import annotations

import argparse
import os
import subprocess
from pathlib import Path

from taco_demo.dreamaudit_adapter import DreamAuditAdapter
from taco_demo.schemas import read_json
from taco_demo.video_utils import create_demo_video


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--mode", choices=["success", "failure", "mitigated"], required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    raw = read_json(args.certificate)
    cert = DreamAuditAdapter().normalize_certificate(raw, args.certificate)
    if cert.replay_command and os.environ.get("TACO_ALLOW_REAL_REPLAY") == "1":
        print(f"Running DreamAudit replay command: {cert.replay_command}")
        try:
            subprocess.run(cert.replay_command, shell=True, check=True)
        except Exception as exc:
            print(f"Real replay unavailable, generating fallback video instead: {exc}")
    path = create_demo_video(args.out, cert.certificate_id, args.mode, cert.failure_type)
    print(f"Wrote replay video placeholder to {path}")


if __name__ == "__main__":
    main()

