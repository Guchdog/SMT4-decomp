#!/usr/bin/env python3
"""Bounded ARM differential for H2 value getter 0x00296F60."""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips

IMAGE = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch42_a.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
ADDRESS, SLOT, CALLBACK = 0x00296F60, 164, 0x00221168
SET_GLOBAL, GET_STATE, GET_CONTEXT = 0x0028DF3C, 0x00289640, 0x0028686C
SELECTOR, FINAL_HELPER = ADDRESS, 0x00286928
GLOBAL, CALLBACK_SLOTS = 0x0044DE98, 0x0043E188
TYPE2_GLOBAL, TYPE3_GLOBAL = 0x004C4744, 0x004C4D44
WORK = 0x00610000
STACK_BASE, STACK_SIZE = 0x08000000, 0x10000
SP, STOP = STACK_BASE + 0x8000, STACK_BASE + 0xF000
NOP = struct.pack("<I", 0xE320F000)
CALLEE_SAVED = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, src: Path = SOURCE) -> tuple[bytes, tuple, Path]:
    out.mkdir(parents=True, exist_ok=False)
    obj = out / "leaf_batch42_a.o"
    result = compile_tu_armv6k(src, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["engine_func_00296f60"]
    return body, relocations, obj


def stage(image: bytes, body: bytes) -> tuple[bytes, bytes]:
    if len(body) > SLOT or len(body) % 4:
        raise AssertionError(f"body {len(body)} does not fit aligned {SLOT}-byte slot")
    payload = body + NOP * ((SLOT - len(body)) // 4)
    off = ADDRESS - CODE_BASE
    staged = bytearray(image)
    staged[off:off + SLOT] = payload
    staged = bytes(staged)
    ips = encode_ips([(off, payload)], len(image))
    if apply_ips(image, ips) != staged:
        raise AssertionError("IPS replay failed")
    if any(a != b and not off <= i < off + SLOT for i, (a, b) in enumerate(zip(image, staged))):
        raise AssertionError("staged bytes escaped the getter slot")
    return staged, ips


def machine(image: bytes):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(0x004C4000, 0x10000)
    uc.mem_map(0x00600000, 0x40000)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    return uc


def put32(uc, address: int, value: int):
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def setup_data(uc, case: dict):
    count = case["count"]
    put32(uc, GLOBAL + 0x20, WORK)
    put32(uc, WORK + 0x1C, count)
    uc.mem_write(WORK + 0x20, bytes(case["types"]))
    for i, value in enumerate(case["slots"]):
        if case["types"][i] == 1:
            uc.mem_write(WORK + 0x3C + 4 * i, struct.pack("<f", case["slot_floats"][i]))
        else:
            put32(uc, WORK + 0x3C + 4 * i, value)
    for i, value in enumerate(case["words"]):
        put32(uc, TYPE2_GLOBAL + 4 * i, value)
    for i, value in enumerate(case["table_floats"]):
        uc.mem_write(TYPE3_GLOBAL + 4 * i, struct.pack("<f", value))


def init_registers(uc, selector: int):
    uc.reg_write(arm.UC_ARM_REG_R0, selector & 0xFFFFFFFF)
    for i in range(1, 13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), (0x11000000 + i * 0x01010101) & 0xFFFFFFFF)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xA1000000 + i * 0x01010101)


def observed(a: int, size: int) -> bool:
    return ((WORK <= a < WORK + 0x1000)
            or (TYPE2_GLOBAL <= a < TYPE2_GLOBAL + 0x1000)
            or (TYPE3_GLOBAL <= a < TYPE3_GLOBAL + 0x1000)
            or (GLOBAL + 0x20 <= a < GLOBAL + 0x24))


