#!/usr/bin/env python3
"""Differential test for camp_func_001f4e2c (0x001f4e2c) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the camp_func_001f4e2c
candidate body, resolves its two direct-call relocations to deterministic stubs
at the pinned addresses, and runs the pinned original
(extracted/exefs/code.bin, 408 B including its literal pool) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log: the full register image of the 0x002A8A08 fetch
    (entry phase, output pointer, zero) plus the output-buffer and phase values
    visible at that instant, and the 0x0028CDE4 call (object, the two pre-call
    s16 stack slots);
  * the full object page (phase + four flag bytes), the full output page and
    the full camp work page (final observable memory);
  * any emulated write outside those pages and the private stack.

Coverage: negative entry phases (no calls, no writes), a negative phase
republished by the fetch, phase 0, all 16 combinations of the four flag bytes
for phase 0x270F, every shift-count boundary (0, 1, 29, 30, 31, 32, 33, 127,
128, 254, 255) for the three fixed entries and the phase-indexed row, 64-bit
carry/borrow through negative sign-extended addends, phase-indexed rows for
small, large, 0x7FFFFFFF and wrapping bases, signed 16-bit helper results at
0x0000/0x7FFF/0x8000/0xFFFF, and the pre-zeroed stack slots (the stack is
filled with 0x5A so an uninitialised slot is visible).  Negative controls
mutate the sentinel phase, one flag offset, one work-table offset, the entry
gate, the phase-0 constant, the post-fetch reload, the shift bound and the
final helper argument order; each mutant must be detected.
"""

from __future__ import annotations

import struct
import random
import sys
from pathlib import Path

import unicorn
from unicorn import arm_const as arm

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.asm_diff import extract_elf_functions_detailed
from tools.build_check import compile_tu_armv6k

ORIG_BIN = ROOT / "extracted/exefs/code.bin"
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_001f4e2c"

FUNC_ADDR = 0x001F4E2C
FUNC_SIZE = 408

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the function and both stub addresses
OBJ_ADDR = 0x00710000
OBJ_SIZE = 0x00004000  # covers +0x3064 and +0x345C..+0x345F
OUT_ADDR = 0x00720000
OUT_SIZE = 0x00001000
CAMP_ADDR = 0x00740000
CAMP_SIZE = 0x00100000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Destination of the two 64-bit outputs handed to the function.
FLAG_OUT_ADDR = OUT_ADDR + 0x40
VALUE_OUT_ADDR = OUT_ADDR + 0x80

# Original object / work offsets recovered from the ARM body.
PHASE_OFFSET = 0x3064
FLAG_OFFSETS = (0x345C, 0x345D, 0x345E, 0x345F)
PHASE_COMPLETE = 0x270F
PHASE_ROW_OFFSET = 0x9107
FIXED_ENTRY_OFFSETS = (0x9108, 0x9109, 0x910A)

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_GET_WORK = 0x002A8A08
STUB_FILL_RESULT = 0x0028CDE4

