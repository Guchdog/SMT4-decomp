#!/usr/bin/env python3
"""Differentially test the isolated title touch-selection family."""
from __future__ import annotations

import hashlib
import itertools
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

TOUCH_START = 0x001E9E4C
TOUCH_STOP = 0x001E9EB8
TOUCH_QUERY = 0x0029D8FC
GLOBAL_PTR = DATA + 0x40
WORK = DATA + 0x100
STATE_ARRAY = DATA + 0x500
REGION_HANDLES = (0x0174, 0x0176, 0x0178, 0x017A)
EXPECTED_SHA256 = "1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558"
DEFAULT_STATES = (-1, 0, 1, 2, 3, 6)


def verify_image(image: bytes) -> dict:
    digest = hashlib.sha256(image).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError("code.bin SHA-256 does not match the pinned game revision")
    import capstone
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    code = image[TOUCH_START - TEXT:TOUCH_STOP - TEXT]
    instructions = list(decoder.disasm(code, TOUCH_START))
    if not instructions or sum(insn.size for insn in instructions) != len(code):
        raise ValueError("incomplete ARM decode in pinned touch window")
    return {"sha256": digest, "start": hex(TOUCH_START), "stop": hex(TOUCH_STOP),
            "instruction_count": len(instructions)}


class TouchMachine:
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
        self.responses: dict[int, int] = {}
        self.calls: list[int] = []
        self.stopped = False
        self.uc.hook_add(unicorn.UC_HOOK_CODE, self._hook)

    def _hook(self, uc, address, _size, _user):
        if address == TOUCH_STOP or address == RETURN:
            self.stopped = True
            uc.emu_stop()
        elif address == TOUCH_QUERY:
            handle = self.signed16(uc.reg_read(self.arm.UC_ARM_REG_R0))
            if handle not in self.responses:
                raise ValueError(f"no explicit touch-state stub response for handle {handle:#x}")
            self.calls.append(handle)
            uc.reg_write(self.arm.UC_ARM_REG_R0, self.responses[handle] & 0xFFFFFFFF)
            uc.reg_write(self.arm.UC_ARM_REG_PC, uc.reg_read(self.arm.UC_ARM_REG_LR))

    @staticmethod
    def signed16(value: int) -> int:
        value &= 0xFFFF
        return value - 0x10000 if value & 0x8000 else value

    def initialize(self, states: tuple[int, ...], cursor: int, confirm: int):
        if len(states) != 4:
            raise ValueError("exactly four stable touch states are required")
        self.uc.mem_write(DATA, bytes(DATA_SIZE))
        self.uc.mem_write(STACK, bytes(STACK_SIZE))
        self.uc.mem_write(GLOBAL_PTR, struct.pack("<I", WORK))
        self.uc.mem_write(WORK + 0x74, struct.pack("<4H", *REGION_HANDLES))
        self.uc.mem_write(STATE_ARRAY, struct.pack("<4i", *states))
        self.uc.mem_write(WORK + 8, struct.pack("<I", cursor & 0xFFFFFFFF))
        self.uc.mem_write(WORK + 0x63, bytes((confirm & 0xFF,)))
        self.responses = {self.signed16(handle): state
                          for handle, state in zip(REGION_HANDLES, states)}
        self.calls.clear()
        self.stopped = False
        arm = self.arm
        self.uc.reg_write(arm.UC_ARM_REG_CPSR, 0x10)
        self.uc.reg_write(arm.UC_ARM_REG_R8, GLOBAL_PTR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, STACK + 0x1000)
        self.uc.reg_write(arm.UC_ARM_REG_LR, RETURN)

    def read_word(self, address: int) -> int:
        return struct.unpack("<I", self.uc.mem_read(address, 4))[0]

    def run_original(self, states: tuple[int, ...], cursor: int, confirm: int) -> dict:
        self.initialize(states, cursor, confirm)
        try:
            self.uc.emu_start(TOUCH_START, 0, count=256)
        except self.unicorn.UcError as error:
            return {"fault": str(error), "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC)}
        return {"fault": None, "stopped": self.stopped,
                "pc": self.uc.reg_read(self.arm.UC_ARM_REG_PC),
                "cursor": self.read_word(WORK + 8),
                "confirm": self.uc.mem_read(WORK + 0x63, 1)[0],
                "calls": self.calls.copy()}

    def run_candidate(self, states: tuple[int, ...], cursor: int, confirm: int) -> dict:
        if self.candidate is None:
            raise ValueError("candidate blob is not loaded")
        self.initialize(states, cursor, confirm)
        arm = self.arm
        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK)
        self.uc.reg_write(arm.UC_ARM_REG_R1, STATE_ARRAY)
        try:
            self.uc.emu_start(INJECT, 0, count=256)
        except self.unicorn.UcError as error:
            return {"fault": str(error), "pc": self.uc.reg_read(arm.UC_ARM_REG_PC)}
        return {"fault": None, "stopped": self.stopped,
                "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
                "cursor": self.read_word(WORK + 8),
                "confirm": self.uc.mem_read(WORK + 0x63, 1)[0],
                "return": self.uc.reg_read(arm.UC_ARM_REG_R0)}


