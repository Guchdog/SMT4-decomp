#!/usr/bin/env python3
"""Focused original-versus-C++ initialization experiment for titleMain."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.semantic_experiment import DATA, DATA_SIZE, INJECT, RETURN, SP, STACK, STACK_SIZE, Runner, arm, unicorn

ADDRESS = 0x001EB02C
STOP = RETURN
GLOBAL = 0x0044E300
ALLOC = 0x002C54F0
CREATE_CALC = 0x002C5978
CREATE_DRAW = 0x002C4C00
WORK_OFFSET = 0x800
ARG_OFFSET = 0x100
TASK_HANDLE = DATA + 0xC00
STRING_NAMES = {
    0x001EB1F8: "TITLE C",
    0x001EB204: "TITLE UDrawLeft",
    0x001EB218: "TITLE UDrawRight",
    0x001EB230: "TITLE D",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_cstring(uc, address: int) -> str:
    result = bytearray()
    for offset in range(64):
        value = uc.mem_read(address + offset, 1)[0]
        if value == 0:
            return result.decode("ascii")
        result.append(value)
    raise ValueError(f"unterminated callback name at {address:#x}")


def run_once(image: bytes, function: bytes | None, *, arg_byte: int | None,
             preexisting_global: bool) -> dict:
    runner = Runner(image, ADDRESS)
    uc = runner.uc
    uc.mem_protect(GLOBAL & ~0xFFF, 0x1000,
                   unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    if function is not None:
        uc.mem_write(INJECT, function)
    work = DATA + WORK_OFFSET
    data = bytearray([0xCD] * DATA_SIZE)
    data[WORK_OFFSET:WORK_OFFSET + 0xA0] = bytes([0xA7] * 0xA0)
    if arg_byte is not None:
        data[ARG_OFFSET] = arg_byte
    uc.mem_write(DATA, bytes(data))
    uc.mem_write(GLOBAL, struct.pack("<I", DATA + 0x900 if preexisting_global else 0))
    uc.mem_write(STACK, bytes([0xD3]) * STACK_SIZE)

    registers = [0xA5A50000 | index for index in range(13)]
    for index, value in enumerate(registers):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), value)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, STOP)
    uc.reg_write(arm.UC_ARM_REG_R0, DATA + ARG_OFFSET if arg_byte is not None else 0)
    for index in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{index}"), 0x1122334400000000 | index)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    calls: list[dict] = []
    stopped = {"value": False}
    entry_global = {"value": None}

    def api_hook(machine, address, _size, _user):
        if address == ADDRESS or address == INJECT:
            entry_global["value"] = hex(struct.unpack("<I", machine.mem_read(GLOBAL, 4))[0])
        if address == STOP:
            stopped["value"] = True
            machine.emu_stop()
            return
        if address not in (ALLOC, CREATE_CALC, CREATE_DRAW):
            return
        args = [machine.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
        sp = machine.reg_read(arm.UC_ARM_REG_SP)
        stack_count = 1 if address == ALLOC else 3 if address == CREATE_CALC else 4
        stack_words = list(struct.unpack("<" + "I" * stack_count,
                                         machine.mem_read(sp, stack_count * 4)))
        name = read_cstring(machine, args[0]) if address in (CREATE_CALC, CREATE_DRAW) else None
        row = {"target": hex(address), "r0_r3": [hex(value) for value in args],
               "stack": [hex(value) for value in stack_words], "name": name}
        calls.append(row)
        if address == ALLOC:
            machine.mem_write(work, bytes([0xA7] * 0xA0))
            machine.reg_write(arm.UC_ARM_REG_R0, work)
        elif address == CREATE_CALC:
            machine.reg_write(arm.UC_ARM_REG_R0, TASK_HANDLE)
        machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))

    uc.hook_add(unicorn.UC_HOOK_CODE, api_hook)
    start = ADDRESS if function is None else INJECT
    try:
        uc.emu_start(start, 0, count=4096)
    except unicorn.UcError as error:
        raise RuntimeError(f"ARM fault at {uc.reg_read(arm.UC_ARM_REG_PC):#x}: {error}") from error
    if not stopped["value"] or uc.reg_read(arm.UC_ARM_REG_PC) != STOP:
        raise RuntimeError(f"title initializer did not return; PC={uc.reg_read(arm.UC_ARM_REG_PC):#x}")
    final = bytes(uc.mem_read(DATA, DATA_SIZE))
    final_work_ptr = struct.unpack("<I", uc.mem_read(GLOBAL, 4))[0]
    preserved = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)]
    preserved += [uc.reg_read(arm.UC_ARM_REG_SP)]
    preserved += [uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)]
    expected_preserved = registers[4:12] + [SP] + [0x1122334400000000 | i for i in range(8, 16)]
    return {"calls": calls,
            "work": final[WORK_OFFSET:WORK_OFFSET + 0xA0].hex(),
            "global_work": hex(final_work_ptr),
            "entry_global": entry_global["value"],
            "preserved": [hex(value) for value in preserved],
            "expected_preserved": [hex(value) for value in expected_preserved],
            "arg_byte": arg_byte, "preexisting_global": preexisting_global}


def compare(reference: dict, candidate: dict) -> str | None:
    for label, result in (("original", reference), ("candidate", candidate)):
        if result["preserved"] != result["expected_preserved"]:
            return f"{label} violates callee-saved register/SP/VFP ABI"
    for key in ("calls", "work", "global_work"):
        if reference[key] != candidate[key]:
            return f"{key} differs"
    return None


EXPECTED_REGISTRATION = [
    {"target": hex(ALLOC), "r0_r3": ["0x10000", "0x100", "0x0", "0xa0"],
     "stack": ["0x1"], "name": None},
    {"target": hex(CREATE_CALC), "r0_r3": ["0x1eb1f8", "0x2", "0x0", "0x0"],
     "stack": ["0x1e989c", "0x2ca6f4", "0x0"], "name": "TITLE C"},
    {"target": hex(CREATE_DRAW), "r0_r3": ["0x1eb204", "0x76", "0x0", "0x0"],
     "stack": ["0x20fd5c", "0x0", "0x0", hex(TASK_HANDLE)], "name": "TITLE UDrawLeft"},
    {"target": hex(CREATE_DRAW), "r0_r3": ["0x1eb218", "0xd4", "0x0", "0x0"],
     "stack": ["0x21f36c", "0x0", "0x0", hex(TASK_HANDLE)], "name": "TITLE UDrawRight"},
    {"target": hex(CREATE_DRAW), "r0_r3": ["0x1eb230", "0xe7", "0x0", "0x0"],
     "stack": ["0x2ca7a8", "0x0", "0x0", hex(TASK_HANDLE)], "name": "TITLE D"},
]


def registration_contract_error(result: dict) -> str | None:
    if result["calls"] != EXPECTED_REGISTRATION:
        return "allocation/task callback registration differs from the pinned call contract"
    return None


def run_experiment(code_path: Path, output_dir: Path, object_path: Path | None = None) -> dict:
    image = code_path.read_bytes()
    if len(image) != 3633152 or sha256(image) != "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558":
        raise ValueError("code.bin is not the pinned US reference image")
    source = ROOT / "experiments/semantic_equivalence/h1_title_main_init.cpp"
    object_path = object_path or output_dir / "title_init.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "candidate compilation failed")
    functions = extract_elf_functions_detailed(object_path)
    for symbol in ("candidate_title_main_init", "negative_title_main_init"):
        if symbol not in functions:
            raise ValueError(f"missing compiled symbol {symbol}")
        code, relocations = functions[symbol]
        if relocations:
            raise ValueError(f"unsupported relocations in {symbol}: {relocations}")
    candidate_code = functions["candidate_title_main_init"][0]
    negative_code = functions["negative_title_main_init"][0]

    compared = 0
    first_mismatch = None
    for arg_byte in [None, *range(256)]:
        original = run_once(image, None, arg_byte=arg_byte, preexisting_global=False)
        rebuilt = run_once(image, candidate_code, arg_byte=arg_byte, preexisting_global=False)
        mismatch = registration_contract_error(original) or registration_contract_error(rebuilt) or compare(original, rebuilt)
        if mismatch and first_mismatch is None:
            first_mismatch = {"case": arg_byte, "reason": mismatch,
                              "original": original, "candidate": rebuilt}
        if mismatch:
            break
        compared += 1

    reuse_results = []
    if first_mismatch is None:
        for arg_byte in (None, 0, 255):
            original = run_once(image, None, arg_byte=arg_byte, preexisting_global=True)
            rebuilt = run_once(image, candidate_code, arg_byte=arg_byte, preexisting_global=True)
            mismatch = registration_contract_error(original) or registration_contract_error(rebuilt) or compare(original, rebuilt)
            reuse_results.append({"arg_byte": arg_byte, "preexisting_global": True,
                                  "mismatch": mismatch})
            if mismatch and first_mismatch is None:
                first_mismatch = {"case": f"reuse-{arg_byte}", "reason": mismatch,
                                  "original": original, "candidate": rebuilt}

    negative_original = run_once(image, None, arg_byte=0xA5, preexisting_global=False)
    negative_candidate = run_once(image, negative_code, arg_byte=0xA5, preexisting_global=False)
    negative_difference = compare(negative_original, negative_candidate)
    negative_work_diff_offsets = [index for index, (left, right) in enumerate(
        zip(bytes.fromhex(negative_original["work"]), bytes.fromhex(negative_candidate["work"])))
        if left != right]
    report = {
        "task_id": "h1-title-init-candidate", "address": hex(ADDRESS),
        "passed": (first_mismatch is None and compared == 257
                   and all(row["mismatch"] is None for row in reuse_results)
                   and negative_difference == "work differs"
                   and negative_work_diff_offsets == [0x10]),
        "evidence_type": "isolated pinned original ARM versus compiled C++ under identical allocation/task-service hooks",
        "code_sha256": sha256(image), "source_sha256": sha256(source.read_bytes()),
        "object_sha256": sha256(object_path.read_bytes()),
        "object_path": str(object_path.resolve()), "candidate_symbol_bytes": len(candidate_code),
        "negative_control_symbol_bytes": len(negative_code),
        "nullable_argument_cases_compared": compared,
        "nullable_argument_domain": "null and all 256 byte values",
        "preexisting_global_cases": reuse_results,
        "negative_control": {"input": "non-null argument byte 0xA5", "detected_difference": negative_difference,
                             "original_flag_0x10": negative_original["work"][0x10 * 2:0x11 * 2],
                             "negative_flag_0x10": negative_candidate["work"][0x10 * 2:0x11 * 2],
                             "differing_work_offsets": [hex(value) for value in negative_work_diff_offsets],
                             "registration_contract_error": registration_contract_error(negative_candidate)},
        "registration_contract": EXPECTED_REGISTRATION,
        "first_counterexample": first_mismatch,
        "limitations": [
            "The allocator and task-factory callees are deterministic hooks; their internal heap/scheduler behavior is outside this function contract.",
            "The work area starts with a sentinel pattern and the allocation hook returns a fixed 0xA0-byte region; allocator success is assumed, matching the original's unchecked use.",
            "Task names use the pinned image's strings so the comparison covers identical string bytes and pointer values.",
            "This is an isolated constructor differential; no live H1 caller or game runtime was exercised.",
        ],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True, help="fresh private output directory")
    parser.add_argument("--object", type=Path, help="candidate object path; defaults under --output")
    args = parser.parse_args()
    report = run_experiment(args.code, args.output, args.object)
    print(f"title init differential {'PASS' if report['passed'] else 'FAIL'}; report: {args.output / 'report.json'}")
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
