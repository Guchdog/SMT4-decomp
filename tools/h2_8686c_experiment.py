#!/usr/bin/env python3
"""Direct and original-callback validation for the 0x0028686C getter."""
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
SOURCE = ROOT / "src/engine/leaf_batch21_b.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CODE_BASE = 0x00100000
CODE_SIZE = 0x00380000
ADDRESS = 0x0028686C
SLOT = 20
CALLBACK = 0x00221168
SET_GLOBAL = 0x0028DF3C
GET_STATE = 0x00289640
SELECT_VALUE = 0x00296F60
FINAL_HELPER = 0x00286928
GLOBAL_SLOTS = 0x0044DE98
CALLBACK_SLOTS = 0x0043E188
TABLE = 0x00600000
OBJECT1 = 0x00610000
OBJECT2 = 0x00611000
HEAP_BASE = 0x00600000
HEAP_SIZE = 0x00030000
STACK_BASE = 0x08000000
STACK_SIZE = 0x00010000
SP = STACK_BASE + 0x8000
STOP = STACK_BASE + 0xF000
NOP = struct.pack("<I", 0xE320F000)
CALLEE_SAVED = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12)]
OBSERVED_GLOBAL_RANGES = ((0x0043E000, 0x0043F000), (0x0044DE00, 0x0044E000))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE) -> tuple[bytes, Path]:
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch21_b.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["func_0028686c"]
    if relocations:
        raise AssertionError(f"getter should have no relocations: {relocations}")
    if len(body) > SLOT or (SLOT - len(body)) % 4:
        raise AssertionError(f"getter body {len(body)} does not fit its {SLOT}-byte ARM slot")
    return body, obj


