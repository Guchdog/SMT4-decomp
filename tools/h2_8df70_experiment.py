#!/usr/bin/env python3
"""Direct and final-helper row-query differential for H2 0x0028DF70."""
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
SOURCE = ROOT / "src/engine/leaf_batch26_b.cpp"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CODE_BASE, CODE_SIZE = 0x00100000, 0x00380000
ADDRESS, SLOT, FINAL_HELPER = 0x0028DF70, 40, 0x00286928
MANAGER_GLOBAL, CALLBACK_SLOTS = 0x0043DA2C, 0x0043E188
MANAGER, OBJECT = 0x00620000, 0x00610000
HEAP_BASE, HEAP_SIZE = 0x00600000, 0x00030000
STACK_BASE, STACK_SIZE = 0x08000000, 0x10000
SP, STOP = STACK_BASE + 0x8000, STACK_BASE + 0xF000
NOP = struct.pack("<I", 0xE320F000)
CALLEE_SAVED = [getattr(arm, f"UC_ARM_REG_R{i}") for i in range(4, 12)]
D8 = arm.UC_ARM_REG_D8

# Branch-path callees are intentionally controlled. 0x0028DF70 remains real.
STUB_RETURNS = {
    0x002C1F28: lambda _a: 0,
    0x002B89A0: lambda _a: 0,
    0x0028E974: lambda _a: 0,
    0x0028DF98: lambda _a: 0,
    0x002C4BF0: lambda _a: 0,
    0x002B90F0: lambda _a: 0,
    0x002F5B2C: lambda a: 0xA0 + a[0],
    0x002D65B4: lambda a: 0xB000 + a[0],
    0x002B8CCC: lambda _a: 0x1234ABCD,
    0x002B8B78: lambda _a: 0,
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_body(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=False)
    obj = out / "leaf_batch26_b.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "affected TU compile failed")
    body, relocs = extract_elf_functions_detailed(obj)["camp_func_0028df70"]
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
        raise AssertionError("IPS roundtrip mismatch")
    if any(a != b and not offset <= i < offset + SLOT for i, (a, b) in enumerate(zip(image, staged))):
        raise AssertionError("staging changed bytes outside the getter slot")
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


def put32(uc, address, value):
    uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))


def put16(uc, address, value):
    uc.mem_write(address, struct.pack("<H", value & 0xFFFF))


def direct_run(image: bytes, index: int, halfwords: list[int], manager_ptr: int):
    uc = machine(image)
    put32(uc, MANAGER_GLOBAL, manager_ptr)
    if manager_ptr == MANAGER:
        uc.mem_write(MANAGER, b"\xCC" * 0x4C0)
        for i, value in enumerate(halfwords):
            put16(uc, MANAGER + 0x496 + 4 * i, value)
    uc.reg_write(arm.UC_ARM_REG_R0, index & 0xFFFFFFFF)
    for i in range(1, 13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0x11000000 + i * 0x01010101)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xA1000000 + i * 0x01010101)
    saved = [uc.reg_read(r) for r in CALLEE_SAVED]
    reads, writes = [], []

    def on_read(_uc, _access, address, size, value, _user):
        if address == MANAGER_GLOBAL or MANAGER <= address < MANAGER + 0x4C0:
            observed = int.from_bytes(_uc.mem_read(address, size), "little")
            reads.append((address, size, observed))

    def on_write(_uc, _access, address, size, value, _user):
        if address == MANAGER_GLOBAL or MANAGER <= address < MANAGER + 0x4C0:
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


