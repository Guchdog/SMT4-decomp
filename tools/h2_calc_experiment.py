#!/usr/bin/env python3
"""Differentially exercise TitleConfig_Calc with explicit mocked services.

This runner executes the pinned ARM callback and compiled C++ candidate in
separate Unicorn machines. Only documented external service boundaries are
stubbed. It is not a guest-input injector or a whole-title/runtime test.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import capstone
import unicorn
from unicorn import arm_const as arm
from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import TEXT, arm_branch

ADDRESS = 0x001EA928
INJECT = 0x01000000
INJECT_SIZE = 0x10000
DATA = 0x02000000
DATA_SIZE = 0x4000
STACK = 0x08000000
STACK_SIZE = 0x8000
SP = STACK + STACK_SIZE // 2
RETURN = INJECT + INJECT_SIZE - 4
WORK = DATA + 0x400
TASK = DATA + 0x900
PAYLOAD = DATA + 0x1000
SOURCE = ROOT / "experiments/semantic_equivalence/h2_calc_candidate.cpp"
CODE_DEFAULT = ROOT / "extracted/exefs/code.bin"
SYMBOL = "candidate_001ea928"
BAD_WRITE = "candidate_001ea928_badwrite"
U32 = 0xFFFFFFFF
TEXT_SIZE = 0x400000
CONFIG_GLOBAL = 0x0044E0F8
WORK_GLOBAL = 0x0044E2D0

SERVICES = {
    0x002A63F8: "resource_available",
    0x002BF9F0: "sprite_ready",
    0x002B88C4: "register_touch",
    0x0029F260: "cursor_scroll",
    0x0029F248: "cursor_row",
    0x002C0EC4: "tbb_table",
    0x002C0E9C: "tbb_payload",
    0x0029F10C: "display_message",
    0x0025A0D0: "message_update",
    0x002972F8: "script_process",
    0x0029D8FC: "touch_state",
    0x002C1830: "logical_query",
    0x0025A0B4: "touch_repeat_ready",
    0x002BF6D0: "special_info",
    0x001C3588: "script_value",
    0x001DD158: "script_index",
    0x002C615C: "bounded_value",
    0x002B91C4: "play_effect",
    0x002C5A6C: "effect_update",
    0x0025A0A4: "audio_value",
    0x0025A004: "audio_set",
    0x002BC210: "effect_prepare",
    0x002BFF9C: "effect_value",
    0x002BFDFC: "effect_play",
    0x0029F278: "cursor_update",
    0x0029EDFC: "cursor_select",
    0x002BC200: "play_ui_effect",
    0x002971E4: "script_start",
    0x002BDAC0: "sprite_animation",
    0x002ADB40: "copy_pair",
    0x0019DFBC: "script_runner",
    0x00297674: "exit_decision",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tbb_row_offset(index: int) -> int:
    """Calc's 32-bit row address delta for an ordinary non-wrapping index."""
    return (0x16 + (index & U32) * 0x96) & U32


def arm_special_helper_arguments(script_value: int, current_value: int,
                                 limit: int = 10) -> tuple[int, int, int]:
    """Expected ARM modulo-u32 arguments for the special-handle helper."""
    difference = ((script_value & U32) - (current_value & U32)) & U32
    scale = (difference * 5) & U32
    return (scale * 2) & U32, limit & U32, scale


def relocated_candidate(obj: Path) -> tuple[bytes, list[dict]]:
    functions = extract_elf_functions_detailed(obj)
    if SYMBOL not in functions:
        raise ValueError(f"object lacks {SYMBOL}")
    code, relocations = functions[SYMBOL]
    fixed = bytearray(code)
    fixup_report = []
    for relocation in relocations:
        if relocation.relocation_type != 2 or relocation.symbol_name:
            raise ValueError(f"unsupported relocation in candidate: {relocation}")
        old = struct.unpack_from("<I", fixed, relocation.offset)[0]
        struct.pack_into("<I", fixed, relocation.offset, (old + INJECT) & U32)
        fixup_report.append({"offset": hex(relocation.offset), "kind": "R_ARM_ABS32 .text",
                             "addend": hex(old), "relocated": hex((old + INJECT) & U32)})
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    decoder.detail = True
    decoded = list(decoder.disasm(bytes(fixed), INJECT))
    if not decoded:
        raise ValueError("candidate code failed to decode")
    for insn in decoded:
        if insn.group(capstone.CS_GRP_CALL):
            if insn.mnemonic not in ("bl", "blx"):
                raise ValueError("unexpected candidate call form")
    return bytes(fixed), fixup_report


