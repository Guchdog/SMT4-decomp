#!/usr/bin/env python3
"""
Leaf Function Candidate Finder for Shin Megami Tensei IV (CTR-P-AMXE).

Scans config/functions.csv for unexplored ('todo') functions, slices their machine
code from extracted/exefs/code.bin, disassembles with Capstone, and identifies
pure leaf functions (no calls, no syscalls, no external branches) sorted by size.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import re
import sys
from collections.abc import MutableMapping
import capstone

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def is_leaf_instruction(
    insn: capstone.CsInsn,
    func_addr: int,
    func_size: int,
    allow_internal_branch: bool = False,
) -> bool:
    """Check if an instruction is permissible in a leaf function."""
    m = insn.mnemonic.lower()
    op = insn.op_str.strip().lower()

    # Subroutine calls: bl, blx
    if m.startswith("bl") or m.startswith("blx"):
        return False

    # Syscalls: svc, swi
    if m in ("svc", "swi"):
        return False

    # Indirect jumps/returns: bx rX. Only bx lr is permitted as a return.
    if m.startswith("bx"):
        if op != "lr":
            return False

    # Branch instructions
    branch_mnemonics = {
        "b", "beq", "bne", "bcs", "bcc", "bmi", "bpl", "bvs", "bvc",
        "bhi", "bls", "bge", "blt", "bgt", "ble", "bhs", "blo", "cbz", "cbnz",
    }
    if m in branch_mnemonics or (m.startswith("b.") and len(m) <= 4):
        if not allow_internal_branch:
            return False
        # If operand has a target address, check whether it stays within the function
        target = None
        if op.startswith("#0x") or op.startswith("#"):
            try:
                target = int(op.lstrip("#"), 16 if "0x" in op else 10)
            except ValueError:
                return False
        elif op.startswith("0x"):
            try:
                target = int(op, 16)
            except ValueError:
                return False

        if target is not None:
            if not (func_addr <= target < func_addr + func_size):
                # Target is outside function boundary: tail call or jump outside
                return False
        else:
            # Unresolved or non-immediate branch target
            return False

    return True


def is_terminal_return(insn: capstone.CsInsn) -> bool:
    """Return whether *insn* is an unconditional ARM/Thumb function return.

    A leaf candidate still needs an explicit way to return to its caller.  Merely
    disassembling a range without calls is not sufficient: alignment words and
    fragments such as ``mov r0, r0`` otherwise look like one-instruction leaf
    functions.  Keep this deliberately conservative; unusual exception returns
    can be investigated manually instead of being ranked as easy candidates.
    """
    mnemonic = insn.mnemonic.lower()
    operands = insn.op_str.replace(" ", "").lower()

    if mnemonic == "bx" and operands == "lr":
        return True
    if mnemonic == "mov" and operands == "pc,lr":
        return True
    if mnemonic == "pop" and "pc" in operands:
        return True
    if mnemonic.startswith("ldm") and mnemonic in {"ldm", "ldmia", "ldmfd"}:
        return operands.startswith("sp!,") and "pc" in operands
    if mnemonic == "ldr" and operands.startswith("pc,[sp]"):
        return True
    return False


_DECOMP_START_RE = re.compile(r"(?m)^\s*//\s*DECOMP_FUNC\(")
_DECOMP_MARKER_RE = re.compile(
    r"(?m)^\s*//\s*DECOMP_FUNC\(0x([0-9a-f]{8}),\s*(\d+)\)\s*$",
    flags=re.IGNORECASE,
)
_ASM_BLOCK_RE = re.compile(
    r"\b(?:__asm__|asm)\b|\.incbin\b|\.word\b|\.inst\b|"
    r"__attribute__\s*\(\([^)]*\bnaked\b"
)


def _asm_backed_index(source: Path) -> dict[tuple[int, int], bool]:
    """Index each DECOMP_FUNC block in one source file with a single scan."""
    if not source.is_file():
        return {}

    text = source.read_text(encoding="utf-8")
    markers = list(_DECOMP_START_RE.finditer(text))
    result: dict[tuple[int, int], bool] = {}
    for index, marker in enumerate(markers):
        end = markers[index + 1].start() if index + 1 < len(markers) else len(text)
        parsed_marker = _DECOMP_MARKER_RE.match(text, marker.start())
        if parsed_marker is None:
            continue
        block = text[marker.end():end]
        key = (int(parsed_marker.group(1), 16), int(parsed_marker.group(2)))
        # The previous row-local search selected the first exact marker if a
        # source happened to contain duplicates; preserve that behavior.
        if key not in result:
            result[key] = _ASM_BLOCK_RE.search(block) is not None
    return result


def is_asm_backed_row(
    row: dict,
    repo_root: Path = Path("."),
    source_index_cache: MutableMapping[Path, dict[tuple[int, int], bool]] | None = None,
) -> bool:
    """Return whether a ledger entry is still implemented with inline assembly.

    Source files frequently contain a mixture of reconstructed C++ and exact
    assembly wrappers, so classify the block attached to the row's exact
    ``DECOMP_FUNC`` marker rather than the whole translation unit.
    """
    src_file = row.get("src_file", "").strip()
    if not src_file:
        return False

    path = Path(src_file)
    if not path.is_absolute():
        path = Path(repo_root) / path
    address = int(row["address"], 16)
    size = int(row["size"])
    source = path.resolve()
    if source_index_cache is None:
        index = _asm_backed_index(source)
    else:
        if source not in source_index_cache:
            source_index_cache[source] = _asm_backed_index(source)
        index = source_index_cache[source]
    return index.get((address, size), False)


def find_leaf_candidates(
    functions_csv: Path = Path("config/functions.csv"),
    code_bytes: bytes = b"",
    max_size: int = 64,
    limit: int = 50,
    category: str | None = None,
    allow_internal_branch: bool = False,
    statuses: tuple[str, ...] = ("todo",),
    asm_backed_only: bool = False,
    repo_root: Path = Path("."),
) -> list[dict]:
    """Scans functions_csv for candidate leaf functions up to max_size.

    Returns list of dicts with:
        address: str (hex)
        size: int
        category: str
        name: str
        instruction_count: int
        terminal_instruction: str
    sorted by size ascending, then instruction_count, then address.
    """
    functions_csv = Path(functions_csv)
    if not code_bytes:
        return []

    cs_arm = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    cs_thumb = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_THUMB)

    candidates: list[dict] = []
    source_index_cache: dict[Path, dict[tuple[int, int], bool]] = {}

    with open(functions_csv, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_status = row["status"].strip()
            if row_status not in statuses:
                continue

            size = int(row["size"])
            if size <= 0 or size > max_size:
                continue

            row_cat = row["category"].strip()
            if category and row_cat.lower() != category.lower():
                continue

            if asm_backed_only and not is_asm_backed_row(
                row,
                repo_root=repo_root,
                source_index_cache=source_index_cache,
            ):
                continue

            addr_str = row["address"].strip()
            addr = int(addr_str, 16)
            offset = addr - 0x00100000

            if offset < 0 or offset + size > len(code_bytes):
                continue

            raw = code_bytes[offset : offset + size]
            thumb = 0x00100048 <= addr < 0x00101300
            cs = cs_thumb if thumb else cs_arm
            insns = list(cs.disasm(raw, addr))
            if not insns:
                continue

            # Must disassemble into full instructions without residual unparsed bytes
            if sum(i.size for i in insns) != size:
                continue

            # Check that every instruction satisfies leaf criteria and that the
            # supplied range actually ends in an explicit, unconditional return.
            # This filters padding and fall-through fragments from the shortlist.
            if (
                all(
                    is_leaf_instruction(
                        insn,
                        addr,
                        size,
                        allow_internal_branch=allow_internal_branch,
                    )
                    for insn in insns
                )
                and is_terminal_return(insns[-1])
            ):
                candidates.append({
                    "address": addr_str,
                    "size": size,
                    "status": row_status,
                    "category": row_cat,
                    "name": row["name"].strip(),
                    "src_file": row["src_file"].strip(),
                    "instruction_count": len(insns),
                    "terminal_instruction": (
                        f"{insns[-1].mnemonic} {insns[-1].op_str}".strip()
                    ),
                })

    candidates.sort(key=lambda c: (c["size"], c["instruction_count"], int(c["address"], 16)))
    if limit is not None and limit > 0:
        candidates = candidates[:limit]

    return candidates


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find candidate leaf functions in SMT4 code.bin"
    )
    parser.add_argument("--functions", type=Path, default=Path("config/functions.csv"), help="Path to functions.csv")
    parser.add_argument("--code", type=Path, default=Path("extracted/exefs/code.bin"), help="Path to code.bin")
    parser.add_argument("--max-size", type=int, default=64, help="Maximum function size in bytes (default: 64)")
    parser.add_argument("--limit", type=int, default=50, help="Maximum number of candidates to show (default: 50)")
    parser.add_argument("--category", type=str, default=None, help="Filter candidates by subsystem category")
    parser.add_argument("--allow-internal-branches", action="store_true", help="Allow internal branch instructions")
    parser.add_argument(
        "--status",
        action="append",
        choices=("todo", "stub", "non_matching", "matching"),
        help="Ledger status to search; repeat for more than one (default: todo)",
    )
    parser.add_argument(
        "--asm-backed-only",
        action="store_true",
        help="Only show entries whose DECOMP_FUNC block still uses inline assembly",
    )
    args = parser.parse_args()

    if not args.code.is_file():
        print(f"Error: {args.code} not found.", file=sys.stderr)
        sys.exit(1)

    code_bytes = args.code.read_bytes()
    candidates = find_leaf_candidates(
        functions_csv=args.functions,
        code_bytes=code_bytes,
        max_size=args.max_size,
        limit=args.limit,
        category=args.category,
        allow_internal_branch=args.allow_internal_branches,
        statuses=tuple(args.status or ("todo",)),
        asm_backed_only=args.asm_backed_only,
        repo_root=_REPO_ROOT,
    )

    statuses = ",".join(args.status or ("todo",))
    print(
        f"Found {len(candidates)} leaf candidates (max size: {args.max_size} B, "
        f"category: {args.category or 'any'}, status: {statuses}, "
        f"asm-backed only: {args.asm_backed_only}):"
    )
    print(f"{'#':<4} | {'Address':<10} | {'Size':>5} | {'Insns':>5} | {'Return':<16} | {'Category':<10} | {'Name'}")
    print("-" * 84)
    for idx, c in enumerate(candidates, 1):
        print(
            f"{idx:<4} | {c['address']:<10} | {c['size']:>3} B | "
            f"{c['instruction_count']:>5} | {c['terminal_instruction']:<16} | "
            f"{c['category']:<10} | {c['name']}"
        )


if __name__ == "__main__":
    main()
