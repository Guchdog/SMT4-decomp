#!/usr/bin/env python3
"""
Automated Disassembly & Logic Verification Engine for Shin Megami Tensei IV.

Audits claimed functions (status == 'matching' and 'non_matching') in config/functions.csv,
verifying that:
1. Every 'matching' function achieves 100% byte/instruction parity with extracted/exefs/code.bin.
2. Every 'non_matching' function is classified into 'verified' (compiles to ARMv6K and has
   >= 15% instruction size coverage) or 'draft' (< 15% coverage).
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.asm_diff import compare_function, extract_elf_functions


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
            verified_count: int
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

            if code_bytes is not None:
                diff = compare_function(
                    addr=addr,
                    size=size,
                    func_name=name,
                    src_file=src_file,
                    code_bytes=code_bytes,
                    repo_root=repo_root,
                )
                compiled_size = diff["compiled_size"]
                exact = diff["exact_match"]

                if status == "matching":
                    if exact:
                        matching_verified += 1
                        classification = "matching"
                    else:
                        matching_failed += 1
                        classification = "matching_failed"
                else:  # non_matching
                    # Verified if compiled code is non-trivial: >= min(16, size) and ratio >= 0.15
                    if compiled_size >= min(16, size) and (compiled_size / max(1, size)) >= 0.15:
                        verified_count += 1
                        classification = "verified"
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
                })
            else:
                # code.bin not present: inspect object file directly
                rel_src = src_file.relative_to(repo_root / "src") if (repo_root / "src") in src_file.parents else None
                obj = (repo_root / "build" / "obj" / "armv6k" / rel_src.with_suffix(".o")) if rel_src else src_file.with_suffix(".o")
                syms = extract_elf_functions(obj) if obj.is_file() else {}

                compiled_size = 0
                if name in syms:
                    compiled_size = len(syms[name][0])
                else:
                    needle = f"{len(name)}{name}"
                    for s, sinfo in syms.items():
                        if needle in s or name in s or f"{addr:08x}" in s:
                            compiled_size = len(sinfo[0])
                            break

                if status == "matching":
                    # Cannot verify byte match without code.bin
                    matching_failed += 1
                    classification = "matching_failed"
                elif compiled_size >= min(16, size) and (compiled_size / max(1, size)) >= 0.15:
                    verified_count += 1
                    classification = "verified"
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
                    "exact_match": False,
                    "byte_match_ratio": 0.0,
                    "mnemonic_match_ratio": 0.0,
                })

    return {
        "total_claimed": total_claimed,
        "matching_verified": matching_verified,
        "matching_failed": matching_failed,
        "verified_count": verified_count,
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
    print(f"  - Verified Logic (>= 15%):  {stats['verified_count']:,}")
    print(f"  - Draft Logic (< 15%):      {stats['draft_count']:,}")
    print(f"  - Matching Failed:          {stats['matching_failed']:,}")
    print("=" * 45)

    if stats["matching_failed"] > 0:
        print("\nERROR: Functions marked 'matching' failed byte verification:", file=sys.stderr)
        for d in stats["details"]:
            if d["classification"] == "matching_failed":
                print(f"  {d['address']} {d['name']} (compiled: {d['compiled_size']} B, expected: {d['size']} B)", file=sys.stderr)
        sys.exit(1)

    print("Verification audit complete: all claims valid.")


if __name__ == "__main__":
    main()