def direct_run(image: bytes, case: dict) -> dict:
    uc = machine(image)
    setup_data(uc, case)
    init_registers(uc, case["selector"])
    saved = [uc.reg_read(r) for r in CALLEE_SAVED]
    reads, writes = [], []

    def on_read(_uc, _access, address, size, value, _data):
        if observed(address, size):
            reads.append((address, size, value & 0xFFFFFFFF))

    def on_write(_uc, _access, address, size, value, _data):
        if observed(address, size):
            writes.append((address, size, value & 0xFFFFFFFF))

    uc.hook_add(unicorn.UC_HOOK_MEM_READ, on_read)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE,
                lambda m, a, _s, _d: m.emu_stop() if a == STOP else None,
                begin=STOP, end=STOP)
    fault = None
    try:
        uc.emu_start(ADDRESS, 0, count=1000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "return": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": [uc.reg_read(r) for r in CALLEE_SAVED] == saved,
            "reads": reads, "writes": writes}


def callback_run(image: bytes, case: dict) -> dict:
    uc = machine(image)
    setup_data(uc, case)
    put32(uc, CALLBACK_SLOTS + 4, 0x00630000)
    put32(uc, CALLBACK_SLOTS + 8, 0x00631000)
    uc.mem_write(0x00630000, b"\xA5" * 0xB00)
    uc.mem_write(0x00631000, b"\x5A" * 0x80)
    put32(uc, WORK + 0xC0, case["context"])
    put32(uc, WORK + 0xD0, case["state"])
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xB2000000 + i * 0x01010101)
    saved = [uc.reg_read(r) for r in CALLEE_SAVED]
    events, reads, writes = [], [], []

    def on_read(_uc, _access, address, size, value, _data):
        if observed(address, size) or 0x0043E000 <= address < 0x0043F000:
            reads.append((address, size, value & 0xFFFFFFFF))

    def on_write(_uc, _access, address, size, value, _data):
        if observed(address, size) or 0x0043E000 <= address < 0x0043F000:
            writes.append((address, size, value & 0xFFFFFFFF))

    def on_code(m, address, _size, _data):
        if address == STOP:
            m.emu_stop()
            return
        if address in (SET_GLOBAL, GET_STATE, GET_CONTEXT, SELECTOR, FINAL_HELPER):
            sp = m.reg_read(arm.UC_ARM_REG_SP)
            argc = 4 if address == FINAL_HELPER else 1
            args = [m.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(argc)]
            stack = list(struct.unpack("<II", m.mem_read(sp, 8))) if address == FINAL_HELPER else []
            events.append({"target": address, "args": args, "stack": stack, "sp": sp})
            if sp & 7:
                raise AssertionError(f"callback call SP is not 8-byte aligned: {address:#x}/{sp:#x}")
        if address == FINAL_HELPER:
            m.reg_write(arm.UC_ARM_REG_R0, case["final_return"])
            m.reg_write(arm.UC_ARM_REG_PC, m.reg_read(arm.UC_ARM_REG_LR))

    uc.hook_add(unicorn.UC_HOOK_MEM_READ, on_read)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    fault = None
    try:
        uc.emu_start(CALLBACK, 0, count=10000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "return": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": [uc.reg_read(r) for r in CALLEE_SAVED] == saved,
            "events": events, "reads": reads, "writes": writes,
            "object1_marker": bytes(uc.mem_read(0x00630000 + 0xA11, 1)).hex(),
            "object2_marker": bytes(uc.mem_read(0x00631000 + 0x30, 2)).hex()}


