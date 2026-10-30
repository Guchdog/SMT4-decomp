#!/usr/bin/env python3
"""Differentially test a compact in-place APT utility-4 candidate offline."""
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

from tools.asm_diff import ElfRelocation, extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment_support import load_pinned_reference

TEXT = 0x00100000
ENTRY = 0x002C0EFC
ENTRY_SIZE = 44
WRAPPER = 0x002B5A1C
CALLER_RETURN = 0x01000000
STACK = 0x08000000
SP = STACK + 0x1000
DATA = 0x02000000
STOP = 0x01000000
BL_CALLERS = (0x002C0F6C, 0x002C1260, 0x002C1304)
B_CALLERS = (0x00106F00, 0x0010700C, 0x002A8164, 0x002C5638)
FALLTHROUGH = 0x002C0EE0
HELPERS = (0x002BB7A0, 0x002BB774)
SOURCE = ROOT / "experiments/semantic_equivalence/h2_apt_utility4_inplace_candidate.cpp"
COMPOSED_H2_SHA256 = "acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446"
REGS = [UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3,
        UC_ARM_REG_R4, UC_ARM_REG_R5, UC_ARM_REG_R6, UC_ARM_REG_R7,
        UC_ARM_REG_R8, UC_ARM_REG_R9, UC_ARM_REG_R10, UC_ARM_REG_R11,
        UC_ARM_REG_R12]
