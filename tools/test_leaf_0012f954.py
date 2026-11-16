#!/usr/bin/env python3
"""Differential test for engine_func_0012f954 (0x0012f954) using Unicorn ARM.

Compiles src/engine/leaf_batch34_c.cpp, extracts the engine_func_0012f954 body,
resolves its seven direct-call targets to deterministic stubs placed at the
original addresses, and runs the pinned original (extracted/exefs/code.bin)
against the candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every register argument (the two stack out-pointers
    of 0x0013FE4C / 0x001419BC are normalised to "<stack>");
  * the cursor value 0x0013FE4C observes, proving r2 was seeded with the buffer
    argument, plus the exact seven size words handed to the body;
  * the full self page and the full node/list page, and the untouched buffer;
  * any emulated write outside the private stack, self and node pages.

Coverage: plan-parse failure, size-read failure, every region's size-check
failure (A/B/C/tail) at the exact boundary and one byte over, zero/one/many
counts in every region, null and non-null converter results, the null record
pointer (`r4 == 0`) path, multiplicative wrap of every stride (including
`word * stride == 0` and `== stride`), unaligned plan cursors, zero buffer and
zero length, source/buffer echo, and a signed-comparison wrap that passes only
because the original compares `(s32)(end - limit)`.
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
SOURCE = ROOT / "src/engine/leaf_batch34_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0012f954"

FUNC_ADDR = 0x0012F954
FUNC_SIZE = 672

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00200000  # covers the body and every stub below 0x00300000
SELF_ADDR = 0x00800000
SELF_SIZE = 0x00001000
NODE_ADDR = 0x00810000
NODE_SIZE = 0x00040000
BUFFER_ADDR = 0x00900000
BUFFER_SIZE = 0x00200000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_13FE4C = 0x0013FE4C
STUB_1419BC = 0x001419BC
STUB_1401CC = 0x001401CC
STUB_140AB0 = 0x00140AB0
STUB_140110 = 0x00140110
STUB_2BF774 = 0x002BF774
STUB_2B5064 = 0x002B5064

STUB_NAMES = {
    STUB_13FE4C: "plan_parse_0013fe4c",
    STUB_1419BC: "read_layer_sizes_001419bc",
    STUB_1401CC: "build_layer_a_node_001401cc",
    STUB_140AB0: "build_layer_b_node_00140ab0",
    STUB_140110: "build_layer_c_node_00140110",
    STUB_2BF774: "link_layer_node_002bf774",
    STUB_2B5064: "select_layer_tail_002b5064",
}

# Candidate relocation symbol fragment -> stub address.
CALL_TARGETS = {
    "0013fe4c": STUB_13FE4C,
    "001419bc": STUB_1419BC,
    "001401cc": STUB_1401CC,
    "00140ab0": STUB_140AB0,
    "00140110": STUB_140110,
    "002bf774": STUB_2BF774,
    "002b5064": STUB_2B5064,
}

# Offsets inside the candidate's LayerPlanState, used to seed lists.
SELF_SOURCE = 0x04
SELF_A_COUNT = 0x3C
SELF_A_HEAD = 0x40
SELF_B_COUNT = 0x5C
SELF_B_HEAD = 0x60
SELF_C_COUNT = 0x7C
SELF_C_HEAD = 0x80
SELF_BUFFER = 0xB4
SELF_LENGTH = 0xB8

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


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0012f954" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_0012f954 not found in {obj_file}: {sorted(funcs)}"
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
        for fragment, address in CALL_TARGETS.items():
            if fragment in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = (target - pc) >> 2
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into("<I", code, rel.offset, cond | (displacement & 0x00FFFFFF))
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch34_c.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
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


def pattern_byte(index: int, seed: int) -> int:
    return (index * 7 + seed) & 0xFF


class Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(BUFFER_ADDR, BUFFER_SIZE)
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
        self.converter_index = 0
        self.case: dict = {}

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _norm(value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_13FE4C:
            seeded = struct.unpack("<I", uc.mem_read(r2, 4))[0]
            self.call_log.append(
                (STUB_NAMES[address], r0, r1, self._norm(r2), r3, seeded)
            )
            if self.case.get("plan_ok", True):
                cursor = self.case["plan_cursor"]
                uc.mem_write(r2, struct.pack("<I", cursor))
                # Real 0x0013FE4C publishes the header count/base at self+0x20/24.
                uc.mem_write(
                    r0 + 0x20,
                    struct.pack(
                        "<II",
                        self.case.get("plan_word20", 0x13FE4C20),
                        self.case.get("plan_word24", 0x13FE4C24),
                    ),
                )
                uc.reg_write(arm.UC_ARM_REG_R0, 1)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            return

        if address == STUB_1419BC:
            self.call_log.append((STUB_NAMES[address], r0, self._norm(r1)))
            if self.case.get("sizes_ok", True):
                uc.mem_write(r1, struct.pack("<7I", *self.case["sizes"]))
                uc.reg_write(arm.UC_ARM_REG_R0, 1)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            return

        if address in (STUB_1401CC, STUB_140AB0, STUB_140110):
            region_base = struct.unpack("<I", uc.mem_read(r1, 4))[0]
            region_size = struct.unpack("<I", uc.mem_read(r1 + 4, 4))[0]
            self.call_log.append(
                (STUB_NAMES[address], r0, r1, region_base, region_size)
            )
            null_key = {
                STUB_1401CC: "null_a",
                STUB_140AB0: "null_b",
                STUB_140110: "null_c",
            }[address]
            if self.case.get(null_key, False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                node = NODE_ADDR + self.converter_index * 0x40
                self.converter_index += 1
                uc.reg_write(arm.UC_ARM_REG_R0, node)
            return

        if address == STUB_2BF774:
            self.call_log.append((STUB_NAMES[address], r0, r1, r2))
            count = struct.unpack("<I", uc.mem_read(r0, 4))[0]
            uc.mem_write(r0, struct.pack("<I", (count + 1) & 0xFFFFFFFF))
            node = r2
            if NODE_ADDR <= node < NODE_ADDR + NODE_SIZE - 8:
                old_tail = struct.unpack("<I", uc.mem_read(r1 + 4, 4))[0]
                uc.mem_write(node, struct.pack("<II", r1, old_tail))
                uc.mem_write(r1 + 4, struct.pack("<I", node))
                if (
                    SELF_ADDR <= old_tail < SELF_ADDR + SELF_SIZE - 4
                    or NODE_ADDR <= old_tail < NODE_ADDR + NODE_SIZE - 4
                ):
                    uc.mem_write(old_tail, struct.pack("<I", node))
            uc.reg_write(arm.UC_ARM_REG_R0, node)
            return

        if address == STUB_2B5064:
            state = r0 - 0xA4
            source = struct.unpack("<I", uc.mem_read(state + 0x04, 4))[0]
            buffer_arg = struct.unpack("<I", uc.mem_read(state + 0xB4, 4))[0]
            length_arg = struct.unpack("<I", uc.mem_read(state + 0xB8, 4))[0]
            # These three fields are stored only after the tail call returns;
            # logging them at call time pins that ordering.
            self.call_log.append(
                (STUB_NAMES[address], r0, source, buffer_arg, length_arg)
            )
            uc.reg_write(arm.UC_ARM_REG_R0, (r0 + 8) & 0xFFFFFFFF)
            uc.reg_write(arm.UC_ARM_REG_R3, 0x000000CC)
            return

        raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict, stack_poison: int) -> dict:
        self.call_log = []
        self.writes = []
        self.converter_index = 0
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)

        self.uc.mem_write(
            SELF_ADDR, bytes(pattern_byte(i, 0x33) for i in range(SELF_SIZE))
        )
        self.uc.mem_write(
            NODE_ADDR, bytes(pattern_byte(i, 0x77) for i in range(NODE_SIZE))
        )
        self.uc.mem_write(
            BUFFER_ADDR, bytes(pattern_byte(i, 0x11) for i in range(BUFFER_SIZE))
        )
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        # Circular list sentinels and zero counters for each region.
        for count_off, head_off in (
            (SELF_A_COUNT, SELF_A_HEAD),
            (SELF_B_COUNT, SELF_B_HEAD),
            (SELF_C_COUNT, SELF_C_HEAD),
        ):
            self.uc.mem_write(SELF_ADDR + count_off, struct.pack("<I", 0))
            self.uc.mem_write(SELF_ADDR + head_off, struct.pack("<I", SELF_ADDR + head_off))

        # Poison the caller argument area above the entry SP.  The two machines
        # use different values, so any read of a fifth argument would diverge.
        self.uc.mem_write(ENTRY_SP, struct.pack("<IIII", stack_poison, stack_poison,
                                                stack_poison, stack_poison))

        self.writes = []
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["source"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["buffer"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["length"] & 0xFFFFFFFF)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for addr, size in self.writes:
            in_stack = STACK_ADDR <= addr < STACK_ADDR + STACK_SIZE
            in_self = SELF_ADDR <= addr < SELF_ADDR + SELF_SIZE
            in_node = NODE_ADDR <= addr < NODE_ADDR + NODE_SIZE
            if not (in_stack or in_self or in_node):
                unexpected_writes.append((addr, size))

        buffer_view = b""
        if case["buffer"] == BUFFER_ADDR:
            buffer_view = bytes(self.uc.mem_read(BUFFER_ADDR, 0x400))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "self_page": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
            "node_page": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
            "buffer_view": buffer_view,
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
    if orig["self_page"] != cand["self_page"]:
        offset = next(
            i
            for i, (a, b) in enumerate(zip(orig["self_page"], cand["self_page"]))
            if a != b
        )
        problems.append(f"self page differs first at +0x{offset:x}")
    if orig["node_page"] != cand["node_page"]:
        offset = next(
            i
            for i, (a, b) in enumerate(zip(orig["node_page"], cand["node_page"]))
            if a != b
        )
        problems.append(f"node page differs first at +0x{offset:x}")
    if orig["buffer_view"] != cand["buffer_view"]:
        problems.append("buffer page was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "source": 0x1234ABCD,
        "buffer": BUFFER_ADDR,
        "length": 0x00100000,
        "plan_ok": True,
        "plan_cursor": None,
        "sizes_ok": True,
        "sizes": [0, 0, 0, 0, 0, 0, 0],
        "null_a": False,
        "null_b": False,
        "null_c": False,
        "expect_ret": 1,
    }
    case.update(overrides)
    cursor = case["plan_cursor"]
    if cursor is None:
        cursor = (case["buffer"] + 0x100) & 0xFFFFFFFF
    case["plan_cursor"] = cursor
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- first helper: plan parse rejection / acceptance -------------------
    cases.append(base_case("plan parse fails", plan_ok=False, expect_ret=0))
    cases.append(base_case("size read fails", sizes_ok=False))
    cases.append(base_case("all sizes zero"))

    # --- full success with multi-element loops ----------------------------
    cases.append(base_case("counts A2 B1 C1 D1",
                           sizes=[2, 1, 1, 0, 0, 1, 0]))
    cases.append(base_case("counts A3 B3 C2 D2",
                           sizes=[3, 2, 2, 0, 0, 3, 0]))
    cases.append(base_case("only tail size", sizes=[0, 1, 0, 0, 0, 0, 0]))
    cases.append(base_case("counts with zero tail", sizes=[1, 0, 1, 0, 0, 1, 0]))

    # --- each region's signed size check ----------------------------------
    # Plan cursor is buffer+0x100; A occupies 0x558, B 0x460, C 0x2BD4, D 0xCC.
    cases.append(base_case("region A exact fit", buffer=BUFFER_ADDR,
                           length=0x100 + 0x558, sizes=[1, 0, 0, 0, 0, 0, 0],
                           expect_ret=1))
    cases.append(base_case("region A one byte over", buffer=BUFFER_ADDR,
                           length=0x100 + 0x558 - 1,
                           sizes=[1, 0, 0, 0, 0, 0, 0], expect_ret=0))
    cases.append(base_case("region B exact fit", buffer=BUFFER_ADDR,
                           length=0x100 + 0x460, sizes=[0, 0, 0, 0, 0, 1, 0],
                           expect_ret=1))
    cases.append(base_case("region B one byte over", buffer=BUFFER_ADDR,
                           length=0x100 + 0x460 - 1,
                           sizes=[0, 0, 0, 0, 0, 1, 0], expect_ret=0))
    cases.append(base_case("region C exact fit", buffer=BUFFER_ADDR,
                           length=0x100 + 0x2BD4, sizes=[0, 0, 1, 0, 0, 0, 0],
                           expect_ret=1))
    cases.append(base_case("region C one byte over", buffer=BUFFER_ADDR,
                           length=0x100 + 0x2BD4 - 1,
                           sizes=[0, 0, 1, 0, 0, 0, 0], expect_ret=0))
    cases.append(base_case("tail exact fit", buffer=BUFFER_ADDR,
                           length=0x100 + 0xCC, sizes=[0, 1, 0, 0, 0, 0, 0],
                           expect_ret=1))
    cases.append(base_case("tail one byte over", buffer=BUFFER_ADDR,
                           length=0x100 + 0xCC - 1,
                           sizes=[0, 1, 0, 0, 0, 0, 0], expect_ret=0))
    # A fits, B fails: A's {base,size} must still be published.
    cases.append(base_case("B fails after A fits", buffer=BUFFER_ADDR,
                           length=0x100 + 0x100,
                           sizes=[0, 0, 0, 0, 0, 1, 0], expect_ret=0))
    # A/B fit, C fails.
    cases.append(base_case("C fails after A/B fit", buffer=BUFFER_ADDR,
                           length=0x100 + 0x100,
                           sizes=[0, 0, 1, 0, 0, 0, 0], expect_ret=0))
    # A/B/C fit, tail fails.
    cases.append(base_case("tail fails after A/B/C fit", buffer=BUFFER_ADDR,
                           length=0x100 + 0x40,
                           sizes=[0, 1, 0, 0, 0, 0, 0], expect_ret=0))

    # --- null converter results and the null record pointer ---------------
    cases.append(base_case("all converters null",
                           sizes=[1, 1, 1, 0, 0, 1, 0],
                           null_a=True, null_b=True, null_c=True))
    cases.append(base_case("mixed null converters",
                           sizes=[2, 1, 1, 0, 0, 1, 0],
                           null_a=True, null_b=False, null_c=True))
    cases.append(base_case("null record pointer A", buffer=BUFFER_ADDR,
                           plan_cursor=0, sizes=[1, 0, 0, 0, 0, 0, 0]))

    # --- multiplicative wrap of every stride ------------------------------
    # 0x20000001 * 0x558 == 0x558 (mod 2^32) -> one element.
    cases.append(base_case("A multiply wraps to one stride",
                           sizes=[0x20000001, 0, 0, 0, 0, 0, 0]))
    # 0x20000000 * 0x558 == 0 (mod 2^32) -> zero elements.
    cases.append(base_case("A multiply wraps to zero",
                           sizes=[0x20000000, 0, 0, 0, 0, 0, 0]))
    # 0x08000001 * 0x460 == 0x460 (mod 2^32).
    cases.append(base_case("B multiply wraps to one stride",
                           sizes=[0, 0, 0, 0, 0, 0x08000001, 0]))
    # 0x40000001 * 0x2BD4 == 0x2BD4 (mod 2^32).
    cases.append(base_case("C multiply wraps to one stride",
                           sizes=[0, 0, 0x40000001, 0, 0, 0, 0]))

    # --- alignment, zero buffer/length, and the signed-compare boundary ---
    cases.append(base_case("unaligned plan cursor", buffer=BUFFER_ADDR,
                           plan_cursor=BUFFER_ADDR + 0x103,
                           sizes=[1, 0, 0, 0, 0, 0, 0]))
    cases.append(base_case("zero buffer zero length succeeds",
                           buffer=0, length=0, plan_cursor=0))
    cases.append(base_case("zero source id", source=0))
    cases.append(base_case("all-ones source id", source=0xFFFFFFFF))
    cases.append(base_case("zero buffer with nonzero length",
                           buffer=0, length=0x100, plan_cursor=0x80,
                           sizes=[0, 0, 0, 0, 0, 0, 0]))
    # end > limit in unsigned terms but end - limit is negative as s32, so the
    # original's signed `bgt` accepts it.  An unsigned check would reject.
    cases.append(base_case("signed comparison wrap passes",
                           buffer=0xFFFFF000, length=0x8000,
                           plan_cursor=0xFFFFF100))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, case, stack_poison=0xAAAAAAAA)
        cand = Runner().run(cand_code, case, stack_poison=0xBBBBBBBB)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        assert orig["ret"] == case["expect_ret"], (
            f"case {case['name']!r} expected r0={case['expect_ret']}, "
            f"original returned {orig['ret']}"
        )
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls, "
              f"r0={orig['ret']})")
    return passed


def main() -> None:
    print("Testing engine_func_0012f954 (0x0012f954)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("layer_a_stride", "constexpr u32 kLayerAStride = 0x558;",
         "constexpr u32 kLayerAStride = 0x55C;"),
        ("layer_b_size_word", "sizes.word[5] * kLayerBStride",
         "sizes.word[6] * kLayerBStride"),
        ("signed_check_to_unsigned",
         "if (static_cast<s32>(end_a - limit) > 0) {",
         "if (end_a > limit) {"),
        ("node_bias",
         "&state->layer_a.node_head,\n                                     node + kNodeBias);",
         "&state->layer_a.node_head,\n                                     node + kNodeBias + 4);"),
        ("length_echo", "state->length_arg = length;",
         "state->length_arg = buffer;"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, case, stack_poison=0xAAAAAAAA)
            bad = Runner().run(mutant_code, case, stack_poison=0xBBBBBBBB)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
