#!/usr/bin/env python3
"""Compare a C++ touch scan with the pinned H1 caller window and real helper ABI."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang, get_armv6k_flags
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, RETURN, STACK, STACK_SIZE, TEXT, arm, unicorn,
    require_unicorn,
)

ADDRESS = 0x001E9E4C
STOP = 0x001E9EB8
TOUCH_QUERY = 0x0029D8FC
GLOBAL_SLOT = 0x0044E300
WORK = DATA + 0x100
DEFAULT_HANDLES = (0x0174, 0x0176, 0x0178, 0x017A)
SP = STACK + 0x1000
EXPECTED_IMAGE = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
FUNCTION_LENGTH = STOP - ADDRESS


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def verify_reference(image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_IMAGE:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    code = image[ADDRESS - TEXT: STOP - TEXT]
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    instructions = list(decoder.disasm(code, ADDRESS))
    if sum(item.size for item in instructions) != len(code):
        raise ValueError("incomplete ARM decode in pinned touch caller window")
    decoded = [(item.mnemonic.lower(), item.op_str.lower()) for item in instructions]
    expected = [
        ("ldr", "r6, [r8]"), ("mov", "r4, #0"), ("add", "r7, r6, r4, lsl #1"),
        ("ldrsh", "r0, [r7, #0x74]"), ("bl", "#0x29d8fc"),
        ("cmp", "r0, #1"), ("nop", ""), ("beq", "#0x1ea014"),
        ("ldrsh", "r0, [r7, #0x74]"), ("bl", "#0x29d8fc"),
        ("cmp", "r0, #2"), ("nop", ""), ("beq", "#0x1ea014"),
        ("add", "r4, r4, #1"), ("cmp", "r4, #4"), ("blt", "#0x1e9e54"),
        ("mov", "r4, #0"), ("mov", "r7, #1"),
        ("add", "r0, r6, r4, lsl #1"), ("ldrsh", "r0, [r0, #0x74]"),
        ("bl", "#0x29d8fc"), ("cmp", "r0, #6"),
        ("streq", "r4, [r6, #8]"), ("add", "r4, r4, #1"),
        ("strbeq", "r7, [r6, #0x63]"), ("cmp", "r4, #4"),
        ("blt", "#0x1e9e94"),
    ]
    if decoded != expected:
        raise ValueError(f"pinned touch caller sequence changed: {decoded}")
    return {"sha256": digest, "address": hex(ADDRESS), "stop": hex(STOP),
            "length": FUNCTION_LENGTH, "instruction_count": len(instructions),
            "sha256_function": hashlib.sha256(code).hexdigest(),
            "helper": hex(TOUCH_QUERY), "handles": [hex(value) for value in DEFAULT_HANDLES]}


def build_candidates(output: Path) -> tuple[dict[str, bytes], Path]:
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/h1_touch_caller_candidate.cpp"
    object_path = output / "h1_touch_caller_candidate.o"
    build = compile_tu_armv6k(source, object_path, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
    functions = extract_elf_functions_detailed(object_path)
    result: dict[str, bytes] = {}
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    for name in ("h1_touch_caller_candidate", "negative_touch_reversed_priority",
                 "negative_touch_ignores_state_one"):
        if name not in functions:
            raise ValueError(f"missing compiled symbol {name}")
        _wrapper, relocations = functions[name]
        if relocations:
            raise ValueError(f"unsupported relocation in {name}: {relocations}")
    implementation = "_ZN12_GLOBAL__N_116scan_title_touchEPvbb"
    if implementation not in functions:
        raise ValueError("missing compiled touch scan implementation")
    code, relocations = functions[implementation]
    if relocations:
        raise ValueError(f"unsupported relocation in {implementation}: {relocations}")
    decoded = list(decoder.disasm(code, INJECT))
    literal = struct.pack("<I", TOUCH_QUERY)
    literal_offset = code.find(literal)
    literal_loads = []
    for item in decoded:
        match = re.search(r"\[pc,\s*#(0x[0-9a-f]+|[0-9]+)\]", item.op_str.lower())
        if item.mnemonic.lower() == "ldr" and item.op_str.lower().startswith("r8,") and match:
            literal_loads.append(item.address + 8 + int(match.group(1), 0) - INJECT)
    if (literal_offset < 0 or literal_loads != [literal_offset]
            or literal_offset + 4 != len(code)
            or sum(item.size for item in decoded) != literal_offset):
        raise ValueError(f"incomplete ARM disassembly or unpinned helper literal in {implementation}")
    if not any(item.mnemonic.lower() == "blx" for item in decoded):
        raise ValueError(f"{implementation} does not call the external helper ABI")
    if code.count(literal) != 1:
        raise ValueError("compiled helper function pointer is not pinned to 0x0029D8FC")
    # The exported wrappers select the normal and deliberate negative-control
    # modes. Execute the shared implementation directly with their ABI args so
    # the isolated code blob keeps its PC-relative literal pool intact.
    for name in ("h1_touch_caller_candidate", "negative_touch_reversed_priority",
                 "negative_touch_ignores_state_one"):
        result[name] = code
    return result, object_path


class TouchCallerMachine:
    def __init__(self, image: bytes, candidate: bytes | None,
                 reverse_selection: bool = False, ignore_state_one: bool = False):
        require_unicorn()
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.arm = arm
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_protect(GLOBAL_SLOT & ~0xFFF, 0x1000,
                            unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.candidate = candidate
        self.reverse_selection = reverse_selection
        self.ignore_state_one = ignore_state_one
        if candidate is not None:
            if len(candidate) > 0x1000:
                raise ValueError("candidate exceeds the reserved injection page")
            self.uc.mem_write(INJECT, candidate)
        self.plan: dict[int, tuple[int, ...]] = {}
        self.counts: dict[int, int] = {}
        self.calls: list[dict] = []
        self.fault: str | None = None
        self.stopped = False
        self.stop_pc = RETURN if candidate is not None else STOP
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, address, _size, _user):
        if address == self.stop_pc:
            self.stopped = True
            uc.emu_stop()
            return
        if address != TOUCH_QUERY:
            return
        raw = uc.reg_read(arm.UC_ARM_REG_R0)
        handle = s16(raw)
        occurrence = self.counts.get(handle, 0)
        responses = self.plan.get(handle, ())
        if occurrence >= len(responses):
            self.fault = f"no external helper response for handle {handle} call {occurrence}"
            uc.emu_stop()
            return
        response = responses[occurrence]
        self.counts[handle] = occurrence + 1
        self.calls.append({"handle_signed": handle, "handle_raw": hex(raw & 0xFFFFFFFF),
                           "occurrence_for_handle": occurrence,
                           "response": response})
        uc.reg_write(arm.UC_ARM_REG_R0, response & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def execute(self, responses: dict[int, tuple[int, ...]], cursor: int,
                confirm: int, handles: tuple[int, ...] = DEFAULT_HANDLES) -> dict:
        if len(handles) != 4:
            raise ValueError("exactly four halfword handles are required")
        data = bytearray([0xCD]) * DATA_SIZE
        struct.pack_into("<4H", data, 0x100 + 0x74, *(handle & 0xFFFF for handle in handles))
        struct.pack_into("<I", data, 0x100 + 8, cursor & 0xFFFFFFFF)
        data[0x100 + 0x63] = confirm & 0xFF
        self.uc.mem_write(DATA, bytes(data))
        self.uc.mem_write(STACK, bytes([0xA5]) * STACK_SIZE)
        self.uc.mem_write(GLOBAL_SLOT, struct.pack("<I", WORK))
        self.plan = {int(handle): tuple(values) for handle, values in responses.items()}
        self.counts.clear()
        self.calls.clear()
        self.fault = None
        self.stopped = False

        for index in range(13):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), 0xA5A50000 | index)
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.uc.reg_write(arm.UC_ARM_REG_R8, GLOBAL_SLOT)
        if self.candidate is not None:
            self.uc.reg_write(arm.UC_ARM_REG_R0, WORK)
            self.uc.reg_write(arm.UC_ARM_REG_R1, int(self.reverse_selection))
            self.uc.reg_write(arm.UC_ARM_REG_R2, int(self.ignore_state_one))
        initial_saved = [0xA5A50000 | index for index in range(4, 12)]
        initial_saved[8 - 4] = GLOBAL_SLOT
        initial_d = [0x1122334455667700 | index for index in range(8, 16)]
        for index, value in enumerate(initial_d, 8):
            self.uc.reg_write(getattr(arm, f"UC_ARM_REG_D{index}"), value)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        try:
            start = INJECT if self.candidate is not None else ADDRESS
            self.uc.emu_start(start, 0, count=1024)
        except unicorn.UcError as error:
            self.fault = f"{self.uc.reg_read(arm.UC_ARM_REG_PC):#x}: {error}"
        work_bytes = bytes(self.uc.mem_read(WORK, 0xA0))
        return {"fault": self.fault, "stopped": self.stopped,
                "pc": hex(self.uc.reg_read(arm.UC_ARM_REG_PC)),
                "cursor": struct.unpack_from("<I", work_bytes, 8)[0],
                "confirm": work_bytes[0x63], "work_hex": work_bytes.hex(),
                "calls": self.calls.copy(), "unused_responses": {
                    str(handle): max(0, len(values) - self.counts.get(handle, 0))
                    for handle, values in self.plan.items()},
                "r0": self.uc.reg_read(arm.UC_ARM_REG_R0),
                "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
                "r4_r11": [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                            for i in range(4, 12)],
                "expected_r4_r11": initial_saved,
                "r8_r11": [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}"))
                           for i in range(8, 12)],
                "d8_d15": [self.uc.reg_read(getattr(arm, f"UC_ARM_REG_D{i}"))
                           for i in range(8, 16)],
                "expected_d8_d15": initial_d}


def compare_runs(original: dict, candidate: dict) -> str | None:
    if original["fault"] or candidate["fault"]:
        return f"fault: original={original['fault']} candidate={candidate['fault']}"
    if not original["stopped"] or original["pc"] != hex(STOP):
        return f"original did not stop at caller continuation {STOP:#x}"
    if not candidate["stopped"] or candidate["pc"] != hex(RETURN):
        return "candidate did not return to its caller sentinel"
    if original["cursor"] != candidate["cursor"]:
        return "cursor differs"
    if original["confirm"] != candidate["confirm"]:
        return "confirmation byte differs"
    if original["work_hex"] != candidate["work_hex"]:
        return "work bytes differ"
    if original["calls"] != candidate["calls"]:
        return "helper call order/arguments/responses differ"
    if candidate["r0"] != candidate["cursor"]:
        return "candidate return r0 does not report its final cursor"
    if candidate["r4_r11"] != candidate["expected_r4_r11"]:
        return "candidate violates C++ callee-saved r4-r11 ABI"
    if (candidate["sp"] != SP or original["sp"] != SP
            or original["d8_d15"] != original["expected_d8_d15"]
            or candidate["d8_d15"] != candidate["expected_d8_d15"]):
        return "SP/VFP state is not preserved"
    if original["r8_r11"] != candidate["r8_r11"]:
        return "stable global/callee-saved r8-r11 values differ"
    return None


def _run_pair(image: bytes, candidates: dict[str, bytes], symbol: str,
              response_plan: dict[int, tuple[int, ...]], cursor: int, confirm: int,
              handles: tuple[int, ...] = DEFAULT_HANDLES) -> tuple[dict, dict, str | None]:
    original = TouchCallerMachine(image, None)
    candidate = TouchCallerMachine(
        image, candidates[symbol],
        reverse_selection=symbol == "negative_touch_reversed_priority",
        ignore_state_one=symbol == "negative_touch_ignores_state_one")
    original_result = original.execute(response_plan, cursor, confirm, handles)
    candidate_result = candidate.execute(response_plan, cursor, confirm, handles)
    mismatch = compare_runs(original_result, candidate_result)
    return original_result, candidate_result, mismatch


def run_experiment(code_path: Path, output: Path) -> dict:
    image = code_path.read_bytes()
    reference = verify_reference(image)
    candidates, object_path = build_candidates(output)
    h0, h1, h2, h3 = DEFAULT_HANDLES
    cases = [
        {"name": "first selection wins; later state 2 cannot replace it",
         "responses": {h0: [1, 0], h1: [2], h2: [0], h3: [0]},
         "cursor": 0xA5A5A5A5, "confirm": 0, "expected_cursor": 0, "expected_confirm": 0},
        {"name": "second helper probe state 2 selects after first nonmatch",
         "responses": {h0: [0, 0, 0], h1: [0, 2, 0], h2: [0], h3: [0]},
         "cursor": 0xA5A5A5A5, "confirm": 0, "expected_cursor": 1, "expected_confirm": 0},
        {"name": "last state 6 wins and sets confirmation",
         "responses": {h0: [0, 0, 0], h1: [0, 0, 6], h2: [0, 0, 6], h3: [0, 0, 6]},
         "cursor": 0xA5A5A5A5, "confirm": 0, "expected_cursor": 3, "expected_confirm": 1},
        {"name": "helper result changes between first and second probe and touch pass",
         "responses": {h0: [0, 2, 6], h1: [0], h2: [0], h3: [0]},
         "cursor": 0xA5A5A5A5, "confirm": 0, "expected_cursor": 0, "expected_confirm": 1},
        {"name": "first probe selection then state 6 in second scan",
         "responses": {h0: [1, 6], h1: [0], h2: [0], h3: [0]},
         "cursor": 0xA5A5A5A5, "confirm": 0, "expected_cursor": 0, "expected_confirm": 1},
        {"name": "no match preserves cursor and sticky confirmation byte",
         "responses": {h0: [0, 0, 0], h1: [3, 0, 0], h2: [-1, 0, 0], h3: [5, 0, 0]},
         "cursor": 0xA5A5A5A5, "confirm": 0x7B,
         "expected_cursor": 0xA5A5A5A5, "expected_confirm": 0x7B},
        {"name": "signed halfword handle boundaries",
         "responses": {-32767: [1, 0], -2: [0], 32767: [0], -1: [6]},
         "handles": (0x8001, 0xFFFE, 0x7FFF, 0xFFFF),
         "cursor": 0xA5A5A5A5, "confirm": 0, "expected_cursor": 3, "expected_confirm": 1},
    ]
    results = []
    for case in cases:
        plan = {int(key): tuple(value) for key, value in case["responses"].items()}
        handles = tuple(case.get("handles", DEFAULT_HANDLES))
        original, candidate, mismatch = _run_pair(
            image, candidates, "h1_touch_caller_candidate", plan,
            case["cursor"], case["confirm"], handles)
        semantic_ok = (mismatch is None and original["cursor"] == case["expected_cursor"]
                       and original["confirm"] == case["expected_confirm"])
        results.append({"name": case["name"], "passed": semantic_ok,
                        "expected_cursor": hex(case["expected_cursor"] & 0xFFFFFFFF),
                        "expected_confirm": case["expected_confirm"],
                        "comparison_error": mismatch,
                        "original": original, "candidate": candidate})

    reversed_plan = {h0: (1, 0), h1: (1, 0), h2: (0,), h3: (1, 0)}
    rev_original, rev_candidate, rev_difference = _run_pair(
        image, candidates, "negative_touch_reversed_priority", reversed_plan,
        0xA5A5A5A5, 0)
    reversed_detected = (rev_difference == "cursor differs"
                         and rev_original["cursor"] == 0 and rev_candidate["cursor"] == 3)

    compare_plan = {h0: (1, 0, 0), h1: (0, 0, 0), h2: (0, 0, 0), h3: (0, 0, 0)}
    cmp_original, cmp_candidate, cmp_difference = _run_pair(
        image, candidates, "negative_touch_ignores_state_one", compare_plan,
        0xA5A5A5A5, 0)
    comparison_detected = (cmp_difference == "cursor differs"
                           and cmp_original["cursor"] == 0
                           and cmp_candidate["cursor"] == 0xA5A5A5A5)

    source = ROOT / "experiments/semantic_equivalence/h1_touch_caller_candidate.cpp"
    report = {
        "task_id": "h1-touch-caller-candidate",
        "passed": all(item["passed"] for item in results)
                   and reversed_detected and comparison_detected,
        "reference": reference,
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "object_sha256": hashlib.sha256(object_path.read_bytes()).hexdigest(),
        "object_path": str(object_path),
        "compiler": str(find_clang()), "compiler_flags": get_armv6k_flags(ROOT, find_clang()),
        "cases": results,
        "negative_controls": {
            "reversed_first_selection_priority": {
                "passed": reversed_detected, "first_difference": rev_difference,
                "original_cursor": hex(rev_original["cursor"]),
                "negative_cursor": hex(rev_candidate["cursor"]),
                "original_calls": rev_original["calls"], "negative_calls": rev_candidate["calls"]},
            "ignores_state_one": {
                "passed": comparison_detected, "first_difference": cmp_difference,
                "original_cursor": hex(cmp_original["cursor"]),
                "negative_cursor": hex(cmp_candidate["cursor"]),
                "original_calls": cmp_original["calls"], "negative_calls": cmp_candidate["calls"]},
        },
        "evidence": {"compiled": "passed", "arm_differential": "passed",
                     "caller": "partial", "runtime": "not_run"},
        "limitations": [
            "The original 0x001E9E4C..0x001E9EB8 caller window and compiled C++ candidate are compared with only the external 0x0029D8FC helper entry stubbed; the helper's physical input implementation is not executed.",
            "Per-handle scripted responses intentionally vary between the first scan's two probes and the second scan; they are test inputs, not runtime response stability claims.",
            "The original window is inline in a larger callback and uses r4/r6/r7 as live scratch. Candidate C++ is a function and must preserve r4-r11/SP/VFP according to AAPCS; raw caller-saved r0 and inline scratch registers are therefore not compared across architectures. Candidate return r0 is checked against final cursor, while original r0 at stop is recorded only.",
            "Only work+8, work+0x63, helper ABI arguments/responses, stop/return PCs, and selected ABI state are established. No preceding timer/blend, following transition, physical coordinates/hitboxes, or Azahar runtime behavior is claimed."
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"H1 touch caller experiment {'PASS' if report['passed'] else 'FAIL'}; "
          f"{sum(item['passed'] for item in results)}/{len(results)} cases; report: {output / 'report.json'}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "build/azahar-validation/exefs/code.bin")
    parser.add_argument("--output", type=Path, required=True,
                        help="fresh private output directory")
    args = parser.parse_args()
    report = run_experiment(args.code, args.output)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
