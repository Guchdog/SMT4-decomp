#!/usr/bin/env python3
"""Differential test for ui_func_001188d0 (0x001188d0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the ui_func_001188d0 body,
resolves its direct calls against deterministic stubs and executes the four
tiny real helpers (0x2C5F7C, 0x2BEFDC, 0x2BEF88, 0x2BDA00) so the push/pop
callbacks at [stack+0x1C] really run.  The pinned original
(extracted/exefs/code.bin) and the relocated candidate are executed in separate
Unicorn machines with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11 and d8/d9;
  * the ordered call log with every register argument and the two architected
    stack words of every helper;
  * the indirect callback target actually taken (two distinct stubs) and the
    stack depth observed by that callback;
  * full panel, render-object, layer-3 command-stack, node-arena and anchor
    pages, plus the 0x2BF6D0 by-id table at 0x0040417C and the global pointer
    at 0x0044EA00 (all must match the original byte for byte);
  * any emulated write outside the private stack and those fixture pages.

Coverage: both accepted status bytes (1, 5) and eight rejected values; kind
0x0B (list) with counts 0, 1, 2, 3, 4, 5, 9, -1 and 0x80000000; kind 0x13
(grid) with counts 0, 1, 2, 3 and negative; four unhandled kind bytes; selected
index equal / lower / higher than every row (including -1 and INT_MAX); signed
s16 coordinate and anchor boundaries; float-to-int row scales chosen so the
arithmetic right shift differs from division (negative odd values); and the
push/pop callback suppression condition (previous entry == pushed 0xF10,
callback flag clear) versus a forced flag byte.  Negative controls mutate the
inactive-row colour, the row offset and the selected-row format id; each mutant
must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_001188d0"

FUNC_ADDR = 0x001188D0
FUNC_SIZE = 660

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers the function and every helper below 0x400000
GLOBAL_ADDR = 0x00400000
GLOBAL_SIZE = 0x00080000  # 0x40417C node-id table and 0x0044EA00 global
STACKBASE_ADDR = 0x00700000
STACKBASE_SIZE = 0x00010000
PANEL_ADDR = 0x00710000
PANEL_SIZE = 0x00001000
RENDER_ADDR = 0x00711000
RENDER_SIZE = 0x00001000
NODE_ADDR = 0x00720000
NODE_SIZE = 0x00010000
ANCHOR_ADDR = 0x00730000
ANCHOR_SIZE = 0x00001000
RODATA_ADDR = 0x00750000
RODATA_SIZE = 0x00010000
CALLBACK_A = 0x00760000
CALLBACK_B = 0x00761000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# 0x2BEFDC / 0x2BEF88 address the layer-3 command stack as
# base + group * 0x20 + 0x11EC and store the depth at +0, the entry array at
# +8, the callback flag at +0x18 and the callback pointer at +0x1C.
STACK_GROUP = 3
STACK_BASE = STACKBASE_ADDR + STACK_GROUP * 0x20 + 0x11EC

PUSHED_COMMAND = 0xF10  # ui_func_002c5f7c(1, 0), verified by the real helper

# Real helper bodies copied verbatim from the pinned binary and executed.
REAL_HELPERS = {
    0x002C5F7C: 0x28,  # ui_func_002c5f7c
    0x002BEFDC: 0x54,  # func_002befdc (push + indirect callback)
    0x002BEF88: 0x54,  # func_002bef88 (pop + indirect callback)
    0x002BDA00: 0x10,  # ui_func_002bda00
}

STUB_CAMP = 0x002BF6D0
STUB_DRAW = 0x002B792C
STUB_LABEL = 0x002BF558
STUB_SCALE = 0x00126754

STUB_NAMES = {
    0x002C5F7C: "ui_func_002c5f7c",
    0x002BEFDC: "func_002befdc",
    0x002BEF88: "func_002bef88",
    0x002BDA00: "ui_func_002bda00",
    STUB_CAMP: "camp_func_002bf6d0",
    STUB_DRAW: "func_002b792c",
    STUB_LABEL: "func_002bf558",
    STUB_SCALE: "func_00126754",
}

STACK_ARGS = {
    0x002C5F7C: 0,
    0x002BEFDC: 0,
    0x002BEF88: 0,
    0x002BDA00: 0,
    STUB_CAMP: 0,
    STUB_DRAW: 2,  # arg5 = 6, arg6 = row index
    STUB_LABEL: 2,  # row y extent, panel kind 0x0B
    STUB_SCALE: 0,
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
    "d8": arm.UC_ARM_REG_D8,
    "d9": arm.UC_ARM_REG_D9,
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
    "d8": 0x0123456789ABCDEF,
    "d9": 0xFEDCBA9876543210,
}

NODE_STRIDE = 0x20
GROUP_B_OFFSET = 0x2000
ANCHOR_ORIGIN = 0x40
ANCHOR_DECOY = 0x80


def get_orig_bytes(address: int, size: int) -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(address - 0x00100000)
        return f.read(size)


def build_global_template() -> bytes:
    """Authentic 0x0040417C..0x0041D3 settings table, zero elsewhere."""
    page = bytearray(GLOBAL_SIZE)
    table = get_orig_bytes(0x0040417C, 0x58)
    offset = 0x0040417C - GLOBAL_ADDR
    page[offset : offset + len(table)] = table
    return bytes(page)


GLOBAL_TEMPLATE = build_global_template()


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


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "001188d0" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"ui_func_001188d0 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (1, 28, 29):
            target = None
            for address, name in STUB_NAMES.items():
                if f"{address:08x}" in rel.symbol_name:
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
        elif rel.relocation_type == 2:  # R_ARM_ABS32 to the static node-id table
            if rel.symbol_name not in ("", ".rodata"):
                raise RuntimeError(
                    f"unexpected ABS32 symbol {rel.symbol_name!r}"
                )
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )

    rodata = elf_sections(obj_file).get(".rodata", b"")
    words = tuple(
        struct.unpack_from("<9i", rodata, 0)
    ) if len(rodata) >= 36 else ()
    if words != (0xA8, 0xA9, 0x9C, 0x9D, 0x9E, 0xB0, 0xB1, 0xB2, 0xB3):
        raise RuntimeError(f"unexpected .rodata node-id table: {words}")
    return bytes(code), rodata


def compile_candidate(path: Path = SOURCE, obj_name: str = "leaf_batch45_a.o"):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / obj_name
    res = compile_tu_armv6k(path, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str):
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_candidate(mutant_src, f"mutant_{name}.o")


# --------------------------------------------------------------------- fixtures
DEFAULT_COORDS = {
    # Path A ids (0x0E node list).
    0xA8: (0x1234, -0x0456),
    0xA9: (-0x0200, 0x0064),
    0x9C: (0x7FFF, -0x8000),
    0x9D: (-0x8000, 0x7FFF),
    0x9E: (0x0000, 0x0000),
    0xB0: (0x0FFF, -0x0001),
    0xB1: (-0x0001, 0x0001),
    0xB2: (0x5555, -0x5555),
    0xB3: (0x7FFE, 0x7FFE),
    # Path B origin and row ids (0x3A node list).
    0x97: (0x0100, 0x0200),
    0x98: (0x0010, -0x0020),
    0x99: (-0x0030, 0x0040),
    0x9A: (0x0050, -0x0060),
    0x9B: (-0x0070, 0x0080),
    0x9C + 0x100: (0, 0),  # placeholder, unused
}


def node_offset(index: int, group: int) -> int:
    base = index * NODE_STRIDE
    if group == 0x3A:
        base += GROUP_B_OFFSET
    return base


def build_nodes(case: dict) -> bytes:
    page = bytearray(NODE_SIZE)
    coords = dict(DEFAULT_COORDS)
    coords.update(case.get("coords", {}))
    for index, (x, y) in coords.items():
        if index > 0xFF:
            continue
        for group in (0x0E, 0x3A):
            offset = node_offset(index, group)
            struct.pack_into("<h", page, offset + 8, x)
            struct.pack_into("<h", page, offset + 0xA, y)
            struct.pack_into("<I", page, offset, 0xC0DE0000 | index)
            anchor = (
                ANCHOR_ADDR + ANCHOR_ORIGIN
                if index == 0x97
                else ANCHOR_ADDR + ANCHOR_DECOY
            )
            struct.pack_into("<I", page, offset + 0xC, anchor)
            struct.pack_into("<I", page, offset + 0x10, 0x5A5A0000 | index)
    return bytes(page)


def build_anchor(case: dict) -> bytes:
    page = bytearray(ANCHOR_SIZE)
    struct.pack_into("<h", page, ANCHOR_ORIGIN, case.get("anchor_x", 0x0006))
    struct.pack_into("<h", page, ANCHOR_ORIGIN + 2, 0x1111)
    struct.pack_into("<h", page, ANCHOR_DECOY, 0x2222)
    struct.pack_into("<h", page, ANCHOR_DECOY + 2, 0x3333)
    return bytes(page)


def build_panel(case: dict) -> bytes:
    page = bytearray(b"\xA5" * PANEL_SIZE)
    struct.pack_into("<I", page, 4, RENDER_ADDR)
    page[8] = case["status"] & 0xFF
    page[9] = case["kind"] & 0xFF
    struct.pack_into("<I", page, 0x18, case["selected"] & 0xFFFFFFFF)
    struct.pack_into("<I", page, 0x20, case["count"] & 0xFFFFFFFF)
    return bytes(page)


def build_render() -> bytes:
    page = bytearray(b"\x3C" * RENDER_SIZE)
    return bytes(page)


def build_stackbase(case: dict) -> bytes:
    page = bytearray(b"\x6D" * STACKBASE_SIZE)
    offset = STACK_BASE - STACKBASE_ADDR
    struct.pack_into("<I", page, offset + 0x00, 0)  # depth
    struct.pack_into("<I", page, offset + 0x04, 0xDEAD0001)  # unused field
    for entry in range(8):
        struct.pack_into("<I", page, offset + 0x08 + entry * 4,
                         0xE0000000 | entry)
    struct.pack_into("<I", page, offset + 0x08, case["stack_entry0"])
    page[offset + 0x18] = case["stack_flag"] & 0xFF
    struct.pack_into(
        "<I",
        page,
        offset + 0x1C,
        CALLBACK_B if case.get("callback") == "b" else CALLBACK_A,
    )
    return bytes(page)


def build_global(case: dict) -> bytes:
    page = bytearray(GLOBAL_TEMPLATE)
    struct.pack_into("<I", page, 0x0044EA00 - GLOBAL_ADDR, STACKBASE_ADDR)
    return bytes(page)


def scale_bits(case: dict, index: int) -> int:
    scales = case.get("scales") or {}
    if index in scales:
        value = scales[index]
    else:
        value = float(index) * 1.5 - 2.0
    return struct.unpack("<I", struct.pack("<f", value))[0]


def read_c_string(uc, address: int, limit: int = 32) -> bytes:  # pragma: no cover
    return b""


class Runner:
    """One Unicorn machine with the pinned helpers and deterministic stubs."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # The original pushes d8 and both bodies use VFP; grant CP10/CP11
        # access and set FPEXC.EN before mapping/execution.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(STACKBASE_ADDR, STACKBASE_SIZE)
        self.uc.mem_map(PANEL_ADDR, PANEL_SIZE)
        self.uc.mem_map(RENDER_ADDR, RENDER_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(ANCHOR_ADDR, ANCHOR_SIZE)
        self.uc.mem_map(RODATA_ADDR, RODATA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_map(CALLBACK_A, 0x1000)
        self.uc.mem_map(CALLBACK_B, 0x1000)

        for address, size in REAL_HELPERS.items():
            self.uc.mem_write(address, get_orig_bytes(address, size))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_helper, begin=address, end=address
            )

        for address in (STUB_CAMP, STUB_DRAW, STUB_LABEL, STUB_SCALE):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )

        for address, tag in ((CALLBACK_A, "a"), (CALLBACK_B, "b")):
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE,
                self._on_callback,
                user_data=tag,
                begin=address,
                end=address,
            )

        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.case: dict = {}

    # ---------------------------------------------------------------- helpers
    def _stack_words(self, count: int) -> tuple:
        if count == 0:
            return ()
        sp = self.uc.reg_read(arm.UC_ARM_REG_SP)
        return struct.unpack(f"<{count}I", self.uc.mem_read(sp, 4 * count))

    def _log(self, name: str, *args) -> None:
        self.call_log.append((name, args))

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_callback(self, uc, address, size, tag) -> None:
        depth = struct.unpack(
            "<I", uc.mem_read(STACK_BASE, 4)
        )[0]
        self._log(f"stack_callback_{tag}", depth)

    def _on_helper(self, uc, address, size, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        if address == 0x002C5F7C:
            self._log("ui_func_002c5f7c", r0, r1)
        elif address == 0x002BEFDC:
            self._log("func_002befdc", r0, r1, r2)
        elif address == 0x002BEF88:
            self._log("func_002bef88", r0, r1)
        elif address == 0x002BDA00:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log("ui_func_002bda00", r0, r1, r2, s0)
        else:  # pragma: no cover - guarded by registration
            raise AssertionError(f"unexpected helper 0x{address:08x}")

    def _on_stub(self, uc, address, size, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)

        if address == STUB_CAMP:
            self._log("camp_func_002bf6d0", r0, r1)
            group = r0 & 0xFF
            index = r1 & 0xFF
            uc.reg_write(
                arm.UC_ARM_REG_R0, NODE_ADDR + node_offset(index, group)
            )
        elif address == STUB_DRAW:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self._log("func_002b792c", r0, r1, r2, r3, s0,
                      *self._stack_words(2))
        elif address == STUB_LABEL:
            self._log("func_002bf558", r0, r1, r2, r3,
                      *self._stack_words(2))
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_SCALE:
            self._log("func_00126754", r0, r1)
            uc.reg_write(arm.UC_ARM_REG_R0, 0x11111111)
            uc.reg_write(arm.UC_ARM_REG_S0, scale_bits(self.case, r1))
        else:  # pragma: no cover
            raise AssertionError(f"unexpected stub 0x{address:08x}")

    # -------------------------------------------------------------- execution
    @staticmethod
    def _normalise(log) -> list:
        normalised = []
        for name, args in log:
            out = []
            for arg in args:
                if isinstance(arg, int) and STACK_ADDR <= arg < STACK_ADDR + STACK_SIZE:
                    out.append("<stack>")
                else:
                    out.append(arg)
            normalised.append((name, tuple(out)))
        return normalised

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        # Clear the function region so stale original bytes are never executed.
        self.uc.mem_write(FUNC_ADDR, b"\x00" * FUNC_SIZE)
        self.uc.mem_write(FUNC_ADDR, code)
        if rodata:
            self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(GLOBAL_ADDR, build_global(case))
        self.uc.mem_write(STACKBASE_ADDR, build_stackbase(case))
        self.uc.mem_write(PANEL_ADDR, build_panel(case))
        self.uc.mem_write(RENDER_ADDR, build_render())
        self.uc.mem_write(NODE_ADDR, build_nodes(case))
        self.uc.mem_write(ANCHOR_ADDR, build_anchor(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, PANEL_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        unexpected_writes = []
        for address, _size in self.writes:
            allowed = (
                STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
                or STACKBASE_ADDR <= address < STACKBASE_ADDR + STACKBASE_SIZE
                or RENDER_ADDR <= address < RENDER_ADDR + RENDER_SIZE
            )
            if not allowed:
                unexpected_writes.append(address)

        global_page = bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE))
        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": self._normalise(self.call_log),
            "fixtures": {
                "panel": bytes(self.uc.mem_read(PANEL_ADDR, PANEL_SIZE)),
                "render": bytes(self.uc.mem_read(RENDER_ADDR, RENDER_SIZE)),
                "stackbase": bytes(self.uc.mem_read(STACKBASE_ADDR, STACKBASE_SIZE)),
                "nodes": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
                "anchor": bytes(self.uc.mem_read(ANCHOR_ADDR, ANCHOR_SIZE)),
                "global_table": global_page[
                    0x00404100 - GLOBAL_ADDR : 0x00404200 - GLOBAL_ADDR
                ],
                "global_pointer": global_page[
                    0x0044EA00 - GLOBAL_ADDR : 0x0044EA04 - GLOBAL_ADDR
                ],
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    keys = ["pc", "sp", "callee_saved"]
    # The rejected status path is an unspecified `void` return, so the original
    # leaves the loaded status byte in r0 while the candidate leaves its masked
    # copy. r0 is part of the contract only when the body (and its final
    # 0x2BEF88 pop) ran.
    if orig["call_log"] or cand["call_log"]:
        keys.insert(0, "ret")
    for key in keys:
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
            problems.append(f"fixture {key} was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "status": 1,
        "kind": 0x0B,
        "selected": 0,
        "count": 2,
        "stack_flag": 0,
        "stack_entry0": 0,
        "callback": "a",
        "anchor_x": 0x0006,
        "coords": {},
        "scales": None,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- status gate: only bytes 1 and 5 enter the body
    for status in (0, 2, 3, 4, 6, 7, 0x80, 0xFF):
        cases.append(base_case(f"status 0x{status:02x} rejected", status=status))
    cases.append(base_case("status 5 accepted (list)", status=5))
    cases.append(base_case("status 5 accepted (grid)", status=5, kind=0x13))

    # --- unhandled kinds still push, reset the render state and pop
    for kind in (0x00, 0x0A, 0x0C, 0x1F, 0xFF):
        cases.append(
            base_case(f"kind 0x{kind:02x} unhandled", kind=kind, count=2)
        )

    # --- path A: list kinds, count selects the node-id window
    for count, selected in (
        (0, 0), (1, 0), (1, 1), (1, -1), (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 1), (3, 2), (3, 3), (4, 0), (4, 1), (4, 2), (4, 3),
        (4, 4), (5, 0), (5, 4), (9, 0), (9, 8), (9, 0x7FFFFFFF),
        (-1, 0), (-0x80000000, 0),
    ):
        cases.append(
            base_case(f"list count {count} selected {selected}",
                      count=count, selected=selected)
        )

    # --- path A signed s16 coordinates and wrap-around offsets
    for index, (x, y) in (
        (0xA8, (-0x8000, 0x7FFF)),
        (0xA9, (0x7FFF, -0x8000)),
        (0xB0, (-1, 1)),
        (0x9E, (0x7FFF, 0x7FFF)),
    ):
        cases.append(
            base_case(f"list node 0x{index:02x} boundary {x}/{y}",
                      count=9, selected=8,
                      coords={index: (x, y)})
        )

    # --- path B: grid rows
    for count, selected in (
        (0, 0), (1, 0), (1, 1), (1, -1), (2, 0), (2, 1), (2, 2),
        (3, 0), (3, 1), (3, 2), (3, 3), (4, 2),
        (-1, 0), (0x80000000, 0),
    ):
        cases.append(
            base_case(f"grid count {count} selected {selected}", kind=0x13,
                      count=count, selected=selected)
        )

    # --- path B coordinate boundaries, anchor extent and row scale
    boundary_pairs = [
        ((-0x8000, -0x8000), (-0x8000, 0x7FFF)),
        ((0x7FFF, 0x7FFF), (0x7FFF, -0x8000)),
        ((-1, 1), (1, -1)),
        ((0x0100, 0x0200), (0x7FFF, -0x8000)),
    ]
    for row, (origin, node) in enumerate(boundary_pairs):
        cases.append(
            base_case(f"grid boundary row {row}", kind=0x13, count=2,
                      selected=1,
                      coords={0x97: origin, 0x98: node})
        )
    for anchor_x in (-0x8000, -1, 0, 1, 0x7FFF):
        cases.append(
            base_case(f"grid anchor_x {anchor_x}", kind=0x13, count=1,
                      anchor_x=anchor_x)
        )
    for label, scales in (
        ("negative odd", {0: -3.5, 1: -7.5, 2: -1.5}),
        ("zero and positive", {0: 0.0, 1: 1.0, 2: 3.5}),
        ("fractional truncation", {0: -0.75, 1: 0.75, 2: -2.5}),
    ):
        cases.append(
            base_case(f"grid scales {label}", kind=0x13, count=3,
                      scales=scales)
        )

    # --- command-stack callback gating (real 0x2BEFDC / 0x2BEF88 execute)
    cases.append(
        base_case("callback suppressed when previous entry equals 0xF10",
                  stack_entry0=PUSHED_COMMAND)
    )
    cases.append(
        base_case("callback forced by flag byte 1", stack_flag=1,
                  stack_entry0=PUSHED_COMMAND)
    )
    cases.append(
        base_case("callback forced by flag byte 0xFF", stack_flag=0xFF)
    )
    cases.append(
        base_case("callback B indirect target", callback="b")
    )
    cases.append(
        base_case("callback B forced by flag", callback="b", stack_flag=1)
    )

    return cases


def run_case_set(orig_code, cand_code, rodata, cases) -> int:
    passed = 0
    for case in cases:
        orig = Runner().run(orig_code, b"", case)
        cand = Runner().run(cand_code, rodata, case)
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
    print("Testing ui_func_001188d0 (0x001188d0)...")
    orig_code = get_orig_bytes(FUNC_ADDR, FUNC_SIZE)
    cand_code, cand_rodata = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B, "
        f"rodata {len(cand_rodata)} B (relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cand_rodata, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("inactive_colour", "0x5A5A5AFFu", "0x5A5A5AFEu"),
        ("row_offset", "static_cast<s32>(*reinterpret_cast<const s16*>(node + 0x0A)) - 4,",
         "static_cast<s32>(*reinterpret_cast<const s16*>(node + 0x0A)) - 8,"),
        ("selected_format", "0x12, node_x, node_y, 0x0B);",
         "0x13, node_x, node_y, 0x0B);"),
        ("node_group", "0x0E, static_cast<u32>(kNodeIds[window + index])",
         "0x0F, static_cast<u32>(kNodeIds[window + index])"),
    ):
        mutant_code, mutant_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = Runner().run(orig_code, b"", case)
            bad = Runner().run(mutant_code, mutant_rodata, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
