#!/usr/bin/env python3
"""Compare APT entry through the observed native caller and return path."""
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

import unicorn as u
from unicorn.arm_const import *

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment_support import load_pinned_reference
from tools.h2_apt_utility4_inplace_experiment import (
    ENTRY, ENTRY_SIZE, TEXT, WRAPPER, STOP, STACK, DATA,
    SOURCE, resolve_call_relocation, compose_in_place, verify_call_target,
    verify_original_callers, verify_original_dependencies,
    sha256, REGS, RETURN_VALUES,
)

CALLER = 0x00103E4C
CALLER_END = 0x00103EE0
BRIDGE = 0x002C5624
BRIDGE_DATA_POINTER = 0x0044E3B0
STUBS = (0x002C541C, 0x002C3B00, 0x002C4244,
         0x00110030, 0x0011001C, 0x00110744,
         0x002C57B4, 0x002C57A4)
DATA_FILE_OFFSET = 0x0032B000
DATA_VMA = 0x0042B000
DATA_SIZE = 0x0004B644
COMPOSED_H2_SHA256 = "acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446"


def caller_result(ready_primary: int, ready_secondary: int) -> int:
    return int(ready_primary == 0 and ready_secondary == 0)


def execute(image: bytes, case: dict) -> dict:
    machine = u.Uc(u.UC_ARCH_ARM, u.UC_MODE_ARM)
    machine.mem_map(TEXT, (len(image) + 0xFFF) & ~0xFFF)
    machine.mem_write(TEXT, image)
    machine.mem_map(STACK, 0x4000)
    machine.mem_write(STACK, case["stack"])
    machine.mem_map(STOP, 0x1000)
    machine.reg_write(UC_ARM_REG_CPSR, 0x10 | case["flags"])
    for register, value in zip(REGS, case["regs"]):
        machine.reg_write(register, value)
    initial_sp = STACK + 0x2000
    machine.reg_write(UC_ARM_REG_SP, initial_sp)
    machine.reg_write(UC_ARM_REG_LR, STOP)
    trace = []

    def hook(uc, address, size, _):
        if address == ENTRY:
            trace.append({"target": hex(address), "lr": uc.reg_read(UC_ARM_REG_LR),
                          "r0": uc.reg_read(UC_ARM_REG_R0)})
        elif address == WRAPPER:
            sp = uc.reg_read(UC_ARM_REG_SP)
            args = [uc.reg_read(register) for register in REGS[:4]]
            args += list(struct.unpack("<2I", uc.mem_read(sp, 8)))
            trace.append({"target": hex(address), "args": args,
                          "sp_align": sp & 7,
                          "thumb": bool(uc.reg_read(UC_ARM_REG_CPSR) & 0x20)})
            uc.reg_write(UC_ARM_REG_R0, case["wrapper_return"])
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address in STUBS:
            args = [uc.reg_read(register) for register in REGS[:4]]
            trace.append({"target": hex(address), "args": args})
            if address == 0x002C57B4:
                result = case["ready_primary"]
            elif address == 0x002C57A4:
                result = case["ready_secondary"]
            else:
                result = case["stub_returns"].get(address, 0)
            uc.reg_write(UC_ARM_REG_R0, result)
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    machine.hook_add(u.UC_HOOK_CODE, hook)
    fault = None
    try:
        machine.emu_start(CALLER, STOP, count=1600)
    except u.UcError as exc:
        fault = str(exc)
    data = bytes(machine.mem_read(DATA_VMA, DATA_SIZE))
    return {"pc": machine.reg_read(UC_ARM_REG_PC),
            "sp": machine.reg_read(UC_ARM_REG_SP),
            "r0": machine.reg_read(UC_ARM_REG_R0),
            "preserved": [machine.reg_read(register) for register in REGS[4:12]],
            "stack": bytes(machine.mem_read(initial_sp, 0x100)).hex(),
            "data_sha256": hashlib.sha256(data).hexdigest(),
            "data_changed": changed_runs(image[DATA_FILE_OFFSET:DATA_FILE_OFFSET + DATA_SIZE], data),
            "trace": trace, "fault": fault}


def changed_runs(before: bytes, after: bytes) -> list[dict]:
    changed = []
    index = 0
    while index < len(before):
        if before[index] == after[index]:
            index += 1
            continue
        start = index
        index += 1
        while index < len(before) and before[index] != after[index]:
            index += 1
        changed.append({"offset": hex(start), "length": index - start,
                        "after_hex": after[start:index].hex()})
    return changed


def make_case(rng: random.Random, wrapper_return: int,
              ready_primary: int, ready_secondary: int) -> dict:
    stub_addresses = (0x002C541C, 0x002C3B00, 0x002C4244,
                     0x00110030, 0x0011001C, 0x00110744)
    return {"regs": [rng.getrandbits(32) for _ in REGS],
            "flags": rng.getrandbits(4) << 28,
            "stack": rng.randbytes(0x4000),
            "wrapper_return": wrapper_return,
            "ready_primary": ready_primary,
            "ready_secondary": ready_secondary,
            "stub_returns": {address: rng.getrandbits(32) for address in stub_addresses}}


