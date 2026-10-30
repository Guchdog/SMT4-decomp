#!/usr/bin/env python3
"""Differentially exercise TitleConfig_IsReady and its experimental C++ candidate.

The only unresolved external dependency, battle_func_002BF41C, is replaced by
the same explicit task-registration model in both emulated executions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang

ADDRESS = 0x002FC0EC
HELPER = 0x002BF41C
GLOBAL = 0x0044E2D0
CODE_BASE = 0x00100000
CODE_MAP_SIZE = 0x00378000
WORK = 0x00500000
WORK_SIZE = 0x1000
TASK = 0x12345678
STACK = 0x08000000
STACK_SIZE = 0x8000
INITIAL_SP = STACK + STACK_SIZE // 2
INJECT = 0x01000000
INJECT_SIZE = 0x1000
RETURN = INJECT + INJECT_SIZE - 4
SOURCE = ROOT / "experiments/semantic_equivalence/h2_ready_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SYMBOL = "candidate_002fc0ec"
BAD_SYMBOL = "candidate_002fc0ec_bad"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compile_candidate(output: Path) -> tuple[bytes, bytes, Path, list[dict]]:
    obj = output / "h2_ready_candidate.o"
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K compilation failed")
    funcs = extract_elf_functions_detailed(obj)
    if SYMBOL not in funcs or BAD_SYMBOL not in funcs:
        raise ValueError("compiled object is missing the expected candidate functions")
    candidate, relocations = funcs[SYMBOL]
    bad, bad_relocations = funcs[BAD_SYMBOL]
    if relocations or bad_relocations:
        raise ValueError(f"unexpected candidate relocations: {relocations}, {bad_relocations}")
    return candidate, bad, obj, list(build.args)


def scenario(label: str, work_ptr: int, task: int, registered: int) -> dict:
    return {"label": label, "work_ptr": work_ptr, "task": task, "registered": registered}


SCENARIOS = [
    scenario("null-global", 0, 0, 0),
    scenario("task-still-registered", WORK, TASK, 1),
    scenario("task-no-longer-registered", WORK, TASK, 0),
    scenario("null-task-handle-forwarded", WORK, 0, 0),
]

CALLEE_SAVED_GPRS = [
    ("r4", arm.UC_ARM_REG_R4), ("r5", arm.UC_ARM_REG_R5),
    ("r6", arm.UC_ARM_REG_R6), ("r7", arm.UC_ARM_REG_R7),
    ("r8", arm.UC_ARM_REG_R8), ("r9", arm.UC_ARM_REG_R9),
    ("r10", arm.UC_ARM_REG_R10), ("r11", arm.UC_ARM_REG_R11),
]
CALLEE_SAVED_VFP = [(f"d{index}", getattr(arm, f"UC_ARM_REG_D{index}"))
                    for index in range(8, 16)]


def regions_overlap(first_base: int, first_size: int, second_base: int,
                    second_size: int) -> bool:
    return first_base < second_base + second_size and second_base < first_base + first_size


def validate_workspace_layout(code_base: int, code_map_size: int,
                              work_base: int, work_size: int) -> None:
    if regions_overlap(code_base, code_map_size, work_base, work_size):
        raise ValueError("synthetic work region overlaps mapped pinned code image")


def run_callback(image: bytes, code: bytes | None, case: dict) -> dict:
    validate_workspace_layout(CODE_BASE, CODE_MAP_SIZE, WORK, WORK_SIZE)
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM | unicorn.UC_MODE_LITTLE_ENDIAN)
    uc.mem_map(CODE_BASE, CODE_MAP_SIZE)
    uc.mem_write(CODE_BASE, image)
    uc.mem_map(INJECT, INJECT_SIZE)
    uc.mem_map(STACK, STACK_SIZE)
    if case["work_ptr"]:
        uc.mem_map(WORK, WORK_SIZE)
    if code is not None:
        if len(code) > INJECT_SIZE - 4:
            raise ValueError("candidate body does not fit injection page")
        uc.mem_write(INJECT, code)
    uc.mem_write(RETURN, b"\x00\x00\xA0\xE1")  # nop, stop from the code hook before it executes
    uc.mem_write(GLOBAL, struct.pack("<I", case["work_ptr"]))
    if case["work_ptr"]:
        uc.mem_write(case["work_ptr"], struct.pack("<I", case["task"]))

    trace: list[dict] = []
    result = {"fault": None, "stopped": False, "return": None, "pc": None,
              "sp": None, "preserved": {}, "trace": trace}

    def hook(emu: unicorn.Uc, address: int, size: int, user_data: object) -> None:
        if address == HELPER:
            handle = emu.reg_read(arm.UC_ARM_REG_R0)
            trace.append({"helper": hex(HELPER), "task": hex(handle),
                          "registered": case["registered"]})
            emu.reg_write(arm.UC_ARM_REG_R0, case["registered"])
            emu.reg_write(arm.UC_ARM_REG_PC, emu.reg_read(arm.UC_ARM_REG_LR))
        elif address == RETURN:
            result["stopped"] = True
            emu.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, hook)
    uc.reg_write(arm.UC_ARM_REG_SP, INITIAL_SP)
    saved_registers = CALLEE_SAVED_GPRS + CALLEE_SAVED_VFP
    before = {}
    for index, (name, register) in enumerate(saved_registers):
        value = (0x4455667700000000 | (index + 1)) if name.startswith("d") else (0x44550000 | (index + 1))
        before[name] = value
        uc.reg_write(register, value)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    entry = INJECT if code is not None else ADDRESS
    try:
        uc.emu_start(entry, RETURN + 4, count=1000)
    except unicorn.UcError as error:
        result["fault"] = str(error)
    result["return"] = uc.reg_read(arm.UC_ARM_REG_R0)
    result["pc"] = uc.reg_read(arm.UC_ARM_REG_PC)
    result["sp"] = uc.reg_read(arm.UC_ARM_REG_SP)
    result["preserved"] = {"sp": result["sp"] == INITIAL_SP}
    for name, register in saved_registers:
        result["preserved"][name] = uc.reg_read(register) == before[name]
    return result


def compare(original: dict, candidate: dict) -> str | None:
    for label, item in (("original", original), ("candidate", candidate)):
        if item["fault"]:
            return f"{label} fault: {item['fault']}"
        if not item["stopped"]:
            return f"{label} did not reach the return sentinel"
        if not all(item["preserved"].values()):
            return f"{label} violated a callee-saved register or SP preservation"
    for field in ("return", "pc", "trace"):
        if original[field] != candidate[field]:
            return f"{field} differs"
    return None


def expected_ready(work_ptr: int, registered: int) -> int:
    """Expected predicate result under the documented helper contract."""
    return int(work_ptr == 0 or registered == 0)


def experiment(code_path: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    image = code_path.read_bytes()
    if len(image) != game["code_bin_size"] or hashlib.sha256(image).hexdigest() != game["code_sha256"]:
        raise ValueError("--code must be the pinned configured original code image")
    candidate, bad, obj, compile_command = compile_candidate(output)
    cases = []
    first_failure = None
    for case in SCENARIOS:
        original = run_callback(image, None, case)
        rebuilt = run_callback(image, candidate, case)
        error = compare(original, rebuilt)
        cases.append({"case": case["label"], "passed": error is None,
                      "original_return": original["return"], "candidate_return": rebuilt["return"],
                      "original_trace": original["trace"], "candidate_trace": rebuilt["trace"],
                      "difference": error})
        if error and first_failure is None:
            first_failure = {"case": case["label"], "reason": error}

    # In the registered-task case the original must return not-ready (0).
    negative_case = SCENARIOS[1]
    negative_original = run_callback(image, None, negative_case)
    negative_bad = run_callback(image, bad, negative_case)
    negative_error = compare(negative_original, negative_bad)
    negative = {"name": "always-ready-candidate", "detected": negative_error == "return differs",
                "difference": negative_error, "original_return": negative_original["return"],
                "bad_return": negative_bad["return"]}
    passed = first_failure is None and negative["detected"]
    report = {
        "schema": 1,
        "passed": passed,
        "scope": "TitleConfig_IsReady isolated callback; original task-registration helper replaced by identical explicit model",
        "reference_sha256": hashlib.sha256(image).hexdigest(),
        "source_sha256": sha256(SOURCE),
        "runner_sha256": sha256(Path(__file__)),
        "object_sha256": sha256(obj),
        "compiler": subprocess.run([str(find_clang()), "--version"], capture_output=True,
                                    text=True, check=True).stdout.splitlines()[0],
        "compile_command": compile_command,
        "candidate_bytes": len(candidate),
        "case_count": len(cases),
        "cases_passed": sum(case["passed"] for case in cases),
        "first_failure": first_failure,
        "negative_control": negative,
        "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed",
                     "caller": "not_run", "runtime": "not_run"},
        "limitations": [
            "battle_func_002BF41C is modeled only as a boolean-like active task-registration lookup shared by both executions; its implementation is not revalidated here.",
            "The caller-facing title state-10 wait/transition is static caller evidence, not an executed caller composition.",
            "No Azahar, game input, persistence, or restart scenario was tested.",
        ],
        "cases": cases,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = experiment(args.code, args.output)
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json"),
                      "cases": report["cases_passed"], "negative_control": report["negative_control"]},
                     indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