STUB_NAMES = {
    STUB_GET_WORK: "camp_func_002a8a08",
    STUB_FILL_RESULT: "camp_func_0028cde4",
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

STACK_FILL = 0x5A


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001f4e2c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_001f4e2c not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for suffix, address in (
            ("002a8a08", STUB_GET_WORK),
            ("0028cde4", STUB_FILL_RESULT),
        ):
            if suffix in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        condition = original & 0xFF000000
        struct.pack_into(
            "<I", code, rel.offset, condition | (displacement & 0x00FFFFFF)
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
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


def as_s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def as_s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def effective_phase(case: dict) -> int:
    after = case["phase_after"]
    return case["entry_phase"] if after is None else after


def build_object(case: dict) -> bytes:
    # 0xA5 fill makes any stray write inside the page visible in the page diff.
    page = bytearray([0xA5] * OBJ_SIZE)
    struct.pack_into("<i", page, PHASE_OFFSET, as_s32(case["entry_phase"]))
    for offset, value in zip(FLAG_OFFSETS, case["flags"]):
        page[offset] = value & 0xFF
    return bytes(page)


def row_address(case: dict) -> int:
    return (
        case["camp"] + PHASE_ROW_OFFSET + (effective_phase(case) & 0xFFFFFFFF)
    ) & 0xFFFFFFFF


def build_camp(case: dict) -> bytes:
    page = bytearray([0xA5] * CAMP_SIZE)
    phase = effective_phase(case)
    signed_phase = as_s32(phase)
    if signed_phase == PHASE_COMPLETE:
        for offset, value in zip(FIXED_ENTRY_OFFSETS, case["fixed_entries"]):
            address = (case["camp"] + offset) & 0xFFFFFFFF
            if not (CAMP_ADDR <= address < CAMP_ADDR + CAMP_SIZE):
                raise RuntimeError(
                    f"fixed entry 0x{offset:x} at 0x{address:08x} is unmapped"
                )
            page[address - CAMP_ADDR] = value & 0xFF
    elif signed_phase > 0:
        address = row_address(case)
        if not (CAMP_ADDR <= address < CAMP_ADDR + CAMP_SIZE):
            raise RuntimeError(
                f"phase row for 0x{phase:08x} at 0x{address:08x} is unmapped"
            )
        page[address - CAMP_ADDR] = case["row_byte"] & 0xFF
    return bytes(page)


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
        self.uc.mem_map(CAMP_ADDR, CAMP_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ----------------------------------------------------------------- helpers
    @staticmethod
    def _normalise(value: int):
        if OBJ_ADDR <= value < OBJ_ADDR + OBJ_SIZE:
            return "<object>"
        if OUT_ADDR <= value < OUT_ADDR + OUT_SIZE:
            return "<out>"
        if CAMP_ADDR <= value < CAMP_ADDR + CAMP_SIZE:
            return "<camp>"
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _read_u64(self, address: int) -> int:
        return struct.unpack("<Q", self.uc.mem_read(address, 8))[0]

    def _read_s16(self, address: int) -> int:
        return struct.unpack("<h", self.uc.mem_read(address, 2))[0]

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    # ------------------------------------------------------------------- stubs
    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        if address == STUB_GET_WORK:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            # The outputs must already be cleared and the object still must
            # hold the entry phase at the instant of the fetch.
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    r0,
                    self._normalise(r1),
                    r2,
                    self._read_u64(FLAG_OUT_ADDR),
                    self._read_u64(VALUE_OUT_ADDR),
                    struct.unpack(
                        "<i", uc.mem_read(OBJ_ADDR + PHASE_OFFSET, 4)
                    )[0],
                )
            )
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["camp"] & 0xFFFFFFFF)
            if self.case["phase_after"] is not None:
                uc.mem_write(
                    OBJ_ADDR + PHASE_OFFSET,
                    struct.pack("<i", as_s32(self.case["phase_after"])),
                )
        elif address == STUB_FILL_RESULT:
            r0 = uc.reg_read(arm.UC_ARM_REG_R0)
            r1 = uc.reg_read(arm.UC_ARM_REG_R1)
            r2 = uc.reg_read(arm.UC_ARM_REG_R2)
            # Both slots are pre-zeroed by the original; only the r2 slot is
            # read back.  Distinct results expose an argument-order swap.
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    self._normalise(r0),
                    self._read_s16(r1),
                    self._read_s16(r2),
                )
            )
            if self.case["write_aux"]:
                uc.mem_write(
                    r1, struct.pack("<h", as_s16(self.case["aux_result"]))
                )
            uc.mem_write(
                r2, struct.pack("<h", as_s16(self.case["value_result"]))
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0xDEADBEEF)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # --------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJ_ADDR, build_object(case))
        self.uc.mem_write(OUT_ADDR, bytes([0xA5]) * OUT_SIZE)
        self.uc.mem_write(CAMP_ADDR, build_camp(case))
        self.uc.mem_write(STACK_ADDR, bytes([STACK_FILL]) * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, FLAG_OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, VALUE_OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = [
            (address, size)
            for address, size, _value in self.writes
            if not (OBJ_ADDR <= address < OBJ_ADDR + OBJ_SIZE)
            and not (OUT_ADDR <= address < OUT_ADDR + OUT_SIZE)
            and not (CAMP_ADDR <= address < CAMP_ADDR + CAMP_SIZE)
            and not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        ]

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "object": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
            "output": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
            "camp": bytes(self.uc.mem_read(CAMP_ADDR, CAMP_SIZE)),
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key in ("object", "output", "camp"):
        if orig[key] != cand[key]:
            differing = [
                index
                for index, (left, right) in enumerate(zip(orig[key], cand[key]))
                if left != right
            ]
            problems.append(f"{key} page differs at offsets {differing[:16]}")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "entry_phase": 0,
        "phase_after": None,
        "flags": (0, 0, 0, 0),
        "fixed_entries": (0, 0, 0),
        "row_byte": 0,
        "camp": CAMP_ADDR,
        "aux_result": 0x5A5A,
        "value_result": 0x1234,
        "write_aux": True,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- entry gate: any negative phase returns 0 before touching the outputs.
    for phase in (0xFFFFFFFF, 0xFFFFFFFE, 0x80000001, 0x80000000, 0xFFFF8000):
        cases.append(base_case(f"entry phase negative 0x{phase:08x}",
                               entry_phase=phase))
    # A negative phase is not republished by the fetch here (no call at all).
    cases.append(base_case("negative entry ignores later value",
                           entry_phase=0xFFFFFFFF, phase_after=0))

    # --- the fetch republishes a negative phase: outputs cleared, mask skipped.
    for entry, after in (
        (0, 0x80000000),
        (0, 0xFFFFFFFF),
        (5, 0xFFFF8000),
        (PHASE_COMPLETE, 0x80000000),
        (0x7FFFFFFF, 0xFFFFFFFE),
    ):
        cases.append(base_case(
            f"fetch publishes negative 0x{after:08x} from 0x{entry:08x}",
            entry_phase=entry, phase_after=after))

    # --- phase 0 stores 1 (also proves the post-fetch reload).
    for entry in (0, 1, 5, 0x100, PHASE_COMPLETE, 0x2710, 0x7FFFFFFF):
        cases.append(base_case(f"phase 0 from 0x{entry:08x}",
                               entry_phase=entry, phase_after=0))

    # --- phase 0x270F: all 16 gate combinations with distinct fixed entries.
    for combo in range(16):
        flags = tuple((combo >> index) & 1 for index in range(4))
        cases.append(base_case(
            f"phase 270F flags {combo:04b}", entry_phase=PHASE_COMPLETE,
            flags=flags, fixed_entries=(1, 2, 3)))

    # --- phase 0x270F: every shift-count boundary on one entry at a time.
    for value in (0, 1, 2, 15, 29, 30, 31, 32, 33, 63, 127, 128, 129,
                  200, 253, 254, 255):
        cases.append(base_case(
            f"phase 270F entry B byte {value}", entry_phase=PHASE_COMPLETE,
            flags=(0, 0xFF, 0, 0), fixed_entries=(value, 0, 0)))
    for value in (0, 1, 30, 31, 32, 255):
        cases.append(base_case(
            f"phase 270F entry C byte {value}", entry_phase=PHASE_COMPLETE,
            flags=(0, 0, 0xFF, 0), fixed_entries=(0, value, 0)))
        cases.append(base_case(
            f"phase 270F entry D byte {value}", entry_phase=PHASE_COMPLETE,
            flags=(0, 0, 0, 0xFF), fixed_entries=(0, 0, value)))
    # Gate-off cases: a non-zero table byte contributes nothing.
    for value in (1, 30, 255):
        cases.append(base_case(
            f"phase 270F gate off ignores byte {value}",
            entry_phase=PHASE_COMPLETE, flags=(0, 0, 0, 0),
            fixed_entries=(value, value, value)))

    # --- phase 0x270F: individual gates (offset identity) and carry cases.
    cases.append(base_case("phase 270F flag A only", entry_phase=PHASE_COMPLETE,
                           flags=(0xFF, 0, 0, 0), fixed_entries=(0, 0, 0)))
    cases.append(base_case("phase 270F flag B only", entry_phase=PHASE_COMPLETE,
                           flags=(0, 0xFF, 0, 0), fixed_entries=(3, 5, 7)))
    cases.append(base_case("phase 270F flag C only", entry_phase=PHASE_COMPLETE,
                           flags=(0, 0, 0xFF, 0), fixed_entries=(3, 5, 7)))
    cases.append(base_case("phase 270F flag D only", entry_phase=PHASE_COMPLETE,
                           flags=(0, 0, 0, 0xFF), fixed_entries=(3, 5, 7)))
    cases.append(base_case("phase 270F all gates carry",
                           entry_phase=PHASE_COMPLETE, flags=(1, 1, 1, 1),
                           fixed_entries=(30, 30, 30)))
    cases.append(base_case("phase 270F borrow from negative addend",
                           entry_phase=PHASE_COMPLETE, flags=(1, 1, 1, 1),
                           fixed_entries=(30, 31, 255)))
    cases.append(base_case("phase 270F two negative addends",
                           entry_phase=PHASE_COMPLETE, flags=(1, 1, 1, 1),
                           fixed_entries=(29, 30, 0)))
    cases.append(base_case("phase 270F entry 0xFF wrap",
                           entry_phase=PHASE_COMPLETE, flags=(1, 1, 1, 1),
                           fixed_entries=(0xFF, 0xFF, 0xFF)))

    # --- phase-indexed row: small/large indices and every shift boundary.
    for phase in (1, 2, 3, 0x270E, 0x2710, 0xFFFF, 0x10000, 0x7FFFF, 0xE0000):
        for value in (0, 1, 30, 31, 32, 255):
            cases.append(base_case(
                f"row phase 0x{phase:x} byte {value}", entry_phase=0,
                phase_after=phase, row_byte=value))
    # A different entry phase proves the row uses the reloaded value.
    cases.append(base_case("row uses reloaded phase", entry_phase=0x270E,
                           phase_after=0x2710, row_byte=30))
    cases.append(base_case("row from completed phase", entry_phase=PHASE_COMPLETE,
                           phase_after=5, row_byte=1))

    # --- row addresses around the 32-bit wrap, with a residual camp base.
    for phase, slot in ((0x7FFFFFFF, 0x20000), (0x40000000, 0x30000),
                        (0x7FFFFFF0, 0x40000)):
        target = CAMP_ADDR + slot
        camp = (target - PHASE_ROW_OFFSET - phase) & 0xFFFFFFFF
        cases.append(base_case(
            f"row phase 0x{phase:08x} wrapped", entry_phase=0,
            phase_after=phase, camp=camp, row_byte=30))

    # --- final signed 16-bit helper result, with a distinct aux result.
    for value in (0, 1, 0x1234, 0x4000, 0x7FFF, 0x8000, 0x8001, 0xFFFE,
                  0xFFFF):
        cases.append(base_case(
            f"helper result 0x{value:04x}", entry_phase=0, phase_after=0,
            aux_result=(value ^ 0x5A5A) & 0xFFFF, value_result=value))
    # The helper is allowed to leave the aux slot untouched.
    for value in (0, 0x7FFF, 0x8000, 0xFFFF):
        cases.append(base_case(
            f"helper writes only r2 result 0x{value:04x}", entry_phase=0,
            phase_after=0, aux_result=0x1234, value_result=value,
            write_aux=False))

    # --- fixed-seed sweep over the independent inputs.
    rng = random.Random(0x001F4E2C)
    rows = (1, 2, 3, 0x270E, 0x2710, 0xFFFF, 0x10000, 0x7FFFF, 0xE0000)
    for index in range(24):
        entry = rng.choice((0, 1, PHASE_COMPLETE, 0x2710, 0x7FFFFFFF,
                            0x80000000, 0xFFFFFFFF))
        if as_s32(entry) < 0:
            cases.append(base_case(f"sweep {index:02d} negative entry",
                                   entry_phase=entry))
            continue
        after = rng.choice((0, 1, PHASE_COMPLETE, rng.choice(rows),
                            0x7FFFFFFF, 0x80000000, 0xFFFFFFFF))
        signed_after = as_s32(after)
        camp = CAMP_ADDR
        if signed_after > 0 and signed_after != PHASE_COMPLETE:
            # Any phase row must land in the mapped camp page; choose a
            # residual camp base that places this row at a known slot.
            target = CAMP_ADDR + 0x10000 + (index * 0x1000) % (CAMP_SIZE - 0x20000)
            camp = (target - PHASE_ROW_OFFSET - (after & 0xFFFFFFFF)) & 0xFFFFFFFF
        flags = tuple(rng.randrange(0, 256) for _ in range(4))
        entries = tuple(rng.randrange(0, 256) for _ in range(3))
        row = rng.randrange(0, 256)
        cases.append(base_case(
            f"sweep {index:02d} entry 0x{entry:08x} after 0x{after:08x}",
            entry_phase=entry,
            phase_after=after,
            camp=camp,
            flags=flags,
            fixed_entries=entries,
            row_byte=row,
            aux_result=rng.randrange(0x8000, 0x10000),
            value_result=rng.randrange(0x10000),
            write_aux=bool(index & 1)))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case)
        cand = Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing camp_func_001f4e2c (0x001f4e2c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("complete_phase", "constexpr s32 kCampPhaseComplete = 0x270F;",
         "constexpr s32 kCampPhaseComplete = 0x270E;"),
        ("flag_b_offset", "constexpr u32 kCampFlagB = 0x345D;",
         "constexpr u32 kCampFlagB = 0x345E;"),
        ("fixed_entry_b_offset", "constexpr u32 kCampEntryB = 0x9108;",
         "constexpr u32 kCampEntryB = 0x9109;"),
        ("entry_gate", "if (entry_phase < 0) {",
         "if (entry_phase <= 0) {"),
        ("zero_phase_value", "*flag_mask = 1;", "*flag_mask = 2;"),
        ("post_fetch_reload",
         "const s32 phase =\n        *reinterpret_cast<const s32*>(object + "
         "kCampPhaseOffset);",
         "const s32 phase = entry_phase;"),
        ("shift_bound",
         "const u32 value = shift < 32u ? (1u << shift) : 0u;",
         "const u32 value = shift < 31u ? (1u << shift) : 0u;"),
        ("result_arg_order",
         "camp_func_0028cde4)(object, &aux, &value);",
         "camp_func_0028cde4)(object, &value, &aux);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case)
            bad = Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
