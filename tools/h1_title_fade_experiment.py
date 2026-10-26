#!/usr/bin/env python3
"""Differentially exercise the readable 0x00210030 C++ front-gate candidate."""
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

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags
from tools.semantic_experiment import TEXT, DATA, STACK, STACK_SIZE, INJECT, RETURN, arm, unicorn, require_unicorn
from tools.semantic_experiment_support import load_pinned_reference

ADDRESS = 0x00210030
SIZE = 68
CHILD = 0x400
CHILD_SECOND = 0x600
CHILD_FINAL = 0x700
OBJECT = 0x100
RECORD_FIRST = 0x800
RECORD_SECOND = 0xA00
CALLBACK_OBJECT = 0xC00
CALLBACK_STUB = 0x01001800
DATA_SIZE = 0x2000
SP = STACK + 0x1000
CODE_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"


def _put32(buf: bytearray, off: int, value: int) -> None:
    struct.pack_into("<I", buf, off, value & 0xFFFFFFFF)


def _putf32(buf: bytearray, off: int, value: float) -> None:
    struct.pack_into("<f", buf, off, value)


def verify_reference(image: bytes, game_info: dict, ledger: list[dict]) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != CODE_SHA256 or digest != game_info["code_sha256"]:
        raise ValueError("code.bin is not the pinned US reference image")
    rows = {int(row["address"], 16): row for row in ledger}
    row = rows.get(ADDRESS)
    if row is None or int(row["size"]) != SIZE or row["status"].strip() != "matching":
        raise ValueError("0x00210030 ledger identity changed")
    body = image[ADDRESS - TEXT: ADDRESS - TEXT + SIZE]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    insns = list(decoder.disasm(body, ADDRESS))
    if sum(i.size for i in insns) != SIZE:
        raise ValueError("original 0x00210030 bytes do not decode completely")
    expected = [
        ("push", "{r4, lr}"), ("mov", "r4, r0"), ("vpush", "{d8}"),
        ("vmov.f32", "s16, s0"), ("ldr", "r0, [r0, #8]"),
        ("bl", "#0x2872a4"), ("vmov.f32", "s0, s16"),
        ("ldr", "r0, [r4, #8]"), ("bl", "#0x20ffa0"),
        ("ldr", "r0, [r4, #8]"), ("vmov.f32", "s0, s16"),
        ("vpop", "{d8}"), ("pop", "{r4, lr}"), ("mov", "r0, r0"),
        ("ldr", "r1, [r0, #0x68]"), ("cmp", "r1, #0"),
        ("bxle", "lr"),
    ]
    decoded = [(i.mnemonic.lower(), i.op_str.lower()) for i in insns]
    if decoded != expected:
        raise ValueError(f"pinned instruction sequence changed: {decoded}")
    return {"address": hex(ADDRESS), "size": SIZE, "sha256": hashlib.sha256(body).hexdigest(),
            "instructions": [f"{m} {o}" for m, o in decoded]}


def _initial_data(first_gate: int, second_gate: int, final_gate: int) -> bytes:
    data = bytearray([0xCD]) * DATA_SIZE
    _put32(data, OBJECT + 8, DATA + CHILD)
    _put32(data, CHILD + 0x34, first_gate)
    _put32(data, CHILD + 0x58, second_gate)
    _put32(data, CHILD + 0x68, final_gate)
    _put32(data, CHILD + 0x2C, DATA + RECORD_SECOND)
    # A positive second gate takes 0x20FFAC but returns at its explicit first
    # guard; this covers that callee path without fabricating its object graph.
    _put32(data, RECORD_SECOND + 0x148, 0)
    # Positive first gate executes its real body and one bounded callback.
    _put32(data, CHILD + 0x4C, DATA + RECORD_FIRST)
    _putf32(data, RECORD_FIRST + 0x44, 0.5)
    _putf32(data, RECORD_FIRST + 0x48, 0.25)
    _put32(data, RECORD_FIRST + 0x4C, CALLBACK_STUB)
    _put32(data, RECORD_FIRST + 0x50, DATA + CALLBACK_OBJECT)
    # Positive final gate falls through to 0x210074; its first guard returns.
    _put32(data, RECORD_SECOND + 0x150, 0)
    # Alternate targets used by the adversarial seam case. The first callback
    # redirects object+8 to CHILD_SECOND; the second helper then redirects it
    # to CHILD_FINAL before the original's third load at 0x00210054.
    _put32(data, CHILD_SECOND + 0x34, 0)
    _put32(data, CHILD_SECOND + 0x58, 0)
    _put32(data, CHILD_SECOND + 0x68, 0xFFFFFFFF)
    _put32(data, CHILD_SECOND + 0x2C, DATA + RECORD_SECOND)
    _put32(data, CHILD_FINAL + 0x34, 0)
    _put32(data, CHILD_FINAL + 0x58, 0)
    _put32(data, CHILD_FINAL + 0x68, 1)
    _put32(data, CHILD_FINAL + 0x2C, DATA + RECORD_SECOND)
    return bytes(data)