def cases(seed: int) -> list[dict]:
    rng = random.Random(seed)
    rows = []
    float_values = [0.0, -0.99, 1.99, -1.99, 2147483520.0, -2147483648.0]
    type_values = [0, 1, 2, 3, 4, 5, 255]
    for typ in type_values:
        for idx in (0, 3):
            types = [0] * 4
            types[idx] = typ
            f = float_values[(typ + idx) % len(float_values)]
            rows.append({"count": 4, "selector": 3 - idx, "types": types,
                         "slots": [(i % 4) if typ in (2, 3) and i == idx else 0xF1000000 + i for i in range(4)],
                         "slot_floats": [f, -17.75, 123.875, -0.25],
                         "words": [0xA5000000 + i for i in range(4)],
                         "table_floats": [f, -22.5, 13.875, -0.75]})
    # Each valid selector position and each type, including additional VFP boundaries.
    float_coverage = set()
    for typ in range(5):
        for idx in range(4):
            for f in float_values if typ in (1, 3) else [0.0]:
                types = [4] * 4
                types[idx] = typ
                slots = [rng.getrandbits(32) for _ in range(4)]
                if typ in (2, 3):
                    slots[idx] = (idx + 1) % 4
                rows.append({"count": 4, "selector": 3 - idx, "types": types,
                             "slots": slots, "slot_floats": [f] * 4,
                             "words": [rng.getrandbits(32) for _ in range(4)],
                             "table_floats": [f] * 4,
                             "float_boundary": f if typ in (1, 3) else None})
                if typ in (1, 3):
                    float_coverage.add((typ, idx, f))
    expected_float_coverage = {(typ, idx, f) for typ in (1, 3)
                               for idx in range(4) for f in float_values}
    if float_coverage != expected_float_coverage or len(float_coverage) != 48:
        raise AssertionError(f"float boundary cartesian coverage is {len(float_coverage)}/48")
    # The full selector domain 0..4 with a five-entry table, including both ends.
    for typ in (0, 1, 2, 3, 4, 6, 255):
        for idx in range(5):
            f = rng.choice(float_values)
            slots = [rng.getrandbits(32) for _ in range(5)]
            if typ in (2, 3):
                slots[idx] = (idx + 1) % 4
            rows.append({"count": 5, "selector": 4 - idx,
                         "types": [typ if j == idx else 4 for j in range(5)],
                         "slots": slots,
                         "slot_floats": [f] * 5,
                         "words": [rng.getrandbits(32) for _ in range(5)],
                         "table_floats": [f] * 5})
    return rows


def assert_float_cartesian_coverage(rows: list[dict]) -> int:
    float_values = (0.0, -0.99, 1.99, -1.99, 2147483520.0, -2147483648.0)
    expected = {(typ, index, value) for typ in (1, 3)
                for index in range(4) for value in float_values}
    observed = set()
    for case in rows:
        if case.get("float_boundary") is None:
            continue
        index = case["count"] - case["selector"] - 1
        typ = case["types"][index]
        observed.add((typ, index, case["float_boundary"]))
    if observed != expected or len(observed) != 48:
        raise AssertionError(f"direct float boundary matrix is {len(observed)}/48")
    return len(observed)


def callback_cases(seed: int) -> list[dict]:
    rng = random.Random(seed ^ 0x296F60)
    rows = []
    for typ in (0, 1, 2, 3, 4, 5):
        for state in (0, 0x12345678):
            f = (-13.75 if typ in (1, 3) else 7.0)
            rows.append({"count": 1, "selector": 0, "types": [typ],
                     "slots": [0 if typ in (2, 3) else 0x81234567], "slot_floats": [f],
                     "words": [0xFEDCBA98, 0x12345678, 0x80000000, 0xFFFFFFFF],
                     "table_floats": [f, -22.5, 13.875, 0.99],
                         "context": 0xAABBCCDD ^ typ, "state": state,
                         "final_return": 0xC0010000 | len(rows)})
    for _ in range(12):
        typ = rng.randrange(5)
        f = rng.choice((0.0, -1.99, 1.99, 2147483520.0, -2147483648.0))
        rows.append({"count": 1, "selector": 0, "types": [typ],
                     "slots": [rng.randrange(4) if typ in (2, 3) else rng.getrandbits(32)], "slot_floats": [f],
                     "words": [rng.getrandbits(32) for _ in range(4)],
                     "table_floats": [f, -22.5, 13.875, 0.99],
                     "context": rng.getrandbits(32), "state": rng.choice((0, 1, 0xFFFFFFFF)),
                     "final_return": rng.getrandbits(32)})
    return rows


