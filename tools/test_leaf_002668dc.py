#!/usr/bin/env python3
"""Differential test for script_vm_func_002668dc (0x002668dc, 892 B).

The candidate in ``src/engine/leaf_batch45_b.cpp`` is compiled with the project
ARMv6K pipeline, extracted from the object file, and run next to the pinned
original (``extracted/exefs/code.bin``) in separate Unicorn machines with
identical fixtures.

Compared outputs:
  * continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the ordered call log with every argument of every direct call (the frame
    scratch copy destination is normalised to ``<stack>``);
  * the full LMAP work page, the global page (pointer slot 0x00447060, the
    layout table, the 0x00476630 guard, the 0x0049F91C mode block and the
    0x004EFD48 matrix) and the actor-list fixture page;
  * the ordered list of writes outside the private stack.

``script_vm_func_002668dc`` has no return contract (its only r0 value is the
dead loop bound and all pinned callers overwrite r0 immediately), so r0 is
reported but not compared.

Coverage: null host pointer; mode 101 with every sub-state 1..9 and the
out-of-range sub-states 0, 10 and 0xFFFFFFFF; counts -1, 0, 1 and 3; enabled
byte 0 and 1; guard word 0 (identity init), 1, 2 (bit 0 clear, non-zero) and
0xFFFFFFFF; placement state 0x63 and 0x00; every placement row 100..103; and
signed-byte digit extremes for the three listing characters.  The title
sub-state and the placement-scale selector are the same word at 0x0049F920, so
the case builder drives both through ``state_word``.

Negative controls mutate the title-mode constant, the layout stride and the
0x63 scale value; each mutant must be detected.

Limits: the helpers are deterministic stubs at their original addresses, so the
test proves the caller contract against those stubs, not the helpers' own
bodies.  A zero relative link word makes the original read address 5 and is not
exercised.  ``[host + 0x40]`` outside 100..103 reads uninitialised stack in the
original and is not exercised.  No runtime/emulator or whole-game behavior is
claimed.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch45_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_002668dc"

FUNC_ADDR = 0x002668DC
FUNC_SIZE = 892

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every direct-call target
GLOB_ADDR = 0x00400000
GLOB_SIZE = 0x00100000  # 0x00447060 .. 0x004EFD48
WORK_ADDR = 0x00600000
WORK_SIZE = 0x00020000
LIST_ADDR = 0x00700000
LIST_SIZE = 0x00040000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Fixture offsets inside the global page.
G_447060 = 0x00447060 - GLOB_ADDR
G_447088 = 0x00447088 - GLOB_ADDR
G_476630 = 0x00476630 - GLOB_ADDR
G_49F91C = 0x0049F91C - GLOB_ADDR
G_49F920 = 0x0049F920 - GLOB_ADDR
G_4EFD48 = 0x004EFD48 - GLOB_ADDR

# Fixture offsets inside the actor-list page.
L_STRUCT = 0
L_ITEMS = 0x00010000
L_SUBS = 0x00020000

RECORD_BASE = 0xAAC
RECORD_STRIDE = 0x88
RECORD_ENABLED = 0x84
SUBLINK_OFFSET = 0x0C
SUBLINK_VALUE = 0x10
MAX_RECORDS = 4

# Original direct-call targets.  Both machines get a stub at the same address,
# so the original branch displacements stay valid and the candidate's resolved
# relocations point at the same code.
STUB_20FE3C = 0x0020FE3C
STUB_265DA4 = 0x00265DA4
STUB_2863F4 = 0x002863F4
STUB_2C00D4 = 0x002C00D4
STUB_3170B8 = 0x003170B8
STUB_328440 = 0x00328440

THUMB_STUBS = {STUB_2C00D4}

STUB_NAMES = {
    STUB_20FE3C: "script_vm_func_0020fe3c",
    STUB_265DA4: "script_vm_func_00265da4",
    STUB_2863F4: "script_vm_func_002863f4",
    STUB_2C00D4: "engine_func_002c00d4",
    STUB_3170B8: "engine_func_003170b8",
    STUB_328440: "script_vm_func_00328440",
}

CALLEE_SAVED = {
    "r4": arm.UC_ARM_REG_R4,
    "r5": arm.UC_ARM_REG_R5,
    "r6": arm.UC_ARM_REG_R6,
    "r7": arm.UC_ARM_REG_R7,
    "r8": arm.UC_ARM_REG_R8,
    "r9": arm.UC_ARM_REG_R9,
    "r10": arm.UC_ARM_REG_R10,
    "r11": arm.UC_ARM_REG_R11,
}
CALLEE_SAVED_START = {
    "r4": 0x44444444,
    "r5": 0x55555555,
    "r6": 0x66666666,
    "r7": 0x77777777,
    "r8": 0x88888888,
    "r9": 0x99999999,
    "r10": 0xAAAAAAAA,
    "r11": 0xBBBBBBBB,
}

VFP_SAVED = {
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
    "d10": arm.UC_ARM_REG_D10,
    "d11": arm.UC_ARM_REG_D11,
    "d12": arm.UC_ARM_REG_D12,
    "d13": arm.UC_ARM_REG_D13,
    "d14": arm.UC_ARM_REG_D14,
    "d15": arm.UC_ARM_REG_D15,
}
VFP_SAVED_START = {
    "d8": 0x8888888888888888,
    "d9": 0x9999999999999999,
    "d10": 0xAAAAAAAAAAAAAAAA,
    "d11": 0xBBBBBBBBBBBBBBBB,
    "d12": 0xCCCCCCCCCCCCCCCC,
    "d13": 0xDDDDDDDDDDDDDDDD,
    "d14": 0xEEEEEEEEEEEEEEEE,
    "d15": 0xFFFFFFFFFFFFFFFF,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002668dc" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_002668dc not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        target = None
        for address in STUB_NAMES:
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(
                f"unresolved relocation type {rel.relocation_type}: "
                f"{rel.symbol_name}"
            )
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        pc = FUNC_ADDR + rel.offset + 8
        offset = target - pc
        if target in THUMB_STUBS:
            if offset & 3:
                raise RuntimeError(f"unaligned Thumb call target 0x{target:08x}")
            instruction = (
                0xFA000000
                | ((offset >> 2) & 0x00FFFFFF)
                | ((offset & 2) << 23)
            )
            struct.pack_into("<I", code, rel.offset, instruction)
        else:
            if offset & 3:
                raise RuntimeError(f"unaligned call target 0x{target:08x}")
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset,
                cond | ((offset >> 2) & 0x00FFFFFF),
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_b.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    result = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


# --------------------------------------------------------------------- fixtures
def build_glob(case: dict) -> bytes:
    page = bytearray([0x33]) * GLOB_SIZE
    struct.pack_into("<I", page, G_447060,
                     0 if case.get("work_null") else WORK_ADDR)
    struct.pack_into("<I", page, G_476630, case.get("guard", 0) & 0xFFFFFFFF)
    struct.pack_into("<I", page, G_49F91C, case.get("mode", 0x65) & 0xFFFFFFFF)
    struct.pack_into("<I", page, G_49F920, case.get("state_word", 1) & 0xFFFFFFFF)
    matrix = case.get("matrix")
    if matrix is None:
        matrix = [0.0] * 9
    for index, value in enumerate(matrix):
        struct.pack_into("<f", page, G_4EFD48 + index * 4, value)
    # The layout table content is never read by the function; only its address
    # is forwarded. Keep a distinct pattern so the page stays deterministic.
    for index in range(9 * 0x50):
        page[G_447088 + index] = (0xA0 + index) & 0xFF
    return bytes(page)


def build_work(case: dict) -> bytes:
    page = bytearray([0x5A]) * WORK_SIZE
    struct.pack_into("<I", page, 0x40, case.get("row", 101) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0xA94, 0x11111111)
    struct.pack_into("<I", page, 0xA98, 0x22222222)
    struct.pack_into("<I", page, 0xA9C, 0x33333333)
    enable = case.get("enable", [])
    for index in range(MAX_RECORDS):
        base = RECORD_BASE + index * RECORD_STRIDE
        for offset in range(RECORD_STRIDE):
            page[base + offset] = (0x40 + index + offset) & 0xFF
        page[base + RECORD_ENABLED] = (
            enable[index] if index < len(enable) else 0xEE
        )
        page[base + RECORD_ENABLED + 1] = 0xAB
    return bytes(page)


def build_list(case: dict) -> bytes:
    page = bytearray([0x11]) * LIST_SIZE
    count = case.get("count", 3)
    struct.pack_into("<I", page, L_STRUCT, LIST_ADDR + L_ITEMS)
    struct.pack_into("<i", page, L_STRUCT + 4, count)
    digits = case.get("digits", [])
    for index in range(MAX_RECORDS):
        # Pointer array entry -> 0x20-byte item object.
        item_addr = LIST_ADDR + L_SUBS + 0x3000 + index * 0x20
        struct.pack_into("<I", page, L_ITEMS + index * 4, item_addr)
        # Item + 8 -> sub object.
        struct.pack_into("<I", page, L_SUBS + 0x3000 + index * 0x20 + 8,
                         LIST_ADDR + L_SUBS + index * 0x40)
        # Sub + 0x0C is a positive relative link to the digit bytes.
        sub = L_SUBS + index * 0x40
        struct.pack_into("<I", page, sub + SUBLINK_OFFSET, SUBLINK_VALUE)
        base = sub + SUBLINK_OFFSET + SUBLINK_VALUE
        c5, c7, c8 = digits[index] if index < len(digits) else (0x31, 0x30, 0x31)
        page[base + 5] = c5 & 0xFF
        page[base + 7] = c7 & 0xFF
        page[base + 8] = c8 & 0xFF
    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOB_ADDR, GLOB_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(LIST_ADDR, LIST_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        # Unicorn's ARM port executes VFP regardless of CPACR/FPEXC, but set
        # them so the environment matches the pinned runtime.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        name = STUB_NAMES[address]
        if address == STUB_3170B8:
            self.call_log.append((name, r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, LIST_ADDR)
        elif address == STUB_328440:
            self.call_log.append((name, r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_20FE3C:
            self.call_log.append((name, r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_265DA4:
            self.call_log.append((name, r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2863F4:
            self.call_log.append((name, r0, r1))
            uc.mem_write(r0, bytes(uc.mem_read(r1, 36)))
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_2C00D4:
            word = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            self.call_log.append((name, r0, word))
            if word == 0:
                uc.mem_write(r0, struct.pack("<I", 1))
                uc.reg_write(arm.UC_ARM_REG_R0, 1)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for entry in log:
            name, args = entry[0], entry[1:]
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def _normalise_writes(self, writes) -> list:
        # Prologue/epilogue and scratch stack traffic is compiler-specific; only
        # writes outside the private stack frame are contract evidence.
        return [
            (address, size)
            for address, size in writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOB_ADDR, build_glob(case))
        self.uc.mem_write(WORK_ADDR, build_work(case))
        self.uc.mem_write(LIST_ADDR, build_list(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(TRAP_ADDR, b"\x00" * 0x1000)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x12345678)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x23456789)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x3456789A)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x456789AB)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_SAVED_START.items():
            self.uc.reg_write(VFP_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "r0_observed": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: self.uc.reg_read(reg) for name, reg in VFP_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "writes": self._normalise_writes(self.writes),
            "glob": bytes(self.uc.mem_read(GLOB_ADDR, GLOB_SIZE)),
            "work": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "list": bytes(self.uc.mem_read(LIST_ADDR, LIST_SIZE)),
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    if sorted(orig["writes"]) != sorted(cand["writes"]):
        problems.append(
            "write set:\n    orig=" + repr(sorted(orig["writes"]))
            + "\n    cand=" + repr(sorted(cand["writes"]))
        )
    for key in ("glob", "work", "list"):
        if orig[key] != cand[key]:
            first = next(
                (i for i, (a, b) in enumerate(zip(orig[key], cand[key])) if a != b),
                None,
            )
            problems.append(
                f"{key} memory differs (first byte {first}):\n"
                f"    orig=0x{orig[key][first]:02x} cand=0x{cand[key][first]:02x}"
                if first is not None else f"{key} memory length differs"
            )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "mode": 0x65,
        "state_word": 1,
        "guard": 1,
        "row": 101,
        "count": 3,
        "enable": [0, 0, 0],
        "digits": [(0x31, 0x30, 0x31), (0x35, 0x33, 0x34),
                   (0x39, 0x39, 0x39)],
        "work_null": False,
        "matrix": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- null host pointer: immediate return, nothing touched except the read
    cases.append(base_case("null host pointer", work_null=True))

    # --- title-screen layout dispatch: every in-range sub-state
    for sub in range(1, 10):
        cases.append(base_case(f"title sub-state {sub}", state_word=sub))
    for sub in (0, 10, 0xFFFFFFFF):
        cases.append(base_case(
            f"title sub-state out of range {sub}", state_word=sub))

    # --- mode gate: non-title mode always runs the enable-all sweep
    for mode in (0, 1, 0x64, 0x66, 0xFFFFFFFF):
        cases.append(base_case(f"mode 0x{mode:08x}", mode=mode))
    cases.append(base_case("mode 0 title", mode=0, state_word=3))

    # --- list counts, including negative and empty
    for count in (-1, 0, 1, 3):
        cases.append(base_case(f"count {count}", mode=0, count=count))
        cases.append(base_case(f"count {count} title", count=count))

    # --- enabled byte: only a zero is promoted to one
    cases.append(base_case("enable byte 0", mode=0, enable=[0, 0, 0]))
    cases.append(base_case("enable byte 1", mode=0, enable=[1, 1, 1]))
    cases.append(base_case("enable byte mixed 0xFF", mode=0,
                           enable=[0xFF, 0x00, 0x80]))
    cases.append(base_case("enable byte title untouched", enable=[0, 0, 0]))

    # --- guard word: identity init vs skip vs non-zero without bit 0
    for guard in (0, 1, 2, 0xFFFFFFFF):
        cases.append(base_case(f"guard 0x{guard:08x}", guard=guard, mode=0))
    cases.append(base_case("guard 0 with pre-seeded matrix", guard=0, mode=0,
                           matrix=[1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5]))
    cases.append(base_case("guard 2 with pre-seeded matrix", guard=2, mode=0,
                           matrix=[-1.0, -2.0, -3.0, -4.0, -5.0, -6.0,
                                   -7.0, -8.0, -9.0]))

    # --- placement state word (0x0049F920, shared with the title sub-state)
    # selects the scale; 0x63 is out of the title range so the sweep still runs.
    for state_word in (0x63, 0x00, 0x64, 0xFFFFFFFF):
        cases.append(base_case(
            f"placement state 0x{state_word:08x}", state_word=state_word,
            mode=0))
        cases.append(base_case(
            f"placement state 0x{state_word:08x} title",
            state_word=state_word))

    # --- every placement row
    for row in (100, 101, 102, 103):
        cases.append(base_case(f"row {row}", row=row))

    # --- signed-byte digit boundaries for the three characters
    digit_sets = [
        (0x31, 0x30, 0x31),  # "1", "0", "1" -> 0
        (0x39, 0x30, 0x31),  # "9" -> 8
        (0x31, 0x39, 0x39),  # c7='9', c8='9'
        (0x7F, 0x7F, 0x7F),
        (0x80, 0x80, 0x80),
        (0x00, 0x00, 0x00),
        (0xFF, 0xFF, 0xFF),
        (0x31, 0x30, 0x39),
    ]
    for index, digits in enumerate(digit_sets):
        cases.append(base_case(
            f"digits {index} {digits}",
            digits=[digits] * 3,
        ))

    # --- combined many-record case with distinct digits per record
    cases.append(base_case(
        "three distinct records",
        guard=0,
        state_word=0,
        row=103,
        count=3,
        enable=[0, 1, 0],
        digits=[(0x31, 0x30, 0x31), (0x35, 0x33, 0x39), (0x39, 0x38, 0x35)],
    ))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = LeafRunner().run(orig_code, case)
        cand = LeafRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(
            f"  [PASS] {case['name']}  "
            f"({len(orig['call_log'])} calls, r0 orig=0x{orig['r0_observed']:08x}"
            f" cand=0x{cand['r0_observed']:08x})"
        )
    return passed


def main() -> None:
    print("Testing script_vm_func_002668dc (0x002668dc)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(call relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("title_mode", "0x65u) {", "0x66u) {"),
        ("layout_stride", "(sub_state - 1u) * 0x50u;", "(sub_state - 1u) * 0x4Cu;"),
        ("scale_63", "? 3775.0f : 3575.0f", "? 3776.0f : 3575.0f"),
        ("guard_mask",
         "if ((*guard & 1u) == 0u && engine_func_002c00d4(guard) != 0u) {\n"
         "            identity[0] = 1.0f;",
         "if ((*guard & 3u) == 0u && engine_func_002c00d4(guard) != 0u) {\n"
         "            identity[0] = 1.0f;"),
    )
    for name, old, new in mutants:
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = LeafRunner().run(orig_code, case)
            bad = LeafRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
