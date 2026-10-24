#!/usr/bin/env python3
"""Differentially test the isolated H1 title-navigation reducer family."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k, find_clang
from tools.semantic_experiment import DATA, DATA_SIZE, INJECT, RETURN, STACK, STACK_SIZE, TEXT, validate_local_blob

GATE_START = 0x001E9D0C
GATE_READY_STOP = 0x001E9D2C
GATE_RETURN_STOP = 0x001EA62C
CORE_START = 0x001E9D48
CORE_STOP = 0x001E9DE0
TRIGGER = 0x002B902C
EVENT_REQUEST = 0x002B91C4
WORK = DATA + 0x100
EVENT = DATA + 0x800
EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
TRIGGER_IDS = (5, 0xE, 6, 0xF)


def verify_image(image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    import capstone
    cs = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    windows = ((GATE_START, GATE_READY_STOP), (CORE_START, CORE_STOP))
    decoded = []
    for start, stop in windows:
        code = image[start - TEXT:stop - TEXT]
        insns = list(cs.disasm(code, start))
        if not insns or sum(i.size for i in insns) != len(code):
            raise ValueError(f"incomplete ARM decode in pinned window {start:#x}..{stop:#x}")
        decoded.append({"start": hex(start), "stop": hex(stop), "instruction_count": len(insns)})
    return {"sha256": digest, "windows": decoded}


class NavigationMachine:
    def __init__(self, image: bytes, candidate: bytes | None = None):
        import unicorn
        from unicorn import arm_const as arm
        self.unicorn, self.arm = unicorn, arm
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.ctl_set_cpu_model(arm.UC_CPU_ARM_11MPCORE)
        self.uc.mem_map(TEXT, 0x400000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_write(TEXT, image)
        self.uc.mem_map(INJECT, 0x2000, unicorn.UC_PROT_READ | unicorn.UC_PROT_EXEC)
        self.uc.mem_map(DATA, DATA_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.uc.mem_map(STACK, STACK_SIZE, unicorn.UC_PROT_READ | unicorn.UC_PROT_WRITE)
        self.candidate = candidate
        if candidate is not None:
            validate_local_blob(candidate)
            if len(candidate) > 0x1000:
                raise ValueError("candidate exceeds isolated code page")
            self.uc.mem_write(INJECT, candidate)
        self.trigger_responses: dict[int, int] = {}
        self.ready_responses: dict[int, int] = {}
        self.ready_calls: list[int] = []
        self.trigger_calls: list[int] = []
        self.event_calls: list[dict] = []
        self.stops: tuple[int, ...] = ()
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, address, _size, _user):
        arm = self.arm
        if address in self.stops:
            self.stopped = True
            uc.emu_stop()
            return
        if address == TRIGGER:
            trigger_id = uc.reg_read(arm.UC_ARM_REG_R0)
            if trigger_id not in self.trigger_responses:
                raise ValueError(f"no explicit stub response for trigger ID {trigger_id}")
            self.trigger_calls.append(trigger_id)
            uc.reg_write(arm.UC_ARM_REG_R0, self.trigger_responses[trigger_id])
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
        elif address in (0x00289924, 0x0025A2BC):
            self.ready_responses[address] = int(self.ready_responses.get(address, 0))
            self.ready_calls.append(address)
            uc.reg_write(arm.UC_ARM_REG_R0, self.ready_responses[address])
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
        elif address == EVENT_REQUEST:
            self.event_calls.append({
                "id": uc.reg_read(arm.UC_ARM_REG_R0),
                "cursor": self.read_u32(WORK + 8),
                "cached_cursor": self.read_u32(WORK + 12),
            })
            # Explicit boundary stub: record the caller-visible request and
            # return. The real helper's event queue/state effects are outside scope.
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def write_u32(self, address: int, value: int):
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    def initialize(self, cursor: int, cached_cursor: int):
        self.uc.mem_write(DATA, bytes(DATA_SIZE))
        self.uc.mem_write(STACK, bytes(STACK_SIZE))
        self.write_u32(WORK + 8, cursor)
        self.write_u32(WORK + 12, cached_cursor)
        arm = self.arm
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 5)
        self.uc.reg_write(arm.UC_ARM_REG_R4, WORK)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK + 0x1000)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self.trigger_calls.clear()
        self.ready_calls.clear()
        self.event_calls.clear()
        self.stopped = False

    def run_gates(self, script_ready: bool, preview_ready: bool) -> dict:
        self.initialize(1, 1)
        self.ready_responses = {0x00289924: int(script_ready), 0x0025A2BC: int(preview_ready)}
        self.stops = (GATE_READY_STOP, GATE_RETURN_STOP)
        try:
            self.uc.emu_start(GATE_START, 0, count=64)
        except self.unicorn.UcError as error:
            return {"fault": str(error), "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC)}
        return {"fault": None, "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                "stopped": self.stopped, "ready_calls": list(self.ready_calls),
                "trigger_calls": list(self.trigger_calls)}

    def run_original_core(self, cursor: int, cached_cursor: int,
                          responses: dict[int, int]) -> dict:
        self.initialize(cursor, cached_cursor)
        self.trigger_responses = {trigger_id: int(responses.get(trigger_id, 0))
                                  for trigger_id in TRIGGER_IDS}
        self.stops = (CORE_STOP,)
        try:
            self.uc.emu_start(CORE_START, 0, count=128)
        except self.unicorn.UcError as error:
            return {"fault": str(error), "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC)}
        return {"fault": None, "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                "stopped": self.stopped, "cursor": self.read_u32(WORK + 8),
                "cached_cursor": self.read_u32(WORK + 12),
                "trigger_calls": list(self.trigger_calls), "events": list(self.event_calls)}

    def run_candidate(self, cursor: int, cached_cursor: int, gate_bits: int,
                      trigger_bits: int) -> dict:
        if self.candidate is None:
            raise ValueError("candidate blob is not loaded")
        self.initialize(cursor, cached_cursor)
        self.uc.mem_write(EVENT, bytes(16))
        arm = self.arm
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK)
        self.uc.reg_write(arm.UC_ARM_REG_R1, gate_bits)
        self.uc.reg_write(arm.UC_ARM_REG_R2, trigger_bits)
        self.uc.reg_write(arm.UC_ARM_REG_R3, EVENT)
        self.stops = (RETURN,)
        try:
            self.uc.emu_start(INJECT, 0, count=128)
        except self.unicorn.UcError as error:
            return {"fault": str(error), "pc": self.uc.reg_read(arm.UC_ARM_REG_PC)}
        observation = struct.unpack("<4I", self.uc.mem_read(EVENT, 16))
        return {"fault": None, "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
                "stopped": self.stopped, "cursor": self.read_u32(WORK + 8),
                "cached_cursor": self.read_u32(WORK + 12),
                "return": self.uc.reg_read(arm.UC_ARM_REG_R0),
                "event": {"count": observation[0], "id": observation[1],
                          "cursor": observation[2], "cached_cursor": observation[3]}}


def mask_for(responses: dict[int, int]) -> int:
    return sum((1 << index) for index, trigger_id in enumerate(TRIGGER_IDS)
               if responses.get(trigger_id, 0))


def compare_case(image: bytes, candidate: bytes, label: str, cursor: int,
                 cached: int, responses: dict[int, int]) -> dict:
    original_machine = NavigationMachine(image)
    original = original_machine.run_original_core(cursor, cached, responses)
    candidate_machine = NavigationMachine(image, candidate)
    rebuilt = candidate_machine.run_candidate(cursor, cached, 3, mask_for(responses))
    expected_event = original["events"]
    event = rebuilt["event"]
    event_match = (
        (not expected_event and event["count"] == 0)
        or (len(expected_event) == 1 and event["count"] == 1
            and event["id"] == expected_event[0]["id"]
            and event["cursor"] == expected_event[0]["cursor"]
            and event["cached_cursor"] == expected_event[0]["cached_cursor"])
    )
    passed = (original.get("fault") is None and original.get("stopped")
              and original.get("pc") == CORE_STOP and rebuilt.get("fault") is None
              and rebuilt.get("stopped") and rebuilt.get("pc") == RETURN
              and rebuilt["cursor"] == original["cursor"]
              and rebuilt["cached_cursor"] == original["cached_cursor"]
              and rebuilt["return"] == original["cursor"] and event_match)
    return {"case": label, "input": {"cursor": cursor, "cached_cursor": cached,
                                        "responses": responses},
            "passed": passed, "original": original, "candidate": rebuilt}


def build_candidate(output: Path) -> bytes:
    source = ROOT / "experiments/semantic_equivalence/title_navigation_family_candidate.cpp"
    obj = output / "title_navigation_family_candidate.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    funcs = extract_elf_functions_detailed(obj)
    name = "title_navigation_reduce"
    if name not in funcs:
        raise ValueError(f"missing candidate symbol {name}")
    code, relocations = funcs[name]
    if relocations:
        raise ValueError(f"unsupported candidate relocations: {relocations}")
    validate_local_blob(code)
    import capstone
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    insns = list(decoder.disasm(code, INJECT))
    if sum(instruction.size for instruction in insns) != len(code):
        raise ValueError("candidate contains undecoded ARM bytes")
    calls = [instruction for instruction in insns
             if instruction.mnemonic in ("bl", "blx")]
    if calls:
        raise ValueError("candidate unexpectedly calls a helper: " +
                         ", ".join(f"{i.mnemonic} {i.op_str}" for i in calls))
    return code


def run(code_path: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    reference = verify_image(image)
    candidate = build_candidate(output)
    gate_tests = []
    for script_ready, preview_ready, expected_pc, expected_calls in (
        (False, False, GATE_RETURN_STOP, [0x00289924]),
        (True, False, GATE_RETURN_STOP, [0x00289924, 0x0025A2BC]),
        (True, True, GATE_READY_STOP, [0x00289924, 0x0025A2BC]),
    ):
        result = NavigationMachine(image).run_gates(script_ready, preview_ready)
        gate_bits = int(script_ready) | (int(preview_ready) << 1)
        gated_candidate = NavigationMachine(image, candidate).run_candidate(
            2, 2, gate_bits, 0)
        passed = (result.get("fault") is None and result["stopped"]
                  and result["pc"] == expected_pc and result["ready_calls"] == expected_calls
                  and not result["trigger_calls"] and gated_candidate.get("fault") is None
                  and gated_candidate["cursor"] == 2
                  and gated_candidate["cached_cursor"] == 2
                  and gated_candidate["event"]["count"] == 0)
        gate_tests.append({"script_ready": script_ready, "preview_ready": preview_ready,
                           "passed": passed, "result": result,
                           "candidate": gated_candidate})

    cases = [
        compare_case(image, candidate, "no-input-cache-hit", 2, 2, {}),
        compare_case(image, candidate, "previous-primary-wrap-0-to-3", 0, 0, {5: 1}),
        compare_case(image, candidate, "previous-alias-wrap-0-to-3", 0, 0, {0xE: 1}),
        compare_case(image, candidate, "previous-short-circuits-alias", 2, 2, {5: 1, 0xE: 1}),
        compare_case(image, candidate, "next-primary-wrap-3-to-0", 3, 3, {6: 1}),
        compare_case(image, candidate, "next-alias-wrap-3-to-0", 3, 3, {0xF: 1}),
        compare_case(image, candidate, "next-short-circuits-alias", 2, 2, {6: 1, 0xF: 1}),
        compare_case(image, candidate, "both-directions-sequential-net-zero", 0, 0, {5: 1, 6: 1}),
        compare_case(image, candidate, "previous-then-next-aliases-net-zero", 1, 1, {0xE: 1, 0xF: 1}),
        compare_case(image, candidate, "changed-selection-event-before-cache", 1, 0, {6: 1}),
        compare_case(image, candidate, "unchanged-selection-no-event", 0, 0, {5: 1, 6: 1}),
    ]
    exhaustive = []
    for cursor in range(4):
        for cached in range(4):
            for bits in range(16):
                responses = {trigger_id: int(bool(bits & (1 << index)))
                             for index, trigger_id in enumerate(TRIGGER_IDS)}
                exhaustive.append(compare_case(
                    image, candidate, f"domain-c{cursor}-cache{cached}-mask{bits:02x}",
                    cursor, cached, responses))
    source = ROOT / "experiments/semantic_equivalence/title_navigation_family_candidate.cpp"
    report = {
        "passed": (all(g["passed"] for g in gate_tests) and all(c["passed"] for c in cases)
                   and all(c["passed"] for c in exhaustive)),
        "scope": "H1 trigger-result-to-cursor family plus separately tested readiness gates; isolated only",
        "reference": reference,
        "candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "candidate_bytes": len(candidate),
        "candidate_external_calls": [],
        "gate_tests": gate_tests,
        "cases": cases,
        "exhaustive_valid_domain": {"case_count": len(exhaustive),
                                    "passed": all(c["passed"] for c in exhaustive),
                                    "cursors": list(range(4)),
                                    "cached_cursors": list(range(4)),
                                    "trigger_masks": list(range(16))},
        "stub_contracts": {
            "trigger": "UiInput_Trigger at 0x002B902C returns explicit per-logical-ID values",
            "event": "UiEvent_Request at 0x002B91C4 records ID and work+8/work+0xC at call time, then returns; real event queue/state internals are not claimed",
        },
        "limitations": [
            "The candidate models logical trigger results, not physical keyboard/gamepad bindings or held-input filtering.",
            "The full callback, animation VFP update, touch path, help-text refresh and confirmation dispatch are outside scope.",
            "Event helper 0x002B91C4 is an explicit call-boundary stub; its internal event-system side effects are not compared.",
            "No division/modulo operator is used, so the candidate has no dependency on helper 0x002C6C10.",
            "Bounded Unicorn differential evidence is not whole-game or emulator verification.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Title navigation family experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-navigation-family")
    args = parser.parse_args()
    try:
        report = run(args.code, args.output)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
