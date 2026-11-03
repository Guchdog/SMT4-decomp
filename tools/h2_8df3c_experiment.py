#!/usr/bin/env python3
"""Direct and original-callback differential for H2 helper 0x0028DF3C."""
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
SOURCE = ROOT / "src/engine/leaf_batch22_b.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
ADDRESS, SLOT, CALLBACK = 0x0028DF3C, 24, 0x00221168
SET_GLOBAL, GET_STATE, GET_CONTEXT = ADDRESS, 0x00289640, 0x0028686C
SELECT_VALUE, FINAL_HELPER = 0x00296F60, 0x00286928
GLOBAL, CALLBACK_SLOTS = 0x0044DE98, 0x0043E188
TABLE, OBJECT1, OBJECT2 = 0x00600000, 0x00610000, 0x00611000
HEAP_BASE, HEAP_SIZE = 0x00600000, 0x00030000
STACK_BASE, STACK_SIZE = 0x08000000, 0x10000
SP, STOP = STACK_BASE + 0x8000, STACK_BASE + 0xF000
NOP = struct.pack("<I", 0xE320F000)
CALLEE_SAVED = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12)]


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=False)
    obj = out / "leaf_batch22_b.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocs = extract_elf_functions_detailed(obj)["ui_func_0028df3c"]
    return body, relocs, obj


def stage(image: bytes, body: bytes):
    if len(body) > SLOT or len(body) % 4:
        raise AssertionError(f"body {len(body)} does not fit aligned {SLOT}-byte slot")
    payload = body + NOP * ((SLOT - len(body)) // 4)
    offset = ADDRESS - CODE_BASE
    patched = bytearray(image)
    patched[offset:offset + SLOT] = payload
    staged = bytes(patched)
    ips = encode_ips([(offset, payload)], len(image))
    if apply_ips(image, ips) != staged:
        raise AssertionError("IPS replay mismatch")
    if any(a != b and not offset <= i < offset + SLOT for i, (a, b) in enumerate(zip(image, staged))):
        raise AssertionError("staging changed bytes outside 0x0028DF3C slot")
    return staged, ips


def machine(image: bytes):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(HEAP_BASE, HEAP_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    return uc


def put32(uc, address: int, value: int):
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def init_regs(uc, value: int):
    uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
    for i in range(1, 13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0x11000000 + i * 0x01010101)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xA1000000 + i * 0x01010101)


def direct_run(image: bytes, value: int, initial_global: int):
    uc = machine(image)
    put32(uc, 0x0043E0BC, initial_global)
    init_regs(uc, value)
    saved = [uc.reg_read(r) for r in CALLEE_SAVED]
    reads, writes = [], []

    def on_read(_uc, _access, address, size, data, _user):
        if 0x0043E000 <= address < 0x0043F000:
            reads.append((address, size, data & 0xFFFFFFFF))

    def on_write(_uc, _access, address, size, data, _user):
        if 0x0043E000 <= address < 0x0043F000:
            writes.append((address, size, data & 0xFFFFFFFF))

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
            "global": struct.unpack("<I", uc.mem_read(0x0043E0BC, 4))[0],
            "reads": reads, "writes": writes}


