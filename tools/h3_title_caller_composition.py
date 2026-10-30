#!/usr/bin/env python3
"""Offline composition check for the H3 title state-7 caller and load entry."""
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
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags
from tools.semantic_experiment import require_unicorn
from tools.h3_candidate_support import relocate_h3_entry
import unicorn
from unicorn import arm_const as arm

CODE = ROOT / "extracted/exefs/code.bin"
CANDIDATE = ROOT / "experiments/semantic_equivalence/h3_title_load_entry_candidate.cpp"
ENTRY = 0x001EA32C
CALL_ENTRY = 0x001EA348
NEXT_STATE_VALUE = 0x001EA34C  # mov r0,#8 before 0x001E9A08 stores r0 at work +0x9c
EXIT = 0x001EA62C
TEXT = 0x00100000
TEXT_SIZE = 0x00480000
INJECT = 0x01000000
DATA = 0x02000000
STACK = 0x08000000
SP = STACK + 0x2000
MANAGER = 0x0044DE28
WORK = DATA + 0x100
POINT = DATA + 0x800
CALC = 0x00202950
GET_POINT = 0x002BF6D0
PREPARE = 0x002A7604
EXPECTED_CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
H1_H2_CODE_SHA256 = "7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291"
H3_FINAL_CODE_SHA256 = "af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def arm_bl(source: int, target: int) -> bytes:
    displacement = target - (source + 8)
    if source & 3 or target & 3 or displacement & 3 or not -(1 << 25) <= displacement < (1 << 25):
        raise ValueError(f"Not an aligned ARM BL target: {source:#x} -> {target:#x}")
    return struct.pack("<I", 0xEB000000 | ((displacement >> 2) & 0xFFFFFF))


def compile_candidate(output: Path) -> tuple[bytes, dict]:
    build_dir = output / "build"
    build_dir.mkdir(parents=True, exist_ok=True)
    obj = build_dir / "h3_title_load_entry_candidate.o"
    result = compile_tu_armv6k(CANDIDATE, obj, ROOT)
    if result.returncode:
        raise RuntimeError(result.stderr or "H3 candidate compile failed")
    functions = extract_elf_functions_detailed(obj)
    code, relocs = functions["h3_title_load_entry_candidate"]
    linked_code, relocation_rows = relocate_h3_entry(code, relocs, INJECT)
    return linked_code, {
        "clang": str(find_clang()),
        "flags": get_armv6k_flags(ROOT, find_clang()),
        "source": str(CANDIDATE.relative_to(ROOT)),
        "source_sha256": sha256(CANDIDATE.read_bytes()),
        "object": str(obj.resolve()),
        "object_sha256": sha256(obj.read_bytes()),
        "function_size": len(code),
        "function_sha256": sha256(code),
        "linked_function_sha256": sha256(linked_code),
        "relocations": relocation_rows,
    }


