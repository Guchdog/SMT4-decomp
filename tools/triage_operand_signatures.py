#!/usr/bin/env python3
"""Suggest repeated ARM/Thumb leaf shapes using normalized operands.

This is inventory triage only. A shared normalized signature is not evidence
that functions have the same semantics, ABI contract, or callers.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import re
import sys

import capstone
import capstone.arm as capstone_arm

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.find_candidates import find_leaf_candidates

TEXT = 0x00100000
THUMB_RANGE = (0x00100048, 0x00101300)
_CONDITION_SUFFIXES = (
    "eq", "ne", "hs", "cs", "lo", "cc", "mi", "pl", "vs", "vc",
    "hi", "ls", "ge", "lt", "gt", "le",
)
_SIMPLE_INTEGER_MNEMONICS = {
    "adc", "add", "adr", "and", "asr", "bfc", "bfi", "bic", "bx",
    "clz", "cmn", "cmp", "eor", "ldr", "ldrb", "ldrd", "ldrh",
    "ldrsb", "ldrsh", "lsl", "lsr", "mla", "mls", "mov", "movt",
    "movw", "mul", "mvn", "orr", "rev", "rev16", "revsh", "rbit",
    "ror", "rsb", "rsc", "sbc", "sbfx", "sdiv", "smull", "str",
    "strb", "strd", "strh", "sub", "teq", "tst", "ubfx", "udiv",
    "umull", "uxtb", "uxth", "sxtb", "sxth",
}
_FLAG_SETTING_MNEMONICS = {
    "adcs", "adds", "ands", "asrs", "bics", "eors", "lsls", "lsrs",
    "movs", "mvns", "orrs", "rors", "rsbs", "sbcs", "subs",
}
_CONDITION_NAMES = {
    value: name.removeprefix("ARM_CC_").lower()
    for name, value in vars(capstone_arm).items()
    if name.startswith("ARM_CC_") and isinstance(value, int)
}
_SHIFT_NAMES = {
    value: name.removeprefix("ARM_SFT_").lower()
    for name, value in vars(capstone_arm).items()
    if name.startswith("ARM_SFT_") and isinstance(value, int)
}
_VFP_GROUPS = tuple(
    value for name in ("ARM_GRP_DPVFP", "ARM_GRP_FPARMV8", "ARM_GRP_FPVMLX", "ARM_GRP_NEON")
    if isinstance((value := getattr(capstone_arm, name, None)), int)
)
_KNOWN_SYMBOL_RE = re.compile(r"(?<![A-Za-z0-9_])candidate_([0-9a-fA-F]{8})(?![A-Za-z0-9_])")


def _decoder(address: int) -> capstone.Cs:
    mode = capstone.CS_MODE_THUMB if THUMB_RANGE[0] <= address < THUMB_RANGE[1] else capstone.CS_MODE_ARM
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, mode)
    decoder.detail = True
    return decoder


def _register_class(name: str) -> str:
    name = name.lower()
    if name in {"sp", "lr", "pc", "cpsr", "spsr"}:
        return f"reg:{name}"
    if name.startswith("r") and name[1:].isdigit():
        return "reg:gpr"
    return f"reg:{name}"


def _shift_shape(operand) -> str:
    shift = getattr(operand, "shift", None)
    if shift is None or not shift.type:
        return ""
    amount = "zero" if shift.value == 0 else "nonzero"
    return f"/shift:{_SHIFT_NAMES.get(shift.type, f'type{shift.type}')}:amount-{amount}"


def _operand_shape(instruction, operand) -> str:
    if operand.type == capstone.arm.ARM_OP_REG:
        return _register_class(instruction.reg_name(operand.reg)) + _shift_shape(operand)
    if operand.type == capstone.arm.ARM_OP_IMM:
        return "imm"
    if operand.type == capstone.arm.ARM_OP_MEM:
        memory = operand.mem
        base = _register_class(instruction.reg_name(memory.base)) if memory.base else "none"
        index = _register_class(instruction.reg_name(memory.index)) if memory.index else "none"
        offset = "zero" if memory.disp == 0 else "nonzero"
        sign = "minus" if memory.disp < 0 else "plus"
        index_sign = "minus" if getattr(operand, "subtracted", False) else "plus"
        scale = abs(getattr(memory, "scale", 1))
        scale_shape = "unit" if scale in (0, 1) else "scaled"
        index_shift = "zero" if getattr(memory, "lshift", 0) == 0 else "nonzero"
        return (f"mem(base={base},index={index}:{index_sign},disp={offset}:{sign},"
                f"scale={scale_shape},shift={index_shift})")
    if operand.type == capstone.arm.ARM_OP_CIMM:
        return "coproc-imm"
    if operand.type == capstone.arm.ARM_OP_PIMM:
        return "coproc-reg"
    return f"operand:{operand.type}"


def normalized_instruction(instruction) -> str:
    """Normalize values while preserving operand/addressing/condition classes."""
    operands = ",".join(_operand_shape(instruction, operand) for operand in instruction.operands)
    condition = _CONDITION_NAMES.get(instruction.cc, f"cc{instruction.cc}")
    flags = "s" if getattr(instruction, "update_flags", False) else "nos"
    writeback = "wb" if getattr(instruction, "writeback", False) else "nowb"
    return f"{instruction.mnemonic.lower()}[{condition};{flags};{writeback}]({operands})"


def _decode_candidate(candidate: dict, code_bytes: bytes) -> tuple[list, list[str]] | None:
    address = int(candidate["address"], 16)
    size = int(candidate["size"])
    offset = address - TEXT
    if offset < 0 or offset + size > len(code_bytes):
        return None
    raw = code_bytes[offset:offset + size]
    instructions = list(_decoder(address).disasm(raw, address))
    if not instructions or sum(item.size for item in instructions) != size:
        return None
    if any(not _is_simple_integer_instruction(instruction) for instruction in instructions):
        return None
    if any(instruction.mnemonic.lower().startswith(("v", "f"))
           or any(instruction.group(group) for group in _VFP_GROUPS)
           for instruction in instructions):
        return None
    return instructions, [normalized_instruction(item) for item in instructions]


def _is_simple_integer_instruction(instruction) -> bool:
    """Keep the triage input to common scalar integer and integer-memory ops."""
    mnemonic = instruction.mnemonic.lower()
    if instruction.cc not in (0, 15):
        for suffix in _CONDITION_SUFFIXES:
            if mnemonic.endswith(suffix):
                mnemonic = mnemonic[:-len(suffix)]
                break
    return (mnemonic in _SIMPLE_INTEGER_MNEMONICS
            or mnemonic in _FLAG_SETTING_MNEMONICS)


def group_operand_shapes(
    candidates: list[dict], code_bytes: bytes,
    known_candidate_addresses: set[str] | None = None,
) -> dict[str, object]:
    """Group integer leaf shapes and optionally annotate known source coverage."""
    grouped: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    accepted = 0
    rejected = 0
    for candidate in candidates:
        decoded = _decode_candidate(candidate, code_bytes)
        if decoded is None:
            rejected += 1
            continue
        instructions, normalized = decoded
        accepted += 1
        address = int(candidate["address"], 16)
        item = dict(candidate)
        item["mode"] = "thumb" if THUMB_RANGE[0] <= address < THUMB_RANGE[1] else "arm"
        item["normalized_instructions"] = normalized
        item["instructions"] = [
            f"{instruction.mnemonic.lower()} {instruction.op_str}".strip()
            for instruction in instructions
        ]
        grouped[tuple(normalized)].append(item)

    groups = []
    for signature, items in grouped.items():
        if len(items) < 2:
            continue
        ordered = sorted(items, key=lambda item: int(item["address"], 16))
        group = {"signature": list(signature), "count": len(ordered), "candidates": ordered}
        if known_candidate_addresses is None:
            group["covered_candidates"] = None
            group["uncovered_candidates"] = None
        else:
            covered = [item["address"].lower() for item in ordered
                       if _normalize_address(item["address"]) in known_candidate_addresses]
            uncovered = [item["address"].lower() for item in ordered
                         if _normalize_address(item["address"]) not in known_candidate_addresses]
            group["covered_candidates"] = covered
            group["uncovered_candidates"] = uncovered
        groups.append(group)
    groups.sort(key=lambda group: (-group["count"], group["signature"]))
    return {
        "schema": 1,
        "candidate_count": len(candidates),
        "decoded_integer_leaf_count": accepted,
        "rejected_or_unsupported_count": rejected,
        "repeated_signature_count": len(groups),
        "repeated_candidate_count": sum(group["count"] for group in groups),
        "groups": groups,
        "limitations": [
            "Suggestions only: normalized instruction shape does not establish semantic equivalence, ABI compatibility, or caller compatibility.",
            "Immediate values and general-purpose register identities are abstracted; memory base/index classes, displacement presence, condition codes, flag updates, and writeback remain visible.",
            "Only complete ARM/Thumb leaf ranges from the asm-backed candidate finder using a small scalar-integer instruction allowlist are considered; VFP/NEON and other instructions are excluded.",
        ],
    }


def _normalize_address(address: str) -> str:
    return f"{int(address, 16):08x}"


def find_known_candidate_addresses(directory: Path) -> set[str]:
    """Collect candidate_<8 hex digits> symbols from candidate-named C++ files."""
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f"known-candidate directory does not exist: {directory}")
    addresses: set[str] = set()
    for source in sorted(directory.rglob("*candidate*.cpp")):
        content = source.read_text(encoding="utf-8", errors="replace")
        addresses.update(match.group(1).lower() for match in _KNOWN_SYMBOL_RE.finditer(content))
    return addresses


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--functions", type=Path, default=ROOT / "config/functions.csv")
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--max-size", type=int, default=64)
    parser.add_argument("--limit", type=int, default=0, help="Candidate limit; 0 means unlimited")
    parser.add_argument("--category")
    parser.add_argument("--status", action="append",
                        choices=("todo", "stub", "non_matching", "matching"))
    parser.add_argument(
        "--known-candidate-dir", type=Path,
        help="Annotate each repeated group against candidate_<8-hex> symbols found recursively in *candidate*.cpp files",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    if not args.code.is_file():
        parser.error(f"code image not found: {args.code}")
    code_bytes = args.code.read_bytes()
    candidates = find_leaf_candidates(
        functions_csv=args.functions, code_bytes=code_bytes,
        max_size=args.max_size, limit=args.limit, category=args.category,
        statuses=tuple(args.status or ("matching",)), asm_backed_only=True,
        repo_root=ROOT,
    )
    known_addresses = None
    if args.known_candidate_dir is not None:
        try:
            known_addresses = find_known_candidate_addresses(args.known_candidate_dir)
        except ValueError as error:
            parser.error(str(error))
    report = group_operand_shapes(candidates, code_bytes, known_addresses)
    output = json.dumps(report, indent=2)
    if args.output is None:
        print(output)
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
        print(f"Wrote {args.output}")


if __name__ == "__main__":
    main()