def _execute(image: bytes, code: bytes | None, data: bytes,
             *, mutation_seams: bool = False, clobber_second_s0: bool = False) -> dict:
    require_unicorn()
    uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
    uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
    uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_write(TEXT, image)
    uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
    uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
    if code is not None:
        uc.mem_write(INJECT, code)
        displacement = INJECT - ADDRESS - 8
        uc.mem_write(ADDRESS, struct.pack("<I", 0xEA000000 | ((displacement >> 2) & 0xFFFFFF)))
    uc.mem_write(CALLBACK_STUB, struct.pack("<I", 0xE12FFF1E))
    uc.mem_write(DATA, data)
    uc.mem_write(STACK, b"\xcd" * STACK_SIZE)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    for i in range(13):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{i}"), 0xA5A50000 | i)
    uc.reg_write(arm.UC_ARM_REG_R0, DATA + OBJECT)
    uc.reg_write(arm.UC_ARM_REG_S0, struct.unpack("<I", struct.pack("<f", 0.75))[0])
    for i in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{i}"), 0x1122334455667788 ^ i)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
    trace: list[int] = []
    callback_count = 0
    calls: list[dict] = []
    events: list[dict] = []
    parent_mutations: list[dict] = []
    initial_preserved = [0xA5A50000 | i for i in range(4, 12)]
    initial_d = [0x1122334455667788 ^ i for i in range(8, 16)]

    def on_code(machine, address, _size, _user):
        nonlocal callback_count
        trace.append(address)
        if address in (0x002872A4, 0x0020FFA0, 0x00210074):
            row = {"target": hex(address),
                   "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                   "s0": hex(machine.reg_read(arm.UC_ARM_REG_S0))}
            calls.append(row)
            events.append({"kind": "direct_entry", **row})
        elif address in (0x002872B0, 0x0020FFAC):
            events.append({"kind": "positive_body", "target": hex(address),
                           "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0))})
        if address == CALLBACK_STUB:
            callback_count += 1
            events.append({"kind": "callback", "target": hex(address),
                           "r0": hex(machine.reg_read(arm.UC_ARM_REG_R0)),
                           "s0": hex(machine.reg_read(arm.UC_ARM_REG_S0)),
                           "s2": hex(machine.reg_read(arm.UC_ARM_REG_S2))})
            if mutation_seams:
                old = struct.unpack("<I", machine.mem_read(DATA + OBJECT + 8, 4))[0]
                machine.mem_write(DATA + OBJECT + 8, struct.pack("<I", DATA + CHILD_SECOND))
                parent_mutations.append({"seam": "first_callback", "old": hex(old),
                                         "new": hex(DATA + CHILD_SECOND)})
        if address == 0x0020FFA0 and mutation_seams:
            old = struct.unpack("<I", machine.mem_read(DATA + OBJECT + 8, 4))[0]
            machine.mem_write(DATA + OBJECT + 8, struct.pack("<I", DATA + CHILD_FINAL))
            parent_mutations.append({"seam": "second_helper", "old": hex(old),
                                     "new": hex(DATA + CHILD_FINAL)})
        if address == 0x0020FFA0 and clobber_second_s0:
            before = machine.reg_read(arm.UC_ARM_REG_S0)
            clobbered = 0x41200000  # 10.0f, distinct from input fade 0.75f
            machine.reg_write(arm.UC_ARM_REG_S0, clobbered)
            events.append({"kind": "second_helper_s0_clobber", "target": hex(address),
                           "before": hex(before), "after": hex(clobbered)})
        if address == RETURN:
            machine.emu_stop()

    uc.hook_add(unicorn.UC_HOOK_CODE, on_code)
    fault = None
    try:
        uc.emu_start(ADDRESS if code is None else ADDRESS, 0, count=4096)
    except unicorn.UcError as error:
        fault = str(error)
    return {"fault": fault, "returned": uc.reg_read(arm.UC_ARM_REG_PC) == RETURN,
            "trace": trace, "callback_count": callback_count,
            "calls": calls, "events": events, "parent_mutations": parent_mutations,
            "memory": bytes(uc.mem_read(DATA, DATA_SIZE)),
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "s0": uc.reg_read(arm.UC_ARM_REG_S0),
            "r4_r11": [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4, 12)],
            "expected_r4_r11": initial_preserved,
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "d8_d15": [uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}")) for i in range(8, 16)],
            "expected_d8_d15": initial_d}


def _difference(original: dict, rebuilt: dict) -> str | None:
    for name, run in (("original", original), ("candidate", rebuilt)):
        if run["fault"] or not run["returned"]:
            return f"{name} did not return: {run['fault']}"
        if run["r4_r11"] != run["expected_r4_r11"]:
            return f"{name} violates r4-r11 preservation"
        if run["sp"] != SP or run["d8_d15"] != run["expected_d8_d15"]:
            return f"{name} violates SP/d8-d15 preservation"
    for key in ("memory", "callback_count", "calls", "events", "parent_mutations", "r0", "s0", "sp", "d8_d15"):
        if original[key] != rebuilt[key]:
            return f"{key} differs"
    if (0x00210074 in original["trace"]) != (0x00210074 in rebuilt["trace"]):
        return "continuation path differs"
    return None


def _check(original: dict, rebuilt: dict, label: str) -> None:
    mismatch = _difference(original, rebuilt)
    if mismatch:
        raise AssertionError(f"{label}: {mismatch}")


def run_experiment(code_path: Path, output: Path, task_dir: Path) -> dict:
    ref = load_pinned_reference(code_path, ROOT / "config/game_info.json", ROOT / "config/functions.csv")
    ref_identity = verify_reference(ref.image, ref.game_info, ref.ledger)
    object_path = output.parent / "h1_title_fade_candidate.o"
    source = ROOT / "experiments/semantic_equivalence/h1_title_fade_candidate.cpp"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(object_path)
    for name in ("candidate_00210030", "wrong_candidate_00210030"):
        if name not in functions:
            raise ValueError(f"missing candidate symbol {name}")
        _, relocs = functions[name]
        if relocs:
            raise ValueError(f"unsupported candidate relocation in {name}: {relocs}")
    good = functions["candidate_00210030"][0]
    wrong = functions["wrong_candidate_00210030"][0]
    cases = [
        ("first gate signed low boundary", 0x80000000, 0, 0),
        ("first gate negative one", 0xFFFFFFFF, 0, 0),
        ("first gate zero", 0, 0, 0),
        ("first gate positive and real indirect callback", 1, 0, 0),
        ("first gate signed high boundary and callback", 0x7FFFFFFF, 0, 0),
        ("second gate signed low boundary", 0, 0x80000000, 0),
        ("second gate negative one", 0, 0xFFFFFFFF, 0),
        ("second gate signed high boundary", 0, 0x7FFFFFFF, 0),
        ("second gate zero", 0, 0, 0),
        ("second gate positive early body return", 0, 1, 0),
        ("third gate signed low boundary", 0, 0, 0x80000000),
        ("third gate negative one", 0, 0, 0xFFFFFFFF),
        ("third gate zero", 0, 0, 0),
        ("third gate positive fallthrough", 0, 0, 1),
        ("third gate signed high boundary fallthrough", 0, 0, 0x7FFFFFFF),
    ]
    rows = []
    for label, first, second, final in cases:
        data = _initial_data(first, second, final)
        original = _execute(ref.image, None, data)
        candidate = _execute(ref.image, good, data)
        _check(original, candidate, label)
        rows.append({"label": label, "passed": True,
                     "return_r0": hex(original["r0"]),
                     "return_s0": hex(original["s0"]),
                     "callback_count": original["callback_count"],
                     "calls": original["calls"],
                     "events": original["events"],
                     "reached_first_body": 0x002872B0 in original["trace"],
                     "reached_second_body": 0x0020FFAC in original["trace"],
                     "reached_final_fallthrough": 0x00210074 in original["trace"]})

    mutation_data = _initial_data(1, 0, 0)
    mutation_original = _execute(ref.image, None, mutation_data, mutation_seams=True)
    mutation_candidate = _execute(ref.image, good, mutation_data, mutation_seams=True)
    _check(mutation_original, mutation_candidate, "parent+8 mutation at callback/helper seams")
    if (mutation_original["calls"][1]["r0"] != hex(DATA + CHILD_SECOND)
            or mutation_original["calls"][2]["r0"] != hex(DATA + CHILD_FINAL)
            or mutation_original["r0"] != DATA + RECORD_SECOND):
        raise AssertionError("adversarial seams did not exercise both subsequent parent+8 reloads")

    s0_cases = []
    for label, final_gate, expected_continuation in (
            ("second-helper-s0-clobber-early-return", 0, False),
            ("second-helper-s0-clobber-positive-continuation", 1, True)):
        data = _initial_data(0, 0, final_gate)
        original_s0 = _execute(ref.image, None, data, clobber_second_s0=True)
        candidate_s0 = _execute(ref.image, good, data, clobber_second_s0=True)
        _check(original_s0, candidate_s0, label)
        input_s0 = struct.unpack("<I", struct.pack("<f", 0.75))[0]
        seam_events = [event for event in original_s0["events"]
                       if event["kind"] == "second_helper_s0_clobber"]
        reached_continuation = 0x00210074 in original_s0["trace"]
        if (original_s0["s0"] != input_s0 or candidate_s0["s0"] != input_s0
                or len(seam_events) != 1 or reached_continuation != expected_continuation):
            raise AssertionError(f"{label}: expected restored s0 or path not reached")
        s0_cases.append({"label": label, "passed": True,
                         "injected_s0": hex(0x41200000), "expected_return_s0": hex(input_s0),
                         "original_return_s0": hex(original_s0["s0"]),
                         "candidate_return_s0": hex(candidate_s0["s0"]),
                         "return_r0_original": hex(original_s0["r0"]),
                         "return_r0_candidate": hex(candidate_s0["r0"]),
                         "reached_positive_continuation": reached_continuation,
                         "seam_event": seam_events[0]})

    zero_data = _initial_data(0, 0, 0)
    original = _execute(ref.image, None, zero_data)
    negative = _execute(ref.image, wrong, zero_data)
    negative_difference = _difference(original, negative)
    negative_detected = (negative_difference is not None
                         and 0x00210074 not in original["trace"]
                         and 0x00210074 in negative["trace"])
    if not negative_detected:
        raise AssertionError("wrong zero-boundary control was not detected")

    report = {
        "task_id": "h1-title-fade-repair", "address": hex(ADDRESS),
        "outcome": "ready_for_review", "passed": True,
        "reference": ref_identity,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "object_path": str(object_path),
        "compiler": str(find_clang()), "compiler_flags": get_armv6k_flags(ROOT, find_clang()),
        "cases": rows,
        "s0_restoration_cases": s0_cases,
        "adversarial_mutation": {
            "passed": True,
            "seams": mutation_original["parent_mutations"],
            "calls": mutation_original["calls"],
            "events": mutation_original["events"],
            "return_r0": hex(mutation_original["r0"]),
            "description": "callback after 0x002872A4 changes object+8 to a second child; entry to 0x0020FFA0 changes it again to a final child. Original/candidate agree on helper arguments, third-load return, memory, callback count and ABI state."
        },
        "negative_control": {"passed": negative_detected,
                              "mutation": "changes final gate from signed <= 0 early return to signed < 0",
                              "expected_failure": "zero gate incorrectly reaches 0x00210074",
                              "first_difference": negative_difference,
                              "original_reached_continuation": 0x00210074 in original["trace"],
                              "wrong_reached_continuation": 0x00210074 in negative["trace"],
                              "original_return_r0": hex(original["r0"]),
                              "wrong_return_r0": hex(negative["r0"])},
        "candidate_first_counterexample": None,
        "evidence": {"compiled": "passed", "arm_differential": "passed",
                     "caller": "not_run", "runtime": "not_run"},
        "limits": [
            "Candidate reconstructs the 0x00210030 front gate and reloads object+8 at all three original use points. It deliberately calls the pinned original 0x002872A4, 0x0020FFA0 and positive 0x00210074 bodies.",
            "The original positive first-gate body was exercised with a counted explicit bx lr callback; its callback target is synthetic.",
            "The positive second-gate body was exercised only through its first zero-field early return; its deeper table and callback path is not covered.",
            "The positive final-gate continuation was exercised only through its first zero-field early return.",
            "Inputs are synthetic ordinary RAM objects; no runtime-normal object graph or Azahar caller observation is claimed.",
            "Return r0 and s0 are compared exactly for exercised early-return and positive-continuation paths; callers' use of these values remains unproven.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "build/azahar-validation/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--task-dir", type=Path, default=ROOT / "build/agent-work/H1-semantic/h1-title-fade-candidate/sleep-20261025-title-fade")
    args = parser.parse_args()
    report = run_experiment(args.code, args.output, args.task_dir)
    print(f"H1 title-fade differential passed ({len(report['cases'])} directed cases); report: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