def build_candidate(output: Path) -> bytes:
    output.mkdir(parents=True, exist_ok=True)
    source = ROOT / "experiments/semantic_equivalence/title_touch_family_candidate.cpp"
    obj = output / "title_touch_family_candidate.o"
    build = compile_tu_armv6k(source, obj, ROOT)
    if build.returncode:
        raise RuntimeError(build.stderr)
    functions = extract_elf_functions_detailed(obj)
    if "title_touch_reduce" not in functions:
        raise ValueError("missing title_touch_reduce candidate symbol")
    code, relocations = functions["title_touch_reduce"]
    if relocations:
        raise ValueError(f"unsupported candidate relocations: {relocations}")
    validate_local_blob(code)
    import capstone
    decoder = capstone.Cs(capstone.CS_ARCH_ARM, capstone.CS_MODE_ARM)
    instructions = list(decoder.disasm(code, INJECT))
    if sum(insn.size for insn in instructions) != len(code):
        raise ValueError("candidate contains undecoded ARM bytes")
    if any(insn.mnemonic in ("bl", "blx") for insn in instructions):
        raise ValueError("candidate unexpectedly calls an external helper")
    return code


def compare_case(image: bytes, candidate: bytes, states: tuple[int, ...],
                 cursor: int, confirm: int, label: str,
                 original_machine: TouchMachine | None = None,
                 candidate_machine: TouchMachine | None = None) -> dict:
    original_machine = original_machine or TouchMachine(image)
    candidate_machine = candidate_machine or TouchMachine(image, candidate)
    original = original_machine.run_original(states, cursor, confirm)
    rebuilt = candidate_machine.run_candidate(states, cursor, confirm)
    passed = (original.get("fault") is None and original.get("stopped")
              and original.get("pc") == TOUCH_STOP and rebuilt.get("fault") is None
              and rebuilt.get("stopped") and rebuilt.get("pc") == RETURN
              and rebuilt["cursor"] == original["cursor"]
              and rebuilt["confirm"] == original["confirm"]
              and rebuilt["return"] == original["cursor"])
    return {"case": label, "states": list(states), "initial_cursor": cursor,
            "initial_confirm": confirm, "passed": passed,
            "original": original, "candidate": rebuilt}


def run(code_path: Path, output: Path, exhaustive: bool = True) -> dict:
    image = code_path.read_bytes()
    reference = verify_image(image)
    candidate = build_candidate(output)
    original_machine = TouchMachine(image)
    candidate_machine = TouchMachine(image, candidate)
    state_vectors = list(itertools.product(DEFAULT_STATES, repeat=4)) if exhaustive else [
        (0, 0, 0, 0), (1, 0, 0, 0), (0, 2, 1, 0), (6, 6, 0, 6),
        (2, 0, 6, 6), (0, 6, 0, 0), (3, 3, 3, 3),
    ]
    cases = []
    for index, states in enumerate(state_vectors):
        for cursor, confirm in ((0xA5A5A5A5, 0), (0xA5A5A5A5, 0x7B)):
            cases.append(compare_case(image, candidate, states, cursor, confirm,
                                      f"vector-{index}-cursor-{cursor:08x}-confirm-{confirm:02x}",
                                      original_machine, candidate_machine))
    groups = []
    for label, states, initial, expected_cursor, expected_confirm in (
        ("first-selection-match-wins", (1, 2, 0, 0), 0xA5A5A5A5, 0, 0),
        ("state-2-selection-after-nonmatch", (3, 2, 0, 0), 0xA5A5A5A5, 1, 0),
        ("last-confirm-match-wins", (6, 0, 6, 6), 0xA5A5A5A5, 3, 1),
        ("confirm-overrides-earlier-selection", (2, 0, 6, 0), 0xA5A5A5A5, 2, 1),
        ("no-match-preserves-cursor-and-confirm", (0, 3, -1, 5), 0xA5A5A5A5, 0xA5A5A5A5, 0x7B),
        ("selection-does-not-clear-existing-confirm", (1, 0, 0, 0), 0xA5A5A5A5, 0, 0x7B),
        ("confirm-is-sticky-if-no-state-6", (0, 0, 0, 0), 0xA5A5A5A5, 0xA5A5A5A5, 1),
    ):
        result = compare_case(image, candidate, states, initial, expected_confirm,
                              f"priority-{label}", original_machine, candidate_machine)
        result["expected_cursor"] = expected_cursor
        result["expected_confirm"] = expected_confirm
        result["semantic_assertion_passed"] = (
            result["passed"] and result["original"]["cursor"] == expected_cursor
            and result["original"]["confirm"] == expected_confirm)
        groups.append(result)

    source = ROOT / "experiments/semantic_equivalence/title_touch_family_candidate.cpp"
    report = {
        "passed": all(case["passed"] for case in cases)
                   and all(group["semantic_assertion_passed"] for group in groups),
        "scope": "only ARM touch scans 0x001E9E4C..0x001E9EB8 with stable, explicit helper responses",
        "reference": reference,
        "candidate_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "candidate_bytes": len(candidate),
        "exhaustive_state_domain": list(DEFAULT_STATES),
        "state_vector_count": len(state_vectors),
        "comparison_count": len(cases),
        "passed_comparisons": sum(case["passed"] for case in cases),
        "priority_cases": groups,
        "stub_contract": "UiTouch_GetRegionTouchState at 0x0029D8FC returns the explicit, stable state keyed by the signed halfword handle; no physical touch simulation is claimed",
        "limitations": [
            "Each region's helper result is held constant across the two scans; time-varying helper responses are not modeled by this reducer.",
            "The experiment does not establish physical touch coordinates, hitboxes, or Azahar behavior.",
            "Only cursor +8 and confirmation byte +0x63 at the end of the touch window are compared; subsequent callback behavior is out of scope.",
        ],
    }
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Title touch family experiment {'PASS' if report['passed'] else 'FAIL'}; "
          f"{report['passed_comparisons']}/{report['comparison_count']} comparisons; "
          f"report: {output / 'report.json'}")
    return report
