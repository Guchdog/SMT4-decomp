#!/usr/bin/env python3
"""Differential test for ui_func_002e03ec (0x002e03ec) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the ui_func_002e03ec body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11, saved d8;
  * the ordered call log with every register argument of each helper, including
    the twelve float single-precision arguments (s0..s11) of 0x29705C;
  * the return value of each applied flush callback and the callback target
    selected from the render-stack node;
  * the full observable pages: render-stack node page, type-7 record page and
    its count word, palette page, render-register global page;
  * every non-stack write (address, width, value), as a sorted multiset.

Coverage: record count 0 (early return, null render base), negative signed
counts, 1/2/12/13 records (palette wrap), records with NaN/Inf/-0.0 fields,
zero/non-zero helper result, render-stack counts 0/1/8 (slots past the four
visible ones), dirty-only push, previous-top mismatch, pop-only callback forced
by a draw helper, draw helper shrinking/growing the record count (re-read
bound), draw helper rebasing the render-register global before the pop, and
incoming vertical offsets including signed, zero, +-100 and NaN.

Negative controls mutate the palette command bits, the vertical step, the
record stride and the palette address; each mutant must be detected.
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
SOURCE = ROOT / "src/engine/leaf_batch41_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_002e03ec"

FUNC_ADDR = 0x002E03EC
FUNC_SIZE = 424

# Code is mapped from 0x00200000 so that the function (0x002E03EC) and every
# direct-call stub (0x0029705C, 0x002C1D3C, 0x002C5F7C, 0x002D4000) fit.
CODE_ADDR = 0x00200000
CODE_SIZE = 0x00200000  # 0x00200000..0x00400000

PALETTE_ADDR = 0x00404000
PALETTE_SIZE = 0x00001000

GLOBALS_ADDR = 0x0044E000   # 0x0044EA00: render-register base pointer
GLOBALS_SIZE = 0x00001000

RECORD_PAGE_ADDR = 0x004BF000  # 0x004BF89C records, 0x004C149C count
RECORD_PAGE_SIZE = 0x00003000

NODE_PAGE_ADDR = 0x00720000   # render base; node at +0x124C
NODE_PAGE_SIZE = 0x00010000

STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Addresses referenced by the function (absolute, in the pinned image).
PALETTE_ENTRIES_ADDR = 0x004049E4   # 0x004049B4 + 0x30, copied to the stack
PALETTE_BASE_ADDR = 0x004049B4      # decoy table: must not be read
RENDER_BASE_PTR_ADDR = 0x0044EA00   # g_RenderRegisterBase
RECORD_BASE = 0x004BF89C
RECORD_COUNT_ADDR = 0x004C149C
RECORD_STRIDE = 0x1C
NODE_OFFSET = 0x124C
SECOND_BASE_OFFSET = 0x2000

# Stub addresses.  Stubs are placed at the original direct-call targets so both
# the original bytes and the relocated candidate resolve to them.
STUB_2C5F7C = 0x002C5F7C   # viewport-command builder
STUB_2C1D3C = 0x002C1D3C   # render-mode selector
STUB_29705C = 0x0029705C   # four-corner element submit
CALLBACK_A = 0x002D4000
CALLBACK_B = 0x002D4100

STUB_NAMES = {
    STUB_2C5F7C: "ui_func_002c5f7c",
    STUB_2C1D3C: "ui_func_002c1d3c",
    STUB_29705C: "func_0029705c",
}
CALLBACK_NAMES = {CALLBACK_A: "flush_a", CALLBACK_B: "flush_b"}

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
D8_START = 0x1122334455667788

# The built viewport command for (5, 1) used by the deterministic stub below.
PUSHED_DEFAULT = 0x1F510000 | (5 << 8) | 1


def pushed_value(case: dict) -> int:
    if case.get("push_zero", False):
        return 0
    raw = case.get("push_value")
    if raw is not None:
        return raw & 0xFFFFFFFF
    return PUSHED_DEFAULT


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def elf_sections(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    e_shoff = struct.unpack_from("<I", data, 32)[0]
    e_shentsize = struct.unpack_from("<H", data, 46)[0]
    e_shnum = struct.unpack_from("<H", data, 48)[0]
    e_shstrndx = struct.unpack_from("<H", data, 50)[0]
    sections = [
        struct.unpack_from("<IIIIIIIIII", data, e_shoff + i * e_shentsize)
        for i in range(e_shnum)
    ]
    shstr = sections[e_shstrndx]
    shstrtab = data[shstr[4] : shstr[4] + shstr[5]]
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002e03ec" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_002e03ec not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address in STUB_NAMES:
                if f"{address:08x}" in rel.symbol_name.lower():
                    target = address
                    break
            if target is None:
                raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            displacement = (target - pc) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 to g_RenderRegisterBase
            if "RenderRegisterBase" not in rel.symbol_name:
                raise RuntimeError(f"unexpected ABS32 relocation: {rel.symbol_name}")
            struct.pack_into("<I", code, rel.offset, RENDER_BASE_PTR_ADDR)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    # The candidate does not reference .rodata; keep the check for completeness.
    rodata = elf_sections(obj_file).get(".rodata.str1.1", b"")
    if rodata:
        raise RuntimeError("unexpected .rodata reference in the candidate")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    obj_file = OUT_DIR / f"mutant_{name}.o"
    res = compile_tu_armv6k(mutant_src, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Mutant compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


# ------------------------------------------------------------------ fixtures
DEFAULT_RECORD_WORDS = (0x3F800000, 0xC0200000, 0x40490FDB, 0x42C80000)


def render_base(case: dict) -> int:
    return NODE_PAGE_ADDR


def build_node_page(case: dict) -> bytes:
    page = bytearray(b"\xCC" * NODE_PAGE_SIZE)
    pushed = pushed_value(case)
    slot_count = case.get("slot_count", 1)
    overrides = case.get("slots", {})
    for index in range(slot_count + 2):
        value = overrides.get(index, pushed)
        struct.pack_into("<I", page, NODE_OFFSET + 0x08 + index * 4, value)
    page[NODE_OFFSET + 0x18] = case.get("dirty", 0) & 0xFF
    callback = CALLBACK_B if case.get("callback_b", False) else CALLBACK_A
    struct.pack_into("<I", page, NODE_OFFSET + 0x1C, callback)
    struct.pack_into("<I", page, NODE_OFFSET + 0x00, slot_count & 0xFFFFFFFF)

    # Second node (base + 0x2000) used by the rebase case.
    second = SECOND_BASE_OFFSET + NODE_OFFSET
    second_count = case.get("second_count", 1)
    second_overrides = case.get("second_slots", {})
    second_pushed = case.get("second_slot_default", pushed)
    for index in range(second_count + 2):
        value = second_overrides.get(index, second_pushed)
        struct.pack_into("<I", page, second + 0x08 + index * 4, value)
    page[second + 0x18] = case.get("second_dirty", 0) & 0xFF
    struct.pack_into("<I", page, second + 0x1C, callback)
    struct.pack_into("<I", page, second + 0x00, second_count & 0xFFFFFFFF)
    return bytes(page)


def build_record_page(case: dict) -> bytes:
    page = bytearray(b"\x5A" * RECORD_PAGE_SIZE)
    count = case["count"]
    records = case.get("records")
    for index in range(max(0, min(count, 32))):
        words = records[index] if records else DEFAULT_RECORD_WORDS
        base = (RECORD_BASE - RECORD_PAGE_ADDR) + index * RECORD_STRIDE
        struct.pack_into("<I", page, base + 0x00, words[0] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x08, words[1] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x0C, words[2] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x14, words[3] & 0xFFFFFFFF)
        page[base + 0x04] = 0x7F
        page[base + 0x05] = 0x7F
        page[base + 0x18] = 0x7F
    struct.pack_into(
        "<i", page, RECORD_COUNT_ADDR - RECORD_PAGE_ADDR, count
    )
    return bytes(page)


def build_palette_page(case: dict) -> bytes:
    page = bytearray(b"\xA7" * PALETTE_SIZE)
    for index in range(12):
        struct.pack_into(
            "<I", page, PALETTE_ENTRIES_ADDR - PALETTE_ADDR + index * 4,
            (0xA5A50000 | index) & 0xFFFFFFFF,
        )
        struct.pack_into(
            "<I", page, PALETTE_BASE_ADDR - PALETTE_ADDR + index * 4,
            (0x5A5A0000 | index) & 0xFFFFFFFF,
        )
    return bytes(page)


def build_globals_page(case: dict) -> bytes:
    page = bytearray(b"\x33" * GLOBALS_SIZE)
    if not case.get("null_render_base", False):
        struct.pack_into(
            "<I", page, RENDER_BASE_PTR_ADDR - GLOBALS_ADDR, render_base(case)
        )
    return bytes(page)


class E03ECRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Enable the VFP/NEON unit (the function saves d8 and uses s16).
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        for address, size in (
            (CODE_ADDR, CODE_SIZE),
            (PALETTE_ADDR, PALETTE_SIZE),
            (GLOBALS_ADDR, GLOBALS_SIZE),
            (RECORD_PAGE_ADDR, RECORD_PAGE_SIZE),
            (NODE_PAGE_ADDR, NODE_PAGE_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(address, size)

        for address in list(STUB_NAMES) + [CALLBACK_A, CALLBACK_B]:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.draw_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    def _log(self, address: int, *args) -> None:
        if address in CALLBACK_NAMES:
            name = CALLBACK_NAMES[address]
        else:
            name = STUB_NAMES[address]
        self.call_log.append((name, args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value & 0xFFFFFFFFFFFFFFFF))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_2C5F7C:
            self._log(address, r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, pushed_value(self.case))
        elif address == STUB_2C1D3C:
            self._log(address, r0, r1)
        elif address == STUB_29705C:
            floats = tuple(
                uc.reg_read(getattr(arm, f"UC_ARM_REG_S{i}")) for i in range(12)
            )
            self._log(address, r0, r1, r2, r3, *floats)
            self.draw_index += 1
            self._after_draw()
        elif address in CALLBACK_NAMES:
            # Only r0 is architected for the flush callback; r1 is the callback
            # pointer and r2/r3 are internal scratch values.
            self._log(address, r0)
            if address == CALLBACK_A:
                uc.reg_write(arm.UC_ARM_REG_R0, (0xC0DE0000 | (r0 & 0xFFFF)) ^ 0xA5)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, (0xBEEF0000 | (r0 & 0xFFFF)) ^ 0x5A)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _after_draw(self) -> None:
        case = self.case
        if case.get("draw_sets_dirty", False):
            self.uc.mem_write(NODE_PAGE_ADDR + NODE_OFFSET + 0x18, b"\x01")
        if case.get("draw_rebase", False):
            self.uc.mem_write(
                RENDER_BASE_PTR_ADDR,
                struct.pack("<I", NODE_PAGE_ADDR + SECOND_BASE_OFFSET),
            )
        shrink_after = case.get("draw_shrink_after")
        if shrink_after is not None and self.draw_index == shrink_after:
            self.uc.mem_write(
                RECORD_COUNT_ADDR, struct.pack("<i", case["draw_shrink_to"])
            )
        grow_after = case.get("draw_grow_after")
        if grow_after is not None and self.draw_index == grow_after:
            self.uc.mem_write(
                RECORD_COUNT_ADDR, struct.pack("<i", case["draw_grow_to"])
            )

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.draw_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(PALETTE_ADDR, build_palette_page(case))
        self.uc.mem_write(GLOBALS_ADDR, build_globals_page(case))
        self.uc.mem_write(RECORD_PAGE_ADDR, build_record_page(case))
        self.uc.mem_write(NODE_PAGE_ADDR, build_node_page(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        vertical_offset = case.get("vertical_offset", 0.0)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x33333333)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x44444444)
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(vertical_offset))
        self.uc.reg_write(arm.UC_ARM_REG_D8, D8_START)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        non_stack_writes = sorted(
            (address, size, value)
            for address, size, value in self.writes
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE)
        )

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "d8": self.uc.reg_read(arm.UC_ARM_REG_D8),
            "call_log": list(self.call_log),
            "fixtures": {
                "node": bytes(self.uc.mem_read(NODE_PAGE_ADDR, NODE_PAGE_SIZE)),
                "records": bytes(
                    self.uc.mem_read(RECORD_PAGE_ADDR, RECORD_PAGE_SIZE)
                ),
                "palette": bytes(self.uc.mem_read(PALETTE_ADDR, PALETTE_SIZE)),
                "globals": bytes(self.uc.mem_read(GLOBALS_ADDR, GLOBALS_SIZE)),
            },
            "non_stack_writes": non_stack_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "callee_saved", "d8"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
    for key, value in orig["fixtures"].items():
        if value != cand["fixtures"][key]:
            first = next(
                (i for i, (a, b) in enumerate(zip(value, cand["fixtures"][key])) if a != b),
                None,
            )
            problems.append(
                f"fixture {key} was modified differently (first differing "
                f"byte at page offset {first})"
            )
    if orig["non_stack_writes"] != cand["non_stack_writes"]:
        problems.append(
            "non-stack writes:\n    orig="
            + repr(orig["non_stack_writes"])
            + "\n    cand="
            + repr(cand["non_stack_writes"])
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count": 1,
        "slot_count": 1,
        "dirty": 0,
        "vertical_offset": 0.0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- count == 0 early return, including a null render base
    cases.append(base_case("count 0 early return", count=0))
    cases.append(
        base_case("count 0 with null render base", count=0, null_render_base=True)
    )

    # --- one record, every push/pop callback combination
    cases.append(base_case("1 record, no callbacks (matching top)"))
    cases.append(
        base_case(
            "1 record, top mismatch -> push+pop callbacks",
            slots={1: 0x12345678},
        )
    )
    cases.append(
        base_case("1 record, dirty-only push callback", dirty=1)
    )
    cases.append(
        base_case("1 record, dirty and mismatch", dirty=0xFF, slots={1: 0}),
        )
    cases.append(
        base_case("1 record, callback B target", callback_b=True,
                  slots={1: 0xDEADBEEF})
    )
    cases.append(
        base_case("1 record, pop-only callback via draw dirty",
                  draw_sets_dirty=True)
    )

    # --- zero / non-zero helper results
    cases.append(base_case("push result 0, matching top", push_zero=True,
                           slots={1: 0}))
    cases.append(base_case("push result 0, top mismatch", push_zero=True,
                           slots={1: 0x12345678}))
    cases.append(base_case("push result 0xFFFFFFFF", push_value=0xFFFFFFFF))

    # --- render-stack slot boundaries
    cases.append(base_case("stack count 0", slot_count=0, slots={0: PUSHED_DEFAULT}))
    cases.append(
        base_case(
            "stack count 8 (past visible slots)",
            slot_count=8,
            slots={8: 0xAAAA5555},
        )
    )
    cases.append(
        base_case(
            "stack count 12, matching top",
            slot_count=12,
            slots={12: PUSHED_DEFAULT},
        )
    )

    # --- record counts: signed bound and palette wrap
    cases.append(base_case("2 records", count=2))
    cases.append(base_case("12 records (full palette)", count=12))
    cases.append(base_case("13 records (palette wraps)", count=13))
    cases.append(base_case("count -1 (no draws)", count=-1))
    cases.append(base_case("count INT_MIN (no draws)", count=-0x80000000))

    # --- record field bit patterns (float payloads are copied verbatim)
    cases.append(
        base_case(
            "record fields NaN/Inf/-0.0",
            records=[(0x7FC00000, 0x7F800000, 0xFF800000, 0x80000000)],
        )
    )
    cases.append(
        base_case(
            "record fields subnormal/huge",
            records=[(0x00000001, 0x7F7FFFFF, 0x00800000, 0xFFFFFFFF)],
        )
    )

    # --- incoming vertical offset, including the +100 step boundaries
    for offset in (0.0, 100.0, -100.0, 1.5, -1.5, 1e9, -1e9):
        cases.append(
            base_case(f"vertical offset {offset}", vertical_offset=offset)
        )
    cases.append(
        base_case("vertical offset NaN", vertical_offset=float("nan"))
    )

    # --- loop bound is re-read and follows helper-induced changes
    cases.append(
        base_case(
            "draw helper shrinks count to 2",
            count=4,
            draw_shrink_after=2,
            draw_shrink_to=2,
        )
    )
    cases.append(
        base_case(
            "draw helper grows count to 2",
            count=1,
            draw_grow_after=1,
            draw_grow_to=2,
        )
    )
    cases.append(
        base_case(
            "draw helper shrinks count negative",
            count=3,
            draw_shrink_after=1,
            draw_shrink_to=-5,
        )
    )

    # --- the render-register global is re-read for the pop
    cases.append(
        base_case(
            "draw helper rebases to second node",
            count=2,
            draw_rebase=True,
            second_count=1,
            second_slots={1: 0x0BADF00D},
        )
    )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = E03ECRunner().run(orig_code, case)
        cand = E03ECRunner().run(cand_code, case)
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
    print("Testing ui_func_002e03ec (0x002e03ec)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        f"(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        (
            "palette_command_bits",
            "constexpr u32 kPaletteCommandBits = 0x70;",
            "constexpr u32 kPaletteCommandBits = 0x71;",
        ),
        (
            "vertical_step",
            "constexpr f32 kPaletteVerticalStep = 100.0f;",
            "constexpr f32 kPaletteVerticalStep = 101.0f;",
        ),
        (
            "record_stride",
            "constexpr u32 kType7RecordStride = 0x1C;",
            "constexpr u32 kType7RecordStride = 0x20;",
        ),
        (
            "palette_address",
            "constexpr u32 kPaletteAddress = 0x004049E4;",
            "constexpr u32 kPaletteAddress = 0x004049B4;",
        ),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = E03ECRunner().run(orig_code, case)
            bad = E03ECRunner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
