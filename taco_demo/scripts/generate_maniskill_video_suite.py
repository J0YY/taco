"""Generate the supplemental ManiSkill/RMA-style video evidence suite."""

from __future__ import annotations

import argparse
from pathlib import Path

from taco_demo.maniskill_suite import SUITE_SIZE, write_maniskill_suite


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--count", type=int, default=SUITE_SIZE)
    parser.add_argument("--data-root", type=Path, default=Path(__file__).resolve().parents[1] / "data")
    args = parser.parse_args()
    manifest = write_maniskill_suite(args.data_root, force=args.force, count=args.count)
    print(f"Generated ManiSkill/RMA video suite manifest at {manifest}")


if __name__ == "__main__":
    main()
