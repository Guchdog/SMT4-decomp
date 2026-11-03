#!/usr/bin/env python3
"""Pinned ARM differential for TitleConfig sprite setup 0x002BDB2C."""
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
SOURCE = ROOT / "src/engine/leaf_batch30_c.cpp"
ADDRESS, SPAN, CODE_BASE = 0x002BDB2C, 152, 0x00100000
CODE_SIZE = 0x00378000
BLOCK, STACK, STACK_SIZE, RETURN = 0x00500000, 0x00600000, 0x10000, 0x00700000
SYMBOL = "camp_func_002bdb2c"
ZERO = 0x002C4B30
CALLER_START, CALLER_STOP = 0x002F4D6C, 0x002F4D8C
CALLEE = [(f"r{i}", getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 11)]
VFP_CALLEE = [(f"d{i}", getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ledger_addresses() -> dict[str, int]:
    found: dict[str, set[int]] = {}
    with (ROOT / "config/functions.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            name, address = row.get("name", "").strip(), row.get("address", "").strip()
            if name and address:
                found.setdefault(name, set()).add(int(address, 16))
    return {name: next(iter(values)) for name, values in found.items() if len(values) == 1}


def compile_body(out: Path) -> tuple[bytes, list, list[str], Path]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch30_c.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "candidate TU compilation failed")
    entry = extract_elf_functions_detailed(obj).get(SYMBOL)
    if entry is None:
        raise ValueError(f"candidate symbol {SYMBOL!r} not found")
    body, relocations = entry
    if not body or len(body) > SPAN or len(body) % 4:
        raise ValueError(f"candidate does not fit its 152-byte slot: {len(body)}")
    if len(relocations) != 1:
        raise ValueError(f"expected only AsdMem_Zero branch relocation, found {relocations}")
    return body, list(relocations), list(result.args), obj


def resolve_calls(body: bytes, relocations: list, original: bytes) -> tuple[bytes, list[dict]]:
    addresses = ledger_addresses()
    resolved = bytearray(body)
    report = []
    for reloc in relocations:
        if reloc.relocation_type != 28 or reloc.explicit_addend is not None:
            raise ValueError(f"unsupported/interworking relocation: {reloc}")
        target = addresses.get(reloc.symbol_name)
        if target is None or target & 3:
            raise ValueError(f"missing, ambiguous, or unaligned ARM target: {reloc}")
        offset = reloc.offset
        word = struct.unpack_from("<I", body, offset)[0]
        if offset % 4 or word & 0xFF000000 != 0xEB000000:
            raise ValueError(f"R_ARM_CALL is not an ARM BL: {reloc}, {word:#x}")
        displacement = target - (ADDRESS + offset + 8)
        if displacement % 4 or not -(1 << 25) <= displacement < (1 << 25):
            raise ValueError(f"ARM BL out of range: {reloc}")
        struct.pack_into("<I", resolved, offset,
                         (word & 0xFF000000) | ((displacement >> 2) & 0xFFFFFF))
        target_word = struct.unpack_from("<I", original, target - CODE_BASE)[0]
        if target_word in (0, 0xFFFFFFFF):
            raise ValueError(f"target entry is not pinned ARM code: {target:#x}")
        report.append({"offset": offset, "type": reloc.relocation_type,
                       "symbol": reloc.symbol_name, "target": f"0x{target:08X}",
                       "bit0": target & 1, "entry_word": f"0x{target_word:08X}"})
    return bytes(resolved), report


def stage(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(original) > CODE_SIZE:
        raise ValueError(f"unexpected code image length {len(original):#x}")
    fill = struct.pack("<I", 0xE320F000)
    payload = body + fill * ((SPAN - len(body)) // 4)
    off = ADDRESS - CODE_BASE
    staged = bytearray(original)
    staged[off:off + SPAN] = payload
    staged = bytes(staged)
    ips = encode_ips([(off, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("one-slot IPS replay failed")
    if original[:off] != staged[:off] or original[off + SPAN:] != staged[off + SPAN:]:
        raise AssertionError("staged replacement changed bytes outside the target slot")
    return staged, ips


def setup_memory(uc, seed: int, case: dict) -> tuple[int, int]:
    uc.mem_map(BLOCK, 0x1000)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    raw = bytes((seed * 31 + i * 43 + 0x59) & 0xFF for i in range(0x1000))
    uc.mem_write(BLOCK, raw)
    sprite = BLOCK + 0x200
    group = sprite - 0x20  # exact TitleConfig topology: the 0x20-byte group ends at sprite
    # Poison the entire output node after writing descriptor data in the preceding group.
    group_words = case["group_words"]
    for i, value in enumerate(group_words):
        uc.mem_write(group + 4 * i, struct.pack("<I", value & 0xFFFFFFFF))
    uc.mem_write(sprite, bytes([case["poison"] & 0xFF]) * 0x8C)
    return sprite, group


def run(image: bytes, case: dict, seed: int, *, caller_slice: bool = False) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    sprite, group = setup_memory(uc, seed, case)
    write_events = []
    zero_calls = []
    start_sp = STACK + STACK_SIZE // 2
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_FPSCR, 0)
    for i, (_, reg) in enumerate(CALLEE):
        uc.reg_write(reg, 0xA5000000 | (i * 0x01010101))
    for i, (_, reg) in enumerate(VFP_CALLEE):
        uc.reg_write(reg, 0x1122334455667700 + i)
    uc.reg_write(arm.UC_ARM_REG_D8, 0xD8A5C17E12345678)
    uc.reg_write(arm.UC_ARM_REG_SP, start_sp)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    uc.reg_write(arm.UC_ARM_REG_S0, case["scale_bits"] & 0xFFFFFFFF)

    def on_write(_uc, _access, address, size, value, _data):
        if sprite <= address < sprite + 0x8C:
            write_events.append((address - sprite, size, value & ((1 << (size * 8)) - 1)))

    def on_code(machine, address, _size, _data):
        if address == ZERO:
            zero_calls.append((machine.reg_read(arm.UC_ARM_REG_R0),
                               machine.reg_read(arm.UC_ARM_REG_R1),
                               machine.reg_read(arm.UC_ARM_REG_SP)))

    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    if caller_slice:
        work = sprite - 0x5C
        uc.reg_write(arm.UC_ARM_REG_R4, work)
        begin, until = CALLER_START, CALLER_STOP
    else:
        uc.mem_write(start_sp, struct.pack("<I", case["panel"] & 0xFFFFFFFF))
        uc.reg_write(arm.UC_ARM_REG_R0, sprite)
        uc.reg_write(arm.UC_ARM_REG_R1, case["type"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R2, case["index"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R3, group)
        begin, until = ADDRESS, RETURN

    fault = None
    try:
        uc.emu_start(begin, until, count=100000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {
        "fault": fault,
        "return": uc.reg_read(arm.UC_ARM_REG_R0),
        "sprite": bytes(uc.mem_read(sprite, 0x8C)),
        "group": bytes(uc.mem_read(group, 0x20)),
        "writes": tuple(write_events),
        "zero_calls": tuple(zero_calls),
        "r4_r10": tuple(uc.reg_read(reg) for _, reg in CALLEE),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "entry_sp": start_sp,
        "d8_d15": tuple(uc.reg_read(reg) for _, reg in VFP_CALLEE),
        "s0": uc.reg_read(arm.UC_ARM_REG_S0),
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
    }


def compare(ref: dict, got: dict) -> str | None:
    for field in ("fault", "return", "sprite", "group", "r4_r10", "sp", "d8_d15"):
        if ref[field] != got[field]:
            return f"{field} differs"
    if tuple(call[:2] for call in ref["zero_calls"]) != tuple(call[:2] for call in got["zero_calls"]):
        return "zero-helper arguments differ"
    if got["fault"] is not None:
        return "candidate faulted"
    if got["sp"] != got["entry_sp"]:
        return "candidate SP differs from entry"
    return None


def direct_cases(seed: int, random_cases: int) -> list[dict]:
    one = struct.unpack("<I", struct.pack("<f", 1.0))[0]
    fixed = [
        {"type": 0x2F, "index": 0, "panel": 0xC9, "scale_bits": one,
         "group_words": (0, 0, 0, 0x00407EC6, 0, 0, 0, 0), "poison": 0xA5},
        {"type": 0, "index": 0xFFFFFFFF, "panel": 0, "scale_bits": 0,
         "group_words": (0, 0, 0, 1, 2, 3, 4, 5), "poison": 0xD3},
        {"type": 0xFFFFFFFF, "index": 0x12345678, "panel": 0x100C9,
         "scale_bits": 0xBF800000, "group_words": (0, 0, 0, 0x87654321, 4, 5, 6, 7), "poison": 0x71},
        {"type": 0x2F, "index": 1, "panel": 0xFFFF, "scale_bits": 0x7FC12345,
         "group_words": (0, 0, 0, 0, 0xFFFFFFFF, 0x80000000, 0x01020304, 0xAABBCCDD), "poison": 0x3C},
    ]
    rng = random.Random(seed)
    for _ in range(random_cases):
        fixed.append({"type": rng.getrandbits(32), "index": rng.getrandbits(32),
                      "panel": rng.getrandbits(32), "scale_bits": rng.getrandbits(32),
                      "group_words": tuple(rng.getrandbits(32) for _ in range(8)),
                      "poison": rng.randrange(1, 256)})
    return fixed


def h2_summary(candidate: dict, expected_case: dict) -> dict:
    if candidate["return"] != BLOCK + 0x200 + 0x8C:
        raise AssertionError("H2 caller raw r0 is not sprite+0x8C")
    block = candidate["sprite"]
    words = {
        "type": struct.unpack_from("<I", block, 0)[0],
        "index": struct.unpack_from("<I", block, 4)[0],
        "sentinel": struct.unpack_from("<I", block, 8)[0],
        "scale_bits": struct.unpack_from("<I", block, 0x20)[0],
        "panel": struct.unpack_from("<H", block, 0x38)[0],
        "group": struct.unpack_from("<I", block, 0x48)[0],
        "group_copy": [struct.unpack_from("<I", block, off)[0]
                       for off in (0x4C, 0x58, 0x64, 0x70, 0x78)],
        "flags": list(block[0x86:0x8B]),
    }
    expected = {"type": 0x2F, "index": 0, "sentinel": 0xFFFFFFFF,
                "scale_bits": 0x3F800000, "panel": 0xC9,
                "group": BLOCK + 0x200 - 0x20,
                "group_copy": list(expected_case["group_words"][3:8]),
                "flags": [1] * 5}
    if words != expected:
        raise AssertionError(f"H2 sprite fields differ: {words!r}")
    return words


def make_zero_mutant(original: bytes, body: bytes, relocation, seed: int) -> dict:
    changed = bytearray(body)
    offset = relocation.offset
    word = struct.unpack_from("<I", changed, offset)[0]
    target = 0x002C3344  # only clears the 32-byte sprite group; the node remains poisoned
    disp = target - (ADDRESS + offset + 8)
    struct.pack_into("<I", changed, offset,
                     (word & 0xFF000000) | ((disp >> 2) & 0xFFFFFF))
    image, _ = stage(original, bytes(changed))
    case = direct_cases(seed, 0)[0]
    return run(image, case, seed)


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
        raise ValueError("pinned original image SHA-256 mismatch")
    body, relocations, command, obj = compile_body(out / "compile")
    staged_body, branch_report = resolve_calls(body, relocations, original)
    staged, ips = stage(original, staged_body)
    (out / "candidate.ips").write_bytes(ips)
    (out / "candidate.bin").write_bytes(staged)

    all_cases = direct_cases(args.seed, args.random_cases)
    results, failures = [], []
    for i, case in enumerate(all_cases):
        ref = run(original, case, i + 1)
        got = run(staged, case, i + 1)
        mismatch = compare(ref, got)
        results.append({"case": i, "input": case, "status": "pass" if mismatch is None else mismatch,
                        "return": f"0x{got['return']:08X}", "zero_calls": [list(x) for x in got["zero_calls"]]})
        if mismatch:
            failures.append(results[-1])

    caller_case = {"group_words": (0, 0, 0, 0x00407EC6, 0, 0, 0, 0),
                   "panel": 0xC9, "type": 0x2F, "index": 0,
                   "scale_bits": 0x3F800000, "poison": 0xA5}
    caller_ref = run(original, caller_case, 0xC9, caller_slice=True)
    caller_got = run(staged, caller_case, 0xC9, caller_slice=True)
    caller_mismatch = compare(caller_ref, caller_got)
    if caller_mismatch:
        failures.append({"caller_slice": caller_mismatch})
    h2 = h2_summary(caller_got, caller_case)

    mutant = make_zero_mutant(original, body, relocations[0], 0x5A)
    mutant_ref = run(original, direct_cases(0x5A, 0)[0], 0x5A)
    mutant_difference = compare(mutant_ref, mutant)
    if mutant_difference is None:
        raise AssertionError("wrong zero-helper negative control was not detected")

    report = {
        "target": "0x002BDB2C", "original_image_sha256": sha(original),
        "original_span_sha256": sha(original[ADDRESS - CODE_BASE:ADDRESS - CODE_BASE + SPAN]),
        "candidate_source_sha256": sha(SOURCE.read_bytes()),
        "candidate_object_sha256": sha(obj.read_bytes()),
        "candidate_body_sha256": sha(staged_body), "candidate_body_size": len(staged_body),
        "slot_size": SPAN, "resolved_branches": branch_report, "compiler_command": command,
        "seed": args.seed, "case_count": len(results), "cases": results,
        "caller_slice": {"start": f"0x{CALLER_START:08X}", "stop": f"0x{CALLER_STOP:08X}",
                         "status": "pass" if caller_mismatch is None else caller_mismatch,
                         "return": f"0x{caller_got['return']:08X}", "fields": h2},
        "negative_control": {"wrong_zero_target": "0x002C3344",
                              "difference_detected": mutant_difference},
        "failures": failures, "status": "passed" if not failures else "failed",
        "domain": "ordinary aligned RAM; distinct non-overlapping 0x8C sprite node and 0x20 group descriptor; original zero helper; VFP scale bits preserved; no resource/rendering behavior",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"candidate={len(staged_body)}/{SPAN} bytes; branches={len(branch_report)}; cases={len(results)}; caller={'pass' if not caller_mismatch else caller_mismatch}; failures={len(failures)}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
