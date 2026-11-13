#!/usr/bin/env python3
"""Differential test for func_0035c754 (0x0035c754) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the func_0035c754 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the ordered call log: the 0x0035C65C reader, 0x00238C44 allocations (pool
    and unit count), the 0x00237F10 / 0x00237EFC payload helpers, and every
    first/second token-handler dispatch with the values their pointer
    arguments see;
  * the state page, the scanner-node chain, the output/value slots, the tree
    nodes, the allocation heap and the pool page after the call;
  * any write outside the private stack and the fixture pages.

Coverage: reader return codes 1/2/3/0xFFFFFFFF/0x1234; token types
0/2/5/0x12/0xFF on the initial fallback; type-1 container creation with several
following token types; allocator failure on the container, the child and a
nested reference; first-handler results 0/1/2/3; second-handler results
0/1/2/3/0xFFFFFFFF; nested-container chains; handler-written values that must
(and must not) be forwarded; the persistent first-out slot across loop
iterations; every type from 0 to 18 exercised at least once; and the odd
this-adjust (virtual member function pointer) form for both handler tables.
Negative controls mutate the post-handler table offset, the container pool
source, the fallback output word and the token-advance link; each mutant must
be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0035c754"

FUNC_ADDR = 0x0035C754
FUNC_SIZE = 616

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
TABLE_ADDR = 0x00470000
TABLE_SIZE = 0x00020000
STATE_ADDR = 0x00710000
STATE_SIZE = 0x00010000
NODE_ADDR = 0x00720000
NODE_SIZE = 0x00010000
OUT_ADDR = 0x00730000
OUT_SIZE = 0x00010000
TREE_ADDR = 0x00740000
TREE_SIZE = 0x00010000
HEAP_ADDR = 0x00750000
HEAP_SIZE = 0x00010000
POOL_ADDR = 0x00760000
POOL_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100
OUT_SLOT = OUT_ADDR + 0x00
VALUE_SLOT = OUT_ADDR + 0x10

A_TABLE = 0x00472B40
B_TABLE = A_TABLE + 0x98
MAX_TYPE = 18

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_READER = 0x0035C65C
STUB_ALLOC = 0x00238C44
STUB_INIT = 0x00237F10
STUB_SET = 0x00237EFC

A_BASE = 0x00310000
B_BASE = 0x00320000

A_BEHAVIORS = (
    "ret0",            # 0
    "ret0_out",        # 1
    "ret0_value",      # 2
    "ret0_out_value",  # 3
    "ret1",            # 4
    "ret1_copy",       # 5
    "ret2",            # 6
    "ret3",            # 7
    "neg1",            # 8
)
# The shipped post-handlers consume the token (they move state->node), so every
# post behaviour that returns 0 or 1 also advances the cursor to a fresh node;
# otherwise the parser loop would re-dispatch the same token forever, exactly
# as the original does.
B_BEHAVIORS = (
    "ret0_advance",           # 0
    "ret0_out_advance",       # 1
    "ret0_value_advance",     # 2
    "ret0_out_value_advance", # 3
    "ret1_advance",           # 4
    "ret2",                   # 5
    "ret3",                   # 6
    "neg1",                   # 7
)
B_DEFAULT = 5  # "ret2": stop the loop deterministically

STUB_NAMES = {
    STUB_READER: "func_0035c65c",
    STUB_ALLOC: "func_00238c44",
    STUB_INIT: "func_00237f10",
    STUB_SET: "func_00237efc",
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
        if "0035c754" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"func_0035c754 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, name in STUB_NAMES.items():
                if name == rel.symbol_name or f"{address:08x}" in rel.symbol_name:
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
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
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


# --------------------------------------------------------------------- fixtures
def build_state(case: dict) -> bytes:
    page = bytearray(STATE_SIZE)
    struct.pack_into("<I", page, 0x00, NODE_ADDR + 0x20 * case.get("start_node", 0))
    struct.pack_into("<I", page, 0x04, STATE_ADDR + 4)
    struct.pack_into("<I", page, 0x08, STATE_ADDR + 4)
    struct.pack_into("<I", page, 0x0C, POOL_ADDR + 0x1000)
    struct.pack_into("<I", page, 0x10, 0x10101010)
    struct.pack_into("<I", page, 0x14, POOL_ADDR + 0x2000)
    struct.pack_into("<I", page, 0x18, 0x18181818)
    struct.pack_into("<I", page, 0x40, 0x40404040)
    return bytes(page)


def build_nodes(case: dict) -> bytes:
    page = bytearray(NODE_SIZE)
    types = case.get("node_types", {})
    next_index = case.get("node_next", {})
    word0 = case.get("node_word0", {})
    word4 = case.get("node_word4", {})
    for index in range(8):
        base = 0x20 * index
        struct.pack_into("<I", page, base + 0x0C, 0xC0C00000 | index)
        for offset in range(0x10, 0x20, 4):
            struct.pack_into("<I", page, base + offset, 0xD0000000 | (index << 8) | offset)
        page[base + 8] = types.get(index, 2) & 0xFF
        page[base + 9] = 0x59
        page[base + 0x0A] = 0x5A
        page[base + 0x0B] = 0x5B
        word_zero = word0.get(index, 0xDEAD0000 | index)
        struct.pack_into("<I", page, base, word_zero & 0xFFFFFFFF)
        if index in word4:
            link = word4[index]
        else:
            link = NODE_ADDR + 0x20 * next_index.get(index, min(index + 1, 7))
        struct.pack_into("<I", page, base + 4, link & 0xFFFFFFFF)
    return bytes(page)


def build_out(case: dict) -> bytes:
    page = bytearray(OUT_SIZE)
    struct.pack_into("<I", page, 0x00, 0x0BADF00D)
    struct.pack_into("<I", page, 0x10, case.get("value", 0x0000BEEF) & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x20, 0x20202020)
    return bytes(page)


def build_tree() -> bytes:
    page = bytearray(TREE_SIZE)
    for index in range(4):
        base = 0x40 * index
        struct.pack_into("<I", page, base + 0x00, 0x7E000000 | index)
        struct.pack_into("<I", page, base + 0x04, 0x7E100000 | index)
        struct.pack_into("<I", page, base + 0x08, TREE_ADDR + base + 8)
        struct.pack_into("<I", page, base + 0x0C, TREE_ADDR + base + 8)
        struct.pack_into("<I", page, base + 0x10, POOL_ADDR + 0x100 * index)
        struct.pack_into("<I", page, base + 0x14, 0x7E200000 | index)
        struct.pack_into("<I", page, base + 0x18, 0x7E300000 | index)
        struct.pack_into("<I", page, base + 0x1C, 0x7E400000 | index)
    return bytes(page)


def build_pool() -> bytes:
    page = bytearray(POOL_SIZE)
    for index in range(0, POOL_SIZE, 4):
        struct.pack_into("<I", page, index, 0x90900000 | index)
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(TABLE_SIZE)
    a_index = case.get("a", {})
    b_index = case.get("b", {})
    a_adjust = case.get("a_adjust", {})
    b_adjust = case.get("b_adjust", {})
    a_handler = case.get("a_handler", {})
    b_handler = case.get("b_handler", {})
    for token in range(MAX_TYPE + 1):
        first = a_handler.get(token, A_BASE + 0x10 * a_index.get(token, 0))
        second = b_handler.get(
            token, B_BASE + 0x10 * b_index.get(token, B_DEFAULT)
        )
        struct.pack_into(
            "<II",
            page,
            A_TABLE - TABLE_ADDR + 8 * token,
            first & 0xFFFFFFFF,
            a_adjust.get(token, 0) & 0xFFFFFFFF,
        )
        struct.pack_into(
            "<II",
            page,
            B_TABLE - TABLE_ADDR + 8 * token,
            second & 0xFFFFFFFF,
            b_adjust.get(token, 0) & 0xFFFFFFFF,
        )
    return bytes(page)


class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(STATE_ADDR, STATE_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(OUT_ADDR, OUT_SIZE)
        self.uc.mem_map(TREE_ADDR, TREE_SIZE)
        self.uc.mem_map(HEAP_ADDR, HEAP_SIZE)
        self.uc.mem_map(POOL_ADDR, POOL_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in (STUB_READER, STUB_ALLOC, STUB_INIT, STUB_SET):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
        for index in range(len(A_BEHAVIORS)):
            self.uc.mem_write(A_BASE + 0x10 * index, struct.pack("<I", 0xE12FFF1E))
        for index in range(len(B_BEHAVIORS)):
            self.uc.mem_write(B_BASE + 0x10 * index, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub,
            begin=STUB_READER, end=STUB_READER,
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub,
            begin=STUB_SET, end=STUB_ALLOC,
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub,
            begin=A_BASE, end=A_BASE + 0x1000 - 4,
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_CODE, self._on_stub,
            begin=B_BASE, end=B_BASE + 0x1000 - 4,
        )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}
        self.alloc_index = 0
        self.heap_ptr = HEAP_ADDR
        self.handler_seq = 0

    # ------------------------------------------------------------------ stubs
    @staticmethod
    def _u32(uc, address: int) -> int:
        return struct.unpack("<I", uc.mem_read(address, 4))[0]

    @staticmethod
    def _put_u32(uc, address: int, value: int) -> None:
        uc.mem_write(address & 0xFFFFFFFF, struct.pack("<I", value & 0xFFFFFFFF))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_READER:
            self.call_log.append(
                ("reader", r0, self._u32(uc, r1), self._u32(uc, r2))
            )
            if self.case["reader_rc"] != 0:
                uc.reg_write(arm.UC_ARM_REG_R0, self.case["reader_rc"] & 0xFFFFFFFF)
                return
            if self.case["reader_write_out"]:
                self._put_u32(uc, r1, self.case["reader_out"])
            if self.case["reader_value"] is not None:
                self._put_u32(uc, r2, self.case["reader_value"])
            uc.reg_write(arm.UC_ARM_REG_R0, 0)
            return

        if address == STUB_ALLOC:
            units = r1
            self.alloc_index += 1
            self.call_log.append(("alloc", r0, units))
            if self.case.get("alloc_fail") == self.alloc_index:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
                return
            size_bytes = (units & 0xFFFFFFFF) * 16
            block = self.heap_ptr
            if block + max(size_bytes, 16) > HEAP_ADDR + HEAP_SIZE:
                raise RuntimeError("heap exhausted in stub allocator")
            uc.mem_write(block, b"\x00" * size_bytes)
            self.heap_ptr = block + size_bytes
            uc.reg_write(arm.UC_ARM_REG_R0, block)
            return

        if address == STUB_INIT:
            self.call_log.append(("init", r0))
            self._put_u32(uc, r0, 0)
            uc.mem_write(r0 + 4, b"\x01")
            self._put_u32(uc, r0 + 8, r0 + 8)
            self._put_u32(uc, r0 + 0x10, 0)
            self._put_u32(uc, r0 + 0x0C, r0 + 8)
            return

        if address == STUB_SET:
            value = self._u32(uc, r1)
            self.call_log.append(("set", r0, value))
            uc.mem_write(r0 + 4, b"\x01")
            self._put_u32(uc, r0, value)
            return

        if A_BASE <= address < B_BASE:
            behavior = A_BEHAVIORS[(address - A_BASE) // 0x10]
            self._dispatch_handler(uc, "A", behavior, r0, r1, r2, None)
            return
        if B_BASE <= address < B_BASE + 0x1000:
            behavior = B_BEHAVIORS[(address - B_BASE) // 0x10]
            previous = self._u32(uc, r3)
            self._dispatch_handler(uc, "B", behavior, r0, r1, r2, previous)
            return
        raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def _dispatch_handler(self, uc, kind, behavior, self_ptr, out_ptr,
                          value_ptr, previous) -> None:
        self.handler_seq += 1
        sequence = self.handler_seq
        out_before = self._u32(uc, out_ptr)
        value_before = self._u32(uc, value_ptr)
        if kind == "A":
            self.call_log.append(("A:" + behavior, self_ptr, out_before,
                                  value_before))
        else:
            self.call_log.append(("B:" + behavior, self_ptr, out_before,
                                  value_before, previous))

        result = 0
        out_value = self.case.get("handler_out")
        if out_value is None:
            out_value = 0xA5000000 | (sequence << 4)
        if behavior in ("ret0_out", "ret0_out_value", "ret0_out_advance",
                        "ret0_out_value_advance"):
            self._put_u32(uc, out_ptr, out_value)
        if behavior in ("ret0_value", "ret0_out_value", "ret0_value_advance",
                        "ret0_out_value_advance"):
            self._put_u32(uc, value_ptr, 0xB5000000 | (sequence << 4))
        if behavior == "ret1":
            result = 1
        elif behavior == "ret1_copy":
            self._put_u32(uc, out_ptr, value_before)
            result = 1
        elif behavior == "ret1_advance":
            result = 1
        elif behavior == "ret2":
            result = 2
        elif behavior == "ret3":
            result = 3
        elif behavior == "neg1":
            result = 0xFFFFFFFF
        if behavior in ("ret0_advance", "ret0_out_advance",
                        "ret0_value_advance", "ret0_out_value_advance",
                        "ret1_advance"):
            self._put_u32(uc, self_ptr, self.case["advance_to"])
        uc.reg_write(arm.UC_ARM_REG_R0, result & 0xFFFFFFFF)

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case
        self.alloc_index = 0
        self.heap_ptr = HEAP_ADDR
        self.handler_seq = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(STATE_ADDR, build_state(case))
        self.uc.mem_write(NODE_ADDR, build_nodes(case))
        self.uc.mem_write(OUT_ADDR, build_out(case))
        self.uc.mem_write(TREE_ADDR, build_tree())
        self.uc.mem_write(HEAP_ADDR, b"\x00" * HEAP_SIZE)
        self.uc.mem_write(POOL_ADDR, build_pool())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, OUT_SLOT)
        self.uc.reg_write(arm.UC_ARM_REG_R2, VALUE_SLOT)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        finish = TRAP_ADDR
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=2_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            finish = f"exception at 0x{pc:08x}: {error}"

        allowed = (
            (STATE_ADDR, STATE_ADDR + STATE_SIZE),
            (NODE_ADDR, NODE_ADDR + NODE_SIZE),
            (OUT_ADDR, OUT_ADDR + OUT_SIZE),
            (TREE_ADDR, TREE_ADDR + TREE_SIZE),
            (HEAP_ADDR, HEAP_ADDR + HEAP_SIZE),
            (STACK_ADDR, STACK_ADDR + STACK_SIZE),
        )
        unexpected_writes = []
        for address, size in self.writes:
            if not any(start <= address < end for start, end in allowed):
                unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "finish": finish,
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self.call_log,
            "fixtures": {
                "state": bytes(self.uc.mem_read(STATE_ADDR, STATE_SIZE)),
                "nodes": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
                "out": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
                "tree": bytes(self.uc.mem_read(TREE_ADDR, TREE_SIZE)),
                "heap": bytes(self.uc.mem_read(HEAP_ADDR, HEAP_SIZE)),
                "pool": bytes(self.uc.mem_read(POOL_ADDR, POOL_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("ret", "pc", "sp", "finish", "callee_saved"):
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
                (i for i, (a, b) in enumerate(zip(value, cand["fixtures"][key]))
                 if a != b),
                None,
            )
            problems.append(
                f"fixture {key} differs (first byte {first}):\n"
                f"    orig={value[first:first + 16]!r}\n"
                f"    cand={cand['fixtures'][key][first:first + 16]!r}"
            )
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "reader_rc": 0,
        "reader_write_out": True,
        "reader_out": TREE_ADDR,
        "reader_value": None,
        "start_node": 0,
        "value": TREE_ADDR,
        "node_types": {},
        "node_next": {},
        "node_word0": {},
        "node_word4": {},
        "a": {},
        "b": {},
        "a_adjust": {},
        "b_adjust": {},
        "a_handler": {},
        "b_handler": {},
        # Default post-handler advance target: node 6 (type 2, default table
        # terminates the loop), so a "continue" result cannot spin forever.
        "advance_to": NODE_ADDR + 0x20 * 6,
    }
    case.update(overrides)
    case["name"] = name
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- reader return codes: the whole result is forwarded unchanged
    for rc in (1, 2, 3, 0xFFFFFFFF, 0x1234):
        cases.append(base_case(f"reader returns 0x{rc:x}", reader_rc=rc,
                               node_types={0: 1}))

    # --- initial token type is not the container type: *out = parsed
    for token in (0, 2, 5, 0x12, 0xFF):
        cases.append(base_case(f"initial type 0x{token:02x}",
                               node_types={0: token}))
    cases.append(base_case("initial fallback forwards parsed word",
                           node_types={0: 0}, reader_out=0x11223344))

    # --- container creation with a following token of every other type
    for token in (0, 3, 0x12):
        cases.append(base_case(f"container then type 0x{token:02x}",
                               node_types={0: 1, 1: token},
                               a={token: 0}, b={token: B_DEFAULT}))
    cases.append(base_case("container from tree node 3",
                           node_types={0: 1, 1: 0},
                           reader_out=TREE_ADDR + 0xC0, a={0: 0},
                           b={0: B_DEFAULT}))

    # --- allocator failures at each allocation
    cases.append(base_case("container alloc fails", node_types={0: 1},
                           alloc_fail=1))
    cases.append(base_case("child alloc fails", node_types={0: 1},
                           alloc_fail=2))
    cases.append(base_case("nested alloc fails", node_types={0: 1, 1: 0},
                           a={0: 4}, alloc_fail=3))

    # --- first handler results
    cases.append(base_case("first handler returns 2", node_types={0: 1, 1: 0},
                           a={0: 6}))
    cases.append(base_case("first handler returns 3", node_types={0: 1, 1: 0},
                           a={0: 7}))
    cases.append(base_case("first handler returns -1", node_types={0: 1, 1: 0},
                           a={0: 8}))

    # --- second handler results (0/1 continue the loop, others return)
    for behavior, label in ((4, "1 and advances"), (5, "2"), (6, "3"),
                            (7, "-1")):
        cases.append(base_case(f"second handler returns {label}",
                               node_types={0: 1, 1: 0},
                               a={0: 0}, b={0: behavior}))

    # --- nested container from the first handler
    cases.append(base_case("first handler descends, next type 0",
                           node_types={0: 1, 1: 0}, a={0: 4},
                           b={0: B_DEFAULT}))
    cases.append(base_case("descend allocates from *value",
                           node_types={0: 1, 1: 0}, a={0: 4},
                           b={0: B_DEFAULT}, value=TREE_ADDR + 0x40))
    cases.append(base_case("descend into tree node 2",
                           node_types={0: 1, 1: 0}, a={0: 4},
                           b={0: B_DEFAULT}, value=TREE_ADDR + 0x80))
    cases.append(base_case("descend then type 1 chain",
                           node_types={0: 1, 1: 1, 2: 0},
                           a={1: 4}, b={2: B_DEFAULT}))

    # --- loop continuation through the second handler
    cases.append(base_case("second handler loops to type 5",
                           node_types={0: 1, 1: 0, 2: 5},
                           a={0: 0, 5: 4}, b={0: 1},
                           advance_to=NODE_ADDR + 0x20 * 2,
                           handler_out=TREE_ADDR + 0x40))
    cases.append(base_case("first out persists across loop iterations",
                           node_types={0: 1, 1: 0, 2: 5},
                           a={0: 1, 5: 0}, b={0: 0},
                           advance_to=NODE_ADDR + 0x20 * 2))
    cases.append(base_case("second out feeds the next first value",
                           node_types={0: 1, 1: 0, 2: 5},
                           a={0: 0, 5: 0}, b={0: 1},
                           advance_to=NODE_ADDR + 0x20 * 2))

    # --- value forwarding rules
    cases.append(base_case("first value write is discarded before second",
                           node_types={0: 1, 1: 0}, a={0: 2}, b={0: 0}))
    cases.append(base_case("first writes value and out",
                           node_types={0: 1, 1: 0}, a={0: 3}, b={0: 0}))
    cases.append(base_case("second value write is forwarded",
                           node_types={0: 1, 1: 0, 2: 0x12},
                           a={0: 0, 0x12: 0}, b={0: 2, 0x12: 5},
                           advance_to=NODE_ADDR + 0x20 * 2))

    # --- every token type exercised once (post-handler terminates the loop)
    for token in range(0, 0x13):
        cases.append(base_case(f"token type 0x{token:02x}",
                               node_types={0: 1, 1: token},
                               a={token: 0}, b={token: B_DEFAULT}))

    # --- type boundaries on the initial fallback
    cases.append(base_case("initial type 0xFF", node_types={0: 0xFF}))
    cases.append(base_case("initial type 0x00 with value wrap",
                           node_types={0: 0}, value=0xFFFFFFFF))

    # --- odd this-adjust (virtual member-function-pointer) slots
    cases.append(base_case(
        "virtual handler slots",
        node_types={0: 1, 1: 3},
        a_handler={3: 0x40}, a_adjust={3: 1},
        b_handler={3: 0x44}, b_adjust={3: 1},
        node_word0={3: A_BASE + 0x10 * 1},
        node_word4={3: B_BASE + 0x10 * 4},
    ))
    cases.append(base_case(
        "virtual first slot only",
        node_types={0: 1, 1: 3},
        a_handler={3: 0x40}, a_adjust={3: 1},
        node_word0={3: A_BASE + 0x10 * 6},
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
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing func_0035c754 (0x0035c754)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
          f"(relocations resolved).")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("post_table_offset",
         "constexpr u32 kMsgSecondHandlerOffset = 0x98;",
         "constexpr u32 kMsgSecondHandlerOffset = 0x90;"),
        ("container_pool_source",
         "    node->pool = state->child_pool;",
         "    node->pool = state->pool;"),
        ("fallback_parsed_word",
         "        *out = parsed;",
         "        *out = 0;"),
        ("advance_link",
         "        state->node = *reinterpret_cast<const u32*>(state->node + 4);",
         "        state->node = *reinterpret_cast<const u32*>(state->node + 0);"),
    ):
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
