#!/usr/bin/env python3
"""Offline pinned-ARM differential for H2 cursor setup 0x0029FAE8."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import struct
from pathlib import Path
import sys

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch40_a.cpp"
ADDRESS, SPAN, CODE_BASE = 0x0029FAE8, 452, 0x00100000
CODE_SIZE = 0x00378000
BLOCK, STACK, STACK_SIZE, RETURN = 0x00500000, 0x00600000, 0x10000, 0x00700000
SYMBOL = "camp_func_0029fae8"
HOOKS = {0x002C615C, 0x00296F18, 0x00296EF8, 0x003170A0}
ARG_COUNTS = {0x002C615C: 2, 0x00296F18: 3, 0x00296EF8: 5, 0x003170A0: 5}
CALLEE = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def function_addresses() -> dict[str, int]:
    found: dict[str, set[int]] = {}
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            name, address = row.get("name", "").strip(), row.get("address", "").strip()
            if name and address:
                found.setdefault(name, set()).add(int(address, 16))
    return {name: next(iter(values)) for name, values in found.items() if len(values) == 1}


def compile_and_resolve(out: Path) -> tuple[bytes, list[str], Path, list[dict]]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch40_a.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "candidate TU compilation failed")
    entry = extract_elf_functions_detailed(obj).get(SYMBOL)
    if entry is None:
        raise ValueError(f"candidate symbol {SYMBOL!r} was not emitted")
    body, relocations = entry
    if not body or len(body) > SPAN or len(body) % 4:
        raise ValueError(f"candidate invalid size: {len(body)} bytes (slot {SPAN})")

    addresses = function_addresses()
    resolved = bytearray(body)
    details = []
    for reloc in relocations:
        if reloc.relocation_type not in (28, 29) or reloc.explicit_addend is not None:
            raise ValueError(f"unsupported/interworking relocation: {reloc}")
        target = addresses.get(reloc.symbol_name)
        if target is None:
            raise ValueError(f"callee is absent or ambiguous in ledger: {reloc.symbol_name}")
        if target & 1:
            raise ValueError(f"Thumb/interworking target requires separate validation: {reloc}")
        offset = reloc.offset
        if offset < 0 or offset % 4 or offset + 4 > len(body):
            raise ValueError(f"invalid branch relocation offset: {reloc}")
        insn = struct.unpack_from("<I", body, offset)[0]
        expected_opcode = 0xEB000000 if reloc.relocation_type == 28 else 0xEA000000
        if insn & 0xFF000000 != expected_opcode:
            raise ValueError(f"relocation does not point at ARM {'BL' if reloc.relocation_type == 28 else 'B'}: {reloc}, {insn:#010x}")
        place = ADDRESS + offset
        displacement = target - (place + 8)
        if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
            raise ValueError(f"ARM branch out of range/alignment: {reloc} -> {target:#x}")
        encoded = (displacement >> 2) & 0x00FFFFFF
        struct.pack_into("<I", resolved, offset, (insn & 0xFF000000) | encoded)
        details.append({"offset": offset, "type": reloc.relocation_type,
                        "symbol": reloc.symbol_name, "target": f"0x{target:08X}",
                        "instruction": "BL" if reloc.relocation_type == 28 else "B"})
    return bytes(resolved), list(result.args), obj, details


def stage(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(original) > CODE_SIZE:
        raise ValueError(f"unexpected code image length {len(original):#x}")
    padding = struct.pack("<I", 0xE320F000)
    payload = body + padding * ((SPAN - len(body)) // 4)
    off = ADDRESS - CODE_BASE
    staged = bytearray(original)
    staged[off:off + SPAN] = payload
    staged = bytes(staged)
    ips = encode_ips([(off, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("slot IPS roundtrip failed")
    if original[:off] != staged[:off] or original[off + SPAN:] != staged[off + SPAN:]:
        raise AssertionError("candidate changed bytes outside its original slot")
    return staged, ips


def verify_interworking(original: bytes, relocations: list[dict]) -> list[dict]:
    verified = []
    for item in relocations:
        target = int(item["target"], 16)
        if item["type"] != 28 or item["instruction"] != "BL":
            raise ValueError(f"unexpected non-linking/interworking relocation: {item}")
        if target & 3:
            raise ValueError(f"ARM BL target is not word aligned: {item}")
        offset = target - CODE_BASE
        if offset < 0 or offset + 4 > len(original):
            raise ValueError(f"branch target lies outside pinned image: {item}")
        entry_word = struct.unpack_from("<I", original, offset)[0]
        if entry_word in (0x00000000, 0xFFFFFFFF):
            raise ValueError(f"branch target entry is not executable ARM code: {item}")
        verified.append({**item, "target_entry_word": f"0x{entry_word:08X}",
                         "target_bit0": target & 1, "arm_word_alignment": True})
    return verified


def execute(image: bytes, args: tuple[int, int, int, int, int, int], seed: int) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(BLOCK, 0x1000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    cursor = bytes((seed * 29 + i * 53 + 0x37) & 0xFF for i in range(0x80))
    uc.mem_write(BLOCK, cursor)
    writes: list[tuple[int, int, int]] = []
    calls: list[tuple[int, tuple[int, ...]]] = []

    def on_write(_uc, _access, address, size, value, _data):
        if BLOCK <= address < BLOCK + 0x100:
            writes.append((address - BLOCK, size, value & 0xFFFFFFFF))

    def on_code(_uc, address, _size, _data):
        if address in HOOKS:
            arg_count = ARG_COUNTS[address]
            regs = tuple(_uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                         for i in range(min(arg_count, 4)))
            sp = _uc.reg_read(arm.UC_ARM_REG_SP)
            stack_count = max(0, arg_count - 4)
            stack_args = tuple(struct.unpack("<I", _uc.mem_read(sp + 4 * i, 4))[0]
                               for i in range(stack_count))
            calls.append((address, regs, stack_args))

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    saved = {name: (0xA5000000 + i * 0x01010101) & 0xFFFFFFFF
             for i, (name, _) in enumerate(CALLEE)}
    for name, reg in CALLEE:
        uc.reg_write(reg, saved[name])
    sp = STACK + STACK_SIZE // 2
    uc.reg_write(arm.UC_ARM_REG_SP, sp)
    uc.mem_write(sp, struct.pack("<II", args[3] & 0xFFFFFFFF, args[4] & 0xFFFFFFFF))
    uc.reg_write(arm.UC_ARM_REG_R0, BLOCK)
    for index, value in enumerate(args[:3], 1):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), value & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    fault = None
    try:
        uc.emu_start(ADDRESS, RETURN, count=100000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "return": uc.reg_read(arm.UC_ARM_REG_R0),
            "cursor": bytes(uc.mem_read(BLOCK, 0x80)), "writes": tuple(writes),
            "calls": tuple(calls), "saved": tuple(uc.reg_read(reg) for _, reg in CALLEE),
            "expected_saved": tuple(saved[name] for name, _ in CALLEE),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP), "entry_sp": sp}


def equivalent(ref: dict, got: dict) -> str | None:
    for field in ("fault", "return", "cursor", "writes", "calls", "saved", "sp"):
        if ref[field] != got[field]:
            return f"{field} differs"
    if got["fault"] is not None:
        return "candidate faulted"
    if got["saved"] != got["expected_saved"] or got["sp"] != got["entry_sp"]:
        return "candidate ABI preservation differs"
    return None


def cases(seed: int, count: int) -> list[tuple[int, int, int, int, int, int]]:
    fixed = [
        (0, 3, 1, 0, 1), (-1, 3, 1, 0, 1),
        (1, 1, 1, 0, 1), (3, 3, 1, 0, 1),
        (8, 3, 1, 0, 1), (4, 2, 2, 0, 1),
        (4, 1, 3, 0, 1), (6, 1, 1, 1, 1),
        (6, 1, 1, 0, 0), (7, 5, 1, 1, 1),
        (2, 1, 7, 0, 1), (0x7FFFFFFF, 1, 1, 0, 1),
    ]
    rng = random.Random(seed)
    for _ in range(count):
        total = rng.randint(1, 100)
        visible = rng.randint(1, total + 10)
        cols = rng.randint(1, 8)
        wrap, repeat = rng.randint(0, 1), rng.randint(0, 1)
        fixed.append((total, visible, cols, wrap, repeat))
    return fixed


def check_h2_composition(result: dict) -> dict:
    expected_calls = (
        (0x002C615C, (3, 1), ()),
        (0x00296F18, (BLOCK, 3, 3), ()),
        (0x00296EF8, (BLOCK, 6, 5, 32), (32,)),
        (0x003170A0, (BLOCK, 15, 14, 32), (32,)),
        (0x00296F18, (BLOCK + 0x28, 1, 1), ()),
        (0x00296EF8, (BLOCK + 0x28, 3, 4, 32), (32,)),
        (0x003170A0, (BLOCK + 0x28, 12, 13, 32), (32,)),
    )
    if result["calls"] != expected_calls:
        raise AssertionError(f"H2 helper sequence/arguments differ: {result['calls']}")
    axis0 = struct.unpack_from("<10I", result["cursor"], 0)
    axis1 = struct.unpack_from("<10I", result["cursor"], 0x28)
    expected_axis0 = (6, 0x20200506, 0x20200E0F, 0, 3, 1, 3, 3, 0, 0)
    expected_axis1 = (6, 0x20200403, 0x20200D0C, 0, 1, 1, 1, 1, 0, 0)
    if axis0 != expected_axis0 or axis1 != expected_axis1:
        raise AssertionError(f"H2 final axes differ: {axis0!r} / {axis1!r}")
    return {"helper_sequence": "passed", "axis0_words": [f"0x{x:08X}" for x in axis0],
            "axis1_words": [f"0x{x:08X}" for x in axis1],
            "return": f"0x{result['return']:08X}"}


def negative_control(original: bytes, body: bytes, relocation_details: list[dict],
                     seed: int) -> dict:
    target = next((item for item in relocation_details
                   if item["symbol"] == "ui_func_00296ef8"), None)
    if target is None:
        raise AssertionError("negative control could not find the axis-ID call")
    changed = bytearray(body)
    offset = target["offset"]
    old_word = struct.unpack_from("<I", changed, offset)[0]
    place = ADDRESS + offset
    displacement = 0x00296F18 - (place + 8)
    struct.pack_into("<I", changed, offset,
                     (old_word & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF))
    mutant_image, _ = stage(original, bytes(changed))
    reference = execute(original, (3, 3, 1, 0, 1), seed)
    mutant = execute(mutant_image, (3, 3, 1, 0, 1), seed)
    mismatch = equivalent(reference, mutant)
    if mismatch is None:
        raise AssertionError("negative control failed to detect a wrong helper target")
    return {"mutated_call_offset": offset, "from": "0x00296EF8",
            "to": "0x00296F18", "detected_difference": mismatch}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261102)
    parser.add_argument("--random-cases", type=int, default=32)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise ValueError("pinned original image hash mismatch")
    body, command, obj, relocations = compile_and_resolve(out / "compile")
    interworking = verify_interworking(original, relocations)
    staged, ips = stage(original, body)
    (out / "candidate.ips").write_bytes(ips)
    (out / "candidate.bin").write_bytes(staged)

    results = []
    failures = []
    test_cases = cases(args.seed, args.random_cases)
    h2_details = None
    for index, values in enumerate(test_cases):
        reference = execute(original, values, index + 1)
        candidate = execute(staged, values, index + 1)
        mismatch = equivalent(reference, candidate)
        if values == (3, 3, 1, 0, 1) and h2_details is None:
            h2_details = check_h2_composition(candidate)
        results.append({"case": index, "args": list(values), "seed": index + 1,
                        "result": "pass" if mismatch is None else mismatch,
                        "ref_return": f"0x{reference['return']:08X}",
                        "candidate_return": f"0x{candidate['return']:08X}",
                        "call_count": len(candidate["calls"])})
        if mismatch:
            failures.append(results[-1])
    if h2_details is None:
        raise AssertionError("H2 TitleConfig argument case was not present")
    negative = negative_control(original, body, relocations, 0x5A)
    report = {
        "target": "0x0029FAE8", "original_image_sha256": sha(original),
        "original_span_sha256": sha(original[ADDRESS - CODE_BASE:ADDRESS - CODE_BASE + SPAN]),
        "candidate_source_sha256": sha(SOURCE.read_bytes()),
        "candidate_object_sha256": sha(obj.read_bytes()), "candidate_body_sha256": sha(body),
        "candidate_body_size": len(body), "slot_size": SPAN,
        "candidate_relocations_resolved": relocations,
        "candidate_arm_interworking": interworking, "compiler_command": command,
        "seed": args.seed, "case_count": len(results), "cases": results,
        "h2_caller_composition": h2_details, "negative_control": negative,
        "failures": failures, "status": "passed" if not failures else "failed",
        "scope": "direct wrapper differential and H2 setup args; pinned sibling helpers; aligned ordinary RAM; no task/input/audio lifecycle",
    }
    encoded = json.dumps(report, indent=2) + "\n"
    (out / "report.json").write_text(encoded, encoding="utf-8")
    print(f"candidate={len(body)}/{SPAN} bytes; relocations={len(relocations)}; cases={len(results)}; failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