@dataclass
class Scenario:
    label: str
    state: int
    row: int = 0
    scroll: int = 0
    values: tuple[int, int, int] = (1, 2, 3)
    logical: dict[tuple[int, int], int] | None = None
    touch: dict[int, int] | None = None
    touch_repeat: int = 1
    resource_available: int = 1
    sprite_ready: int = 1
    cursor_changed: int = 0
    script_runner: int = 2
    exit_decision: int = 2
    row_handle: int = -1
    decrement_handle: int = -1
    increment_handle: int = -1
    special_handle: int = -1
    handle_count: int = 0
    missing_script_handles: bool = False
    script_value: int = 12
    script_index: int = 4
    bounded_value_result: int = 5


def directed_scenarios(seed: int, samples: int) -> list[Scenario]:
    cases = [
        Scenario("state0-resource-wait", 0, resource_available=0),
        Scenario("state0-sprite-wait", 0, sprite_ready=0),
        Scenario("state0-missing-script-handle", 0, missing_script_handles=True),
        Scenario("state0-initialize", 0),
        Scenario("state1-noop", 1),
        Scenario("state1-decrement", 1, row=0, values=(1, 2, 3), logical={(4, 0): 1}),
        Scenario("state1-decrement-at-zero", 1, row=0, values=(0, 2, 3), logical={(4, 0): 1}),
        Scenario("state1-increment", 1, row=1, values=(1, 9, 3), logical={(3, 0): 1}),
        Scenario("state1-increment-at-ten", 1, row=1, values=(1, 10, 3), logical={(3, 0): 1}),
        Scenario("state1-touch-decrement", 1, row=2, values=(1, 2, 3), decrement_handle=0x111,
                 touch={0x111: 2}),
        Scenario("state1-touch-default-row", 1, row=1, values=(1, 2, 3), row_handle=0x110,
                 touch={0x110: 6}),
        Scenario("state1-touch-default-row-zero", 1, row=0, values=(1, 2, 3), row_handle=0x110,
                 touch={0x110: 6}),
        Scenario("state1-touch-default-row-two", 1, row=2, values=(1, 2, 3), row_handle=0x110,
                 touch={0x110: 6}),
        Scenario("state1-logical-default-row", 1, row=0, values=(1, 2, 3), row_handle=0x110,
                 logical={(9, 1): 1}),
        Scenario("state1-registered-handle-touch", 1, row=1, values=(1, 2, 3),
                 touch={0x101: 6}),
        Scenario("state1-touch-state-one-decrement", 1, row=2, values=(1, 2, 3),
                 decrement_handle=0x111, touch={0x111: 1}, touch_repeat=0),
        Scenario("state1-special-handle", 1, row=2, values=(1, 2, 3), special_handle=0x112,
                 touch={0x112: 2}),
        Scenario("state1-special-wrap-max-minus-min", 1, row=2, special_handle=0x112,
                 touch={0x112: 2}, script_value=0x7FFFFFFF,
                 script_index=-(1 << 31), bounded_value_result=3),
        Scenario("state1-special-wrap-min-minus-max", 1, row=2, special_handle=0x112,
                 touch={0x112: 2}, script_value=-(1 << 31),
                 script_index=0x7FFFFFFF, bounded_value_result=7),
        Scenario("state1-special-scale-positive-extreme", 1, row=2, special_handle=0x112,
                 touch={0x112: 2}, script_value=0x7FFFFFFF, script_index=0,
                 bounded_value_result=10),
        Scenario("state1-special-scale-negative-extreme", 1, row=2, special_handle=0x112,
                 touch={0x112: 2}, script_value=-(1 << 31), script_index=0,
                 bounded_value_result=0),
        Scenario("state1-transition-state2", 1, logical={(0, 1): 1}),
        Scenario("state1-transition-state3", 1, logical={(1, 1): 1}),
    ]
    for row in (0, 1, 2):
        cases.append(Scenario(f"state1-cursor-refresh-row-{row}", 1, row=row,
                              scroll=0, values=(1, 2, 3), cursor_changed=1))
    for decision in (0, 1, 2, 3):
        cases.append(Scenario(f"state2-exit-result-{decision}", 2, exit_decision=decision))
    cases.extend((Scenario("state2-script-pending", 2, script_runner=1),
                  Scenario("state3-not-ready", 3, sprite_ready=0),
                  Scenario("state3-ready", 3, sprite_ready=1),
                  Scenario("state4-terminal", 4),
                  Scenario("state5-common", 5),
                  Scenario("state-high-unsigned", 0x80000000)))
    rng = random.Random(seed)
    for index in range(samples):
        row = rng.randrange(3)
        values = tuple(rng.randrange(11) for _ in range(3))
        logical: dict[tuple[int, int], int] = {}
        if index % 3 == 0:
            logical[(4, 0)] = 1
        elif index % 3 == 1:
            logical[(3, 0)] = 1
        cases.append(Scenario(f"seed-{seed}-valid-{index}", 1, row=row, values=values,
                              logical=logical))
    return cases