def run_caller(image: bytes, candidate: bytes | None, *, guard: int = 0,
               wrong_next_state: bool = False) -> dict:
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_ALL)
    uc.mem_write(TEXT, image)
    uc.mem_map(INJECT, 0x10000, unicorn.UC_PROT_ALL)
    uc.mem_map(DATA, 0x10000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_map(STACK, 0x4000, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_write(INJECT, candidate or b"")

    manager = bytearray(0x20)
    struct.pack_into("<I", manager, 4, WORK)
    uc.mem_write(MANAGER, bytes(manager))
    work = bytearray(((i * 47 + 0xA9) & 0xFF) for i in range(0x400))
    work[0x7C] = guard
    struct.pack_into("<I", work, 0x9C, 7)
    uc.mem_write(WORK, bytes(work))
    point = bytearray(0xC)
    struct.pack_into("<hh", point, 8, -32768, 32767)
    uc.mem_write(POINT, bytes(point))

    if candidate is not None:
        uc.mem_write(CALL_ENTRY, arm_bl(CALL_ENTRY, INJECT))
    if wrong_next_state:
        # The caller's `mov r0,#8` is the expected next-state value.
        uc.mem_write(NEXT_STATE_VALUE, struct.pack("<I", 0xE3A00007))

    calls: list[dict] = []
    stopped = False
    fault = None

    def hook(machine, address, _size, _user):
        nonlocal stopped
        if address == EXIT:
            stopped = True
            machine.emu_stop()
            return
        if address in (PREPARE, CALC, GET_POINT):
            args = [machine.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
            calls.append({"target": hex(address), "args": [hex(v) for v in args]})
            ret = {PREPARE: 0xA7604001, CALC: 0xCA1C0001, GET_POINT: POINT}[address]
            machine.reg_write(arm.UC_ARM_REG_R0, ret)
            machine.reg_write(arm.UC_ARM_REG_PC, machine.reg_read(arm.UC_ARM_REG_LR))

    uc.hook_add(unicorn.UC_HOOK_CODE, hook)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    for i in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0x51510000 | i)
    uc.reg_write(arm.UC_ARM_REG_R5, WORK)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, EXIT)
    try:
        uc.emu_start(ENTRY, 0, count=4096)
    except unicorn.UcError as exc:
        fault = f"{exc}; pc={uc.reg_read(arm.UC_ARM_REG_PC):#x}"

    final_manager = bytes(uc.mem_read(MANAGER, 0x20))
    final_work = bytes(uc.mem_read(WORK, 0x400))
    return {
        "stopped_at_exit": stopped,
        "stop_pc": hex(uc.reg_read(arm.UC_ARM_REG_PC)),
        "fault": fault,
        "state": struct.unpack_from("<I", final_work, 0x9C)[0],
        "manager_sha256": sha256(final_manager),
        "manager_hex": final_manager.hex(),
        "work_sha256": sha256(final_work),
        "work_hex": final_work.hex(),
        "calls": calls,
        "return_r0": hex(uc.reg_read(arm.UC_ARM_REG_R0)),
    }


def run_experiment(output: Path, code_path: Path = CODE, patched_code_path: Path | None = None) -> dict:
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"Output directory is not fresh: {output}")
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    image_hash = sha256(image)
    if image_hash not in (EXPECTED_CODE_SHA256, H1_H2_CODE_SHA256):
        raise ValueError(f"Unpinned code image SHA-256: {image_hash}")
    # Assert the pinned original caller contains an ARM BL to the original H3 entry.
    original_bl = struct.unpack_from("<I", image, CALL_ENTRY - TEXT)[0]
    if original_bl >> 24 != 0xEB:
        raise ValueError("Caller does not contain an ARM BL at the expected state-7 site")
    original_target = CALL_ENTRY + 8 + ((original_bl & 0xFFFFFF) << 2 if not original_bl & 0x800000 else ((original_bl & 0xFFFFFF) - 0x1000000) * 4)
    if original_target != 0x0030A9A4:
        raise ValueError(f"Unexpected state-7 caller target: {original_target:#x}")

    candidate, build = compile_candidate(output)
    original = run_caller(image, None)
    in_place = None
    if patched_code_path is not None:
        patched_image = patched_code_path.read_bytes()
        if sha256(patched_image) != H3_FINAL_CODE_SHA256:
            raise ValueError("Pinned H3 final image SHA-256 mismatch")
        in_place = run_caller(patched_image, None)
    patched = run_caller(image, candidate)
    guard_original = run_caller(image, None, guard=1)
    guard_patched = run_caller(image, candidate, guard=1)
    mutant = run_caller(image, candidate, wrong_next_state=True)

    fields = ("stopped_at_exit", "stop_pc", "fault", "state", "manager_hex", "work_hex", "return_r0")
    equivalence = {field: original[field] == patched[field] for field in fields}
    # The H3 body has no contract for caller-saved r2/r3. Compare each dependency's
    # target and the documented argument registers r0/r1, while retaining full traces.
    call_signature = lambda result: [(c["target"], tuple(c["args"][:2])) for c in result["calls"]]
    equivalence["call_sequence_and_contract_args"] = call_signature(original) == call_signature(patched)
    expected_calls = ["0x2a7604", "0x202950", "0x2bf6d0"]
    caller_assertions = {
        "original_entry_called": [c["target"] for c in original["calls"]] == expected_calls,
        "candidate_entry_called": [c["target"] for c in patched["calls"]] == expected_calls,
        "next_state_is_8": original["state"] == patched["state"] == 8,
        "caller_exit_reached": original["stopped_at_exit"] and patched["stopped_at_exit"],
        "no_fault": original["fault"] is None and patched["fault"] is None,
        "manager_and_work_equal": original["manager_hex"] == patched["manager_hex"] and original["work_hex"] == patched["work_hex"],
    }
    guard_case = {
        "original_skips_entry": [c["target"] for c in guard_original["calls"]] == [],
        "candidate_skips_entry": [c["target"] for c in guard_patched["calls"]] == [],
        "state_remains_7": guard_original["state"] == guard_patched["state"] == 7,
        "memories_equal": guard_original["manager_hex"] == guard_patched["manager_hex"] and guard_original["work_hex"] == guard_patched["work_hex"],
    }
    negative = {
        "mutant_next_state": mutant["state"],
        "detected": mutant["state"] != 8 and mutant["state"] != patched["state"],
        "control": "caller mov r0,#8 changed to mov r0,#7; post-call state assertion detects it",
    }
    in_place_fields = ("stopped_at_exit", "stop_pc", "fault", "state", "manager_hex", "work_hex", "return_r0")
    in_place_equivalence = ({field: original[field] == in_place[field] for field in in_place_fields} if in_place is not None else None)
    if in_place is not None:
        in_place_equivalence["call_sequence_and_contract_args"] = call_signature(original) == call_signature(in_place)
    passed = all(equivalence.values()) and all(caller_assertions.values()) and all(guard_case.values()) and negative["detected"] and (in_place_equivalence is None or all(in_place_equivalence.values()))
    report = {
        "task_id": "h3-title-caller-composition",
        "address": hex(0x0030A9A4),
        "caller_entry": hex(ENTRY),
        "passed": passed,
        "reference": {"code_sha256": sha256(image), "original_target": hex(original_target), "arm_bl_word": hex(original_bl), "caller_target_low_bit": original_target & 1},
        "build": build,
        "dependency_stubs": {"0x002a7604": "returns 0xa7604001", "0x00202950": "returns 0xca1c0001", "0x002bf6d0": f"returns point {POINT:#x} with signed halfwords (-32768,32767)"},
        "comparison_fields": equivalence,
        "caller_assertions": caller_assertions,
        "guard_case": guard_case,
        "negative_control": negative,
        "original": original,
        "candidate": patched,
        "in_place_final_image": in_place,
        "in_place_equivalence": in_place_equivalence,
        "guard_original": guard_original,
        "guard_candidate": guard_patched,
        "negative_control_result": mutant,
        "limitations": ["Offline Unicorn ARM composition only; no emulator/runtime scenario.", "The caller's 0x002a7604 and H3 entry dependencies are deterministic stubs; their internal behavior is outside this composition check.", "Only state-7 success gate and its nonzero skip gate are exercised; state-8 polling and downstream save/load behavior are not covered."],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Fresh report output directory")
    parser.add_argument("--code", type=Path, default=CODE, help="Pinned original or H1/H2 composed image")
    parser.add_argument("--patched-code", type=Path, help="Pinned H3 final composed image for in-place validation")
    args = parser.parse_args()
    report = run_experiment(args.output, args.code, args.patched_code)
    print(f"H3 title caller composition {'PASS' if report['passed'] else 'FAIL'}: {args.output / 'report.json'}")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
