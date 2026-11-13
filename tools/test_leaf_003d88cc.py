#!/usr/bin/env python3
"""Differential test for func_003d88cc (0x003D88CC) using Unicorn ARM.

The routine restarts the result-panel animation state object.  It clears bit 21
of ``object+0x634`` on every path, returns early when bit 20 is set, and
otherwise snapshots current animation samples into interpolation bases
(``object+0x5F0``/``+0x620``/``+0x62C``/``+0x630`` plus the .bss tracks at
0x00493518/0x00493530), clears the matching targets and phase counters,
publishes one word to 0x004342F4, zeroes 0x004342F8, stores ``1`` at +0x684 and
the ``r2`` argument at +0x680, then sets bit 4 of +0x634.

The routine is a leaf: there are no direct or indirect calls and no
architected stack arguments, so the ordered call log is always empty.

The runner compiles ``src/engine/leaf_batch36_b.cpp``, extracts
``func_003d88cc``, and runs the pinned original (``extracted/exefs/code.bin``)
against the candidate in separate Unicorn machines with identical fixtures.

Compared per case:
  * return r0 (the object pointer on the early path, the updated flag word on
    the completed path), continuation PC, final SP, callee-saved r4-r11;
  * every emulated write outside the private stack (sorted by address; the
    original and the compiler are free to schedule non-aliasing stores in a
    different order);
  * the complete ``self`` page, the global page covering 0x004342C8..0x004342FF
    and the .bss track page covering 0x00493518..0x00493544, including every
    byte the routine must not touch.

Coverage: bit 20/bit 21 gate combinations, both return paths, low/high flag
bits, the sign and magnitude boundaries of the r2 argument, an r1 value that
must be ignored, zero/0xFF page fills, and NaN/denormal/infinity bit patterns
in every copied field (the routine must copy bits, not evaluate floats).

An independent expected model validates both the original and the candidate:
the early/completed return value, the exact final pages, and every untouched
byte.  Negative controls recompile mutated source (flag masks, branch,
copy direction, global/track addresses, started flag, timer/limit, vector lane
and dropped stores); every mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch36_b.cpp"
OUT_DIR = ROOT / "build/test_leaf_003d88cc"

FUNC_NAME = "func_003d88cc"
FUNC_ADDR = 0x003D88CC
FUNC_SIZE = 404

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000          # original/candidate body at 0x003D88CC
SELF_ADDR = 0x00500000
SELF_SIZE = 0x00010000
GLOBAL_ADDR = 0x00434000        # 0x004342C8..0x004342FF live here
GLOBAL_SIZE = 0x00001000
BSS_ADDR = 0x00493000           # 0x00493518..0x00493544 live here
BSS_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

CLEAR_PENDING = 0x00200000      # bit 21, cleared on both paths
BLOCKED = 0x00100000            # bit 20, early-return gate
STARTED = 0x00000010            # bit 4, set on the completed path

GLOBAL_WORD_ADDR = 0x004342F4   # literal 0x004342C8 + 0x2C
GLOBAL_SCALAR_ADDR = 0x004342F8 # literal 0x004342C8 + 0x30

TRACK_A_BASE = 0x00493518
TRACK_A_TARGET = 0x00493524
TRACK_B_BASE = 0x00493530
TRACK_B_TARGET = 0x0049353C

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

# Distinct default contents prove that every source offset is read exactly
# once and from the correct address.  The values are arbitrary bit patterns.
DEFAULT_SELF_WORDS = {
    0x5A4: 0x11111111,
    0x5AC: 0x22222222, 0x5B0: 0x23232323, 0x5B4: 0x24242424,
    0x5DC: 0x33333333,
    0x5E8: 0x34343434, 0x5EC: 0x35353535,
    0x5F0: 0x36363636, 0x5F4: 0x37373737, 0x5F8: 0x38383838,
    0x620: 0x39393939,
    0x62C: 0x3A3A3A3A, 0x630: 0x3B3B3B3B,
    0x658: 0x3C3C3C3C, 0x65C: 0x3D3D3D3D, 0x660: 0x3E3E3E3E,
    0x670: 0x3F3F3F3F,
    0x680: 0x40404040, 0x684: 0x41414141,
    0x698: 0x42424242,
    0x6A8: 0x43434343,
    0x6B8: 0x44444444,
    0x6CC: 0x45454545, 0x6D0: 0x46464646, 0x6D4: 0x47474747,
    0x6E4: 0x48484848, 0x6E8: 0x49494949, 0x6EC: 0x4A4A4A4A,
    0x794: 0x4B4B4B4B, 0x798: 0x4C4C4C4C, 0x79C: 0x4D4D4D4D,
    0x7A4: 0x4E4E4E4E,
    0x7AC: 0x4F4F4F4F, 0x7B0: 0x50505050, 0x7B4: 0x51515151,
    0x7BC: 0x52525252,
    0x7C4: 0x53535353, 0x7C8: 0x54545454, 0x7CC: 0x55555555,
    0x7D0: 0x56565656, 0x7D4: 0x57575757, 0x7D8: 0x58585858,
    0x7E0: 0x59595959,
    0x7E8: 0x5B5B5B5B, 0x7EC: 0x5C5C5C5C, 0x7F0: 0x5D5D5D5D,
    0x7F4: 0x5E5E5E5E, 0x7F8: 0x5F5F5F5F, 0x7FC: 0x60606060,
    0x800: 0x61616161, 0x804: 0x62626262, 0x808: 0x63636363,
    0x810: 0x64646464,
    0x818: 0x65656565, 0x81C: 0x66666666, 0x820: 0x67676767,
    0x824: 0x68686868, 0x828: 0x69696969, 0x82C: 0x6A6A6A6A,
    0x830: 0x6B6B6B6B, 0x834: 0x6C6C6C6C, 0x838: 0x6D6D6D6D,
    0x840: 0x6E6E6E6E,
}
DEFAULT_GLOBAL_WORDS = {
    GLOBAL_WORD_ADDR: 0x72727272,
    GLOBAL_SCALAR_ADDR: 0x73737373,
}
DEFAULT_BSS_WORDS = {
    TRACK_A_BASE + 0x0: 0x81818181,
    TRACK_A_BASE + 0x4: 0x82828282,
    TRACK_A_BASE + 0x8: 0x83838383,
    TRACK_A_TARGET + 0x0: 0x84848484,
    TRACK_A_TARGET + 0x4: 0x85858585,
    TRACK_A_TARGET + 0x8: 0x86868686,
    TRACK_B_BASE + 0x0: 0x87878787,
    TRACK_B_BASE + 0x4: 0x88888888,
    TRACK_B_BASE + 0x8: 0x89898989,
    TRACK_B_TARGET + 0x0: 0x8A8A8A8A,
    TRACK_B_TARGET + 0x4: 0x8B8B8B8B,
    TRACK_B_TARGET + 0x8: 0x8C8C8C8C,
}


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def make_case(name: str, *, flags: int = 0, value: int = 2, arg1: int = 0,
              self_fill: int = 0x5A, global_fill: int = 0x71,
              bss_fill: int = 0x31, distinct: bool = True,
              self_words: dict | None = None,
              global_words: dict | None = None,
              bss_words: dict | None = None) -> dict:
    return {
        "name": name,
        "flags": u32(flags),
        "value": s32(value),
        "arg1": u32(arg1),
        "self_fill": self_fill,
        "global_fill": global_fill,
        "bss_fill": bss_fill,
        "distinct": distinct,
        "self_words": dict(self_words or {}),
        "global_words": dict(global_words or {}),
        "bss_words": dict(bss_words or {}),
    }


def build_self_page(case: dict) -> bytearray:
    page = bytearray(bytes([case["self_fill"]]) * SELF_SIZE)
    if case["distinct"]:
        for offset, bits in DEFAULT_SELF_WORDS.items():
            struct.pack_into("<I", page, offset, bits)
    for offset, bits in case["self_words"].items():
        struct.pack_into("<I", page, offset, u32(bits))
    struct.pack_into("<I", page, 0x634, case["flags"])
    return page


def build_global_page(case: dict) -> bytearray:
    page = bytearray(bytes([case["global_fill"]]) * GLOBAL_SIZE)
    if case["distinct"]:
        for address, bits in DEFAULT_GLOBAL_WORDS.items():
            struct.pack_into("<I", page, address - GLOBAL_ADDR, bits)
    for address, bits in case["global_words"].items():
        struct.pack_into("<I", page, address - GLOBAL_ADDR, u32(bits))
    return page


def build_bss_page(case: dict) -> bytearray:
    page = bytearray(bytes([case["bss_fill"]]) * BSS_SIZE)
    if case["distinct"]:
        for address, bits in DEFAULT_BSS_WORDS.items():
            struct.pack_into("<I", page, address - BSS_ADDR, bits)
    for address, bits in case["bss_words"].items():
        struct.pack_into("<I", page, address - BSS_ADDR, u32(bits))
    return page


# ---------------------------------------------------------------------------
# Independent expected model (hand-derived from the ARM store list)
# ---------------------------------------------------------------------------
def expected_run(case: dict) -> tuple:
    """Return (r0, self_page, global_page, bss_page)."""
    page = build_self_page(case)
    glob = build_global_page(case)
    bss = build_bss_page(case)

    def rd32(buf: bytearray, offset: int) -> int:
        return struct.unpack_from("<I", buf, offset)[0]

    def wr32(buf: bytearray, offset: int, bits: int) -> None:
        struct.pack_into("<I", buf, offset, u32(bits))

    def wr_abs(address: int, bits: int) -> None:
        if GLOBAL_ADDR <= address < GLOBAL_ADDR + GLOBAL_SIZE:
            wr32(glob, address - GLOBAL_ADDR, bits)
        elif BSS_ADDR <= address < BSS_ADDR + BSS_SIZE:
            wr32(bss, address - BSS_ADDR, bits)
        else:
            raise AssertionError(f"unexpected absolute store 0x{address:08X}")

    def copy(dst: int, src: int, count: int = 1) -> None:
        for lane in range(count):
            wr32(page, dst + 4 * lane, rd32(page, src + 4 * lane))

    def zero(offset: int) -> None:
        wr32(page, offset, 0)

    flags = rd32(page, 0x634)
    masked = flags & ~CLEAR_PENDING
    wr32(page, 0x634, masked)
    if masked & BLOCKED:
        return SELF_ADDR, bytes(page), bytes(glob), bytes(bss)

    zero(0x6B8)

    copy(0x798, 0x794)
    copy(0x7B0, 0x7AC)
    copy(0x7D4, 0x7D0)
    copy(0x7C8, 0x7C4)
    copy(0x7F4, 0x7E8, 3)
    copy(0x824, 0x818, 3)

    zero(0x79C)
    zero(0x7B4)
    zero(0x7D8)
    zero(0x7CC)
    zero(0x808)
    zero(0x804)
    zero(0x800)
    zero(0x838)
    zero(0x834)
    zero(0x830)

    zero(0x7A4)
    zero(0x7BC)
    zero(0x7E0)
    zero(0x810)
    zero(0x840)

    copy(0x620, 0x698)
    wr_abs(GLOBAL_WORD_ADDR, rd32(page, 0x670))
    copy(0x630, 0x6A8)
    copy(0x62C, 0x5A4)

    copy(0x5F0, 0x6CC, 3)

    for lane in range(3):
        wr_abs(TRACK_A_BASE + 4 * lane, rd32(page, 0x658 + 4 * lane))
    for lane in range(3):
        wr_abs(TRACK_B_BASE + 4 * lane, rd32(page, 0x6E4 + 4 * lane))

    zero(0x5DC)
    wr_abs(GLOBAL_SCALAR_ADDR, 0)
    zero(0x5EC)
    zero(0x5E8)
    zero(0x5AC)
    zero(0x5B0)
    zero(0x5B4)

    for lane in range(3):
        wr_abs(TRACK_A_TARGET + 4 * lane, 0)
    for lane in range(3):
        wr_abs(TRACK_B_TARGET + 4 * lane, 0)

    wr32(page, 0x684, 1)
    wr32(page, 0x680, case["value"])

    updated = rd32(page, 0x634) | STARTED
    wr32(page, 0x634, updated)
    return updated, bytes(page), bytes(glob), bytes(bss)


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(src_file, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")
    funcs = extract_elf_functions_detailed(obj_file)
    entry = funcs.get(FUNC_NAME)
    if entry is None:
        raise RuntimeError(
            f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}"
        )
    raw, relocs = entry
    if relocs:
        raise RuntimeError(f"unexpected relocations in {obj_file.name}: {relocs}")
    return bytes(raw)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    return compile_variant(SOURCE, OUT_DIR / "leaf_batch36_b.o")


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(
            f"mutation anchor {old!r} occurs {text.count(old)} times, expected 1"
        )
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Machine
# ---------------------------------------------------------------------------
class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (SELF_ADDR, SELF_SIZE),
            (GLOBAL_ADDR, GLOBAL_SIZE),
            (BSS_ADDR, BSS_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        self.orig_code = get_orig_bytes()
        self.call_log: list = []
        self.writes: list = []
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & ((1 << (8 * size)) - 1)))

    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.call_log = []

        # Reproduce the exact 404-byte original span (including its literal
        # pool) for the original run, and clear the same span before a
        # possibly shorter candidate so no stale literal data is visible.
        uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        uc.mem_write(FUNC_ADDR,
                     self.orig_code if candidate is None else candidate)
        uc.mem_write(SELF_ADDR, bytes(build_self_page(case)))
        uc.mem_write(GLOBAL_ADDR, bytes(build_global_page(case)))
        uc.mem_write(BSS_ADDR, bytes(build_bss_page(case)))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        uc.reg_write(arm.UC_ARM_REG_R1, case["arg1"])
        uc.reg_write(arm.UC_ARM_REG_R2, case["value"] & 0xFFFFFFFF)
        uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        for name, register in CALLEE_SAVED.items():
            uc.reg_write(register, CALLEE_SAVED_START[name])
        for index in range(32):
            uc.reg_write(getattr(arm, f"UC_ARM_REG_S{index}"),
                         0x3F000000 + index)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            pc = uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        return {
            "call_log": list(self.call_log),
            "ret": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: uc.reg_read(register)
                for name, register in CALLEE_SAVED.items()
            },
            "writes": sorted(
                write for write in self.writes
                if not STACK_ADDR <= write[0] < STACK_ADDR + STACK_SIZE
            ),
            "self": bytes(uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "globals": bytes(uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
            "bss": bytes(uc.mem_read(BSS_ADDR, BSS_SIZE)),
        }


# ---------------------------------------------------------------------------
# Case table
# ---------------------------------------------------------------------------
def build_cases() -> list[dict]:
    special_self_words = {
        0x5A4: 0x7FC00001,                          # quiet NaN payload
        0x5AC: 0x7F800001, 0x5B0: 0xFFC00002,       # sNaN, quiet NaN
        0x5B4: 0x80000000,                          # -0.0
        0x5DC: 0x7F7FFFFF,                          # max finite
        0x5E8: 0x00800000, 0x5EC: 0x00000001,       # min normal, denormal
        0x5F0: 0xFF800000, 0x5F4: 0x7F800000, 0x5F8: 0x807FFFFF,
        0x620: 0xFFC00003, 0x62C: 0x7FC00004, 0x630: 0xFF800001,
        0x658: 0x7F800002, 0x65C: 0xFFC00005, 0x660: 0x00000002,
        0x670: 0x7FC00006,
        0x698: 0xFFC00007, 0x6A8: 0x7F800003,
        0x6B8: 0xFFC00008,
        0x6CC: 0x80000001, 0x6D0: 0x007FFFFF, 0x6D4: 0xFF800004,
        0x6E4: 0x7FC00009, 0x6E8: 0xFFC0000A, 0x6EC: 0x7F800005,
        0x794: 0x7FC0000B, 0x798: 0xFFC0000C, 0x79C: 0x7F800006,
        0x7A4: 0xFFC0000D,
        0x7AC: 0x7FC0000E, 0x7B0: 0xFFC0000F, 0x7B4: 0x7F800007,
        0x7BC: 0xFFC00010,
        0x7C4: 0x7FC00011, 0x7C8: 0xFFC00012, 0x7CC: 0x7F800008,
        0x7D0: 0x7FC00013, 0x7D4: 0xFFC00014, 0x7D8: 0x7F800009,
        0x7E0: 0xFFC00015,
        0x7E8: 0x7FC00016, 0x7EC: 0xFFC00017, 0x7F0: 0x7F80000A,
        0x7F4: 0x7FC00018, 0x7F8: 0xFFC00019, 0x7FC: 0x7F80000B,
        0x800: 0x7FC0001A, 0x804: 0xFFC0001B, 0x808: 0x7F80000C,
        0x810: 0xFFC0001C,
        0x818: 0x7FC0001D, 0x81C: 0xFFC0001E, 0x820: 0x7F80000D,
        0x824: 0x7FC0001F, 0x828: 0xFFC00020, 0x82C: 0x7F80000E,
        0x830: 0x7FC00021, 0x834: 0xFFC00022, 0x838: 0x7F80000F,
        0x840: 0xFFC00023,
    }

    return [
        # -- gate combinations and both return paths ------------------------
        make_case("complete default", flags=0x00000000, value=2),
        make_case("pending bit only", flags=0x00200000, value=1),
        make_case("blocked", flags=0x00100000, value=1),
        make_case("blocked clears pending", flags=0x00300000, value=7),
        make_case("blocked all bits", flags=0xFFFFFFFF, value=-1),
        make_case("already started", flags=0x00000010, value=2),
        make_case("started and pending", flags=0x00200010, value=2),
        make_case("low bits only", flags=0x000FFFFF, value=2),
        make_case("high bit", flags=0x80000000, value=2),
        make_case("high bit blocked", flags=0x80100000, value=2),
        make_case("pending plus low bit", flags=0x00200001, value=2),

        # -- r2 argument boundaries, r1 must be ignored ---------------------
        make_case("r2 zero", flags=0, value=0),
        make_case("r2 one", flags=0, value=1),
        make_case("r2 minus one", flags=0, value=-1),
        make_case("r2 INT_MIN", flags=0, value=-0x80000000),
        make_case("r2 INT_MAX", flags=0, value=0x7FFFFFFF),
        make_case("r2 0xFFFFFFFF", flags=0, value=0xFFFFFFFF),
        make_case("r1 nonzero ignored", flags=0, value=3, arg1=0xFFFFFFFF),
        make_case("r1 nonzero ignored 2", flags=0, value=3, arg1=0x12345678),

        # -- page patterns ---------------------------------------------------
        make_case("zero pages", flags=0, value=5, self_fill=0x00,
                  global_fill=0x00, bss_fill=0x00, distinct=False),
        make_case("0xFF pages", flags=0, value=-5, self_fill=0xFF,
                  global_fill=0xFF, bss_fill=0xFF, distinct=False),
        make_case("NaN and denormal bits", flags=0, value=4,
                  self_words=special_self_words),
        make_case("special bits blocked", flags=0x00100000, value=4,
                  self_words=special_self_words),
    ]


# ---------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------
COMPARE_KEYS = (
    "ret", "pc", "sp", "callee_saved", "call_log", "writes",
    "self", "globals", "bss",
)


def compare(orig: dict, cand: dict, name: str) -> None:
    for key in COMPARE_KEYS:
        if orig[key] != cand[key]:
            raise AssertionError(
                f"{key} mismatch on {name}:\n"
                f"  Orig: {orig[key]!r}\n  Cand: {cand[key]!r}"
            )


def check_expected(case: dict, result: dict) -> None:
    ret, page, glob, bss = expected_run(case)
    assert result["ret"] == ret, (
        f"r0 mismatch on {case['name']}: 0x{result['ret']:08X} != 0x{ret:08X}"
    )
    for key, expected, base in (
        ("self", page, 0),
        ("globals", glob, GLOBAL_ADDR),
        ("bss", bss, BSS_ADDR),
    ):
        actual = result[key]
        if actual != expected:
            differing = [
                index for index in range(len(expected))
                if actual[index] != expected[index]
            ]
            raise AssertionError(
                f"{key} page mismatch on {case['name']} at "
                f"{[hex(base + index) for index in differing[:16]]}"
            )


# ---------------------------------------------------------------------------
# Negative controls
# ---------------------------------------------------------------------------
def build_mutants() -> list[tuple[str, str, str]]:
    return [
        (
            "clear_mask",
            "constexpr u32 kClearPendingFlag = 0x00200000;",
            "constexpr u32 kClearPendingFlag = 0x00100000;",
        ),
        (
            "gate_mask",
            "constexpr u32 kBlockedFlag = 0x00100000;",
            "constexpr u32 kBlockedFlag = 0x00200000;",
        ),
        (
            "gate_removed",
            "if ((flags & kBlockedFlag) != 0) {",
            "if ((flags & kBlockedFlag) != 0 && false) {",
        ),
        (
            "snapshot_direction",
            "ctx->field_798 = ctx->field_794;",
            "ctx->field_794 = ctx->field_798;",
        ),
        (
            "vector_snapshot_lane",
            "ctx->field_7f4[1] = ctx->field_7e8[1];",
            "ctx->field_7f4[1] = ctx->field_7e8[2];",
        ),
        (
            "base_620_source",
            "ctx->base_620 = ctx->value_698;",
            "ctx->base_620 = ctx->value_6a8;",
        ),
        (
            "global_snapshot_address",
            "constexpr u32 kGlobalSnapshotAddress = 0x004342F4;",
            "constexpr u32 kGlobalSnapshotAddress = 0x004342F0;",
        ),
        (
            "global_scalar_address",
            "constexpr u32 kGlobalScalarAddress = 0x004342F8;",
            "constexpr u32 kGlobalScalarAddress = 0x004342FC;",
        ),
        (
            "track_a_base",
            "constexpr u32 kTrackABase = 0x00493518;",
            "constexpr u32 kTrackABase = 0x0049351C;",
        ),
        (
            "track_b_target",
            "constexpr u32 kTrackBTarget = 0x0049353C;",
            "constexpr u32 kTrackBTarget = 0x00493540;",
        ),
        (
            "started_flag",
            "const u32 updated = ctx->flags_634 | kStartedFlag;",
            "const u32 updated = ctx->flags_634;",
        ),
        (
            "timer_constant",
            "ctx->field_684 = 1;",
            "ctx->field_684 = 2;",
        ),
        (
            "limit_argument",
            "ctx->field_680 = value;",
            "ctx->field_680 = 0;",
        ),
        (
            "track_b_lane_source",
            "track_b_base[0] = ctx->value_6e4[0];",
            "track_b_base[0] = ctx->value_6cc[0];",
        ),
        (
            "dropped_counter_zero",
            "    ctx->field_7a4 = 0;\n",
            "\n",
        ),
        (
            "duplicate_target_lane",
            "ctx->target_5ac[1] = 0.0f;",
            "ctx->target_5ac[2] = 0.0f;",
        ),
    ]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    print("Testing func_003d88cc (0x003D88CC)...")
    candidate = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(candidate)} B")

    cases = build_cases()
    machine = Machine()
    results = {}
    passed = 0
    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(candidate, case)
        compare(res_orig, res_cand, case["name"])
        check_expected(case, res_orig)
        check_expected(case, res_cand)
        assert res_orig["call_log"] == [] and res_cand["call_log"] == [], (
            f"unexpected call on {case['name']}"
        )
        assert res_orig["pc"] == TRAP_ADDR, (
            f"original did not stop at trap on {case['name']}"
        )
        assert res_cand["pc"] == TRAP_ADDR, (
            f"candidate did not stop at trap on {case['name']}"
        )
        assert res_orig["sp"] == res_cand["sp"] == ENTRY_SP, (
            f"SP mismatch on {case['name']}"
        )
        results[case["name"]] = res_orig
        passed += 1
        print(f"  [PASS] {case['name']}  "
              f"(r0=0x{res_orig['ret']:08X}, "
              f"{len(res_orig['writes'])} stores)")

    print("\nNegative controls:")
    mutants = build_mutants()
    detected = 0
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        witness = None
        for case in cases:
            res_mut = machine.run(mutant, case)
            if any(results[case["name"]][key] != res_mut[key]
                   for key in COMPARE_KEYS):
                witness = case["name"]
                break
        if witness is None:
            raise AssertionError(f"mutant {name} was not detected")
        detected += 1
        print(f"  [DETECTED] {name} (case: {witness})")

    print(f"\nResult: {passed}/{len(cases)} differential cases passed; "
          f"{detected}/{len(mutants)} negative controls detected.")


if __name__ == "__main__":
    main()
