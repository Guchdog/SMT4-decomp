#!/usr/bin/env python3
"""Group small leaf candidates by ARM/Thumb mnemonic sequence.

These are triage groups only. Matching opcode names do not establish the same
semantics: operands, flags, memory contracts, and caller use still need review.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

import capstone

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.find_candidates import find_leaf_candidates


def group_candidates_by_mnemonics(
    candidates: list[dict], code_bytes: bytes
) -> dict[str, object]:
    """Return repeated opcode-sequence groups without conflating operands."""
    cs_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs_thumb = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)
    grouped: dict[tuple[str, ...], list[dict]] = defaultdict(list)

    for candidate in candidates:
        address = int(candidate["address"], 16)
        size = int(candidate["size"])
        offset = address - 0x00100000
        if offset < 0 or offset + size > len(code_bytes):
            continue
        raw = code_bytes[offset:offset + size]
        thumb = 0x00100048 <= address < 0x00101300
        instructions = list((cs_thumb if thumb else cs_arm).disasm(raw, address))
        if sum(instruction.size for instruction in instructions) != size:
            continue

        signature = tuple(instruction.mnemonic.lower() for instruction in instructions)
        item = dict(candidate)
        item["instructions"] = [
            f"{instruction.mnemonic} {instruction.op_str}".strip()
            for instruction in instructions
        ]
        grouped[signature].append(item)

    repeated = [
        {
            "mnemonics": list(signature),
            "count": len(items),
            "candidates": sorted(items, key=lambda item: int(item["address"], 16)),
        }
        for signature, items in grouped.items()
        if len(items) > 1
    ]
    repeated.sort(key=lambda group: (-group["count"], group["mnemonics"]))
    return {
        "candidate_count": sum(len(items) for items in grouped.values()),
        "unique_signatures": len(grouped),
        "repeated_signature_count": len(repeated),
        "repeated_candidate_count": sum(group["count"] for group in repeated),
        "groups": repeated,
        "note": (
            "Mnemonic sequences are triage hints only. Different operands, flags, "
            "memory behavior, and callers may make functions semantically distinct."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Group small asm-backed leaf candidates by opcode sequence"
    )
    parser.add_argument("--functions", type=Path, default=Path("config/functions.csv"))
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"))
    parser.add_argument("--max-size", type=int, default=64)
    parser.add_argument("--limit", type=int, default=0, help="Candidate scan limit; 0 means unlimited")
    parser.add_argument("--category", type=str)
    parser.add_argument(
        "--status",
        action="append",
        choices=("todo", "stub", "non_matching", "matching"),
        help="Ledger status to search (default: matching)",
    )
    parser.add_argument("--include-non-asm", action="store_true")
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()

    if not args.code.is_file():
        parser.error(f"code image not found: {args.code}")
    code_bytes = args.code.read_bytes()
    candidates = find_leaf_candidates(
        functions_csv=args.functions,
        code_bytes=code_bytes,
        max_size=args.max_size,
        limit=args.limit,
        category=args.category,
        statuses=tuple(args.status or ("matching",)),
        asm_backed_only=not args.include_non_asm,
        repo_root=_REPO_ROOT,
    )
    report = group_candidates_by_mnemonics(candidates, code_bytes)
    output = json.dumps(report, indent=2)
    if args.output is None:
        print(output)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
