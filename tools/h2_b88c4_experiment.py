#!/usr/bin/env python3
"""Pinned ARM differential for the H2 touch-region registrar and helper chain."""
from __future__ import annotations

import hashlib
import json
import random
import struct
import sys
from pathlib import Path

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

IMAGE = (ROOT / "extracted/exefs/code.bin").read_bytes()
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
CALLER_SOURCE = ROOT / "src/engine/leaf_batch32_c.cpp"
MANAGER_SOURCE = ROOT / "src/engine/leaf_batch39_a.cpp"
OUT = ROOT / "build/agent-work/H2-semantic/h2-helper-002b88c4-touch-region-convert/run001"
CALLER = 0x002B88C4
CALLER_SPAN = 220
SLOT_HELPER = 0x002BF6D0
SLOT_SPAN = 64
MANAGER_SERVICE = 0x002B0188
MANAGER_SPAN = 24
MANAGER_TABLE_PTR = 0x0044EA28
MANAGER_TABLE = 0x00940000
CANDIDATE = 0x00800000
STOP = 0x0080F000
TEXT = 0x00100000
TOUCH_GLOBAL_PTR = 0x0043DCB4
TOUCH_WORK = 0x00920000
MANAGER = 0x00901000
MANAGER_ENTRY = 0x00902000
INDIRECT = 0x00900100
NODE_BASE = 0x00910000
RECT = 0x00930000
STACK = 0x00A0FF00
GROUP = 0x1D
NODE_ID = 0x572


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_function(source: Path, function: str, name: str, entry: int, limit: int):
    OUT.mkdir(parents=True, exist_ok=True)
    obj = OUT / name
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)[function]
    fixed = bytearray(body)
    resolved = []
    expected = {"camp_func_002b88c4": {"camp_func_002bf6d0": SLOT_HELPER}}[function]
    for rel in relocs:
        if rel.relocation_type != 28 or rel.symbol_name not in expected or rel.explicit_addend is not None:
            raise AssertionError(f"unsupported relocation: {rel}")
        target = expected[rel.symbol_name]
        place = entry + rel.offset
        ins = struct.unpack_from("<I", fixed, rel.offset)[0]
        if ins & 0xFF000000 != 0xEB000000:
            raise AssertionError(f"expected ARM BL at {rel.offset:#x}, got {ins:#010x}")
        delta = target - (place + 8)
        struct.pack_into("<I", fixed, rel.offset, 0xEB000000 | ((delta >> 2) & 0xFFFFFF))
        resolved.append({"offset": rel.offset, "target": hex(target), "type": rel.relocation_type})
    if len(fixed) > limit or len(fixed) % 4:
        raise AssertionError(f"{function} body {len(fixed)} exceeds slot {limit}")
    return bytes(fixed), resolved