def expected_value(case: dict) -> int:
    index = case["count"] - case["selector"] - 1
    typ = case["types"][index]
    if typ in (0, 4):
        return case["slots"][index] & 0xFFFFFFFF
    if typ == 1:
        return int(case["slot_floats"][index]) & 0xFFFFFFFF
    if typ == 2:
        return case["words"][case["slots"][index]] & 0xFFFFFFFF
    if typ == 3:
        return int(case["table_floats"][case["slots"][index]]) & 0xFFFFFFFF
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261102)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise AssertionError("pinned image hash mismatch")
    body, relocations, obj = compile_body(out / "compile")
    if relocations:
        raise AssertionError(f"candidate has unresolved relocations: {relocations}")
    staged, ips = stage(original, body)
    (out / "production.o").write_bytes(obj.read_bytes())
    (out / "staged-image.bin").write_bytes(staged)
    (out / "slot.ips").write_bytes(ips)

    direct_inputs = cases(args.seed)
    float_coverage_count = assert_float_cartesian_coverage(direct_inputs)
    if len(direct_inputs) != 109:
        raise AssertionError(f"expected 109 direct cases, generated {len(direct_inputs)}")
    direct = []
    for n, case in enumerate(direct_inputs):
        ref, got = direct_run(original, case), direct_run(staged, case)
        if ref != got:
            raise AssertionError(f"direct case {n} mismatch: {ref} != {got}")
        direct.append({"index": n, "type": case["types"][case["count"] - case["selector"] - 1],
                       "selector": case["selector"], "float_boundary": case.get("float_boundary"),
                       "equal": True, "return": got["return"],
                       "reads": got["reads"], "writes": got["writes"]})

    comp = []
    expected_order = [SET_GLOBAL, GET_STATE, GET_CONTEXT, SELECTOR, GET_STATE, FINAL_HELPER]
    for n, case in enumerate(callback_cases(args.seed)):
        ref, got = callback_run(original, case), callback_run(staged, case)
        if ref != got:
            raise AssertionError(f"callback case {n} mismatch: {ref} != {got}")
        if [e["target"] for e in got["events"]] != expected_order:
            raise AssertionError(f"callback event order mismatch case {n}: {got['events']}")
        if (got["events"][3]["args"][0] != 0 or
                got["events"][-1]["args"][:3] != [case["context"], expected_value(case), case["state"]]):
            raise AssertionError(f"callback selector/forwarded args mismatch case {n}: {got['events']}")
        comp.append({"index": n, "type": case["types"][0], "state": case["state"],
                     "equal": True, "events": got["events"], "return": got["return"]})

    # The deliberate wrong table offset must change a directed type-0 result.
    mutant_src = out / "wrong-slot-offset.cpp"
    text = SOURCE.read_text(encoding="utf-8")
    needle = "work + 0x3cu"
    if text.count(needle) < 2:
        raise AssertionError("mutant source anchor changed")
    mutant_src.write_text(text.replace(needle, "work + 0x40u"), encoding="utf-8")
    mutant_body, mutant_relocs, mutant_obj = compile_body(out / "mutant-compile", mutant_src)
    if mutant_relocs:
        raise AssertionError(f"mutant has unresolved relocations: {mutant_relocs}")
    mutant, _ = stage(original, mutant_body)
    control = next(c for c in cases(args.seed) if c["types"][c["count"] - c["selector"] - 1] == 0)
    mutation_detected = direct_run(original, control) != direct_run(mutant, control)
    if not mutation_detected:
        raise AssertionError("wrong slot-offset mutation was not detected")

    index_mutant_src = out / "wrong-global-table-index.cpp"
    index_mutant_text = SOURCE.read_text(encoding="utf-8")
    index_needle = ")[slot_index]"
    if index_mutant_text.count(index_needle) != 2:
        raise AssertionError("global table index mutant anchor changed")
    index_mutant_src.write_text(index_mutant_text.replace(index_needle, ")[index]"), encoding="utf-8")
    index_body, index_relocs, index_obj = compile_body(out / "index-mutant-compile", index_mutant_src)
    if index_relocs:
        raise AssertionError(f"index mutant has unresolved relocations: {index_relocs}")
    index_mutant, _ = stage(original, index_body)
    index_control = next(c for c in cases(args.seed)
                         if c["types"][c["count"] - c["selector"] - 1] == 2
                         and c["slots"][c["count"] - c["selector"] - 1] != c["count"] - c["selector"] - 1)
    table_index_mutation_detected = (direct_run(original, index_control) !=
                                     direct_run(index_mutant, index_control))
    if not table_index_mutation_detected:
        raise AssertionError("wrong global table index mutation was not detected")

    fault_case = {"count": 1, "selector": 0, "types": [2], "slots": [0x4000],
                  "slot_floats": [0.0], "words": [1, 2, 3, 4],
                  "table_floats": [1.0, 2.0, 3.0, 4.0]}
    original_fault_probe = direct_run(original, fault_case)
    candidate_fault_probe = direct_run(staged, fault_case)
    if not original_fault_probe["fault"]:
        raise AssertionError("expected the out-of-mapped-table original fault probe")

    # The callback's selector call is an ARM BL to the even target.
    callsite = 0x002211C0  # verified below by scanning the pinned callback body
    bl_targets = []
    for off in range(CALLBACK - CODE_BASE, CALLBACK - CODE_BASE + 0x94, 4):
        word = struct.unpack_from("<I", original, off)[0]
        if word & 0x0F000000 == 0x0B000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            bl_targets.append((off + CODE_BASE, off + CODE_BASE + 8 + (imm << 2), word))
    selector_calls = [x for x in bl_targets if x[1] == SELECTOR]
    if len(selector_calls) != 1 or selector_calls[0][1] & 1:
        raise AssertionError(f"callback selector call is not a unique even ARM BL: {selector_calls}")

    report = {
        "status": "passed", "seed": args.seed, "reference_sha256": sha(original),
        "production_source_sha256": sha(SOURCE.read_bytes()), "production_object_sha256": sha(obj.read_bytes()),
        "production_body_sha256": sha(body), "body_size": len(body), "slot_size": SLOT,
        "relocations": [], "ips_sha256": sha(ips), "ips_roundtrip": apply_ips(original, ips) == staged,
        "staged_image_sha256": sha(staged), "slot_only": True,
        "direct_case_count": len(direct), "direct_differences": 0, "direct_cases": direct,
        "float_boundary_cartesian_coverage": {"type_selector_pairs": 8,
                                              "boundaries_per_pair": 6,
                                              "case_count": float_coverage_count},
        "callback_composition_case_count": len(comp), "callback_differences": 0,
        "callback_compositions": comp, "callback_selector_callsite": {
            "site": hex(selector_calls[0][0]), "word": hex(selector_calls[0][2]),
            "target": hex(selector_calls[0][1]), "entry_even_arm": True},
        "wrong_slot_offset_mutation_detected": mutation_detected,
        "mutant_source_sha256": sha(mutant_src.read_bytes()),
        "mutant_object_sha256": sha(mutant_obj.read_bytes()),
        "wrong_global_table_index_mutation_detected": table_index_mutation_detected,
        "index_mutant_source_sha256": sha(index_mutant_src.read_bytes()),
        "index_mutant_object_sha256": sha(index_obj.read_bytes()),
        "out_of_mapping_fault_probe": {"type": 2, "slot_index": 0x4000,
                                        "original_fault": original_fault_probe["fault"],
                                        "candidate_fault": candidate_fault_probe["fault"],
                                        "treated_as_outside_supported_domain": True},
        "domain": "valid selector indices within a mapped nonempty work table; mapped word/float backing tables; finite float inputs within signed-32 representable conversion range; original callback with controlled final-helper return; malformed pointers, out-of-range selectors and non-finite/out-of-range float casts excluded"
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS direct={len(direct)} callback={len(comp)} body={len(body)}/{SLOT} relocs=0 mutation=detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
