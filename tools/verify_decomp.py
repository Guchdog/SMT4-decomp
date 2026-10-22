#!/usr/bin/env python3
"""
Machine-code matching and compiled-size coverage audit for Shin Megami Tensei IV.

Audits claimed functions (status == 'matching' and 'non_matching') in config/functions.csv,
verifying that:
1. Every 'matching' function achieves 100% byte/instruction parity with extracted/exefs/code.bin.
2. Every 'non_matching' function is classified into 'compiled' (compiles to ARMv6K and has
   >= 15% size coverage) or 'draft' (< 15% coverage). Neither verifies logic.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.asm_diff import compare_function


def audit_claimed_functions(
    functions_csv: Path = Path("config/functions.csv"),
    repo_root: Path = Path("."),
    code_path: Path | None = None,
) -> dict:
    """Audit all claimed decompiled functions against ARMv6K compilation and code.bin.

    Returns:
        dict with keys:
            total_claimed: int
            matching_verified: int
            matching_failed: int
            compiled_count: int (size threshold only, no semantic verification)
            verified_count: int (legacy alias for compiled_count)
            compilation_failed: int
            draft_count: int
            details: list[dict]
    """
    repo_root = Path(repo_root).resolve()
    functions_csv = Path(functions_csv)
    if not functions_csv.is_absolute():
        functions_csv = repo_root / functions_csv

    if code_path is None:
        code_path = repo_root / "extracted" / "exefs" / "code.bin"
    else:
        code_path = Path(code_path)
        if not code_path.is_absolute():
            code_path = repo_root / code_path

    code_bytes = code_path.read_bytes() if (code_path and code_path.is_file()) else None

    total_claimed = 0
    matching_verified = 0
    matching_failed = 0
    verified_count = 0
    draft_count = 0
    compilation_failed = 0
    details: list[dict] = []

    with open(functions_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            status = row["status"].strip()
            if status not in ("matching", "non_matching"):
                continue

            total_claimed += 1
            addr = int(row["address"], 16)
            size = int(row["size"])
            name = row["name"].strip()
            src_file = repo_root / row["src_file"].strip()

            # compare_function also ensures fresh compilation when code.bin is
            # absent. Empty expected bytes permit size inspection, never a match.
            diff = compare_function(
                addr=addr,
                size=size,
                func_name=name,
                src_file=src_file,
                code_bytes=code_bytes if code_bytes is not None else b"",
                repo_root=repo_root,
            )
            compiled_size = diff["compiled_size"]
            exact = diff["exact_match"]

            if compiled_size <= 0:
                compilation_failed += 1
                classification = "compilation_failed"
                if status == "matching":
                    matching_failed += 1
            elif status == "matching":
                if exact:
                    matching_verified += 1
                    classification = "matching"
                else:
                    matching_failed += 1
                    classification = "matching_failed"
            else:  # non_matching
                # Size coverage alone does not establish semantic equivalence.
                if compiled_size >= min(16, size) and (compiled_size / max(1, size)) >= 0.15:
                    verified_count += 1
                    classification = "compiled"
                else:
                    draft_count += 1
                    classification = "draft"

            details.append({
                "address": row["address"],
                "name": name,
                "status": status,
                "classification": classification,
                "size": size,
                "compiled_size": compiled_size,
                "exact_match": exact,
                "byte_match_ratio": diff["byte_match_ratio"],
                "mnemonic_match_ratio": diff["mnemonic_match_ratio"],
                "diagnostics": diff["diff_lines"] if compiled_size <= 0 else [],
            })

    return {
        "total_claimed": total_claimed,
        "matching_verified": matching_verified,
        "matching_failed": matching_failed,
        "verified_count": verified_count,
        "compiled_count": verified_count,
        "compilation_failed": compilation_failed,
        "draft_count": draft_count,
        "details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit and verify claimed functions in SMT4 decompilation"
    )
    parser.add_argument("--functions", type=Path, default=Path("config/functions.csv"))
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--root", type=Path, default=Path("."))
    args = parser.parse_args()

    print("Auditing claimed functions...")
    stats = audit_claimed_functions(args.functions, args.root, args.code)

    print("\nDecompilation Verification Audit Summary")
    print("=" * 45)
    print(f"Total Claimed Functions:   {stats['total_claimed']:,}")
    print(f"  - Matching (Byte-for-Byte): {stats['matching_verified']:,}")
    print(f"  - Compiled Coverage (>=15%): {stats['compiled_count']:,} (logic unverified)")
    print(f"  - Draft Logic (< 15%):      {stats['draft_count']:,}")
    print(f"  - Matching Failed:          {stats['matching_failed']:,}")
    print(f"  - Compilation Failed:       {stats['compilation_failed']:,}")
    print("=" * 45)

    if stats["matching_failed"] > 0 or stats["compilation_failed"] > 0:
        print("\nERROR: Function compilation or byte verification failed:", file=sys.stderr)
        for d in stats["details"]:
            if d["classification"] in ("matching_failed", "compilation_failed"):
                print(f"  {d['address']} {d['name']} (compiled: {d['compiled_size']} B, expected: {d['size']} B)", file=sys.stderr)
                for diagnostic in d.get("diagnostics", []):
                    print(f"    {diagnostic}", file=sys.stderr)
        sys.exit(1)

    print("Audit complete: exact-match claims checked; remaining functions classified by compiled size only.")


if __name__ == "__main__":
    main()
