"""Normalize real DreamAudit certificates for TACO."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from taco_demo.dreamaudit_adapter import DreamAuditAdapter
from taco_demo.schemas import write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    adapter = DreamAuditAdapter(data_root=args.output_dir.parent)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    written = 0
    for path in sorted(args.input_dir.rglob("*.json")):
        if args.limit is not None and written >= args.limit:
            break
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(raw, dict) or not any(k in raw for k in ("certificate_id", "patch_recipe", "minimality", "simulator_validation")):
            continue
        cert = adapter.normalize_certificate(raw, path)
        out = args.output_dir / f"{cert.certificate_id}.json"
        if out.exists() and not args.overwrite:
            continue
        write_json(cert, out)
        written += 1
    print(f"Normalized {written} DreamAudit certificate(s) into {args.output_dir}")


if __name__ == "__main__":
    main()