class CalcMachine:
    def __init__(self, image: bytes, entry_code: bytes | None = None,
                 scenario: Scenario | None = None):
        self.scenario = scenario or Scenario("default", 1)
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, TEXT_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, INJECT_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_ALL)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_ALL)
        if entry_code is not None:
            self.uc.mem_write(INJECT, entry_code)
            self.uc.mem_write(ADDRESS, arm_branch(ADDRESS, INJECT))
        self.trace: list[tuple] = []
        self.reads: set[int] = set()
        self.writes: set[int] = set()
        self.stop = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._code)
        self.uc.hook_add(unicorn.UC_HOOK_MEM_READ | unicorn.UC_HOOK_MEM_WRITE, self._memory)
        self._initialize()

    def _initialize(self):
        work = bytearray(0x158)
        struct.pack_into("<I", work, 0x00, TASK)
        struct.pack_into("<I", work, 0x08, self.scenario.state & U32)
        struct.pack_into("<HHH", work, 0x14, 0x101, 0x102, 0x103)
        struct.pack_into("<H", work, 0x1A, 0)
        struct.pack_into("<hhhh", work, 0x1C, self.scenario.row_handle,
                         self.scenario.decrement_handle, self.scenario.increment_handle,
                         self.scenario.special_handle)
        struct.pack_into("<III", work, 0x28, *self.scenario.values)
        struct.pack_into("<II", work, 0x34, 0x30505032, 0x00000000)
        script_bf = 0 if self.scenario.missing_script_handles else DATA + 0x1200
        msg_mbm = 0 if self.scenario.missing_script_handles else DATA + 0x1300
        struct.pack_into("<I", work, 0x14C, script_bf)
        struct.pack_into("<I", work, 0x150, msg_mbm)
        struct.pack_into("<I", work, 0x154, TASK)
        # Minimal stable cursor object: its actual services are modeled at the
        # explicit service boundary. The documented count/disabled fields agree.
        work[0xE8 + 0x62] = 0
        struct.pack_into("<I", work, 0xE8 + 0x50, 3)
        self.uc.mem_write(WORK, bytes(work))
        self.uc.mem_write(WORK_GLOBAL, struct.pack("<I", WORK))
        self.uc.mem_write(CONFIG_GLOBAL, bytes((0x32, 0x50, 0x50, 0x30, 0, 0, 0, 0)))
        self.uc.mem_write(PAYLOAD + 0x0C, struct.pack("<I", PAYLOAD + 0x20))
        self.uc.mem_write(PAYLOAD + 0x20, struct.pack("<h", 10))
        self.uc.mem_write(DATA + 0xB00 + 0x0C, struct.pack("<I", PAYLOAD + 0x20))

    def _memory(self, uc, access, address, size, value, _):
        target = self.reads if access == unicorn.UC_MEM_READ else self.writes
        if (WORK <= address < WORK + 0x158 or
                CONFIG_GLOBAL <= address < CONFIG_GLOBAL + 8 or
                WORK_GLOBAL <= address < WORK_GLOBAL + 4):
            target.update(range(address, address + size))

    def _ret(self, uc, value: int = 0):
        uc.reg_write(arm.UC_ARM_REG_R0, value & U32)
        uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def _code(self, uc, address, size, _):
        if address == RETURN:
            self.stop = True
            uc.emu_stop()
            return
        name = SERVICES.get(address)
        if name is None:
            return
        r = [uc.reg_read(getattr(arm, f"UC_ARM_REG_R{i}")) for i in range(4)]
        s0 = uc.reg_read(arm.UC_ARM_REG_S0)
        s1 = uc.reg_read(arm.UC_ARM_REG_S1)
        sc = self.scenario
        result = 0
        if address == 0x002A63F8:
            result = sc.resource_available
        elif address == 0x002BF9F0:
            result = sc.sprite_ready
        elif address == 0x002B88C4:
            result = 0x100 + (r[1] & 0xFF)
        elif address == 0x0029F260:
            result = sc.scroll
        elif address == 0x0029F248:
            result = sc.handle_count if r[0] != WORK + 0xE8 else sc.row
        elif address == 0x002C0EC4:
            result = PAYLOAD
        elif address == 0x002C0E9C:
            result = PAYLOAD + 0x100
        elif address == 0x0029D8FC:
            result = (sc.touch or {}).get(r[0] & 0xFFFF, 0)
        elif address == 0x002C1830:
            result = (sc.logical or {}).get((r[0], r[1]), 0)
        elif address == 0x0025A0B4:
            result = sc.touch_repeat
        elif address == 0x002BF6D0:
            result = DATA + 0xB00
        elif address == 0x001C3588:
            result = sc.script_value
        elif address == 0x001DD158:
            result = sc.script_index
        elif address == 0x002C615C:
            result = sc.bounded_value_result
        elif address == 0x0029F10C:
            self.trace.append((name, r[0], r[1]))
        elif address == 0x002972F8:
            result = 0x13579BDF
        elif address == 0x0025A0A4:
            result = 0x55
        elif address == 0x0029F278:
            result = sc.cursor_changed
        elif address == 0x0019DFBC:
            result = sc.script_runner
        elif address == 0x00297674:
            result = sc.exit_decision
        elif address == 0x002ADB40:
            self.uc.mem_write(r[0], bytes(self.uc.mem_read(r[1], 8)))
        if address == 0x002BFDFC:
            self.trace.append((name, *r, s0, s1))
        else:
            argument_counts = {
                0x002A63F8: 2, 0x002BF9F0: 1, 0x002B88C4: 2,
                0x0029F260: 1, 0x0029F248: 1, 0x002C0EC4: 2,
                0x002C0E9C: 1, 0x0029F10C: 2, 0x0025A0D0: 0,
                0x002972F8: 2, 0x0029D8FC: 1, 0x002C1830: 2,
                0x0025A0B4: 0, 0x002BF6D0: 2, 0x001C3588: 0,
                0x001DD158: 1, 0x002C615C: 3, 0x002B91C4: 1,
                0x002C5A6C: 0, 0x0025A0A4: 0, 0x0025A004: 3,
                0x002BC210: 0, 0x002BFF9C: 0, 0x0029F278: 2,
                0x0029EDFC: 2, 0x002BC200: 1, 0x002971E4: 2,
                0x002BDAC0: 3, 0x002ADB40: 2, 0x0019DFBC: 1,
                0x00297674: 0,
            }
            self.trace.append((name, *r[:argument_counts[address]], result & U32))
        self._ret(uc, result)

    def run(self) -> dict:
        reg_ids = tuple(getattr(arm, f"UC_ARM_REG_R{i}") for i in range(13))
        values = [((0xA5A50000 + i * 0x10101) & U32) for i in range(13)]
        values[0] = 0xCAFEBABE
        cpsr = 0x10 | 0x60000000
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, cpsr)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for reg, val in zip(reg_ids, values):
            self.uc.reg_write(reg, val)
        self.uc.reg_write(arm.UC_ARM_REG_SP, SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        d_regs = tuple(getattr(arm, f"UC_ARM_REG_D{i}") for i in range(8, 16))
        expected_d = tuple(0x0123456789ABCDEF ^ i for i in range(8))
        for reg, val in zip(d_regs, expected_d):
            self.uc.reg_write(reg, val)
        self.trace.clear()
        self.reads.clear()
        self.writes.clear()
        fault = None
        try:
            self.uc.emu_start(ADDRESS, 0, count=100000)
        except unicorn.UcError as exc:
            fault = str(exc)
        preserved_regs = tuple(self.uc.reg_read(reg) for reg in reg_ids[4:12])
        preserved_regs += (self.uc.reg_read(arm.UC_ARM_REG_SP),)
        preserved_regs += tuple(self.uc.reg_read(reg) for reg in d_regs)
        expected_preserved = tuple(values[4:12]) + (SP,) + expected_d
        return {
            "stopped": self.stop,
            "fault": fault,
            "return": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "preserved": preserved_regs,
            "expected_preserved": expected_preserved,
            "work": bytes(self.uc.mem_read(WORK, 0x158)),
            "config": bytes(self.uc.mem_read(CONFIG_GLOBAL, 8)),
            "trace": list(self.trace),
            "reads": frozenset(self.reads),
            "writes": frozenset(self.writes),
        }


def compare(left: dict, right: dict) -> str | None:
    for label, item in (("original", left), ("candidate", right)):
        if item["fault"]:
            return f"{label} fault: {item['fault']}"
        if not item["stopped"]:
            return f"{label} failed to reach return sentinel"
        if item["preserved"] != item["expected_preserved"]:
            return f"{label} violates callee-saved register/SP/d8-d15 ABI"
    for field in ("return", "pc", "work", "config", "trace"):
        if left[field] != right[field]:
            return f"{field} differs"
    return None


def compare_fixture(code: bytes, image: bytes, scenario: Scenario) -> tuple[dict, dict, str | None]:
    original = CalcMachine(image, scenario=scenario).run()
    candidate = CalcMachine(image, entry_code=code, scenario=scenario).run()
    return original, candidate, compare(original, candidate)


def experiment(code_path: Path, output: Path, seed: int, samples: int) -> dict:
    started = time.perf_counter()
    output.mkdir(parents=True, exist_ok=False)
    image = code_path.read_bytes()
    code_hash = hashlib.sha256(image).hexdigest()
    game = json.loads((ROOT / "config/game_info.json").read_text(encoding="utf-8"))
    if len(image) != game["code_bin_size"] or code_hash != game["code_sha256"]:
        raise ValueError("--code must be the pinned configured original code image")
    original_hash = code_hash
    source_hash = sha256(SOURCE)
    obj = output / "h2_calc_candidate.o"
    build = compile_tu_armv6k(SOURCE, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr or "ARMv6K C++ compilation failed")
    candidate, relocations = relocated_candidate(obj)

    results = []
    first_counterexample = None
    for scenario in directed_scenarios(seed, samples):
        original, rebuilt, error = compare_fixture(candidate, image, scenario)
        item = {"case": scenario.label, "state": hex(scenario.state & U32), "passed": error is None,
                "return": hex(original["return"]), "trace_count": len(original["trace"]),
                "config": original["config"].hex(), "counterexample": error,
                "bounded_value_calls": [list(call) for call in original["trace"]
                                         if call[0] == "bounded_value"]}
        results.append(item)
        if error and first_counterexample is None:
            first_counterexample = {"case": scenario.label, "reason": error,
                                    "original_return": hex(original["return"]),
                                    "candidate_return": hex(rebuilt["return"]),
                                    "original_config": original["config"].hex(),
                                    "candidate_config": rebuilt["config"].hex(),
                                    "original_trace": original["trace"],
                                    "candidate_trace": rebuilt["trace"]}

    # Targeted corrupted-observable negative control: deliberately flip config[3]
    # after a correctly executed candidate and prove the comparison rejects it.
    neg_scenario = Scenario("negative-control-state1-increment", 1, row=1,
                            values=(1, 9, 3), logical={(3, 0): 1})
    neg_original, neg_candidate, _ = compare_fixture(candidate, image, neg_scenario)
    corrupt = dict(neg_candidate)
    corrupt["config"] = bytes((neg_candidate["config"][0], neg_candidate["config"][1],
                               neg_candidate["config"][2], neg_candidate["config"][3] ^ 1,
                               *neg_candidate["config"][4:]))
    negative_error = compare(neg_original, corrupt)
    negative = {"name": "flip-config-byte-plus-3-after-candidate",
                "detected": negative_error == "config differs", "difference": negative_error}

    if sha256(SOURCE) != source_hash:
        raise RuntimeError("candidate source changed during experiment")
    compiler = subprocess.run([str(find_clang()), "--version"], capture_output=True,
                              text=True, check=True).stdout.splitlines()[0]
    passed = first_counterexample is None and negative["detected"]
    report = {
        "schema": 1,
        "passed": passed,
        "scope": "TitleConfig_Calc isolated callback with explicit external service stubs",
        "reference_sha256": original_hash,
        "image_sha256": code_hash,
        "source_sha256": source_hash,
        "runner_sha256": sha256(Path(__file__)),
        "test_sha256": sha256(ROOT / "tests/test_h2_calc_experiment.py"),
        "object_sha256": sha256(obj),
        "compiler": compiler,
        "compile_command": build.args,
        "compile_exit": build.returncode,
        "candidate_bytes": len(candidate),
        "relocations_applied": relocations,
        "seed": seed,
        "random_valid_state1_cases": samples,
        "case_count": len(results),
        "cases_passed": sum(case["passed"] for case in results),
        "first_counterexample": first_counterexample,
        "negative_control": negative,
        "evidence": {"compiled": "passed", "arm_differential": "passed" if passed else "failed",
                     "caller": "not_run", "runtime": "not_run"},
        "limits": [
            "The ARM callback and candidate are run with identical deterministic mocks for external service boundaries; this isolates Calc branching and memory effects, not actual service internals.",
            "The logical event IDs and modes are preserved without mapping them to physical button names.",
            "Cursor, touch, script, task, renderer, audio, animation, and state-decision services are modeled at their call boundary. Mapper and byte encoder helpers execute original ARM from the pinned image.",
            "The state-1 special handle calculation is exercised only through its mocked helper calls; its semantic domain is unresolved.",
            "No title caller, changed-option cancellation/confirmation semantics, persistence, Azahar runtime, RSP input, or UI-visible behavior is covered.",
            "Cursor row/scroll and valid work values are constrained to initialized cases; malformed cursor indices and arbitrary work layouts are not claimed equivalent.",
            "The corrupted-byte negative control validates the comparator, not a separately compiled faulty C++ implementation.",
        ],
        "cases": results,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=CODE_DEFAULT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--samples", type=int, default=16)
    args = parser.parse_args()
    start = time.perf_counter()
    report = experiment(args.code, args.output, args.seed, args.samples)
    report["elapsed_seconds"] = round(time.perf_counter() - start, 3)
    (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": report["passed"], "report": str(args.output / "report.json"),
                      "case_count": report["case_count"],
                      "cases_passed": report["cases_passed"],
                      "first_counterexample": report["first_counterexample"],
                      "negative_control": report["negative_control"]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
