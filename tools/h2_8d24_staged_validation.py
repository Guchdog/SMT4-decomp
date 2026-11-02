#!/usr/bin/env python3
"""Differentially validate the final staged 0x002B8D24 image offline."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.h2_8d24_experiment import validate_staged_image


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--base-image", type=Path,
                        help="known base image; bytes outside the function slot must match it")
    args = parser.parse_args()
    validate_staged_image(args.image, args.base_image)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
