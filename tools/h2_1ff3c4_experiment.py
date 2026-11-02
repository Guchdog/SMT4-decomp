"""Focused original-vs-C++ differential for H2 cursor-axis mover 0x001FF3C4."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed, load_function_addresses
from tools.build_check import compile_tu_armv6k
from tools import h2_29f278_slot_experiment as slot
from tools import h2_calc_experiment as calc

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch43_a.cpp"
LEDGER = ROOT / "config/functions.csv"
SYMBOL = "camp_func_001ff3c4"
FORWARD = "_ZN12_GLOBAL__N_112axis_forwardEPVj"
REVERSE = "_ZN12_GLOBAL__N_112axis_reverseEPVj"
ENTRY = 0x001FF3C4
SPAN = 1104
QUERY = 0x00254CA8
TEXT_BASE = 0x00100000
DATA = 0x00500000
DATA_SIZE = 0x00200000
OBJ = ROOT / "build/h2-1ff3c4-experiment/candidate.o"
STACK = 0x0F000000
STACK_SIZE = 0x20000
SP = STACK + 0x18000
RETURN = 0x01000000
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def candidate_body() -> tuple[bytes, list[dict]]:
    result = compile_tu_armv6k(SOURCE, OBJ, ROOT)
    if result.returncode:
        raise RuntimeError(f"affected TU compile failed: {result.stderr}")
    funcs = extract_elf_functions_detailed(OBJ)
    if SYMBOL not in funcs:
        raise RuntimeError(f"missing compiled symbol {SYMBOL}")
    body, relocs = funcs[SYMBOL]
    forward, forward_relocs = funcs[FORWARD]
    reverse, reverse_relocs = funcs[REVERSE]
    if forward_relocs or reverse_relocs:
        raise RuntimeError("unexpected relocations in outlined axis helpers")
    addresses = load_function_addresses(LEDGER)
    fixed = bytearray(body)
    census = []
    for reloc in relocs:
        if reloc.relocation_type != 28 or reloc.symbol_name != "ui_func_00254ca8" or reloc.explicit_addend is not None:
            raise RuntimeError(f"unexpected relocation: {reloc}")
        target = addresses.get(reloc.symbol_name)
        if target != QUERY or target & 1:
            raise RuntimeError(f"query target is not pinned ARM address: {target}")
        insn = struct.unpack_from("<I", fixed, reloc.offset)[0]
        if insn & 0x0F000000 != 0x0B000000:
            raise RuntimeError(f"relocation is not ARM BL at {reloc.offset:#x}")
        place = ENTRY + reloc.offset
        delta = target - (place + 8)
        if delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise RuntimeError("query BL out of ARM range")
        struct.pack_into("<I", fixed, reloc.offset, (insn & 0xFF000000) | ((delta >> 2) & 0xFFFFFF))
        census.append({"offset": hex(reloc.offset), "target": hex(target), "symbol": reloc.symbol_name})
    if len(census) != 10:
        raise RuntimeError(f"expected ten eager query relocations, got {len(census)}")
    # Clang outlines the two local movement routines directly after the symbol;
    # branches from the main body target these adjacent emitted functions.
    if len(fixed) != 580 or len(forward) != 152 or len(reverse) != 148:
        raise RuntimeError(f"outlined helper layout changed: {len(fixed)}/{len(forward)}/{len(reverse)}")
    census.extend([
        {"symbol": FORWARD, "offset": hex(len(fixed)), "bytes": len(forward), "relocations": 0},
        {"symbol": REVERSE, "offset": hex(len(fixed) + len(forward)), "bytes": len(reverse), "relocations": 0},
    ])
    return bytes(fixed) + forward + reverse, census


def base_fixture(name: str, *, flags=0, width=3, start=0, threshold=1,
                 count=4, index=0, offset=0, results=None) -> dict:
    b = bytearray(0x28)
    struct.pack_into("<I", b, 0x00, flags)
    b[4:12] = bytes((6, 5, 30, 31, 15, 14, 12, 13))
    for off, value in ((0x10, width), (0x14, start), (0x18, threshold),
                       (0x1c, count), (0x20, index), (0x24, offset)):
        struct.pack_into("<I", b, off, value & 0xFFFFFFFF)
    return {"name": name, "record": bytes(b).hex(), "results": list(results or [0] * 10)}


def fixtures(seed: int, samples: int) -> list[dict]:
    out = []
    zero = [0] * 10
    # Query result slots: A0,B0,A2,B2,A1,B1,C2,D2,C1,D1.
    def one(name, slot, **kw):
        r = zero.copy(); r[slot] = 1
        if slot in (6, 7): r[slot + 2] = 1
        if slot in (2, 3): r[slot + 2] = 1
        out.append(base_fixture(name, results=r, **kw))
    one("primary-forward-wrap-reset", 0, flags=2, width=3, start=2, count=3, index=2, offset=0xFFFFFFFF)
    one("primary-reverse-subs-zero", 1, flags=0, width=3, start=1, count=4, index=0, offset=0)
    one("primary-reverse-subs-overflow", 1, flags=0, width=3, start=0, count=4, index=0, offset=0x80000000)
    one("primary-reverse-offset-max", 1, flags=4, width=5, start=0, count=2, index=0, offset=0xFFFFFFFF)
    one("C-count-zero-width-greater", 6, width=7, count=0, index=9, offset=3, threshold=2)
    one("C-count-one-original-width-advance", 6, width=4, count=1, index=0, offset=0, threshold=1)
    one("C-width-greater-count", 6, width=7, count=3, index=2, offset=0, threshold=1)
    one("D-no-count-gate", 7, width=2, count=0, index=0, offset=9, threshold=1)
    one("fallback-forward-count-one", 2, width=2, start=0, count=1, index=0, offset=0)
    one("fallback-reverse-overflow", 3, width=3, start=0, count=5, index=0, offset=0x80000000)
    # Exercise query priority and status gates with simultaneous outcomes.
    for name, slots, vals in (("priority-A-over-B", (0, 1), (1, 1)),
                              ("priority-C-before-D", (6, 7), (1, 1)),
                              ("primary-over-fallback", (0, 2, 4), (1, 1, 1)),
                              ("secondary-A1-fails", (2,), (1,))):
        r = zero.copy()
        for i, v in zip(slots, vals): r[i] = v
        if r[6]: r[8] = 1
        if r[7]: r[9] = 1
        out.append(base_fixture(name, flags=1, width=3, start=1, count=4,
                                 index=1, offset=0, results=r))
    # Boundary matrix covers signed/high-bit values and all decision families.
    values = [0, 1, 2, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF]
    for slot, label in ((0, "a0"), (1, "b0"), (6, "c"), (7, "d"), (2, "a2"), (3, "b2")):
        for j, v in enumerate(values):
            r = zero.copy(); r[slot] = 1
            if slot in (6, 7): r[slot + 2] = 1
            if slot in (2, 3): r[slot + 2] = 1
            out.append(base_fixture(f"{label}-boundary-{j}", flags=j & 7,
                                    width=values[(j + 1) % len(values)],
                                    start=values[(j + 2) % len(values)],
                                    threshold=values[(j + 3) % len(values)],
                                    count=v, index=values[(j + 4) % len(values)],
                                    offset=values[(j + 5) % len(values)], results=r))
    rng = random.Random(seed)
    for i in range(samples):
        r = [rng.randrange(2) for _ in range(10)]
        out.append(base_fixture(f"seeded-{i}", flags=rng.randrange(8),
                                width=rng.getrandbits(32), start=rng.getrandbits(32),
                                threshold=rng.getrandbits(32), count=rng.getrandbits(32),
                                index=rng.getrandbits(32), offset=rng.getrandbits(32),
                                results=r))
    return out


def execute(image: bytes, record: bytes, results: list[int]) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    code_size = (len(image) + 0xFFF) & ~0xFFF
    uc.mem_map(TEXT_BASE, code_size)
    uc.mem_write(TEXT_BASE, image)
    uc.mem_map(DATA, DATA_SIZE)
    uc.mem_map(STACK, STACK_SIZE)
    uc.mem_map(RETURN, 0x1000)
    obj = DATA + 0x1000
    uc.mem_write(obj, record)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    uc.reg_write(arm.UC_ARM_REG_R0, obj)
    calls, writes = [], []
    idx = [0]

    def code_hook(machine, address, size, _):
        if address == QUERY:
            args = tuple(machine.reg_read(r) for r in (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2))
            if idx[0] >= len(results):
                raise RuntimeError("too many query calls")
            value = results[idx[0]] & 0xFFFFFFFF
            calls.append({"args": list(args), "result": value})
            idx[0] += 1
            machine.reg_write(arm.UC_ARM_REG_R0, value)
            machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))
        elif address == RETURN:
            machine.emu_stop()

    def mem_hook(machine, access, address, size, value, _):
        if obj <= address < obj + 0x28:
            writes.append({"offset": address - obj, "size": size, "value": value & ((1 << (8 * size)) - 1)})

    invalid = []
    def invalid_hook(machine, access, address, size, value, _):
        invalid.append({"access": access, "address": hex(address), "size": size,
                        "pc": hex(machine.reg_read(arm.UC_ARM_REG_PC))})
        return False

    uc.hook_add(unicorn.UC_HOOK_CODE, code_hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, mem_hook)
    uc.hook_add(unicorn.UC_HOOK_MEM_INVALID, invalid_hook)
    error = None
    try:
        uc.emu_start(ENTRY, RETURN, count=100000)
    except unicorn.UcError as e:
        error = str(e)
    return {
        "error": error,
        "invalid": invalid,
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "record": bytes(uc.mem_read(obj, 0x28)).hex(),
        "ret": uc.reg_read(arm.UC_ARM_REG_R0),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "saved": [uc.reg_read(r) for r in (arm.UC_ARM_REG_R4, arm.UC_ARM_REG_R5,
                    arm.UC_ARM_REG_R6, arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R8,
                    arm.UC_ARM_REG_R9, arm.UC_ARM_REG_R10, arm.UC_ARM_REG_R11)],
        "calls": calls, "writes": writes,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--seed", type=int, default=20261107)
    ap.add_argument("--samples", type=int, default=100)
    args = ap.parse_args()
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned original image hash mismatch")
    body, relocs = candidate_body()
    if len(body) > SPAN:
        raise SystemExit("candidate exceeds original function slot")
    overlay = bytearray(original)
    off = ENTRY - TEXT_BASE
    overlay[off:off + len(body)] = body
    fixtureset = fixtures(args.seed, args.samples)
    rows, failures = [], []
    for case in fixtureset:
        record = bytes.fromhex(case["record"])
        a = execute(original, record, case["results"])
        b = execute(bytes(overlay), record, case["results"])
        equal = a == b
        row = {"name": case["name"], "pass": equal, "original": a, "candidate": b}
        rows.append(row)
        if not equal: failures.append(case["name"])
    caller_rows = []
    caller_scenarios = [
        ("title-calc-stable-cursor", calc.Scenario("cursor-stable", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("title-calc-active-cursor-no-input", calc.Scenario("cursor-active", 1, row=1),
         dict(first_threshold=2, second_threshold=2, first_base=1, second_base=1,
              total=3, input_state=0, counts={})),
        ("title-calc-cursor-logical-bits", calc.Scenario("cursor-bits", 1, row=1),
         dict(first_threshold=1, second_threshold=1, first_base=1, second_base=1,
              total=3, input_state=0x1F8, counts={})),
        ("title-calc-h2-initialized-cursor", calc.Scenario("cursor-h2-setup", 1, row=1),
         dict(first_threshold=3, second_threshold=1, first_width=3, second_width=1,
              first_start=2, first_count=3, second_count=1, first_flags=6,
              second_flags=6, first_base=0, second_base=0, total=3,
              first_ids=(6, 5, 0x20, 0x20, 15, 14, 0x20, 0x20),
              second_ids=(3, 4, 0x20, 0x20, 12, 13, 0x20, 0x20),
              input_state=0, counts={})),
    ]
    for label, scenario, cursor in caller_scenarios:
        left = slot.CalcWithActualCursor(original, scenario=scenario)
        right = slot.CalcWithActualCursor(bytes(overlay), scenario=scenario)
        left.initialize_cursor(**cursor)
        right.initialize_cursor(**cursor)
        a, b = left.run(), right.run()
        error = calc.compare(a, b)
        caller_rows.append({"label": label, "pass": error is None, "error": error,
                            "original_return": hex(a["return"]),
                            "trace_count": len(a["trace"])})
    # A deliberately wrong first query target must alter the ordered call trace.
    bad = bytearray(overlay)
    first_call = relocs[0]
    place = ENTRY + int(first_call["offset"], 16)
    word = struct.unpack_from("<I", bad, place - TEXT_BASE)[0]
    delta = (QUERY + 4) - (place + 8)
    struct.pack_into("<I", bad, place - TEXT_BASE,
                     (word & 0xFF000000) | ((delta >> 2) & 0x00FFFFFF))
    neg_case = fixtureset[0]
    neg_original = execute(original, bytes.fromhex(neg_case["record"]), neg_case["results"])
    neg_candidate = execute(bytes(bad), bytes.fromhex(neg_case["record"]), neg_case["results"])
    negative_control_detected = neg_original != neg_candidate
    args.output.mkdir(parents=True, exist_ok=True)
    report = {
        "target": hex(ENTRY), "source_sha256": sha(SOURCE.read_bytes()),
        "image_sha256": sha(original), "candidate_body_sha256": sha(body),
        "candidate_body_bytes": len(body), "relocations": relocs,
        "seed": args.seed, "samples": args.samples,
        "direct_cases": len(rows), "passed": len(rows) - len(failures),
        "failures": failures, "cases": rows,
        "caller_compositions": caller_rows,
        "wrong_query_target_control_detected": negative_control_detected,
    }
    out = args.output / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("target", "candidate_body_bytes", "direct_cases", "passed", "failures", "caller_compositions", "wrong_query_target_control_detected")}, indent=2))
    return 1 if failures or any(not row["pass"] for row in caller_rows) or not negative_control_detected else 0


if __name__ == "__main__":
    raise SystemExit(main())