def stage(image: bytes, body: bytes) -> tuple[bytes, bytes]:
    payload = body + NOP * ((SLOT - len(body)) // 4)
    offset = ADDRESS - CODE_BASE
    patched = bytearray(image)
    patched[offset:offset + SLOT] = payload
    staged = bytes(patched)
    ips = encode_ips([(offset, payload)], len(image))
    if apply_ips(image, ips) != staged:
        raise AssertionError("getter IPS replay mismatch")
    changed = [i for i, (a, b) in enumerate(zip(image, staged)) if a != b]
    if any(not offset <= i < offset + SLOT for i in changed):
        raise AssertionError("staging changed bytes outside the getter slot")
    return staged, ips


def in_observed_data(address: int) -> bool:
    if HEAP_BASE <= address < HEAP_BASE + HEAP_SIZE:
        return True
    return any(lo <= address < hi for lo, hi in OBSERVED_GLOBAL_RANGES)


def base_machine(image: bytes):
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(HEAP_BASE, HEAP_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    return uc


def set_words(uc, address: int, *values: int) -> None:
    uc.mem_write(address, struct.pack("<" + "I" * len(values), *(v & 0xFFFFFFFF for v in values)))


def direct_run(image: bytes, case: dict) -> dict:
    uc = base_machine(image)
    set_words(uc, GLOBAL_SLOTS + 0x20, TABLE)
    set_words(uc, TABLE + 0xC0, case["context_value"])
    set_words(uc, TABLE + 0xC4, case["wrong_offset_value"])
    uc.reg_write(arm.UC_ARM_REG_R0, case["ignored_input"])
    uc.reg_write(arm.UC_ARM_REG_R1, 0x11112222)
    uc.reg_write(arm.UC_ARM_REG_R2, 0x33334444)
    uc.reg_write(arm.UC_ARM_REG_R3, 0x55556666)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xA1000000 + i * 0x01010101)
    before = [uc.reg_read(reg) for reg in CALLEE_SAVED]
    reads, writes = [], []

    def on_read(machine, _access, address, size, value, _data):
        if in_observed_data(address):
            reads.append((address, size, value & 0xFFFFFFFF))

    def on_write(_machine, _access, address, size, value, _data):
        writes.append((address, size, value & 0xFFFFFFFF))

    uc.hook_add(unicorn.UC_HOOK_MEM_READ, on_read)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE,
                lambda machine, address, _size, _data: machine.emu_stop() if address == STOP else None,
                begin=STOP, end=STOP)
    fault = None
    try:
        uc.emu_start(ADDRESS, 0, count=1000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {
        "fault": fault,
        "return": uc.reg_read(arm.UC_ARM_REG_R0),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "callee_saved": [uc.reg_read(reg) for reg in CALLEE_SAVED] == before,
        "reads": reads,
        "writes": writes,
        "context_value_after": struct.unpack("<I", uc.mem_read(TABLE + 0xC0, 4))[0],
        "wrong_offset_value_after": struct.unpack("<I", uc.mem_read(TABLE + 0xC4, 4))[0],
    }


def callback_case(image: bytes, case: dict) -> dict:
    uc = base_machine(image)
    # The callback's global slot table and both getter chains use mapped ordinary RAM.
    set_words(uc, CALLBACK_SLOTS + 4, OBJECT1)
    set_words(uc, CALLBACK_SLOTS + 8, OBJECT2)
    set_words(uc, GLOBAL_SLOTS + 0x20, TABLE)
    set_words(uc, TABLE + 0xC0, case["context_value"])
    set_words(uc, TABLE + 0xC4, case["wrong_offset_value"])
    set_words(uc, TABLE + 0xD0, case["first_state"])
    uc.mem_write(OBJECT1, b"\xA5" * 0xB00)
    uc.mem_write(OBJECT2, b"\x5A" * 0x80)
    set_words(uc, OBJECT1 + 0xA10, 0xDEADBEEF)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xB2000000 + i * 0x01010101)
    before = [uc.reg_read(reg) for reg in CALLEE_SAVED]
    events, reads, writes, returns = [], [], [], {}
    stack_words = (arm.UC_ARM_REG_SP,)

    def on_read(_machine, _access, address, size, value, _data):
        if in_observed_data(address):
            reads.append((address, size, value & 0xFFFFFFFF))

    def on_write(_machine, _access, address, size, value, _data):
        writes.append((address, size, value & 0xFFFFFFFF))

    def on_code(machine, address, _size, _data):
        if address == STOP:
            machine.emu_stop()
            return
        if address == 0x0022117C:
            returns["first_state"] = machine.reg_read(arm.UC_ARM_REG_R0)
        elif address == 0x002211B8:
            returns["context"] = machine.reg_read(arm.UC_ARM_REG_R0)
        elif address == 0x002211C4:
            returns["selected"] = machine.reg_read(arm.UC_ARM_REG_R0)
        elif address == 0x002211D0:
            returns["second_state"] = machine.reg_read(arm.UC_ARM_REG_R0)
        if address not in (SET_GLOBAL, GET_STATE, ADDRESS, SELECT_VALUE, FINAL_HELPER):
            return
        sp = machine.reg_read(arm.UC_ARM_REG_SP)
        if sp & 7:
            raise AssertionError(f"unaligned callback helper SP at {address:#x}: {sp:#x}")
        regs = [machine.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
        words = list(struct.unpack("<II", machine.mem_read(sp, 8)))
        events.append({"target": address, "args": regs, "stack": words, "sp": sp})
        if address == SELECT_VALUE:
            if case["mutate_state"]:
                set_words(machine, TABLE + 0xD0, case["second_state"])
            machine.reg_write(arm.UC_ARM_REG_R0, case["selected_value"])
            machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))
        elif address == FINAL_HELPER:
            machine.reg_write(arm.UC_ARM_REG_R0, case["final_return"])
            machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))

    uc.hook_add(unicorn.UC_HOOK_MEM_READ, on_read)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    fault = None
    try:
        uc.emu_start(CALLBACK, 0, count=10000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {
        "fault": fault,
        "return": uc.reg_read(arm.UC_ARM_REG_R0),
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "callee_saved": [uc.reg_read(reg) for reg in CALLEE_SAVED] == before,
        "events": events,
        "getter_returns": returns,
        "reads": reads,
        "writes": writes,
        "global_zero": struct.unpack("<I", uc.mem_read(0x0043E0BC, 4))[0],
        "object1_effects": bytes(uc.mem_read(OBJECT1 + 0xA11, 1)),
        "object2_effects": bytes(uc.mem_read(OBJECT2 + 0x30, 2)),
        "table_c0_c4_d0": bytes(uc.mem_read(TABLE + 0xC0, 0x14)),
    }


def direct_cases(seed: int) -> list[dict]:
    rng = random.Random(seed)
    values = (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF, 0x12345678)
    cases = []
    for i, value in enumerate(values):
        cases.append({"ignored_input": (0, 0xFFFFFFFF, 0x0044DEB8)[i % 3],
                      "context_value": value,
                      "wrong_offset_value": value ^ 0xA55AA55A})
    for _ in range(32):
        cases.append({"ignored_input": rng.getrandbits(32),
                      "context_value": rng.getrandbits(32),
                      "wrong_offset_value": rng.getrandbits(32)})
    return cases


def callback_cases(seed: int) -> list[dict]:
    rng = random.Random(seed ^ 0x28686C)
    rows = []
    directed = [(state, context, selected, final, mutate)
                for state in (0, 1, 0x80000000)
                for context in (0, 0x12345678)
                for selected, final, mutate in ((0, 0, False), (1, 0x89ABCDEF, False),
                                                 (0xFEDCBA98, 1, True))]
    for state, context, selected, final, mutate in directed:
        rows.append({"first_state": state, "context_value": context,
                     "wrong_offset_value": context ^ 0xA5A55A5A,
                     "selected_value": selected, "final_return": final,
                     "mutate_state": mutate, "second_state": 0xF00D0000 | len(rows)})
    for _ in range(32):
        rows.append({"first_state": rng.choice((0, 1, 0x80000000, 0xFFFFFFFF)),
                     "context_value": rng.getrandbits(32),
                     "wrong_offset_value": rng.getrandbits(32),
                     "selected_value": rng.getrandbits(32),
                     "final_return": rng.choice((0, 1, 0x89ABCDEF, 0xFFFFFFFF)),
                     "mutate_state": bool(rng.getrandbits(1)),
                     "second_state": rng.getrandbits(32)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261130)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise AssertionError("pinned original image hash mismatch")
    call_site = 0x002211B4
    call_word = struct.unpack_from("<I", original, call_site - CODE_BASE)[0]
    call_imm = call_word & 0x00FFFFFF
    if call_imm & 0x00800000:
        call_imm -= 0x01000000
    call_target = call_site + 8 + (call_imm << 2)
    if call_word & 0x0F000000 != 0x0B000000 or call_target != ADDRESS or ADDRESS & 1:
        raise AssertionError(f"callback getter BL is not even ARM target: {call_site:#x}->{call_target:#x}")

    body, obj = compile_body(out / "compile")
    staged, ips = stage(original, body)
    (out / "production.o").write_bytes(obj.read_bytes())
    (out / "staged-image.bin").write_bytes(staged)
    (out / "getter-slot.ips").write_bytes(ips)

    direct_rows = []
    for index, case in enumerate(direct_cases(args.seed)):
        ref = direct_run(original, case)
        got = direct_run(staged, case)
        if ref != got or got["return"] != case["context_value"] or got["writes"]:
            raise AssertionError(f"direct getter mismatch case {index}: {ref} != {got}")
        direct_rows.append({"index": index, "equal": True, "return": got["return"],
                            "reads": got["reads"], "writes": got["writes"]})

    composition_rows = []
    cases = callback_cases(args.seed)
    for index, case in enumerate(cases):
        ref = callback_case(original, case)
        got = callback_case(staged, case)
        if ref != got:
            raise AssertionError(f"original callback composition mismatch case {index}: {ref} != {got}")
        expected = [SET_GLOBAL, GET_STATE, ADDRESS, SELECT_VALUE, GET_STATE, FINAL_HELPER]
        if [event["target"] for event in got["events"]] != expected:
            raise AssertionError(f"callback helper order mismatch case {index}")
        final = got["events"][-1]
        if final["args"] != [case["context_value"], case["selected_value"],
                              case["second_state"] if case["mutate_state"] else case["first_state"], 6]:
            raise AssertionError(f"final helper argument mismatch case {index}: {final}")
        if final["stack"] != [1, 0] or got["return"] != case["final_return"]:
            raise AssertionError(f"callback raw return/stack mismatch case {index}")
        composition_rows.append({"index": index, "equal": True, "calls": expected,
                                 "final_args": final["args"], "final_stack": final["stack"],
                                 "getter_returns": got["getter_returns"],
                                 "callback_return": got["return"]})

    mutant_source = out / "wrong-offset-mutant.cpp"
    source_text = SOURCE.read_text(encoding="utf-8")
    needle = "context + 0xc0u"
    if source_text.count(needle) != 1:
        raise AssertionError("wrong-offset mutation needle is not unique")
    mutant_source.write_text(source_text.replace(needle, "context + 0xc4u", 1), encoding="utf-8")
    mutant_body, mutant_obj = compile_body(out / "mutant-compile", mutant_source)
    mutant_image, _mutant_ips = stage(original, mutant_body)
    control = {"ignored_input": 0xCAFEBABE, "context_value": 0x12345678,
               "wrong_offset_value": 0xA5A55A5A}
    direct_mutation_detected = direct_run(original, control) != direct_run(mutant_image, control)
    callback_control = callback_cases(args.seed)[0]
    callback_mutation_detected = callback_case(original, callback_control) != callback_case(mutant_image, callback_control)
    if not direct_mutation_detected or not callback_mutation_detected:
        raise AssertionError("wrong-offset mutation was not detected in direct and callback cases")

    helper_entry = struct.unpack_from("<I", original, ADDRESS - CODE_BASE)[0]
    if helper_entry & 0x0F000000 == 0x0A000000:
        raise AssertionError("getter entry unexpectedly begins with a branch")
    report = {
        "status": "passed",
        "seed": args.seed,
        "reference_sha256": sha(original),
        "production_source_sha256": sha(SOURCE.read_bytes()),
        "production_object_sha256": sha(obj.read_bytes()),
        "production_body_sha256": sha(body),
        "body_size": len(body),
        "slot_size": SLOT,
        "relocations": [],
        "ips_sha256": sha(ips),
        "ips_roundtrip": apply_ips(original, ips) == staged,
        "staged_image_sha256": sha(staged),
        "changed_bytes_within_slot": True,
        "direct_case_count": len(direct_rows),
        "direct_differences": 0,
        "direct_cases": direct_rows,
        "callback_composition_case_count": len(composition_rows),
        "callback_composition_differences": 0,
        "callback_compositions": composition_rows,
        "callback_original": "0x00221168",
        "getter_address": "0x0028686C",
        "callback_getter_callsite": {"site": hex(call_site), "word": hex(call_word),
                                     "target": hex(call_target), "entry_even_arm": True},
        "wrong_offset_mutation_detected": {
            "direct": direct_mutation_detected,
            "callback_composition": callback_mutation_detected,
            "mutant_source_sha256": sha(mutant_source.read_bytes()),
            "mutant_object_sha256": sha(mutant_obj.read_bytes()),
        },
        "domain": "mapped ordinary-RAM pointer chain; callback uses real original 0x0028DF3C and 0x00289640, with controlled 0x00296F60 and 0x00286928 helper events; SVC/runtime effects and arbitrary invalid pointers are outside scope",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS direct={len(direct_rows)} callback={len(composition_rows)} body={len(body)}/{SLOT} wrong_offset=detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