RETURN_VALUES = (0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def resolve_call_relocation(body: bytes, relocations: tuple[ElfRelocation, ...],
                            place: int, target: int = WRAPPER) -> tuple[bytes, list[dict]]:
    """Resolve one ELF32 ARM R_ARM_CALL, rejecting all other code relocations."""
    fixed = bytearray(body)
    if len(relocations) != 1:
        raise ValueError(f"expected exactly one function relocation; got {len(relocations)}")
    relocation = relocations[0]
    if relocation.relocation_type != 28 or relocation.symbol_name != "apt_wrapper":
        raise ValueError(f"unsupported call relocation: {relocation}")
    if relocation.explicit_addend is not None:
        raise ValueError("unexpected explicit ARM call addend")
    offset = relocation.offset
    if offset < 0 or offset + 4 > len(fixed):
        raise ValueError("call relocation lies outside candidate body")
    instruction = struct.unpack_from("<I", fixed, offset)[0]
    if instruction & 0x0F000000 != 0x0B000000:
        raise ValueError(f"R_ARM_CALL does not point to ARM BL: {instruction:#010x}")
    encoded_addend = instruction & 0x00FFFFFF
    if encoded_addend & 0x00800000:
        encoded_addend -= 0x01000000
    addend = encoded_addend << 2
    call_pc = place + offset
    displacement = target + addend - call_pc
    if displacement & 3 or displacement < -0x02000000 or displacement > 0x01FFFFFC:
        raise ValueError(f"ARM BL target is out of range/alignment: {displacement:#x}")
    linked = (instruction & 0xFF000000) | ((displacement >> 2) & 0x00FFFFFF)
    struct.pack_into("<I", fixed, offset, linked)
    signed_imm = linked & 0x00FFFFFF
    if signed_imm & 0x00800000:
        signed_imm -= 0x01000000
    decoded_target = call_pc + 8 + (signed_imm << 2)
    if decoded_target != target:
        raise ValueError("resolved ARM BL does not decode to the required wrapper")
    return bytes(fixed), [{"offset": offset, "type": "R_ARM_CALL",
                           "symbol": relocation.symbol_name,
                           "addend": addend, "place": hex(call_pc),
                           "target": hex(target), "instruction": hex(linked)}]


def verify_call_target(body: bytes, relocation: ElfRelocation, place: int,
                       expected_target: int) -> None:
    instruction = struct.unpack_from("<I", body, relocation.offset)[0]
    if instruction & 0x0F000000 != 0x0B000000:
        raise ValueError("candidate call instruction is not ARM BL")
    immediate = instruction & 0x00FFFFFF
    if immediate & 0x00800000:
        immediate -= 0x01000000
    actual_target = place + relocation.offset + 8 + (immediate << 2)
    if actual_target != expected_target:
        raise ValueError(f"candidate wrapper target {actual_target:#x} != {expected_target:#x}")


def compose_in_place(reference: bytes, body: bytes) -> bytes:
    if len(reference) != 0x377000:
        raise ValueError(f"unexpected pinned image size: {len(reference):#x}")
    if len(body) <= 0 or len(body) > ENTRY_SIZE:
        raise ValueError(f"candidate body must fit the {ENTRY_SIZE}-byte original entry")
    offset = ENTRY - TEXT
    if reference[offset:offset + ENTRY_SIZE] == bytes(ENTRY_SIZE):
        raise ValueError("original entry unexpectedly empty")
    if ENTRY + ENTRY_SIZE != 0x002C0F28:
        raise ValueError("unexpected adjacent function boundary")
    patched = bytearray(reference)
    patched[offset:offset + len(body)] = body
    if patched[:offset] != reference[:offset] or patched[offset + ENTRY_SIZE:] != reference[offset + ENTRY_SIZE:]:
        raise ValueError("in-place body changed bytes outside the original entry")
    if patched[offset + len(body):offset + ENTRY_SIZE] != reference[offset + len(body):offset + ENTRY_SIZE]:
        raise ValueError("candidate overwrote trailing bytes in the original entry")
    return bytes(patched)


def verify_original_callers(image: bytes, original: bytes) -> None:
    for address, expects_link in tuple((site, True) for site in BL_CALLERS) + tuple(
            (site, False) for site in B_CALLERS):
        offset = address - TEXT
        raw = image[offset:offset + 4]
        if raw != original[offset:offset + 4]:
            raise ValueError(f"selected base changed caller instruction at {address:#x}")
        instruction = struct.unpack("<I", raw)[0]
        if instruction & 0x0E000000 != 0x0A000000:
            raise ValueError(f"caller is not an ARM B/BL at {address:#x}")
        if ((instruction >> 24) & 1) != expects_link or instruction >> 28 != 0xE:
            raise ValueError(f"caller branch kind/condition mismatch at {address:#x}")
        immediate = instruction & 0x00FFFFFF
        if immediate & 0x00800000:
            immediate -= 0x01000000
        if address + 8 + (immediate << 2) != ENTRY:
            raise ValueError(f"caller target mismatch at {address:#x}")


def verify_original_dependencies(image: bytes, original: bytes) -> None:
    ranges = ((0x002C0EE0, 28, "fallthrough entry"),
              (0x002C0F28, 1016, "following function"),
              (WRAPPER, 204, "original wrapper"),
              (0x002BB7A0, 16, "first fallthrough helper"),
              (0x002BB774, 44, "second fallthrough helper"))
    for address, size, name in ranges:
        offset = address - TEXT
        if image[offset:offset + size] != original[offset:offset + size]:
            raise ValueError(f"selected base changed pinned {name} at {address:#x}")


def make_case(rng: random.Random, result: int) -> dict:
    return {"regs": [rng.getrandbits(32) for _ in REGS],
            "flags": rng.getrandbits(4) << 28, "ret": result,
            "stack": rng.randbytes(0x2000), "data": rng.randbytes(0x1000)}


def execute(image: bytes, start: int, case: dict) -> dict:
    machine = u.Uc(u.UC_ARCH_ARM, u.UC_MODE_ARM)
    machine.mem_map(TEXT, (len(image) + 0xFFF) & ~0xFFF)
    machine.mem_write(TEXT, image)
    machine.mem_map(STACK, 0x2000)
    machine.mem_write(STACK, case["stack"])
    machine.mem_map(DATA, 0x1000)
    machine.mem_write(DATA, case["data"])
    machine.mem_map(STOP, 0x1000)
    machine.reg_write(UC_ARM_REG_CPSR, 0x10 | case["flags"])
    for register, value in zip(REGS, case["regs"]):
        machine.reg_write(register, value)
    machine.reg_write(UC_ARM_REG_SP, SP)
    machine.reg_write(UC_ARM_REG_LR, STOP)
    trace = []

    def hook(uc, address, size, _):
        if address in HELPERS:
            trace.append({"target": hex(address), "r0": uc.reg_read(UC_ARM_REG_R0)})
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))
        elif address == WRAPPER:
            wrapper_sp = uc.reg_read(UC_ARM_REG_SP)
            args = [uc.reg_read(register) for register in REGS[:4]]
            args += list(struct.unpack("<2I", uc.mem_read(wrapper_sp, 8)))
            trace.append({"target": hex(address), "args": args,
                          "sp_align": wrapper_sp & 7,
                          "thumb": bool(uc.reg_read(UC_ARM_REG_CPSR) & 0x20)})
            uc.reg_write(UC_ARM_REG_R0, case["ret"])
            uc.reg_write(UC_ARM_REG_PC, uc.reg_read(UC_ARM_REG_LR))

    machine.hook_add(u.UC_HOOK_CODE, hook)
    end = start + 4 if start in BL_CALLERS else STOP
    fault = None
    try:
        machine.emu_start(start, end, count=300)
    except u.UcError as exc:
        fault = str(exc)
    return {"pc": machine.reg_read(UC_ARM_REG_PC),
            "sp": machine.reg_read(UC_ARM_REG_SP),
            "r0": machine.reg_read(UC_ARM_REG_R0),
            "preserved": [machine.reg_read(register) for register in REGS[4:12]],
            "data": bytes(machine.mem_read(DATA, 0x1000)).hex(),
            "live_stack": bytes(machine.mem_read(SP, 0x1000)).hex(),
            "trace": trace, "fault": fault}