def compose(image: bytes, case: dict):
    uc = machine(image)
    put32(uc, MANAGER_GLOBAL, MANAGER)
    uc.mem_write(MANAGER, b"\xCC" * 0x4C0)
    put16(uc, MANAGER + 0x496, case["getter_value"])
    put32(uc, CALLBACK_SLOTS + 4, OBJECT)
    put32(uc, CALLBACK_SLOTS + 8, OBJECT + 0x1000)
    uc.mem_write(OBJECT, b"\xA5" * 0xB00)
    uc.mem_write(OBJECT + 0x1000, b"\x5A" * 0x100)
    uc.mem_write(OBJECT + 8, b"\x00")
    uc.mem_write(OBJECT + 9, bytes([case["row"]]))
    uc.mem_write(OBJECT + 0x2E, b"\x00")
    uc.mem_write(OBJECT + 0x35, b"\x00")
    put32(uc, OBJECT + 4, 0x00630000)
    # Incoming raw helper args and original stack words (arg5=1, arg6=0).
    for reg, value in ((arm.UC_ARM_REG_R0, 0x13579BDF),
                       (arm.UC_ARM_REG_R1, 0x2468ACE0),
                       (arm.UC_ARM_REG_R2, 0), (arm.UC_ARM_REG_R3, 6)):
        uc.reg_write(reg, value)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    put32(uc, SP, 1)
    put32(uc, SP + 4, 0)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    for i, reg in enumerate(CALLEE_SAVED):
        uc.reg_write(reg, 0xB2000000 + i * 0x01010101)
    uc.reg_write(D8, 0x0123456789ABCDEF)
    saved = [uc.reg_read(r) for r in CALLEE_SAVED]
    saved_d8 = uc.reg_read(D8)
    reads, writes, events = [], [], []

    def relevant(address):
        return ((0x0043DA00 <= address < 0x0043DB00) or
                (0x0043E000 <= address < 0x0043F000) or
                (MANAGER <= address < MANAGER + 0x4C0) or
                (OBJECT <= address < OBJECT + 0xB00) or
                (OBJECT + 0x1000 <= address < OBJECT + 0x1100))

    def on_read(_uc, _access, address, size, value, _user):
        if relevant(address):
            reads.append((address, size, value & 0xFFFFFFFF))

    def on_write(_uc, _access, address, size, value, _user):
        if relevant(address):
            writes.append((address, size, value & 0xFFFFFFFF))

    argc = {0x002C1F28: 0, 0x002B89A0: 0, 0x0028E974: 4, 0x0028DF98: 2,
            0x002C4BF0: 2, 0x002B90F0: 2, 0x002F5B2C: 1, 0x002D65B4: 1,
            0x002B8CCC: 0, 0x002B8B78: 1, ADDRESS: 1}
    stackc = {0x0028E974: 3}

    def on_code(m, address, _size, _user):
        if address == STOP:
            m.emu_stop()
            return
        if address not in STUB_RETURNS and address != ADDRESS:
            return
        sp = m.reg_read(arm.UC_ARM_REG_SP)
        if sp & 7:
            raise AssertionError(f"final-helper call SP unaligned at {address:#x}/{sp:#x}")
        nreg = argc[address]
        args = [m.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(nreg)]
        nstack = stackc.get(address, 0)
        stack = list(struct.unpack("<" + "I" * nstack, m.mem_read(sp, 4 * nstack))) if nstack else []
        events.append({"target": address, "args": args, "stack": stack, "sp": sp})
        if address == ADDRESS:
            return
        result = STUB_RETURNS[address](args)
        m.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
        m.reg_write(arm.UC_ARM_REG_PC, m.reg_read(arm.UC_ARM_REG_LR))

    uc.hook_add(unicorn.UC_HOOK_MEM_READ, on_read)
    uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, on_write)
    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    fault = None
    try:
        uc.emu_start(FINAL_HELPER, 0, count=50000)
    except unicorn.UcError as exc:
        fault = str(exc)
    return {"fault": fault, "return": uc.reg_read(arm.UC_ARM_REG_R0),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": [uc.reg_read(r) for r in CALLEE_SAVED] == saved,
            "d8_preserved": uc.reg_read(D8) == saved_d8,
            "events": events, "reads": reads, "writes": writes,
            "row_byte": bytes(uc.mem_read(OBJECT + 0xA26, 1)).hex(),
            "result_byte": bytes(uc.mem_read(OBJECT + 0xA12, 1)).hex(),
            "manager_halfword": struct.unpack("<H", uc.mem_read(MANAGER + 0x496, 2))[0]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261105)
    args = parser.parse_args()
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.mkdir(parents=True, exist_ok=False)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise AssertionError("pinned image hash mismatch")

    body, relocs, obj = compile_body(out / "compile")
    if relocs:
        raise AssertionError(f"candidate has unresolved relocations: {relocs}")
    staged, ips = stage(original, body)
    (out / "production.o").write_bytes(obj.read_bytes())
    (out / "staged-image.bin").write_bytes(staged)
    (out / "slot.ips").write_bytes(ips)

    rng = random.Random(args.seed)
    half_patterns = [0, 1, 4, 5, 0x7FFF, 0x8000, 0xFFFE, 0xFFFF]
    direct_inputs = [(index, value) for index in range(6) for value in half_patterns]
    direct_inputs += [(index, half_patterns[i % len(half_patterns)])
                      for i, index in enumerate((6, 7, 0x7FFFFFFF, 0x80000000,
                                                 0xFFFFFFFE, 0xFFFFFFFF))]
    direct_inputs += [(rng.getrandbits(32), rng.getrandbits(16)) for _ in range(40)]
    direct = []
    for i, (index, selected_halfword) in enumerate(direct_inputs):
        data = [rng.getrandbits(16) for _ in range(6)]
        if index < 6:
            data[index] = selected_halfword
        ptr = MANAGER if index < 6 else 0x12345000  # invalid path must not dereference it
        ref, got = direct_run(original, index, data, ptr), direct_run(staged, index, data, ptr)
        expected = data[index] if index < 6 else 0
        if ref != got or got["fault"] or got["return"] != expected or got["writes"]:
            raise AssertionError(f"direct index={index:#x}: {ref} != {got}, expected {expected:#x}")
        expected_reads = ([(MANAGER_GLOBAL, 4, MANAGER),
                           (MANAGER + 0x496 + 4 * index, 2, expected)] if index < 6 else [])
        if got["reads"] != expected_reads:
            raise AssertionError(f"direct read domain/order mismatch index={index:#x}: {got['reads']}")
        direct.append({"index": i, "input": index, "return": got["return"],
                       "reads": got["reads"], "writes": got["writes"], "equal": True})

    # Predicate control rejects index 5; offset control reads the preceding halfword.
    src_text = SOURCE.read_text(encoding="utf-8")
    pred_needle = "if (index >= 6u)"
    if src_text.count(pred_needle) != 1:
        raise AssertionError("bound-mutant anchor changed")
    pred_src = out / "bound-mutant.cpp"
    pred_src.write_text(src_text.replace(pred_needle, "if (index >= 5u)"), encoding="utf-8")
    pred_body, pred_relocs, pred_obj = compile_body(out / "bound-mutant-build", pred_src)
    if pred_relocs:
        raise AssertionError(f"bound mutant relocations: {pred_relocs}")
    pred_img, _ = stage(original, pred_body)
    bound_control = [0x1234] * 6
    bound_control[5] = 5
    bound_detected = direct_run(original, 5, bound_control, MANAGER) != direct_run(pred_img, 5, bound_control, MANAGER)

    offset_needle = "[%1, #0x96]"
    if src_text.count(offset_needle) != 1:
        raise AssertionError("offset-mutant anchor changed")
    offset_src = out / "offset-mutant.cpp"
    offset_src.write_text(src_text.replace(offset_needle, "[%1, #0x94]"), encoding="utf-8")
    offset_body, offset_relocs, offset_obj = compile_body(out / "offset-mutant-build", offset_src)
    if offset_relocs:
        raise AssertionError(f"offset mutant relocations: {offset_relocs}")
    offset_img, _ = stage(original, offset_body)
    offset_control = [0, 1, 2, 3, 4, 5]
    offset_detected = direct_run(original, 0, offset_control, MANAGER) != direct_run(offset_img, 0, offset_control, MANAGER)
    if not bound_detected or not offset_detected:
        raise AssertionError("a direct negative control was not detected")

    compose_rows = []
    for row in (7, 8, 9):
        for value in (5, 4, 0xFFFF):
            case = {"row": row, "getter_value": value}
            ref, got = compose(original, case), compose(staged, case)
            if ref != got:
                raise AssertionError(f"final-helper composition row={row} value={value:#x}: {ref} != {got}")
            getter_events = [e for e in got["events"] if e["target"] == ADDRESS]
            if len(getter_events) != 1 or getter_events[0]["args"] != [0]:
                raise AssertionError(f"row getter call mismatch: {getter_events}")
            should_trigger = value == 5
            expected_row_byte = "01" if should_trigger else "a5"
            expected_result_byte = "cd" if should_trigger else "00"
            if got["row_byte"] != expected_row_byte or got["result_byte"] != expected_result_byte:
                raise AssertionError(f"row branch/store mismatch: {got}")
            tail_targets = [e["target"] for e in got["events"]]
            if (0x002B8CCC in tail_targets) != should_trigger or (0x002B8B78 in tail_targets) != should_trigger:
                raise AssertionError(f"row continuation mismatch: {tail_targets}")
            compose_rows.append({"row": row, "getter_value": value, "equal": True,
                                 "getter_call": getter_events[0], "call_targets": tail_targets,
                                 "row_byte": got["row_byte"], "result_byte": got["result_byte"],
                                 "return": got["return"]})

    # Verify original final-helper BL target state.
    targets = []
    for off in range(FINAL_HELPER - CODE_BASE, FINAL_HELPER - CODE_BASE + 820, 4):
        word = struct.unpack_from("<I", original, off)[0]
        if word & 0x0F000000 == 0x0B000000:
            imm = word & 0xFFFFFF
            if imm & 0x800000:
                imm -= 0x1000000
            targets.append((off + CODE_BASE, off + CODE_BASE + 8 + (imm << 2), word))
    calls = [x for x in targets if x[1] == ADDRESS]
    if len(calls) != 1 or calls[0][1] & 1:
        raise AssertionError(f"0x00286928 row call is not a unique even ARM BL: {calls}")

    report = {
        "status": "passed", "seed": args.seed, "reference_sha256": sha(original),
        "production_source_sha256": sha(SOURCE.read_bytes()),
        "production_object_sha256": sha(obj.read_bytes()),
        "production_body_sha256": sha(body), "body_size": len(body), "slot_size": SLOT,
        "relocations": [], "ips_sha256": sha(ips),
        "ips_roundtrip": apply_ips(original, ips) == staged,
        "staged_image_sha256": sha(staged), "slot_only": True,
        "direct_case_count": len(direct), "direct_differences": 0, "direct_cases": direct,
        "callback_composition_case_count": len(compose_rows), "callback_differences": 0,
        "final_helper_compositions": compose_rows,
        "final_helper_getter_callsite": {"site": hex(calls[0][0]), "word": hex(calls[0][2]),
                                          "target": hex(calls[0][1]), "even_arm": True},
        "mutations_detected": {"bound": bound_detected, "offset": offset_detected},
        "mutant_hashes": {"bound_source": sha(pred_src.read_bytes()),
                          "bound_object": sha(pred_obj.read_bytes()),
                          "offset_source": sha(offset_src.read_bytes()),
                          "offset_object": sha(offset_obj.read_bytes())},
        "controlled_callees": [hex(x) for x in STUB_RETURNS],
        "domain": "direct raw 32-bit indices and mapped manager rows; original 0x00286928 row 7/8/9 path with controlled unrelated callees and actual row getter; other final-helper states and complete helper/runtime semantics are outside scope",
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS direct={len(direct)} final_helper={len(compose_rows)} body={len(body)}/{SLOT} relocs=0 mutants=detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
