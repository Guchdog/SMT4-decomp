#!/usr/bin/env python3
"""Pinned direct and H2 caller differential for helper 0x002BF6D0."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import random
import struct
import sys

from unicorn import Uc, UcError, UC_ARCH_ARM, UC_MODE_ARM, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn.arm_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h2_calc_code_patch import apply_ips, encode_ips
from tools import h2_b88c4_experiment as caller

IMAGE = ROOT / "extracted/exefs/code.bin"
IMAGE_SHA = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
SOURCE = ROOT / "src/engine/leaf_batch27_b.cpp"
ADDRESS = 0x002BF6D0
SLOT_SIZE = 64
RESOLVER = 0x002B0188
DIVIDER = 0x002C615C
TEXT = 0x00100000
MANAGER = 0x00901000
INDIRECT = 0x00900100
NODE_BASE = 0x00910000
STACK = 0x00A0FF00
STOP = 0x00B00000
DATA_BASE = 0x00900000
DATA_SIZE = 0x00050000
STACK_BASE = 0x00A00000
STACK_SIZE = 0x00010000
CALLEE_SAVED = (UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6,
                UC_ARM_REG_R7, UC_ARM_REG_R8, UC_ARM_REG_R9,
                UC_ARM_REG_R10, UC_ARM_REG_R11)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compile_function(out: Path, source: Path = SOURCE):
    out.mkdir(parents=True, exist_ok=True)
    obj = out / "leaf_batch27_b.o"
    result = compile_tu_armv6k(source, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "production TU compilation failed")
    body, relocations = extract_elf_functions_detailed(obj)["camp_func_002bf6d0"]
    if len(body) > SLOT_SIZE or len(body) % 4:
        raise ValueError(f"candidate body {len(body)} does not fit the 64-byte ARM slot")
    fixed = bytearray(body)
    records = []
    targets = {"ui_func_002b0188": RESOLVER, "ui_func_002c615c": DIVIDER}
    for relocation in relocations:
        if relocation.relocation_type != 28 or relocation.symbol_name not in targets \
                or relocation.explicit_addend is not None:
            raise ValueError(f"unsupported relocation: {relocation}")
        target = targets[relocation.symbol_name]
        place = ADDRESS + relocation.offset
        delta = target - (place + 8)
        if target & 1 or delta & 3 or not -(1 << 25) <= delta < (1 << 25):
            raise ValueError(f"invalid ARM BL relocation {place:#x}->{target:#x}")
        word = 0xEB000000 | ((delta >> 2) & 0xFFFFFF)
        struct.pack_into("<I", fixed, relocation.offset, word)
        records.append({"offset": relocation.offset, "symbol": relocation.symbol_name,
                        "target": hex(target), "entry_bit0": target & 1,
                        "type": "R_ARM_CALL", "word": hex(word)})
    if {row["target"] for row in records} != {hex(RESOLVER), hex(DIVIDER)}:
        raise ValueError(f"expected resolver and divider calls, found {records}")
    return bytes(fixed), records, list(result.args)


def slot_payload(body: bytes) -> bytes:
    if len(body) > SLOT_SIZE or (SLOT_SIZE - len(body)) % 4:
        raise ValueError("compiled body cannot be padded within the ARM slot")
    return body + struct.pack("<I", 0xE320F000) * ((SLOT_SIZE - len(body)) // 4)


def stage_image(original: bytes, body: bytes) -> tuple[bytes, bytes]:
    payload = slot_payload(body)
    offset = ADDRESS - TEXT
    staged = bytearray(original)
    staged[offset:offset + SLOT_SIZE] = payload
    return bytes(staged), payload


def direct_machine(image: bytes):
    uc = Uc(UC_ARCH_ARM, UC_MODE_ARM)
    uc.mem_map(TEXT, 0x00500000)
    uc.mem_write(TEXT, image)
    uc.mem_map(DATA_BASE, DATA_SIZE)
    uc.mem_map(STACK_BASE, STACK_SIZE)
    uc.mem_map(STOP, 0x1000)
    uc.mem_write(MANAGER + 4, struct.pack("<I", INDIRECT))
    uc.mem_write(INDIRECT, struct.pack("<I", NODE_BASE))
    state = {"resolver_args": [], "writes": [], "stopped": False}

    def on_code(machine, address, _size, _data):
        if address == RESOLVER:
            state["resolver_args"].append((machine.reg_read(UC_ARM_REG_R0),
                                           machine.reg_read(UC_ARM_REG_R1)))
            machine.reg_write(UC_ARM_REG_R0, MANAGER)
            machine.reg_write(UC_ARM_REG_PC, machine.reg_read(UC_ARM_REG_LR))
        elif address == STOP:
            state["stopped"] = True
            machine.emu_stop()

    def on_write(_machine, _kind, address, size, value, _data):
        state["writes"].append((address, size, value & 0xFFFFFFFF))

    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    return uc, state


def invoke_direct(uc, state: dict, group: int, node_index: int, seed: int) -> dict:
    state.update(resolver_args=[], writes=[], stopped=False)
    rng = random.Random(seed)
    before = []
    for i, reg in enumerate(CALLEE_SAVED):
        value = (0xB7000000 + i * 0x01020305) & 0xFFFFFFFF
        uc.reg_write(reg, value)
        before.append(value)
    uc.reg_write(UC_ARM_REG_SP, STACK)
    uc.reg_write(UC_ARM_REG_LR, STOP)
    uc.reg_write(UC_ARM_REG_R0, group & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R1, node_index & 0xFFFFFFFF)
    uc.reg_write(UC_ARM_REG_R2, rng.getrandbits(32))
    uc.reg_write(UC_ARM_REG_R3, rng.getrandbits(32))
    fault = None
    try:
        uc.emu_start(ADDRESS, 0, count=10000)
    except (UcError, OSError) as error:
        fault = type(error).__name__ + ": " + str(error)
    return {
        "fault": fault, "stopped": state["stopped"],
        "raw_r0": uc.reg_read(UC_ARM_REG_R0),
        "callee_saved": [uc.reg_read(reg) for reg in CALLEE_SAVED],
        "callee_saved_preserved": [uc.reg_read(reg) for reg in CALLEE_SAVED] == before,
        "sp": uc.reg_read(UC_ARM_REG_SP), "resolver_args": state["resolver_args"],
        "non_stack_writes": [w for w in state["writes"]
                             if not STACK - 0x100 <= w[0] < STACK + 0x100],
        "stack_write_count": sum(STACK - 0x100 <= w[0] < STACK + 0x100
                                  for w in state["writes"]),
    }


def compare_direct(result: dict) -> dict:
    return {key: result[key] for key in (
        "fault", "stopped", "raw_r0", "callee_saved", "callee_saved_preserved",
        "sp", "resolver_args", "non_stack_writes")}


def compile_mutant(out: Path, name: str, before: str, after: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(before) != 1:
        raise ValueError(f"mutation {name} anchor is not unique")
    path = out / "mutants" / f"{name}.cpp"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.replace(before, after, 1), encoding="utf-8")
    body, _relocs, _args = compile_function(out / "mutants" / f"{name}-compile", path)
    return body


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=20261114)
    parser.add_argument("--direct-count", type=int, default=256)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    original = IMAGE.read_bytes()
    if sha(original) != IMAGE_SHA:
        raise SystemExit("pinned code.bin hash mismatch")

    body, relocations, compiler_args = compile_function(args.out / "compile")
    staged, payload = stage_image(original, body)
    offset = ADDRESS - TEXT
    ips = encode_ips([(offset, payload)], len(original))
    if apply_ips(original, ips) != staged:
        raise AssertionError("exact-slot IPS replay failed")
    if original[:offset] != staged[:offset] or original[offset + SLOT_SIZE:] != staged[offset + SLOT_SIZE:]:
        raise AssertionError("patch changed bytes outside helper slot")
    (args.out / "staged-image.bin").write_bytes(staged)
    (args.out / "staged-slot.ips").write_bytes(ips)

    directed = set(range(-1000, 1001))
    directed.update((-0x80000000, -0x80000000 + 1, -0x80000000 + 999,
                     -0x7FFFFFFF, -1000001, -1000000, -999999, -1, 0, 1,
                     999999, 1000000, 1000001, 0x7FFFFFFF - 999,
                     0x7FFFFFFF - 1, 0x7FFFFFFF))
    indices = sorted(directed)
    rng = random.Random(args.seed ^ 0xBF6D0)
    indices.extend(rng.randint(-0x80000000, 0x7FFFFFFF)
                   for _ in range(args.direct_count))
    groups = (0, 1, 0x1D, 0x24, 0x2F, 0xFFFFFFFF)

    original_uc, original_state = direct_machine(original)
    candidate_uc, candidate_state = direct_machine(staged)
    mismatches = []
    direct_count = 0
    for i, node_index in enumerate(indices):
        group = groups[i % len(groups)]
        seed = args.seed ^ i
        ref = invoke_direct(original_uc, original_state, group, node_index, seed)
        got = invoke_direct(candidate_uc, candidate_state, group, node_index, seed)
        if compare_direct(ref) != compare_direct(got):
            mismatches.append({"index": i, "group": group,
                               "node_index": node_index,
                               "original": ref, "candidate": got})
        if got["resolver_args"] != [(group, node_index & 0xFFFFFFFF)]:
            mismatches.append({"index": i, "kind": "resolver forwarding",
                               "expected": [group, node_index & 0xFFFFFFFF],
                               "candidate": got["resolver_args"]})
        signed_quotient = abs(node_index) // 1000
        if node_index < 0:
            signed_quotient = -signed_quotient
        expected_remainder = node_index - signed_quotient * 1000
        expected_pointer = (NODE_BASE + expected_remainder * 20) & 0xFFFFFFFF
        if got["raw_r0"] != expected_pointer or got["sp"] != STACK \
                or not got["callee_saved_preserved"] or got["non_stack_writes"]:
            mismatches.append({"index": i, "kind": "contract", "group": group,
                               "node_index": node_index, "expected_return": expected_pointer,
                               "candidate": got})
        direct_count += 1

    # Existing H2 touch caller reads the returned node at +4/+8/+0xC and
    # therefore checks the computed remainder pointer in a real consumer.
    original_profile = caller.setup(image=original)
    candidate_profile = caller.setup(image=staged)
    caller_cases = []
    counts = (0, 1, 37, 199, 200)
    cases = [(n, custom, 0x20261114 + i) for i, (n, custom) in enumerate(
        (pair for n in counts for pair in ((n, False), (n, True))))]
    caller_rng = random.Random(args.seed ^ 0x88C4)
    cases.extend((caller_rng.randrange(0, 200), bool(i & 1), caller_rng.getrandbits(32))
                 for i in range(32))
    for i, (count, custom, case_seed) in enumerate(cases):
        ref, _ = caller.execute(original_profile, caller.CALLER, count, custom, case_seed)
        got, _ = caller.execute(candidate_profile, caller.CALLER, count, custom, case_seed)
        # The candidate calls the original divide helper, whose documented
        # stack spill residue differs from the inline-magic original. Stack
        # below the caller SP is not treated as caller-visible object memory.
        for result in (ref, got):
            result["external_writes"] = [w for w in result["external_writes"]
                                          if not caller.STACK - 0x100 <= w[0] < caller.STACK]
        if ref != got:
            caller_cases.append({"case": i, "count": count, "custom": custom,
                                 "seed": case_seed, "original": ref, "candidate": got})

    affected_tus = []
    for tu_name in ("leaf_batch27_b", "leaf_batch32_c"):
        obj = args.out / "affected-tus" / f"{tu_name}.o"
        obj.parent.mkdir(parents=True, exist_ok=True)
        compiled = compile_tu_armv6k(ROOT / f"src/engine/{tu_name}.cpp", obj, ROOT)
        affected_tus.append({"tu": tu_name, "returncode": compiled.returncode,
                             "object": str(obj), "compiler_args": list(compiled.args)})
        if compiled.returncode:
            raise RuntimeError(compiled.stderr or f"{tu_name} compilation failed")

    controls_spec = [
        ("wrong_block_divisor", "ui_func_002c615c(node_index, 1000)",
         "ui_func_002c615c(node_index, 999)", 999),
        ("resolver_index_forwarding", "ui_func_002b0188(group, node_index)",
         "ui_func_002b0188(group, node_index - node_index)", 0x572),
        ("node_stride", "static_cast<u32>(remainder * 20)",
         "static_cast<u32>(remainder * 16)", 0x572),
    ]
    controls = {}
    for name, before, after, node_index in controls_spec:
        mutant_body = compile_mutant(args.out, name, before, after)
        mutant_image, mutant_payload = stage_image(original, mutant_body)
        ref = invoke_direct(original_uc, original_state, 0x1D, node_index, args.seed)
        mutant_uc, mutant_state = direct_machine(mutant_image)
        mutant = invoke_direct(mutant_uc, mutant_state, 0x1D, node_index, args.seed)
        controls[name] = {"detected": compare_direct(ref) != compare_direct(mutant),
                          "original": ref, "mutant": mutant,
                          "body_bytes": len(mutant_body)}

    report = {
        "image_sha256": sha(original), "source_sha256": sha(SOURCE.read_bytes()),
        "candidate_body_sha256": sha(body), "candidate_body_bytes": len(body),
        "original_slot_bytes": SLOT_SIZE, "byte_identical": body == original[offset:offset + len(body)],
        "relocations": relocations, "direct_cases": direct_count,
        "direct_mismatches": mismatches, "caller_cases": len(cases),
        "caller_mismatches": caller_cases, "mutation_controls": controls,
        "ips_replay": apply_ips(original, ips) == staged,
        "only_original_slot_changed": original[:offset] == staged[:offset]
            and original[offset + SLOT_SIZE:] == staged[offset + SLOT_SIZE:],
        "compiler_args": compiler_args, "affected_tus": affected_tus,
        "scope": "original 0x002B0188 manager resolver and 0x002C615C signed divider, direct helper and original 0x002B88C4 caller",
        "limits": ["valid aligned synthetic ordinary RAM", "candidate divider call leaves stack spill bytes below SP; stack spill residue is not compared",
                   "manager resolver uses real code in caller composition and deterministic return seam in direct cases",
                   "runtime/lifecycle and arbitrary alias/fault domains are not claimed"]
    }
    (args.out / "report.json").write_text(
        json.dumps(report, indent=2, default=lambda value: value.hex()
                   if isinstance(value, bytes) else str(value)) + "\n")
    print(json.dumps({"candidate_body_bytes": len(body), "slot_bytes": SLOT_SIZE,
                      "relocations": relocations, "direct_cases": direct_count,
                      "direct_mismatches": len(mismatches),
                      "caller_cases": len(cases), "caller_mismatches": len(caller_cases),
                      "controls": {name: row["detected"] for name, row in controls.items()},
                      "ips_replay": report["ips_replay"],
                      "only_original_slot_changed": report["only_original_slot_changed"]}, indent=2))
    return 0 if not mismatches and not caller_cases and all(x["detected"] for x in controls.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