def expected_trace(start: int) -> list[dict]:
    trace = []
    if start == FALLTHROUGH:
        trace += [{"target": hex(HELPERS[0]), "r0": 0},
                  {"target": hex(HELPERS[1]), "r0": 1}]
    trace.append({"target": hex(WRAPPER), "args": [4, 0, 0, 0, 0, 0],
                  "sp_align": 0, "thumb": False})
    return trace


def differences(original: dict, patched: dict, start: int, case: dict) -> list[str]:
    end = start + 4 if start in BL_CALLERS else STOP
    errors = []
    for name, result in (("original", original), ("patched", patched)):
        expected = {"pc": end, "fault": None, "sp": SP, "r0": case["ret"],
                    "preserved": case["regs"][4:12], "data": case["data"].hex(),
                    "live_stack": case["stack"][0x1000:].hex(),
                    "trace": expected_trace(start)}
        for key, value in expected.items():
            if result[key] != value:
                errors.append(f"{name}:{key}")
    for key in original:
        if original[key] != patched[key]:
            errors.append("differential:" + key)
    return errors


def run_experiment(code_path: Path, output: Path,
                   base_path: Path | None = None,
                   base_sha256: str | None = None) -> bool:
    output.mkdir(parents=True, exist_ok=False)
    pinned = load_pinned_reference(code_path, ROOT / "config/game_info.json",
                                   ROOT / "config/functions.csv")
    if base_path is None:
        base_image = pinned.image
        base_identity = sha256(base_image)
        if base_sha256 is not None and base_identity != base_sha256:
            raise ValueError("requested base hash does not match pinned original")
        base_kind = "pinned original"
    else:
        base_image = base_path.read_bytes()
        base_identity = sha256(base_image)
        if base_sha256 is None or base_identity != base_sha256:
            raise ValueError("selected composed base requires an exact matching SHA-256")
        if base_identity != COMPOSED_H2_SHA256:
            raise ValueError("unrecognized composed H2 base identity")
        if len(base_image) != len(pinned.image):
            raise ValueError("composed H2 base length differs from the pinned original")
        base_kind = "reviewed composed H2 image"
        off = ENTRY - TEXT
        if base_image[off:off + ENTRY_SIZE] != pinned.image[off:off + ENTRY_SIZE]:
            raise ValueError("selected H2 composition changes the candidate entry span")
    verify_original_callers(base_image, pinned.image)
    verify_original_dependencies(base_image, pinned.image)
    source_hash = sha256(SOURCE.read_bytes())
    object_path = output / "candidate.o"
    build = compile_tu_armv6k(SOURCE, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    symbols = extract_elf_functions_detailed(object_path)
    body, relocations = symbols["candidate_002c0efc"]
    linked_body, applied = resolve_call_relocation(body, relocations, ENTRY)
    verify_call_target(linked_body, relocations[0], ENTRY, WRAPPER)
    patched_image = compose_in_place(base_image, linked_body)

    failure_rows = []
    per_start = {}
    starts = BL_CALLERS + B_CALLERS + (FALLTHROUGH, ENTRY)
    for start in starts:
        per_start[hex(start)] = 0
        for seed in (19, 2026):
            rng = random.Random(seed ^ start)
            for index in range(8 if start == ENTRY else 5):
                case = make_case(rng, RETURN_VALUES[index % len(RETURN_VALUES)])
                left = execute(base_image, start, case)
                right = execute(patched_image, start, case)
                errs = differences(left, right, start, case)
                if errs:
                    failure_rows.append({"start": hex(start), "seed": seed,
                                         "index": index, "errors": errs})
                else:
                    per_start[hex(start)] += 1

    wrong_command = bytearray(patched_image)
    wrong_command[ENTRY - TEXT + 16:ENTRY - TEXT + 20] = bytes.fromhex("0500a0e3")
    negative_case = make_case(random.Random(9), 0x80000000)
    wrong_command_errors = differences(
        execute(base_image, B_CALLERS[0], negative_case),
        execute(bytes(wrong_command), B_CALLERS[0], negative_case),
        B_CALLERS[0], negative_case)
    oversized_rejected = False
    try:
        compose_in_place(pinned.image, linked_body + b"\x00" * 5)
    except ValueError:
        oversized_rejected = True
    wrong_target_rejected = False
    try:
        wrong_body, _ = resolve_call_relocation(body, relocations, ENTRY,
                                                target=WRAPPER + 4)
        verify_call_target(wrong_body, relocations[0], ENTRY, WRAPPER)
    except ValueError:
        wrong_target_rejected = True

    passed = (not failure_rows and bool(wrong_command_errors)
              and oversized_rejected and wrong_target_rejected
              and sha256(SOURCE.read_bytes()) == source_hash)
    report = {"passed": passed, "entry": hex(ENTRY), "entry_span": ENTRY_SIZE,
              "candidate_size": len(body), "candidate_fits_original": len(body) <= ENTRY_SIZE,
              "function_relocations": [{"offset": r.offset,
                                        "relocation_type": r.relocation_type,
                                        "symbol_name": r.symbol_name,
                                        "explicit_addend": r.explicit_addend}
                                       for r in relocations],
              "applied_relocations": applied,
              "reference_sha256": sha256(pinned.image),
              "candidate_source_sha256": source_hash,
              "candidate_object_sha256": sha256(object_path.read_bytes()),
              "resolved_body_sha256": sha256(linked_body),
              "resolved_body_hex": linked_body.hex(),
              "base_kind": base_kind, "base_image_sha256": base_identity,
              "patched_image_sha256": sha256(patched_image),
              "caller_counts": per_start, "failures": failure_rows,
              "negative_controls": {"wrong_command_detected": bool(wrong_command_errors),
                                     "wrong_command_errors": wrong_command_errors,
                                     "oversized_body_rejected": oversized_rejected,
                                     "wrong_target_rejected": wrong_target_rejected},
              "compile_command": build.args,
              "protected_entry_tail_length": ENTRY_SIZE - len(linked_body),
              "limits": ["wrapper and two fallthrough helpers are controlled hooks",
                         "actual caller instructions only; caller setup and continuations are not executed",
                         "Thumb/interworking, live service effects and emulator runtime not tested",
                         "even when based on the reviewed H2 image, this is an offline test artifact and was not runtime-verified"]}
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "candidate_size": len(body),
                      "caller_counts": per_start, "failures": failure_rows,
                      "negative_controls": report["negative_controls"]}))
    return passed


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--code", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-image", type=Path)
    parser.add_argument("--base-sha256")
    args = parser.parse_args()
    raise SystemExit(0 if run_experiment(args.code, args.output,
                                        args.base_image, args.base_sha256) else 1)