def compare(left: dict, right: dict, case: dict) -> list[str]:
    errors = []
    for name, result in (("original", left), ("candidate", right)):
        if result["fault"] is not None:
            errors.append(name + ":fault")
        if result["pc"] != STOP:
            errors.append(name + ":caller return PC")
        if result["sp"] != STACK + 0x2000:
            errors.append(name + ":caller SP")
        if result["r0"] != caller_result(case["ready_primary"], case["ready_secondary"]):
            errors.append(name + ":caller result")
        if result["preserved"] != case["regs"][4:12]:
            errors.append(name + ":callee saves")
        if result["stack"] != case["stack"][0x2000:0x2100].hex():
            errors.append(name + ":caller-visible stack")
        if result["trace"].count({"target": hex(ENTRY), "lr": 0x00103E84,
                                   "r0": BRIDGE_DATA_POINTER}) != 1:
            errors.append(name + ":observed entry context")
        wrappers = [row for row in result["trace"] if row.get("target") == hex(WRAPPER)]
        if wrappers != [{"target": hex(WRAPPER), "args": [4, 0, 0, 0, 0, 0],
                         "sp_align": 0, "thumb": False}]:
            errors.append(name + ":wrapper ABI")
        if len([row for row in result["trace"] if row.get("target") == hex(BRIDGE)]) != 0:
            errors.append(name + ":unexpected bridge hook")
    for key in ("pc", "sp", "r0", "preserved", "stack", "data_sha256", "data_changed", "trace", "fault"):
        if left[key] != right[key]:
            errors.append("differential:" + key)
    return errors


def build_body(output: Path) -> tuple[bytes, tuple, list, bytes, list]:
    obj = output / "candidate.o"
    result = compile_tu_armv6k(SOURCE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr)
    body, relocations = extract_elf_functions_detailed(obj)["candidate_002c0efc"]
    resolved, applied = resolve_call_relocation(body, relocations, ENTRY)
    verify_call_target(resolved, relocations[0], ENTRY, WRAPPER)
    return body, relocations, applied, resolved, result.args


def run(code: Path, output: Path, composed_image: Path) -> bool:
    output.mkdir(parents=True, exist_ok=False)
    pinned = load_pinned_reference(code, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    final = composed_image.read_bytes()
    if sha256(final) != COMPOSED_H2_SHA256:
        raise ValueError("reviewed H2 composition hash mismatch")
    if len(final) != len(pinned.image):
        raise ValueError("reviewed H2 composition length mismatch")
    for image in (pinned.image, final):
        verify_original_callers(image, pinned.image)
        verify_original_dependencies(image, pinned.image)
        if image[CALLER - TEXT:CALLER_END - TEXT] != pinned.image[CALLER - TEXT:CALLER_END - TEXT]:
            raise ValueError("selected base changed observed caller window")
        if image[BRIDGE - TEXT:BRIDGE + 0x1C - TEXT] != pinned.image[BRIDGE - TEXT:BRIDGE + 0x1C - TEXT]:
            raise ValueError("selected base changed observed branch bridge")

    body, relocations, applied, resolved, compile_command = build_body(output)
    if len(body) > ENTRY_SIZE:
        raise ValueError("candidate no longer fits original entry")
    candidates = [compose_in_place(pinned.image, resolved), compose_in_place(final, resolved)]
    bases = [("pinned original", pinned.image), ("reviewed composed H2", final)]
    outcomes = ((1, 0), (0, 1), (0, 0), (0xFFFFFFFF, 0))
    failures = []
    counts = {name: 0 for name, _ in bases}
    for (name, base), candidate in zip(bases, candidates):
        for seed in (41, 2026):
            rng = random.Random(seed)
            for primary, secondary in outcomes:
                for returned in RETURN_VALUES:
                    case = make_case(rng, returned, primary, secondary)
                    left, right = execute(base, case), execute(candidate, case)
                    errors = compare(left, right, case)
                    if errors:
                        failures.append({"base": name, "seed": seed,
                                         "ready": [hex(primary), hex(secondary)],
                                         "wrapper_return": hex(returned), "errors": errors})
                    else:
                        counts[name] += 1

    report = {"passed": not failures,
              "caller": hex(CALLER), "caller_return": hex(CALLER_END - 4),
              "observed_lr_at_candidate": hex(0x00103E84),
              "candidate_size": len(body), "entry_size": ENTRY_SIZE,
              "relocations": [{"offset": item.offset, "type": item.relocation_type,
                               "symbol": item.symbol_name,
                               "explicit_addend": item.explicit_addend}
                              for item in relocations],
              "applied_relocations": applied,
              "base_hashes": {name: sha256(image) for name, image in bases},
              "candidate_image_hashes": {name: sha256(candidate)
                                         for (name, _), candidate in zip(bases, candidates)},
              "cases_by_base": counts, "failures": failures,
              "branch_scenarios": [{"ready_primary": hex(a), "ready_secondary": hex(b),
                                    "expected caller result": caller_result(a, b)}
                                   for a, b in outcomes],
              "compile_command": compile_command,
              "limitations": ["The APT wrapper and non-APT dependencies are controlled hooks.",
                              "The native caller, 0x002C5624 bridge, actual stores and return continuation execute from the pinned image.",
                              "This is an offline Unicorn composition; service effects, Thumb callers, indirect paths and Azahar runtime remain untested."]}
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "cases_by_base": counts,
                      "failures": failures[:5], "candidate_size": len(body)}))
    return report["passed"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--composed-image", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if run(args.code, args.output, args.composed_image) else 1)
