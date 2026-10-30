"""Independent caller-window check for the two title alpha-helper calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import struct
import unittest

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k
from tools.h1_alpha_experiment import verify_reference
from tools.semantic_experiment import (
    DATA, DATA_SIZE, INJECT, SP, STACK, STACK_SIZE, TEXT, Runner, arm, arm_branch,
    unicorn,
)
from tools.semantic_experiment_support import load_pinned_reference


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "build/agent-work/H1-semantic/h1-alpha-caller-review/sleep-20261025/checks/caller-window"
SOURCE = ROOT / "experiments/semantic_equivalence/h1_alpha_candidates.cpp"
CODE = ROOT / "extracted/exefs/code.bin"
CALLER_START = 0x001EA070
CALLER_STOP = 0x001EA128
ALPHA_ENTRY = 0x0029BDB4
CALL_A_RETURN = 0x001EA09C
CALL_B_RETURN = 0x001EA128
WORK, HANDLE_A, HANDLE_B = 0x100, 0x300, 0x340
CHILD_A, CHILD_B = 0x400, 0x600
NESTED_A, NESTED_B = 0x800, 0xA00
TARGET_A, TARGET_B = 0xC00, 0xE00
ALPHA_A = 0x3F400000  # 0.75, preloaded in child A +0x78
ALPHA_B = 0x3F000000  # 0.5, preloaded in child B +0x78
S16 = 0x3F000000     # Caller applies this to A's component scale.
S17 = 0x3E800000     # Caller applies this to B's component scale.


def put32(data: bytearray, offset: int, value: int) -> None:
    struct.pack_into("<I", data, offset, value & 0xFFFFFFFF)


def caller_memory(flags_a: int, flags_b: int, gate_a: int, gate_b: int) -> bytes:
    data = bytearray([0xCD]) * DATA_SIZE
    put32(data, WORK + 0x8C, DATA + HANDLE_A)
    put32(data, WORK + 0x90, DATA + HANDLE_B)
    put32(data, WORK + 8, 0)
    data[WORK + 0x94] = 0
    put32(data, HANDLE_A, flags_a)
    put32(data, HANDLE_B, flags_b)
    put32(data, HANDLE_A + 8, DATA + CHILD_A)
    put32(data, HANDLE_B + 8, DATA + CHILD_B)
    for child, nested, target, gate, alpha in (
        (CHILD_A, NESTED_A, TARGET_A, gate_a, ALPHA_A),
        (CHILD_B, NESTED_B, TARGET_B, gate_b, ALPHA_B),
    ):
        put32(data, child + 0x34, gate)
        put32(data, child + 0x2C, DATA + nested)
        put32(data, child + 0x58, 0)
        put32(data, child + 0x4C, DATA + target)
        put32(data, child + 0x74, 0x40000000)  # Caller overwrites this from S16/S17.
        put32(data, child + 0x78, alpha)
        put32(data, target + 0x40, 0x41200000)
        put32(data, target + 0x44, 0x3F000000)
        put32(data, target + 0x48, 0x3F400000)
        put32(data, target + 0x4C, INJECT + 0x100)  # Controlled return-only callback for fade helper.
        put32(data, target + 0x50, 0)
    return bytes(data)


def run_window(image: bytes, memory: bytes, helper: bytes | None,
               candidate_name: str) -> dict:
    runner = Runner(image, ALPHA_ENTRY)
    # The original fade helper indirect-call path reaches this synthetic stub
    # when the alpha gate is positive; it only returns, with no hidden effects.
    runner.uc.mem_write(INJECT + 0x100, struct.pack("<I", 0xE12FFF1E))  # bx lr
    if helper is not None:
        runner.uc.mem_write(INJECT, helper)
        runner.uc.mem_write(ALPHA_ENTRY, arm_branch(ALPHA_ENTRY, INJECT))
    uc = runner.uc
    runner.stops = (CALLER_STOP,)
    calls: list[int] = []

    def count_call(_uc, address, _size, _user):
        if address in (CALL_A_RETURN - 4, CALL_B_RETURN - 4):
            calls.append(address)

    uc.hook_add(unicorn.UC_HOOK_CODE, count_call)
    uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
    uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
    uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
    regs = [0xA5A50000 | index for index in range(13)]
    regs[4] = DATA + WORK
    regs[5] = DATA + WORK
    regs[7] = 1
    for index, value in enumerate(regs):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_R{index}"), value)
    for index in range(8, 16):
        uc.reg_write(getattr(arm, f"UC_ARM_REG_D{index}"), 0)
    uc.reg_write(arm.UC_ARM_REG_S16, S16)
    uc.reg_write(arm.UC_ARM_REG_S17, S17)
    uc.reg_write(arm.UC_ARM_REG_SP, SP)
    uc.reg_write(arm.UC_ARM_REG_LR, CALLER_STOP)
    uc.mem_write(DATA, memory)
    uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
    runner.reads.clear()
    runner.writes.clear()
    runner.stopped = False
    fault = None
    try:
        uc.emu_start(CALLER_START, 0, count=2048)
    except unicorn.UcError as error:
        fault = str(error)
    return {
        "name": candidate_name,
        "stopped": runner.stopped,
        "pc": uc.reg_read(arm.UC_ARM_REG_PC),
        "fault": fault,
        "calls": calls,
        "gp": [uc.reg_read(reg) for reg in runner.reg_ids],
        "sp": uc.reg_read(arm.UC_ARM_REG_SP),
        "fpscr": uc.reg_read(arm.UC_ARM_REG_FPSCR),
        "fpexc": uc.reg_read(arm.UC_ARM_REG_FPEXC),
        "d8_d15": [uc.reg_read(reg) for reg in runner.d_ids],
        "data": bytes(uc.mem_read(DATA, DATA_SIZE)),
        "stack": bytes(uc.mem_read(STACK, STACK_SIZE)),
        "reads": sorted(runner.reads),
        "writes": sorted(runner.writes),
    }


def observable_difference(reference: dict, other: dict) -> str | None:
    if not reference["stopped"] or reference["pc"] != CALLER_STOP or reference["fault"]:
        return "reference did not reach caller stop cleanly"
    if not other["stopped"] or other["pc"] != CALLER_STOP or other["fault"]:
        return "replacement did not reach caller stop cleanly"
    if reference["calls"] != other["calls"]:
        return "helper call-site trace"
    if reference["gp"][4:12] != other["gp"][4:12] or reference["sp"] != other["sp"]:
        return "callee-saved GP/SP state"
    if reference["d8_d15"] != other["d8_d15"]:
        return "callee-saved VFP state"
    for key in ("fpscr", "fpexc", "data", "stack", "reads", "writes"):
        if reference[key] != other[key]:
            return key
    return None


class H1AlphaCallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        pinned = load_pinned_reference(CODE, ROOT / "config/game_info.json",
                                       ROOT / "config/functions.csv")
        cls.image = pinned.image
        cls.reference = verify_reference(cls.image, pinned.game_info, pinned.ledger)
        build = compile_tu_armv6k(SOURCE, OUTPUT / "h1_alpha_candidates.o", ROOT)
        if build.returncode:
            raise RuntimeError(build.stderr or "ARMv6K candidate compilation failed")
        cls.object_path = OUTPUT / "h1_alpha_candidates.o"
        functions = extract_elf_functions_detailed(cls.object_path)
        if any(relocations for _body, relocations in functions.values()):
            raise RuntimeError("caller review requires relocation-free local helper blobs")
        cls.blobs = {name: body for name, (body, _relocations) in functions.items()}
        if not {"candidate_0029bdb4", "negative_wrong_offset"} <= cls.blobs.keys():
            raise RuntimeError("compiled TU is missing expected candidate/control")

    def test_two_title_call_sites_and_negative_control(self):
        cases = [
            # A enters when bit 2 is clear; B enters when bit 2 is set.
            ("both-helper-calls-positive-gates", 0, 4, 1, 1, [CALL_A_RETURN - 4, CALL_B_RETURN - 4]),
            ("both-helper-calls-nonpositive-gates", 0, 4, 0, -1, [CALL_A_RETURN - 4, CALL_B_RETURN - 4]),
            # Opposite flag states suppress both helper calls.
            ("both-helper-calls-skipped", 4, 0, 1, 1, []),
        ]
        results = []
        negative = None
        for label, flags_a, flags_b, gate_a, gate_b, expected_calls in cases:
            memory = caller_memory(flags_a, flags_b, gate_a, gate_b)
            original = run_window(self.image, memory, None, "original")
            candidate = run_window(self.image, memory,
                                   self.blobs["candidate_0029bdb4"], "candidate")
            self.assertEqual(original["calls"], expected_calls, label)
            self.assertIsNone(observable_difference(original, candidate), label)
            target_a = int.from_bytes(candidate["data"][TARGET_A + 0x40:TARGET_A + 0x44], "little")
            target_b = int.from_bytes(candidate["data"][TARGET_B + 0x40:TARGET_B + 0x44], "little")
            if label == "both-helper-calls-positive-gates":
                self.assertEqual((target_a, target_b), (0x3EC00000, 0x3E000000))
            else:
                self.assertEqual((target_a, target_b), (0x41200000, 0x41200000))
            results.append({"case": label, "calls": [hex(pc) for pc in original["calls"]],
                            "passed": True,
                            "handle_a_flags": int.from_bytes(candidate["data"][HANDLE_A:HANDLE_A + 4], "little"),
                            "handle_b_flags": int.from_bytes(candidate["data"][HANDLE_B:HANDLE_B + 4], "little"),
                            "work_0x98_bits": candidate["data"][WORK + 0x98:WORK + 0x9C].hex(),
                            "child_a_alpha_bits": candidate["data"][CHILD_A + 0x78:CHILD_A + 0x7C].hex(),
                            "child_b_alpha_bits": candidate["data"][CHILD_B + 0x78:CHILD_B + 0x7C].hex(),
                            "target_a_alpha_bits": candidate["data"][TARGET_A + 0x40:TARGET_A + 0x44].hex(),
                            "target_b_alpha_bits": candidate["data"][TARGET_B + 0x40:TARGET_B + 0x44].hex()})
            if label == "both-helper-calls-positive-gates":
                wrong = run_window(self.image, memory, self.blobs["negative_wrong_offset"], "negative_wrong_offset")
                negative = {"detected": observable_difference(original, wrong) is not None,
                            "first_difference": observable_difference(original, wrong),
                            "changed_child_a_0x78": original["data"][CHILD_A + 0x78:CHILD_A + 0x7C].hex()
                            != wrong["data"][CHILD_A + 0x78:CHILD_A + 0x7C].hex(),
                            "changed_child_b_0x78": original["data"][CHILD_B + 0x78:CHILD_B + 0x7C].hex()
                            != wrong["data"][CHILD_B + 0x78:CHILD_B + 0x7C].hex()}
                negative["changed_child_a_0x7c"] = (
                    original["data"][CHILD_A + 0x7C:CHILD_A + 0x80].hex()
                    != wrong["data"][CHILD_A + 0x7C:CHILD_A + 0x80].hex())
                negative["changed_child_b_0x7c"] = (
                    original["data"][CHILD_B + 0x7C:CHILD_B + 0x80].hex()
                    != wrong["data"][CHILD_B + 0x7C:CHILD_B + 0x80].hex())
                self.assertTrue(negative["detected"])
                self.assertTrue(negative["changed_child_a_0x7c"])
                self.assertTrue(negative["changed_child_b_0x7c"])

        report = {
            "schema": 1,
            "passed": all(item["passed"] for item in results) and bool(negative and negative["detected"]),
            "scope": "synthetic ARM caller window 0x001EA070..0x001EA128, comparing original/candidate helper and a wrong-offset control",
            "reference_sha256": hashlib.sha256(self.image).hexdigest(),
            "reference_function": self.reference,
            "candidate_source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "review_runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "candidate_object_sha256": hashlib.sha256(self.object_path.read_bytes()).hexdigest(),
            "caller_range": [hex(CALLER_START), hex(CALLER_STOP)],
            "call_sites": {"A": {"return_pc": hex(CALL_A_RETURN), "condition": "handle A flags bit 2 clear", "helper_child_alpha": "child A +0x78 loaded into s0; s16 stored to +0x74"},
                           "B": {"return_pc": hex(CALL_B_RETURN), "condition": "handle B flags bit 2 set", "helper_child_alpha": "child B +0x78 loaded into s0; s17 stored to +0x74"}},
            "cases": results,
            "negative_control": negative,
            "comparison_policy": ["stop/fault and call-site trace", "callee-saved r4-r11 and SP", "callee-saved d8-d15", "FPSCR/FPEXC", "full mapped ordinary data and stack", "ordinary-memory read/write byte sets"],
            "caller_saved_policy": "r0-r3/r12, s0-s15, and NZCV are not compared at the stop because the caller does not consume them before the next instruction; helper returns no value.",
            "limitations": ["Synthetic handle/child/target graph and alpha values; no capture from Azahar or runtime-normal object proof.", "Window begins at the helper-mutator block, not readiness/fade entry, and ends immediately after the second helper return.", "Does not execute the following help-table lookup, Camp_SetSlotMessage, renderer, complete callback, IPS, emulator, or game scenario."],
        }
        report_path = OUTPUT / "report.json"
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        self.assertEqual(len(results), 3)
        self.assertEqual(len(results[0]["calls"]), 2)
        self.assertEqual(len(results[1]["calls"]), 2)
        self.assertEqual(len(results[2]["calls"]), 0)
        self.assertIsNotNone(report_path)


if __name__ == "__main__":
    unittest.main()
