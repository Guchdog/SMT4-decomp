#!/usr/bin/env python3
"""Compare a continuous title callback slice with isolated reducer composition.

The reference path runs original ARM navigation, animation/VFP, and touch code
in one Unicorn machine. The hybrid path substitutes only the existing C++
navigation and stable-touch reducers; it deliberately retains the original
ARM VFP bridge, sharing its work memory and FP registers with both reducers.
"""
from __future__ import annotations

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
from tools.semantic_experiment import DATA, DATA_SIZE, INJECT, RETURN, STACK, STACK_SIZE, TEXT, validate_local_blob

NAV_START = 0x001E9D48
ANIM_START = 0x001E9DE0
TOUCH_START = 0x001E9E4C
TOUCH_STOP = 0x001E9EB8
TRIGGER = 0x002B902C
EVENT_REQUEST = 0x002B91C4
TOUCH_QUERY = 0x0029D8FC
GLOBAL_PTR = DATA + 0x40
WORK = DATA + 0x100
EVENT = DATA + 0x300
REGION_HANDLES = (0x174, 0x176, 0x178, 0x17A)
NAV_INJECT = INJECT
TOUCH_INJECT = INJECT + 0x800
EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
RESPONSE_IDS = (5, 0xE, 6, 0xF)


def verify_image(image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    import capstone
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    windows = ((NAV_START, ANIM_START), (ANIM_START, TOUCH_START),
               (TOUCH_START, TOUCH_STOP))
    decoded = []
    for start, stop in windows:
        data = image[start - TEXT:stop - TEXT]
        instructions = list(decoder.disasm(data, start))
        if not instructions or sum(i.size for i in instructions) != len(data):
            raise ValueError(f"incomplete ARM decode in {start:#x}..{stop:#x}")
        decoded.append({"start": hex(start), "stop": hex(stop),
                        "instruction_count": len(instructions)})
    return {"sha256": digest, "windows": decoded}


def build_reducer(source_name: str, symbol: str, output: Path, address: int) -> bytes:
    source = ROOT / "experiments/semantic_equivalence" / source_name
    obj = output / f"{symbol}.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(obj)
    if symbol not in functions:
        raise ValueError(f"missing reducer symbol {symbol}")
    code, relocations = functions[symbol]
    if relocations:
        raise ValueError(f"unsupported relocations in {symbol}: {relocations}")
    validate_local_blob(code)
    import capstone
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    instructions = list(decoder.disasm(code, address))
    if sum(i.size for i in instructions) != len(code):
        raise ValueError(f"undecoded ARM bytes in {symbol}")
    if any(i.mnemonic in ("bl", "blx") for i in instructions):
        raise ValueError(f"unexpected external call in {symbol}")
    return code


class ContinuousMachine:
    def __init__(self, image: bytes, nav_code: bytes | None = None,
                 touch_code: bytes | None = None):
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
        self.nav_code, self.touch_code = nav_code, touch_code
        if nav_code is not None:
            self.uc.mem_write(NAV_INJECT, nav_code)
        if touch_code is not None:
            self.uc.mem_write(TOUCH_INJECT, touch_code)
        self.trigger_scripts: dict[int, list[int]] = {}
        self.trigger_calls: list[dict] = []
        self.event_calls: list[dict] = []
        self.touch_scripts: dict[int, list[int]] = {}
        self.touch_offsets: dict[int, int] = {}
        self.touch_calls: list[dict] = []
        self.stop_at: int | None = None
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def read_u32(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def write_u32(self, address: int, value: int):
        self.uc.mem_write(address, struct.pack("<I", value & 0xFFFFFFFF))

    @staticmethod
    def signed16(value: int) -> int:
        value &= 0xFFFF
        return value - 0x10000 if value & 0x8000 else value

    def _hook(self, uc, address, _size, _user):
        arm = self.arm
        if address == self.stop_at or address == RETURN:
            self.stopped = True
            uc.emu_stop()
            return
        if address == TRIGGER:
            trigger_id = uc.reg_read(arm.UC_ARM_REG_R0)
            offset = sum(1 for call in self.trigger_calls if call["id"] == trigger_id)
            values = self.trigger_scripts.get(trigger_id, [])
            if offset >= len(values):
                raise ValueError(f"missing call-counted trigger response for ID {trigger_id:#x}, call {offset + 1}")
            value = values[offset]
            self.trigger_calls.append({"id": trigger_id, "ordinal_for_id": offset + 1,
                                       "response": value})
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
        elif address == EVENT_REQUEST:
            args = [uc.reg_read(register) for register in
                    (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1,
                     arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3)]
            self.event_calls.append({"args_r0_r3": args,
                                     "id": args[0],
                                     "cursor": self.read_u32(WORK + 8),
                                     "cached_cursor": self.read_u32(WORK + 12)})
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))
        elif address == TOUCH_QUERY:
            handle = self.signed16(uc.reg_read(arm.UC_ARM_REG_R0))
            ordinal = self.touch_offsets.get(handle, 0)
            values = self.touch_scripts.get(handle, [])
            if ordinal >= len(values):
                raise ValueError(f"missing call-counted touch response for handle {handle:#x}, call {ordinal + 1}")
            value = values[ordinal]
            self.touch_offsets[handle] = ordinal + 1
            self.touch_calls.append({"handle": handle, "ordinal_for_handle": ordinal + 1,
                                     "global_call": len(self.touch_calls) + 1,
                                     "response": value})
            uc.reg_write(arm.UC_ARM_REG_R0, value & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_PC, uc.reg_read(arm.UC_ARM_REG_LR))

    def initialize(self, cursor: int, cached: int, confirm: int,
                   anim_counter: int, anim_value_bits: int, s17_bits: int,
                   trigger_scripts: dict[int, list[int]],
                   touch_scripts: dict[int, list[int]]):
        # Initialize only callback-reachable fields; separate objects are not
        # fabricated or zero-page-backed as substitutes for real UI objects.
        # Sentinel backing makes accidental reads of unmodeled fields visible;
        # only the callback fields listed below are set to scenario values.
        self.uc.mem_write(DATA, bytes([0xCD]) * DATA_SIZE)
        self.uc.mem_write(STACK, bytes([0xCD]) * STACK_SIZE)
        self.write_u32(GLOBAL_PTR, WORK)
        self.write_u32(WORK + 8, cursor)
        self.write_u32(WORK + 12, cached)
        self.uc.mem_write(WORK + 0x63, bytes((confirm & 0xFF,)))
        self.write_u32(WORK + 0x64, anim_counter)
        self.write_u32(WORK + 0x68, anim_value_bits)
        self.uc.mem_write(WORK + 0x74, struct.pack("<4H", *REGION_HANDLES))
        self.trigger_scripts = {key: list(value) for key, value in trigger_scripts.items()}
        self.trigger_calls.clear()
        self.event_calls.clear()
        self.touch_scripts = {key: list(value) for key, value in touch_scripts.items()}
        self.touch_offsets.clear()
        self.touch_calls.clear()
        self.stopped = False
        arm = self.arm
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        for register in (arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2,
                         arm.UC_ARM_REG_R3, arm.UC_ARM_REG_R5, arm.UC_ARM_REG_R6,
                         arm.UC_ARM_REG_R7, arm.UC_ARM_REG_R9, arm.UC_ARM_REG_R10,
                         arm.UC_ARM_REG_R11, arm.UC_ARM_REG_R12):
            self.uc.reg_write(register, 0xA5A50000 | (register & 0xFFFF))
        self.uc.reg_write(arm.UC_ARM_REG_R4, WORK)
        self.uc.reg_write(arm.UC_ARM_REG_R8, GLOBAL_PTR)
        # The callback arrives after readiness gates and starts by querying ID 5.
        self.uc.reg_write(arm.UC_ARM_REG_R0, 5)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK + 0x1000)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)
        self._set_fp_seed(s17_bits)

    def _set_fp_seed(self, s17_bits: int):
        # Seed all single-precision lanes explicitly so prior emulator state
        # cannot silently become part of the reference contract.
        for index in range(32):
            register = getattr(self.arm, f"UC_ARM_REG_S{index}")
            bits = s17_bits if index == 17 else (0x3F000000 + index * 0x100)
            self.uc.reg_write(register, bits & 0xFFFFFFFF)
        self.uc.reg_write(self.arm.UC_ARM_REG_FPSCR, 0)
        self.uc.reg_write(self.arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(self.arm.UC_ARM_REG_FPEXC, 0x40000000)

    def _execute(self, start: int, stop: int, count: int) -> dict:
        self.stop_at = stop
        self.stopped = False
        try:
            self.uc.emu_start(start, 0, count=count)
        except (self.unicorn.UcError, ValueError) as error:
            return {"fault": str(error), "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                    "stopped": False}
        return {"fault": None, "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                "stopped": self.stopped}

    def _run_original(self, cursor: int, cached: int, confirm: int,
                      anim_counter: int, anim_value_bits: int, s17_bits: int,
                      trigger_scripts: dict[int, list[int]],
                      touch_scripts: dict[int, list[int]]) -> dict:
        self.initialize(cursor, cached, confirm, anim_counter, anim_value_bits,
                        s17_bits, trigger_scripts, touch_scripts)
        stages = []
        stages.append(self._execute(NAV_START, ANIM_START, 256))
        if stages[-1]["fault"] is None and stages[-1]["pc"] == ANIM_START:
            stages.append(self._execute(ANIM_START, TOUCH_START, 128))
        if stages and stages[-1]["fault"] is None and stages[-1]["pc"] == TOUCH_START:
            stages.append(self._execute(TOUCH_START, TOUCH_STOP, 256))
        return self._observation(stages)

    def _run_hybrid(self, cursor: int, cached: int, confirm: int,
                    anim_counter: int, anim_value_bits: int, s17_bits: int,
                    trigger_scripts: dict[int, list[int]],
                    touch_scripts: dict[int, list[int]]) -> dict:
        if self.nav_code is None or self.touch_code is None:
            raise ValueError("hybrid reducers are not loaded")
        if any(len(values) != 1 for values in trigger_scripts.values()):
            raise ValueError("current navigation reducer only accepts one response per logical ID")
        self.initialize(cursor, cached, confirm, anim_counter, anim_value_bits,
                        s17_bits, trigger_scripts, touch_scripts)
        trigger_bits = sum(1 << i for i, trigger_id in enumerate(RESPONSE_IDS)
                           if trigger_scripts.get(trigger_id, [0])[0])
        self.uc.mem_write(EVENT, bytes(16))
        arm = self.arm
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 3)
        self.uc.reg_write(arm.UC_ARM_REG_R2, trigger_bits)
        self.uc.reg_write(arm.UC_ARM_REG_R3, EVENT)
        stages = [self._execute(NAV_INJECT, RETURN, 256)]
        nav_event = struct.unpack("<4I", self.uc.mem_read(EVENT, 16))
        if stages[-1]["fault"] is None and stages[-1]["pc"] == RETURN:
            self.uc.reg_write(arm.UC_ARM_REG_R4, WORK)
            stages.append(self._execute(ANIM_START, TOUCH_START, 128))
        stable_touch = all(len(values) == 3 and len(set(values)) == 1
                           for values in touch_scripts.values())
        if not stable_touch:
            return self._observation(stages, nav_event,
                                     "touch reducer contract requires three equal explicit replies per handle")
        stable_states = tuple(touch_scripts[handle][0] for handle in REGION_HANDLES)
        state_array = DATA + 0x500
        self.uc.mem_write(state_array, struct.pack("<4i", *stable_states))
        if stages[-1]["fault"] is None and stages[-1]["pc"] == TOUCH_START:
            self.uc.reg_write(arm.UC_ARM_REG_R0, WORK)
            self.uc.reg_write(arm.UC_ARM_REG_R1, state_array)
            stages.append(self._execute(TOUCH_INJECT, RETURN, 256))
        return self._observation(stages, nav_event)

    def _observation(self, stages: list[dict], nav_event=None, limitation=None) -> dict:
        arm = self.arm
        fp = {f"s{i}": self.uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}"))
              for i in (0, 1, 16, 17)}
        return {"stages": stages, "cursor": self.read_u32(WORK + 8),
                "cached_cursor": self.read_u32(WORK + 12),
                "confirm": self.uc.mem_read(WORK + 0x63, 1)[0],
                "anim_counter": self.read_u32(WORK + 0x64),
                "anim_value_bits": self.read_u32(WORK + 0x68),
                "work_callback_bytes": bytes(self.uc.mem_read(WORK, 0x80)).hex(),
                "fp": fp, "fpscr": self.uc.reg_read(arm.UC_ARM_REG_FPSCR),
                "fpexc": self.uc.reg_read(arm.UC_ARM_REG_FPEXC),
                "trigger_calls": self.trigger_calls.copy(),
                "event_calls": self.event_calls.copy(),
                "candidate_event": list(nav_event) if nav_event is not None else None,
                "touch_calls": self.touch_calls.copy(),
                "touch_call_counts": {hex(key): value for key, value in self.touch_offsets.items()},
                "limitation": limitation}


def compare_case(image: bytes, nav_code: bytes, touch_code: bytes,
                 label: str, cursor: int, cached: int, confirm: int,
                 anim_counter: int, anim_value_bits: int, s17_bits: int,
                 trigger_scripts: dict[int, list[int]],
                 touch_scripts: dict[int, list[int]], compare_hybrid: bool = True) -> dict:
    reference = ContinuousMachine(image)
    original = reference._run_original(cursor, cached, confirm, anim_counter,
                                       anim_value_bits, s17_bits,
                                       trigger_scripts, touch_scripts)
    hybrid = None
    passed = all(s["fault"] is None and s["stopped"] for s in original["stages"])
    if compare_hybrid:
        candidate = ContinuousMachine(image, nav_code, touch_code)
        hybrid = candidate._run_hybrid(cursor, cached, confirm, anim_counter,
                                       anim_value_bits, s17_bits,
                                       trigger_scripts, touch_scripts)
        expected_events = original["event_calls"]
        candidate_event = hybrid["candidate_event"] or [0, 0, 0, 0]
        event_match = ((not expected_events and candidate_event[0] == 0)
                       or (len(expected_events) == 1 and candidate_event[0] == 1
                           and candidate_event[1] == expected_events[0]["id"]
                           and candidate_event[2] == expected_events[0]["cursor"]
                           and candidate_event[3] == expected_events[0]["cached_cursor"]))
        passed = passed and all(s["fault"] is None and s["stopped"] for s in hybrid["stages"])
        passed = passed and hybrid["cursor"] == original["cursor"]
        passed = passed and hybrid["cached_cursor"] == original["cached_cursor"]
        passed = passed and hybrid["confirm"] == original["confirm"]
        passed = passed and hybrid["anim_counter"] == original["anim_counter"]
        passed = passed and hybrid["anim_value_bits"] == original["anim_value_bits"]
        passed = passed and hybrid["work_callback_bytes"] == original["work_callback_bytes"]
        passed = passed and hybrid["fp"] == original["fp"] and hybrid["fpscr"] == original["fpscr"]
        passed = passed and hybrid["fpexc"] == original["fpexc"]
        passed = passed and event_match
    return {"case": label, "passed": passed,
            "inputs": {"cursor": cursor, "cached_cursor": cached, "confirm": confirm,
                       "anim_counter": anim_counter, "anim_value_bits": anim_value_bits,
                       "s17_bits": s17_bits, "trigger_scripts": trigger_scripts,
                       "touch_scripts": touch_scripts},
            "original_continuous_arm": original, "hybrid_reducers_with_arm_vfp": hybrid}


def run(code_path: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    image = code_path.read_bytes()
    reference = verify_image(image)
    nav_code = build_reducer("title_navigation_family_candidate.cpp",
                             "title_navigation_reduce", output, NAV_INJECT)
    touch_code = build_reducer("title_touch_family_candidate.cpp",
                               "title_touch_reduce", output, TOUCH_INJECT)
    # Stable candidate-composition cases make every helper reply explicit and
    # avoid state 1/2, whose ARM path escapes to 0x001EA014 before TOUCH_STOP.
    cases = [
        compare_case(image, nav_code, touch_code, "stable-neutral-and-state6", 1, 1,
                     0, 0x3F000000, 0x3F000000, 0x3F800000,
                     {5: [0], 0xE: [0], 6: [0], 0xF: [0]},
                     {handle: [state, state, state] for handle, state in
                      zip(REGION_HANDLES, (0, 6, 3, -1))}),
        compare_case(image, nav_code, touch_code, "navigation-event-and-vfp-clamp", 3, 2,
                     0x7B, 0x3F800001, 0x40000000, 0x3F400000,
                     {5: [0], 0xE: [0], 6: [1], 0xF: [0]},
                     {handle: [0, 0, 0] for handle in REGION_HANDLES}),
        compare_case(image, nav_code, touch_code, "wrap-and-touch-confirm", 0, 3,
                     0, 0x3F000000, 0x3F000000, 0x3F800000,
                     {5: [1], 0xE: [0], 6: [0], 0xF: [1]},
                     {handle: [6, 6, 6] for handle in REGION_HANDLES}),
        # Time-varying helper evidence is checked against continuous ARM only;
        # the current reducer has a stable-per-region input contract.
        compare_case(image, nav_code, touch_code, "time-varying-touch-call-sequence-arm-only",
                     2, 2, 0, 0x3F000000, 0x3F000000, 0x3F800000,
                     {5: [0], 0xE: [0], 6: [0], 0xF: [0]},
                     {0x174: [3, 0, 6], 0x176: [0, 3, 0],
                      0x178: [3, 0, 3], 0x17A: [0, 3, 0]},
                     compare_hybrid=False),
    ]
    report = {
        "passed": all(case["passed"] for case in cases),
        "scope": "continuous original ARM navigation -> original VFP animation -> touch scan; hybrid existing navigation/touch reducers with original VFP bridge",
        "reference": reference,
        "candidate_sha256": {
            "navigation": hashlib.sha256((ROOT / "experiments/semantic_equivalence/title_navigation_family_candidate.cpp").read_bytes()).hexdigest(),
            "touch": hashlib.sha256((ROOT / "experiments/semantic_equivalence/title_touch_family_candidate.cpp").read_bytes()).hexdigest(),
        },
        "cases": cases,
        "stub_contracts": {
            "trigger": "UiInput_Trigger at 0x002B902C: explicit per-ID response queues; each invocation is recorded with its ordinal and value",
            "event": "UiEvent_Request at 0x002B91C4: records ID and work+8/work+0xC at call time, then returns; real queue effects are not modeled",
            "touch": "UiTouch_GetRegionTouchState at 0x0029D8FC: explicit per-handle response queues; every query records global order, per-handle ordinal, handle and response",
        },
        "limits": [
            "The VFP block 0x001E9DE0..0x001E9E4C is original ARM in both paths; no independent C++ reconstruction is claimed.",
            "The touch reducer accepts one stable state per region. Its composed cases explicitly supply three identical replies per handle; changing call sequences are exercised only on original ARM.",
            "Touch states 1/2 branch out to 0x001EA014 before 0x001E9EB8; this harness restricts composed-path touch states to avoid claiming that later transition path.",
            "Trigger candidate input is a projection of the explicit per-ID script into the reducer's bitmask contract; only the original ARM path invokes and call-counts UiInput_Trigger.",
            "Only callback-reachable work fields are initialized. Separate UI object graphs, readiness/renderer helpers, later transition branches, physical touch timing and Azahar behavior are outside scope.",
            "No function is counted as reconstructed by this composition harness.",
        ],
    }
    report_path = output / "report.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Title callback continuity experiment {'PASS' if report['passed'] else 'FAIL'}; report: {report_path}")
    return report


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code", type=Path, default=ROOT / "extracted/exefs/code.bin")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "build/semantic-equivalence/title-callback-continuity")
    args = parser.parse_args()
    try:
        report = run(args.code, args.output)
    except (RuntimeError, ValueError, OSError) as error:
        parser.exit(2, f"Experiment error: {error}\n")
    raise SystemExit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