def callback_run(image: bytes, case: dict):
    uc = machine(image)
    # Original state/context/value getters use a one-entry, fully mapped work object.
    put32(uc, GLOBAL + 0x20, TABLE)
    put32(uc, TABLE + 0x1C, 1)
    uc.mem_write(TABLE + 0x20, b"\x00")
    put32(uc, TABLE + 0x3C, case["selected"])
    put32(uc, TABLE + 0xC0, case["context"])
    put32(uc, TABLE + 0xD0, case["state"])
    put32(uc, CALLBACK_SLOTS + 4, OBJECT1)
    put32(uc, CALLBACK_SLOTS + 8, OBJECT2)
    uc.mem_write(OBJECT1, b"\xA5" * 0xB00)
    uc.mem_write(OBJECT2, b"\x5A" * 0x80)
    put32(uc, OBJECT1 + 0xA10, 0xDEADBEEF)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xB2000000 + i * 0x01010101)
    saved = [uc.reg_read(r) for r in CALLEE_SAVED]
    reads, writes, events = [], [], []

    def on_read(_uc, _access, address, size, data, _user):
        if (0x0043E000 <= address < 0x0043F000 or
                0x0044DE00 <= address < 0x0044E000 or
                TABLE <= address < TABLE + 0x1000 or
                OBJECT1 <= address < OBJECT1 + 0xB00 or
                OBJECT2 <= address < OBJECT2 + 0x80):
            reads.append((address, size, data & 0xFFFFFFFF))

    def on_write(_uc, _access, address, size, data, _user):
        if (0x0043E000 <= address < 0x0043F000 or
                0x0044DE00 <= address < 0x0044E000 or
                TABLE <= address < TABLE + 0x1000 or
                OBJECT1 <= address < OBJECT1 + 0xB00 or
                OBJECT2 <= address < OBJECT2 + 0x80):
            writes.append((address, size, data & 0xFFFFFFFF))

    def on_code(m, address, _size, _data):
        if address == STOP:
            m.emu_stop()
            return
        if address in (SET_GLOBAL, GET_STATE, GET_CONTEXT, SELECT_VALUE, FINAL_HELPER):
            sp = m.reg_read(arm.UC_ARM_REG_SP)
            argc = 4 if address == FINAL_HELPER else 1
            args = [m.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(argc)]
            stack = list(struct.unpack("<II", m.mem_read(sp, 8))) if address == FINAL_HELPER else []
            events.append({"target": address, "args": args, "stack": stack, "sp": sp})
            if sp & 7:
                raise AssertionError(f"callback call SP unaligned at {address:#x}")
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
            "global": struct.unpack("<I", uc.mem_read(0x0043E0BC, 4))[0],
            "object1_marker": bytes(uc.mem_read(OBJECT1 + 0xA11, 1)).hex(),
            "object2_marker": bytes(uc.mem_read(OBJECT2 + 0x30, 2)).hex()}


