#!/usr/bin/env python3
"""Differential test for func_00150f54 (0x00150f54) using Unicorn ARM.

The candidate C++ in ``src/engine/leaf_batch45_a.cpp`` is compiled with the
project's pinned ARMv6K flags, its direct ``bl``/``b`` relocations are retargeted
to deterministic stubs placed at the original addresses, and the pinned original
(``extracted/exefs/code.bin``) is run against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs
  * return r0 (the canned tail-callee return), continuation PC, final SP;
  * the callee-saved core registers r4-r11 and the callee-saved VFP registers
    s16-s19 (d8/d9);
  * the ordered call log with every argument of every helper:
      0x002B4EB8(obj, slot), 0x002A3418(s8 slot, f32 blend bits),
      0x00153160(element) / 0x001531AC(element),
      0x002BB270(), 0x001579D8(list, flags),
      0x002BCE38(f32 blend bits);
  * the full 4 KiB object page, the untouched guard page and the element page;
  * the set of object writes (address + access width) and any CPU write outside
    the private stack and the object page.

Coverage
  * every branch of the two clipped counters per slot: first-only advance,
    second-only advance, both, neither, and the second counter reaching its
    limit (which calls 0x002B4EB8);
  * signed counter/limit boundaries (INT_MIN, INT_MAX, -1, 0) for both counter
    pairs, including INT_MIN -> INT_MIN+1 saturation;
  * the interpolation vs. end-value selection for all three ranges, including a
    negative limit, a zero limit, infinite and NaN range endpoints, and the
    clamp boundaries 0 and 1;
  * null, non-null, non-type-2 and type-2 elements in both element slots, with
    helper results 0 (clear) and non-zero (keep) in every position;
  * both object-level counter updates and their equality/less/greater arms,
    plus the final lerp at/under/over its limit.

Negative controls mutate the element type selector, the notification flag, the
slot stride and the clamp limit; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch45_a.cpp"
OUT_DIR = ROOT / "build/test_leaf_00150f54"

FUNC_ADDR = 0x00150F54
FUNC_SIZE = 656

# One 2 MiB code window covers the original body (0x150f54) and every stub,
# the highest being 0x002bce38.
CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000

OBJ_ADDR = 0x00710000
OBJ_SIZE = 0x00001000
GUARD_ADDR = 0x00720000
GUARD_SIZE = 0x00001000
ELEM_ADDR = 0x00730000
ELEM_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Direct-call targets from the pinned body.
STUB_153160 = 0x00153160
STUB_1531AC = 0x001531AC
STUB_1579D8 = 0x001579D8
STUB_2A3418 = 0x002A3418
STUB_2B4EB8 = 0x002B4EB8
STUB_2BB270 = 0x002BB270
STUB_2BCE38 = 0x002BCE38

STUB_NAMES = {
    STUB_153160: "func_00153160",
    STUB_1531AC: "func_001531ac",
    STUB_1579D8: "func_001579d8",
    STUB_2A3418: "func_002a3418",
    STUB_2B4EB8: "func_002b4eb8",
    STUB_2BB270: "engine_func_002bb270",
    STUB_2BCE38: "engine_func_002bce38",
}

# 0x002BB270 returns the notification list head; 0x002BCE38 returns a canned
# value so the tail-return path is observable (its real r0 input is ignored by
# the thunk and therefore differs between the two bodies).
RET_LIST = 0x00740000
RET_TAIL = 0x000BCE38

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
    "s16": arm.UC_ARM_REG_S16,
    "s17": arm.UC_ARM_REG_S17,
    "s18": arm.UC_ARM_REG_S18,
    "s19": arm.UC_ARM_REG_S19,
}
VFP_SAVED_START = {
    "s16": 0x3F8CCCCD,
    "s17": 0xBF8CCCCD,
    "s18": 0x41200000,
    "s19": 0xC1200000,
}

# ------------------------------------------------------------------- fixtures
def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


F_ZERO = 0x00000000
F_NEG_ZERO = 0x80000000
F_ONE = 0x3F800000
F_TWO = 0x40000000
F_NEG_ONE = 0xBF800000
F_INF = 0x7F800000
F_NEG_INF = 0xFF800000
F_NAN = 0x7FC00000

INT_MIN = -0x80000000
INT_MAX = 0x7FFFFFFF

# Object offsets used by the body.
A_0C, A_10 = 0x0C, 0x10
F_14, F_18 = 0x14, 0x18
A_1C, A_20 = 0x1C, 0x20
SLOT_STRIDE = 0x10
S_START_A, S_END_A, S_LIM_A, S_CUR_A = 0x44, 0x48, 0x4C, 0x50
S_START_B, S_END_B, S_LIM_B, S_CUR_B = 0x24, 0x28, 0x2C, 0x30
S_ELEM0, S_ELEM1 = 0x2A0, 0x2A8
ELEM_TYPE_OFF = 4

ELEM_PTRS = (ELEM_ADDR + 0x100, ELEM_ADDR + 0x200,
             ELEM_ADDR + 0x300, ELEM_ADDR + 0x400)


def build_obj(case: dict) -> bytes:
    page = bytearray(OBJ_SIZE)
    for index in range(OBJ_SIZE):
        page[index] = (index * 7 + 3) & 0xFF

    def put_u32(offset: int, value: int) -> None:
        struct.pack_into("<I", page, offset, value & 0xFFFFFFFF)

    def put_s32(offset: int, value: int) -> None:
        struct.pack_into("<i", page, offset, value)

    put_s32(A_0C, case.get("a0c", 0))
    put_s32(A_10, case.get("a10", 0))
    put_u32(F_14, case.get("f14", F_ZERO))
    put_u32(F_18, case.get("f18", F_ONE))
    put_s32(A_1C, case.get("a1c", 10))
    put_s32(A_20, case.get("a20", 10))

    for slot in range(2):
        base = slot * SLOT_STRIDE
        prefix = f"s{slot}_"
        put_u32(base + S_START_A, case.get(prefix + "start_a", F_ZERO))
        put_u32(base + S_END_A, case.get(prefix + "end_a", F_ONE))
        put_s32(base + S_LIM_A, case.get(prefix + "lim_a", 10))
        put_s32(base + S_CUR_A, case.get(prefix + "cur_a", 2))
        put_u32(base + S_START_B, case.get(prefix + "start_b", F_ZERO))
        put_u32(base + S_END_B, case.get(prefix + "end_b", F_ONE))
        put_s32(base + S_LIM_B, case.get(prefix + "lim_b", 10))
        put_s32(base + S_CUR_B, case.get(prefix + "cur_b", 2))
        put_u32(base + S_ELEM0, case.get(prefix + "elem0", ELEM_PTRS[slot * 2]))
        page[base + S_ELEM0 + ELEM_TYPE_OFF] = case.get(prefix + "type0", 2) & 0xFF
        put_u32(base + S_ELEM1, case.get(prefix + "elem1", ELEM_PTRS[slot * 2 + 1]))
        page[base + S_ELEM1 + ELEM_TYPE_OFF] = case.get(prefix + "type1", 2) & 0xFF

    return bytes(page)


def read_c_string(uc, address: int, limit: int = 32) -> bytes:  # pragma: no cover
    out = bytearray()
    for index in range(limit):
        byte = uc.mem_read(address + index, 1)[0]
        if byte == 0:
            break
        out.append(byte)
    return bytes(out)


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    functions = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in functions.items():
        if "00150f54" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_00150f54 not found in {obj_file}: {sorted(functions)}"
        )

    raw, relocations = candidate
    code = bytearray(raw)
    for rel in relocations:
        target = None
        for address, name in STUB_NAMES.items():
            if f"{address:08x}" in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved relocation: {rel.symbol_name}")
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unexpected relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
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
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Both bodies use VFP: grant CP10/CP11 access and set FPEXC.EN.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(OBJ_ADDR, OBJ_SIZE)
        self.uc.mem_map(GUARD_ADDR, GUARD_SIZE)
        self.uc.mem_map(ELEM_ADDR, ELEM_SIZE)
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
        self.alive: list = []
        self.alive_index = 0

    def _s0_bits(self) -> int:
        return self.uc.reg_read(arm.UC_ARM_REG_S0) & 0xFFFFFFFF

    def _signed(self, value: int) -> int:
        return value - (1 << 32) if value & 0x80000000 else value

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_2B4EB8:
            self.call_log.append((STUB_NAMES[address], r0, r1))
        elif address == STUB_2A3418:
            self.call_log.append(
                (STUB_NAMES[address], self._signed(r0), self._s0_bits())
            )
        elif address in (STUB_153160, STUB_1531AC):
            self.call_log.append((STUB_NAMES[address], r0))
            if self.alive_index < len(self.alive):
                result = self.alive[self.alive_index]
            else:
                result = 0
            self.alive_index += 1
            uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)
        elif address == STUB_2BB270:
            self.call_log.append((STUB_NAMES[address],))
            uc.reg_write(arm.UC_ARM_REG_R0, RET_LIST)
        elif address == STUB_1579D8:
            self.call_log.append((STUB_NAMES[address], r0, r1))
        elif address == STUB_2BCE38:
            self.call_log.append((STUB_NAMES[address], self._s0_bits()))
            uc.reg_write(arm.UC_ARM_REG_R0, RET_TAIL)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.alive = list(case.get("alive", []))
        self.alive_index = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(OBJ_ADDR, build_obj(case))
        self.uc.mem_write(GUARD_ADDR, b"\xA5" * GUARD_SIZE)
        self.uc.mem_write(ELEM_ADDR, b"\x5A" * ELEM_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, OBJ_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)
        for name, value in VFP_SAVED_START.items():
            self.uc.reg_write(VFP_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        object_writes = set()
        for address, size in self.writes:
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            in_object = OBJ_ADDR <= address < OBJ_ADDR + OBJ_SIZE
            if in_object:
                object_writes.add((address - OBJ_ADDR, size))
            elif not in_stack:
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: self.uc.reg_read(reg) & 0xFFFFFFFF
                for name, reg in VFP_SAVED.items()
            },
            "call_log": list(self.call_log),
            "object_writes": sorted(object_writes),
            "unexpected_writes": unexpected_writes,
            "memory": {
                "object": bytes(self.uc.mem_read(OBJ_ADDR, OBJ_SIZE)),
                "guard": bytes(self.uc.mem_read(GUARD_ADDR, GUARD_SIZE)),
                "element": bytes(self.uc.mem_read(ELEM_ADDR, ELEM_SIZE)),
            },
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "vfp_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    if orig["object_writes"] != cand["object_writes"]:
        problems.append(
            "object write set:\n    orig="
            + repr(orig["object_writes"])
            + "\n    cand="
            + repr(cand["object_writes"])
        )
    for key, value in orig["memory"].items():
        if value != cand["memory"][key]:
            problems.append(f"{key} memory was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {"name": name}
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline: both slots advance smoothly, elements stay alive
    cases.append(base_case("both slots advance, elements kept"))

    # --- counter-selection arms -------------------------------------------------
    cases.append(base_case(
        "first counter only (slot0), second only (slot1)",
        s0_cur_a=2, s0_lim_a=10, s0_cur_b=10, s0_lim_b=10,
        s1_cur_a=10, s1_lim_a=10, s1_cur_b=2, s1_lim_b=10,
    ))
    cases.append(base_case(
        "neither counter advances (both slots)",
        s0_cur_a=10, s0_lim_a=10, s0_cur_b=10, s0_lim_b=10,
        s1_cur_a=11, s1_lim_a=10, s1_cur_b=11, s1_lim_b=10,
    ))
    cases.append(base_case(
        "second counter reaches limit in both slots",
        s0_cur_a=10, s0_lim_a=10, s0_cur_b=9, s0_lim_b=10,
        s1_cur_a=0, s1_lim_a=0, s1_cur_b=0, s1_lim_b=1,
    ))
    cases.append(base_case(
        "second counter advances but stays below limit",
        s0_cur_b=3, s0_lim_b=10,
        s1_cur_b=INT_MIN, s1_lim_b=INT_MIN + 2,
    ))

    # --- signed boundaries for the first counter pair ---------------------------
    first_boundaries = [
        (-1, 0), (0, -1), (INT_MIN, INT_MAX), (INT_MAX, INT_MIN),
        (INT_MIN, INT_MIN), (INT_MAX, INT_MAX), (-2, -1), (1, -2),
    ]
    for cur, lim in first_boundaries:
        cases.append(base_case(
            f"slot0 first counter {cur}/{lim}",
            s0_cur_a=cur, s0_lim_a=lim,
            s0_cur_b=10, s0_lim_b=10,
        ))

    # --- signed boundaries for the second counter pair --------------------------
    second_boundaries = [
        (-1, 0), (0, -1), (INT_MIN, INT_MAX), (INT_MAX, INT_MIN),
        (INT_MIN, INT_MIN + 1), (INT_MIN, INT_MIN + 2),
        (INT_MAX - 1, INT_MAX), (INT_MAX, INT_MAX),
    ]
    for cur, lim in second_boundaries:
        cases.append(base_case(
            f"slot1 second counter {cur}/{lim}",
            s1_cur_a=10, s1_lim_a=10, s1_cur_b=cur, s1_lim_b=lim,
            s0_cur_a=0, s0_lim_a=0, s0_cur_b=0, s0_lim_b=0,
        ))

    # --- interpolation / clamp boundaries --------------------------------------
    clamp_ranges = [
        ("below zero", F_NEG_ONE, F_NEG_ZERO, 1, 4),
        ("above one", F_ZERO, F_TWO, 3, 4),
        ("exact zero", F_NEG_ONE, F_ZERO, 1, 2),
        ("exact one", F_ZERO, F_ONE, 1, 1),
        ("negative zero", F_NEG_ZERO, F_NEG_ZERO, 1, 4),
        ("reversed range", F_ONE, F_NEG_ONE, 1, 4),
        ("negative limit", F_ZERO, F_ONE, -2, -1),
        ("positive inf", F_ZERO, F_INF, 1, 4),
        ("negative inf", F_NEG_INF, F_ZERO, 1, 4),
        ("nan range", F_NAN, F_NAN, 1, 4),
        ("nan endpoint", F_ZERO, F_NAN, 1, 4),
        ("nan start", F_NAN, F_ONE, 1, 4),
    ]
    for label, start, end, cur, lim in clamp_ranges:
        cases.append(base_case(
            f"slot0 first range {label}",
            s0_start_a=start, s0_end_a=end, s0_cur_a=cur, s0_lim_a=lim,
        ))
        cases.append(base_case(
            f"slot1 second range {label}",
            s1_start_b=start, s1_end_b=end, s1_cur_b=cur, s1_lim_b=lim,
        ))

    # zero limit reached through a negative counter expands to +/-inf then clamps
    cases.append(base_case(
        "slot0 first zero limit, negative counter",
        s0_cur_a=-1, s0_lim_a=0, s0_start_b=F_NEG_ONE, s0_end_b=F_ONE,
    ))
    cases.append(base_case(
        "slot1 second zero limit, negative counter",
        s1_cur_b=-1, s1_lim_b=0, s1_start_b=F_NEG_ONE, s1_end_b=F_ONE,
    ))

    # --- element handling -------------------------------------------------------
    cases.append(base_case(
        "all elements null", s0_elem0=0, s0_elem1=0, s1_elem0=0, s1_elem1=0))
    cases.append(base_case(
        "non-type-2 elements only",
        s0_type0=0, s0_type1=1, s1_type0=3, s1_type1=0xFF,
        alive=[0, 0, 0, 0]))
    cases.append(base_case(
        "null pointer overrides type 2",
        s0_elem0=0, s0_type0=2, s1_elem1=0, s1_type1=2))
    cases.append(base_case(
        "mixed clear/keep across both slots",
        alive=[0, 1, 1, 0]))
    cases.append(base_case(
        "all type-2 elements cleared", alive=[0, 0, 0, 0]))
    cases.append(base_case(
        "all type-2 elements kept", alive=[0xFFFFFFFF, 1, 2, 0x80000000]))
    cases.append(base_case(
        "only slot1 elements active",
        s0_type0=1, s0_type1=1, alive=[0, 1]))
    cases.append(base_case(
        "only slot0 elements active",
        s1_type0=1, s1_type1=1, alive=[1, 0]))

    # --- object-level counter updates ------------------------------------------
    for a0c, a10 in (
        (0, 0), (5, 5), (-1, 0), (1, 0), (INT_MAX, INT_MAX - 1),
        (INT_MIN, INT_MIN + 1),
    ):
        cases.append(base_case(
            f"object first counter {a0c}/{a10}", a0c=a0c, a10=a10))
    for a20, a1c in (
        (0, 0), (10, 0), (INT_MAX, INT_MIN), (INT_MIN, INT_MAX),
        (INT_MAX - 1, INT_MAX), (INT_MIN + 1, INT_MIN),
    ):
        cases.append(base_case(
            f"object second counter {a20}/{a1c}", a20=a20, a1c=a1c))

    # --- final range selection --------------------------------------------------
    for label, start, end, cur, lim in (
        ("below limit", F_ZERO, F_TWO, 1, 4),
        ("at limit", F_ZERO, F_TWO, 4, 4),
        ("above limit", F_ZERO, F_TWO, 5, 4),
        ("below zero", F_NEG_ONE, F_NEG_ONE, 1, 4),
        ("above one", F_ZERO, F_TWO, 3, 4),
        ("negative limit", F_ZERO, F_ONE, -2, -1),
        ("zero limit", F_ONE, F_TWO, -1, 0),
        ("nan range", F_NAN, F_NAN, 1, 4),
    ):
        cases.append(base_case(
            f"final range {label}", f14=start, f18=end, a20=cur, a1c=lim))

    # --- slot isolation / combined -------------------------------------------------
    cases.append(base_case(
        "distinct per-slot fields",
        s0_start_a=F_ZERO, s0_end_a=F_ONE, s0_cur_a=1, s0_lim_a=4,
        s0_start_b=F_ONE, s0_end_b=F_ZERO, s0_cur_b=3, s0_lim_b=4,
        s1_start_a=F_NEG_ONE, s1_end_a=F_ONE, s1_cur_a=2, s1_lim_a=4,
        s1_start_b=F_ZERO, s1_end_b=F_TWO, s1_cur_b=1, s1_lim_b=4,
        a0c=10, a10=0, a20=0, a1c=10,
    ))
    cases.append(base_case(
        "everything advances to limits",
        s0_cur_a=0, s0_lim_a=1, s0_cur_b=0, s0_lim_b=1,
        s1_cur_a=0, s1_lim_a=1, s1_cur_b=0, s1_lim_b=1,
        a0c=1, a10=0, a1c=1, a20=0,
        alive=[0, 0, 0, 0],
    ))

    return cases


def run_case_set(orig_code: bytes, cand_code: bytes, cases: list[dict]) -> int:
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
    print("Testing func_00150f54 (0x00150f54)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    mutants = (
        ("element_type", "constexpr u8 kActiveElementType = 2;",
         "constexpr u8 kActiveElementType = 3;"),
        ("notification_flag", "constexpr u32 kNotificationFlags = 0x40;",
         "constexpr u32 kNotificationFlags = 0x20;"),
        ("slot_stride", "constexpr u32 kSlotStride = 0x10;",
         "constexpr u32 kSlotStride = 0x8;"),
        ("clamp_limit", "constexpr f32 kClampMax = 1.0f;",
         "constexpr f32 kClampMax = 0.5f;"),
    )
    for name, old, new in mutants:
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