def setup(caller_body=None, caller_entry=CANDIDATE, image=IMAGE):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(TEXT, 0x00500000)
    uc.mem_write(TEXT, image)
    uc.mem_map(0x00800000, 0x10000)
    uc.mem_map(0x00900000, 0x50000)
    uc.mem_map(0x00A00000, 0x10000)
    uc.mem_write(TOUCH_GLOBAL_PTR, struct.pack("<I", TOUCH_WORK))
    uc.mem_write(INDIRECT, struct.pack("<I", NODE_BASE))
    uc.mem_write(MANAGER + 4, struct.pack("<I", INDIRECT))
    uc.mem_write(MANAGER_TABLE_PTR, struct.pack("<I", MANAGER_TABLE))
    # 0x00138B90 selects manager base + trunc(node_id / 1000) * 32.
    uc.mem_write(MANAGER_TABLE + GROUP * 24, struct.pack("<I", MANAGER_ENTRY))
    uc.mem_write(MANAGER_ENTRY, struct.pack("<I", MANAGER - (NODE_ID // 1000) * 32))
    if caller_body is not None:
        uc.mem_write(caller_entry, caller_body)
    state = {"done": False, "writes": [], "caller_args": [], "manager_args": [], "events": []}

    def on_code(machine, address, _size, _data):
        if address == SLOT_HELPER:
            state["caller_args"].append((machine.reg_read(UC_ARM_REG_R0), machine.reg_read(UC_ARM_REG_R1)))
            state["events"].append("slot-helper")
        elif address == MANAGER_SERVICE:
            state["manager_args"].append((machine.reg_read(UC_ARM_REG_R0), machine.reg_read(UC_ARM_REG_R1)))
            state["events"].append("manager-service")
        elif address == STOP:
            state["done"] = True
            machine.emu_stop()

    def on_write(_machine, _kind, address, size, value, _data):
        state["writes"].append((address, size, value & 0xFFFFFFFF))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    uc._state = state
    return uc


def fixture(uc, count: int, custom: bool, seed: int):
    rng = random.Random(seed)
    signed_rem = NODE_ID % 1000
    node_addr = NODE_BASE + signed_rem * 20
    node = bytearray(20)
    struct.pack_into("<HHhhI", node, 4, rng.getrandbits(15) | 0x8000, rng.getrandbits(15) | 0x8000,
                      rng.randint(-32768, 32767), rng.randint(-32768, 32767), RECT if custom else 0)
    rect = struct.pack("<hh", rng.randint(-32768, 32767), rng.randint(-32768, 32767))
    uc.mem_write(node_addr, bytes(node))
    uc.mem_write(RECT, rect)
    uc.mem_write(TOUCH_WORK, bytes(0x700))
    uc.mem_write(TOUCH_WORK + 0x64A, struct.pack("<h", count))
    # Vary the whole record area so the observation includes preservation.
    uc.mem_write(TOUCH_WORK + 0x0A, bytes(rng.getrandbits(8) for _ in range(0x640)))
    uc.mem_write(TOUCH_WORK + 0x64A, struct.pack("<h", count))
    return node_addr


def execute(uc, entry: int, count: int, custom: bool, seed: int):
    state = uc._state
    state.update(done=False, writes=[], caller_args=[], manager_args=[], events=[])
    node_addr = fixture(uc, count, custom, seed)
    rng = random.Random(seed ^ 0xB88C4)
    regs = (UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
            UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11)
    before = {reg: rng.getrandbits(32) for reg in regs}
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, STOP)
    for reg, value in before.items():
        uc.reg_write(reg, value)
    uc.reg_write(UC_ARM_REG_R0, GROUP)
    uc.reg_write(UC_ARM_REG_R1, NODE_ID)
    try:
        uc.emu_start(entry, 0, count=2000)
        fault = None
    except (UcError, OSError) as exc:
        fault = str(exc)
    sp = uc.reg_read(UC_ARM_REG_SP)
    external_writes = tuple(w for w in state["writes"] if not STACK - 32 <= w[0] < STACK)
    observed = {
        "return": uc.reg_read(UC_ARM_REG_R0),
        "callee_saved": all(uc.reg_read(reg) == value for reg, value in before.items() if reg not in (UC_ARM_REG_R2, UC_ARM_REG_R3)),
        "sp": sp == STACK,
        "caller_args": tuple(state["caller_args"]),
        "manager_args": tuple(state["manager_args"]),
        "external_writes": external_writes,
        "count": struct.unpack("<h", uc.mem_read(TOUCH_WORK + 0x64A, 2))[0],
        "records": bytes(uc.mem_read(TOUCH_WORK + 0x0A, 0x640)),
        "done": state["done"],
        "fault": fault,
    }
    if not observed["done"] or fault or not observed["callee_saved"] or not observed["sp"]:
        raise AssertionError(f"execution/ABI failure: {observed}")
    if observed["caller_args"] != ((GROUP, NODE_ID),):
        raise AssertionError(f"caller helper args differ: {observed['caller_args']}")
    if observed["manager_args"] != ((GROUP, NODE_ID),):
        raise AssertionError(f"manager args differ: {observed['manager_args']}")
    return observed, node_addr


def candidate_at(body: bytes, entry: int):
    return setup(body, entry)


def compile_manager(entry: int):
    obj = OUT / ("manager-final.o" if entry == MANAGER_SERVICE else "manager-temp.o")
    result = compile_tu_armv6k(MANAGER_SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocs = extract_elf_functions_detailed(obj)["ui_func_002b0188"]
    fixed = bytearray(body)
    resolved = []
    if len(relocs) != 1:
        raise AssertionError(f"expected one manager tail relocation, got {relocs}")
    for rel in relocs:
        if rel.relocation_type != 29 or rel.symbol_name != "func_00138b90" or rel.explicit_addend is not None:
            raise AssertionError(f"unsupported manager relocation: {rel}")
        ins = struct.unpack_from("<I", fixed, rel.offset)[0]
        if ins & 0x0F000000 != 0x0A000000:
            raise AssertionError(f"expected ARM B at {rel.offset:#x}, got {ins:#010x}")
        struct.pack_into("<I", fixed, rel.offset,
                         (ins & 0xFF000000) | (((0x00138B90 - (entry + rel.offset + 8)) >> 2) & 0xFFFFFF))
        resolved.append({"offset": rel.offset, "target": "0x138b90", "type": rel.relocation_type})
    if len(fixed) > MANAGER_SPAN:
        raise AssertionError(f"manager candidate {len(fixed)} exceeds slot {MANAGER_SPAN}")
    return bytes(fixed), resolved


def run():
    caller_temp, caller_temp_relocs = compile_function(CALLER_SOURCE, "camp_func_002b88c4", "caller-temp.o", CANDIDATE, CALLER_SPAN)
    caller_final, caller_final_relocs = compile_function(CALLER_SOURCE, "camp_func_002b88c4", "caller-final.o", CALLER, CALLER_SPAN)
    manager_final, manager_final_relocs = compile_manager(MANAGER_SERVICE)
    original = setup()
    temporary = candidate_at(caller_temp, CANDIDATE)
    integrated = candidate_at(caller_final, CALLER)
    integrated.mem_write(MANAGER_SERVICE, manager_final)
    counts = (0, 1, 37, 199, 200)
    cases = [(count, custom, 0x20261102 + i) for i, (count, custom) in enumerate(
        ( (n, c) for n in counts for c in (False, True) ))]
    rng = random.Random(20261102)
    cases.extend((rng.randrange(0, 200), bool(i & 1), rng.getrandbits(32)) for i in range(48))
    for i, (count, custom, seed) in enumerate(cases):
        ref, _ = execute(original, CALLER, count, custom, seed)
        cand, _ = execute(temporary, CANDIDATE, count, custom, seed)
        final, _ = execute(integrated, CALLER, count, custom, seed)
        if ref != cand or ref != final:
            def compact(value):
                return {k: (sha(v) if k == "records" else v) for k, v in value.items()}
            raise AssertionError(f"case {i} count={count} custom={custom}: reference={compact(ref)} candidate={compact(cand)} final={compact(final)}")
    controls = []
    source_text = CALLER_SOURCE.read_text(encoding="utf-8")
    for name, old, new, count, custom in (
        ("capacity", "kRegionCapacity = 0xC8", "kRegionCapacity = 0xC7", 199, False),
        ("flag-mask", "flags_a & 0x7FFFu", "flags_a", 0, False),
    ):
        if source_text.count(old) != 1:
            raise AssertionError(f"mutant anchor not unique: {name}")
        mutant_source = OUT / f"mutant-{name}.cpp"
        mutant_source.write_text(source_text.replace(old, new, 1), encoding="utf-8")
        mutant, _ = compile_function(mutant_source, "camp_func_002b88c4", f"mutant-{name}.o", CANDIDATE, CALLER_SPAN)
        ref, _ = execute(original, CALLER, count, custom, 9000)
        mut_profile = candidate_at(mutant, CANDIDATE)
        mutated, _ = execute(mut_profile, CANDIDATE, count, custom, 9000)
        if ref == mutated:
            raise AssertionError(f"negative control missed: {name}")
        controls.append({"name": name, "detected": True, "count": count, "custom": custom})
    return {
        "cases": len(cases), "directed_counts": list(counts), "custom_and_inline_region_forms": True,
        "seeded_cases": 48, "seed": "20261102", "negative_controls": controls,
        "composition": "original 0x002BF6D0 body and 0x00138B90 execute in all profiles; final profile installs compiled 0x002B0188 and records both inputs",
        "store_order_note": "volatile work/count reloads and region stores preserve the original load/check/store order; ordered write traces match.",
    }, caller_temp, caller_final, caller_temp_relocs, caller_final_relocs, manager_final, manager_final_relocs


def main():
    if sha(IMAGE) != IMAGE_SHA:
        raise SystemExit("pinned image hash mismatch")
    direct, body, final_body, relocs, final_relocs, manager_body, manager_relocs = run()
    report = {
        "function": "camp_func_002b88c4", "address": hex(CALLER),
        "reference_image_sha256": sha(IMAGE),
        "caller_source_sha256": sha(CALLER_SOURCE.read_bytes()),
        "caller_body_sha256": sha(body), "caller_body_size": len(body),
        "caller_byte_identical": body == IMAGE[CALLER - TEXT:CALLER - TEXT + CALLER_SPAN],
        "caller_relocations": relocs, "final_caller_relocations": final_relocs,
        "manager_source_sha256": sha(MANAGER_SOURCE.read_bytes()),
        "manager_body_sha256": sha(manager_body), "manager_body_size": len(manager_body),
        "manager_relocations": manager_relocs,
        "helper_contract": "original 0x002BF6D0 and 0x00138B90 execute; final profile installs compiled 0x002B0188",
        "direct_and_composed": direct,
        "runtime": "not_run; offline pinned-ARM caller/helper composition only",
    }
    out = OUT / "report.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"report: {out}")


if __name__ == "__main__":
    main()