def direct_values(seed: int):
    rng = random.Random(seed)
    fixed = [0, 1, 2, 3, 0xFFFFFFFE, 0xFFFFFFFF, 0x80000000, 0x7FFFFFFF,
             0xFFFFFFFD, 0x40000000, 0xFFFF0000]
    return list(dict.fromkeys(fixed + [rng.getrandbits(32) for _ in range(48)]))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261104)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise AssertionError("pinned image hash mismatch")

    body, relocs, obj = compile_body(out / "compile")
    if relocs:
        raise AssertionError(f"production helper has unresolved relocations: {relocs}")
    staged, ips = stage(original, body)
    (out / "production.o").write_bytes(obj.read_bytes())
    (out / "staged-image.bin").write_bytes(staged)
    (out / "slot.ips").write_bytes(ips)

    direct = []
    for i, value in enumerate(direct_values(args.seed)):
        initial = (0xD00DFEED ^ value) & 0xFFFFFFFF
        ref, got = direct_run(original, value, initial), direct_run(staged, value, initial)
        expected_store = value if ((value + 1) & 0xFFFFFFFF) < 3 else initial
        expected_writes = [(0x0043E0BC, 4, value)] if expected_store != initial else []
        if ref != got or got["return"] != value or got["global"] != expected_store or got["writes"] != expected_writes:
            raise AssertionError(f"direct case {i} value={value:#x}: {ref} != {got}")
        direct.append({"index": i, "input": value, "return": got["return"],
                       "global": got["global"], "writes": got["writes"], "equal": True})

    # Mutant A uses a non-wrapping range predicate; mutant B stores a normalized value.
    source_text = SOURCE.read_text(encoding="utf-8")
    predicate_needle = "value + 1u < 3u"
    if source_text.count(predicate_needle) != 1:
        raise AssertionError("predicate mutant anchor changed")
    pred_src = out / "predicate-mutant.cpp"
    pred_src.write_text(source_text.replace(predicate_needle, "value < 2u"), encoding="utf-8")
    pred_body, pred_relocs, pred_obj = compile_body(out / "predicate-mutant-build", pred_src)
    if pred_relocs:
        raise AssertionError(f"predicate mutant relocations: {pred_relocs}")
    pred_img, _ = stage(original, pred_body)
    predicate_detected = direct_run(original, 0xFFFFFFFF, 0xAABBCCDD) != direct_run(pred_img, 0xFFFFFFFF, 0xAABBCCDD)

    store_needle = "0x0043e0bcu) = value;"
    if source_text.count(store_needle) != 1:
        raise AssertionError("stored-value mutant anchor changed")
    store_src = out / "stored-value-mutant.cpp"
    store_src.write_text(source_text.replace(store_needle, "0x0043e0bcu) = value + 1u;"), encoding="utf-8")
    store_body, store_relocs, store_obj = compile_body(out / "stored-value-mutant-build", store_src)
    if store_relocs:
        raise AssertionError(f"stored-value mutant relocations: {store_relocs}")
    store_img, _ = stage(original, store_body)
    store_detected = direct_run(original, 1, 0xAABBCCDD) != direct_run(store_img, 1, 0xAABBCCDD)
    if not predicate_detected or not store_detected:
        raise AssertionError("one or more negative controls were not detected")

    callback_cases = []
    for state in (0, 1, 0x80000000):
        for selected in (0, 1, 0xFFFFFFFF):
            for final in (0, 0x89ABCDEF):
                callback_cases.append({"state": state, "selected": selected,
                                      "context": 0x12345678 ^ selected,
                                      "final_return": final})
    comp = []
    expected_order = [SET_GLOBAL, GET_STATE, GET_CONTEXT, SELECT_VALUE, GET_STATE, FINAL_HELPER]
    for i, case in enumerate(callback_cases):
        ref, got = callback_run(original, case), callback_run(staged, case)
        if ref != got:
            raise AssertionError(f"callback composition case {i}: {ref} != {got}")
        if [event["target"] for event in got["events"]] != expected_order:
            raise AssertionError(f"callback call order mismatch: {got['events']}")
        if got["events"][0]["args"] != [0] or got["events"][-1]["args"] != [case["context"], case["selected"], case["state"], 6]:
            raise AssertionError(f"callback forwarded arguments mismatch: {got['events']}")
        if got["events"][-1]["stack"] != [1, 0] or got["global"] != 0 or got["return"] != case["final_return"]:
            raise AssertionError(f"callback raw return/store/stack mismatch: {got}")
        comp.append({"index": i, "case": case, "equal": True,
                     "events": got["events"], "global": got["global"],
                     "return": got["return"]})

    # Find the callsite in the pinned original and require an even ARM BL target.
    targets = []
    for off in range(CALLBACK - CODE_BASE, CALLBACK - CODE_BASE + 0x94, 4):
        word = struct.unpack_from("<I", original, off)[0]
        if word & 0x0F000000 == 0x0B000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            targets.append((off + CODE_BASE, off + CODE_BASE + 8 + (imm << 2), word))
    calls = [x for x in targets if x[1] == ADDRESS]
    if len(calls) != 1 or calls[0][1] & 1:
        raise AssertionError(f"callback BL target not unique even ARM: {calls}")

    report = {
        "status": "passed", "seed": args.seed, "reference_sha256": sha(original),
        "production_source_sha256": sha(SOURCE.read_bytes()),
        "production_object_sha256": sha(obj.read_bytes()),
        "production_body_sha256": sha(body), "body_size": len(body), "slot_size": SLOT,
        "relocations": [], "ips_sha256": sha(ips),
        "ips_roundtrip": apply_ips(original, ips) == staged,
        "staged_image_sha256": sha(staged), "slot_only": True,
        "direct_case_count": len(direct), "direct_differences": 0, "direct_cases": direct,
        "callback_composition_case_count": len(comp), "callback_differences": 0,
        "callback_compositions": comp,
        "callback_helper_callsite": {"site": hex(calls[0][0]), "word": hex(calls[0][2]),
                                      "target": hex(calls[0][1]), "even_arm": True},
        "mutations_detected": {"nonwrapping_predicate": predicate_detected,
                               "normalized_store_value": store_detected},
        "mutant_hashes": {"predicate_source": sha(pred_src.read_bytes()),
                          "predicate_object": sha(pred_obj.read_bytes()),
                          "stored_value_source": sha(store_src.read_bytes()),
                          "stored_value_object": sha(store_obj.read_bytes())},
        "cross_tu_boundaries": {
            "leaf_batch30_c": "h2_set_global is declared uint32_t and its raw return feeds 0x00289640; original callback calls with 0.",
            "leaf_batch45_a": "caller declares ui_func_0028df3c(uint32_t) as void and discards r0; original call uses 0xFFFFFFFF.",
        },
        "domain": "all 32-bit inputs for direct helper; callback composition uses mapped ordinary RAM, real original getters/selector, and controlled final helper; runtime and unrelated helper semantics are outside scope",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS direct={len(direct)} callback={len(comp)} body={len(body)}/{SLOT} relocs=0 mutants=detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
