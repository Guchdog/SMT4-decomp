#!/usr/bin/env python3
"""Differential test for camp_func_0025a0d0 (0x0025a0d0) using Unicorn ARM.

The routine refreshes the title-config touch regions.  It reads the workspace
pointer from `g_TitleConfigWork` (0x0044E2D0), releases the regions recorded by
the previous call (signed halfword count at +0x24), clears the four region
handles at +0x1C..+0x23 through 0x0027EDF8, queries the selected settings row
with 0x0029F248, resolves five 0x2F-group layout records with 0x002BF6D0, and
registers four rectangles with 0x0029E2F4 before leaving the updated count in
r0 and at +0x24.

Every direct call is replaced by a deterministic stub at the original branch
target.  The stubs log their register arguments and reproduce the observable
effects the routine consumes:

  * 0x0027EDF8 fills eight bytes with the replicated low byte of its value;
  * 0x0029F248 returns the case's selected row;
  * 0x002BF6D0 returns a case-controlled node pointer or null (address 0);
  * 0x0029E2F4 returns a scripted s16 region handle per call.

Each case runs the pinned original and the compiled candidate with identical
fixtures and compares the ordered call log, r0, continuation PC, SP,
callee-saved r4-r11, the complete work/node/zero-page windows, the page holding
the global workspace pointer, and the stack outside the dead push frame.  The
same values are also checked against an independent Python model of the
recovered behavior.
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
FUNC_ADDR = 0x0025A0D0
FUNC_SIZE = 408
TU_PATH = ROOT / "src/engine/leaf_batch33_c.cpp"
OUT_DIR = ROOT / "build/test_leaf_0025a0d0"

# ---------------------------------------------------------------------------
# Emulated address space
# ---------------------------------------------------------------------------
IMAGE_ADDR = 0x00100000
IMAGE_SIZE = 0x00400000              # 0x00100000..0x00500000 (includes 0x0044E2D0)
WORK_ADDR = 0x00600000
WORK_SIZE = 0x00002000
NODE_ADDR = 0x00700000
NODE_SIZE = 0x00010000
ZERO_SIZE = 0x00001000               # mapped at address 0 for null node pointers
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000
ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

GLOBAL_ADDR = 0x0044E2D0
GLOBAL_PAGE = 0x00440000
GLOBAL_PAGE_SIZE = 0x00010000

# Work offsets (ARM evidence only).
REGION_HANDLES = 0x1C
REGION_COUNT = 0x24
LIST_CURSOR = 0xE8
NODE_GROUP = 0x2F
ANCHOR_NODE_OFFSET = 0x100
NODE_1B_OFFSET = 0x200
NODE_34_OFFSET = 0x300
NODE_38_OFFSET = 0x400
NODE_33_OFFSET = 0x500
DIMS_OFFSET = 0x800
FIXED_NODE_OFFSETS = {
    0x1B: NODE_1B_OFFSET,
    0x34: NODE_34_OFFSET,
    0x38: NODE_38_OFFSET,
    0x33: NODE_33_OFFSET,
}

# Direct-call stubs (original branch targets).
STUB_2B9008 = 0x002B9008
STUB_27EDF8 = 0x0027EDF8
STUB_29F248 = 0x0029F248
STUB_2BF6D0 = 0x002BF6D0
STUB_29E2F4 = 0x0029E2F4

STUB_BY_SYMBOL = {
    "camp_func_002b9008": STUB_2B9008,
    "camp_func_0027edf8": STUB_27EDF8,
    "camp_func_0029f248": STUB_29F248,
    "camp_func_002bf6d0": STUB_2BF6D0,
    "camp_func_0029e2f4": STUB_29E2F4,
}

CALLEE_SAVED = [
    arm.UC_ARM_REG_R4,
    arm.UC_ARM_REG_R5,
    arm.UC_ARM_REG_R6,
    arm.UC_ARM_REG_R7,
    arm.UC_ARM_REG_R8,
    arm.UC_ARM_REG_R9,
    arm.UC_ARM_REG_R10,
    arm.UC_ARM_REG_R11,
]


# ---------------------------------------------------------------------------
# Candidate preparation
# ---------------------------------------------------------------------------
def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as image:
        image.seek(FUNC_ADDR - 0x00100000)
        return image.read(FUNC_SIZE)


def image_bytes() -> bytes:
    return ORIG_BIN.read_bytes()


def sign_extend_24(value: int) -> int:
    return value - 0x1000000 if value & 0x800000 else value


def compile_variant(src_file: Path, obj_file: Path) -> bytes:
    result = compile_tu_armv6k(Path(src_file), Path(obj_file), ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed for {src_file}: {result.stderr}")

    funcs = extract_elf_functions_detailed(Path(obj_file))
    entry = funcs.get("camp_func_0025a0d0")
    if entry is None:
        raise RuntimeError(
            "camp_func_0025a0d0 not found in object: " + ", ".join(sorted(funcs))
        )

    raw, relocs = entry
    code = bytearray(raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = STUB_BY_SYMBOL.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unexpected call relocation: {rel}")
            inst = struct.unpack_from("<I", code, rel.offset)[0]
            addend = sign_extend_24(inst & 0x00FFFFFF) << 2
            place = FUNC_ADDR + rel.offset
            disp = (target + addend - place) >> 2
            struct.pack_into(
                "<I", code, rel.offset, (inst & 0xFF000000) | (disp & 0x00FFFFFF)
            )
        else:
            raise RuntimeError(f"unsupported relocation: {rel}")

    return bytes(code)


def compile_candidate() -> bytes:
    return compile_variant(TU_PATH, OUT_DIR / "leaf_batch33_c.o")


def compile_mutant(name: str, old: str, new: str) -> bytes:
    text = TU_PATH.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor {old!r} occurs {text.count(old)} times")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_src.write_text(text.replace(old, new), encoding="utf-8")
    return compile_variant(mutant_src, OUT_DIR / f"mutant_{name}.o")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
def u16(value: int) -> int:
    return value & 0xFFFF


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def anchor_node_id(selected: int) -> int:
    return (selected + 0x1F) & 0xFFFFFFFF


def node_address(case: dict, node_id: int) -> int:
    if node_id in case["null_ids"]:
        return 0
    if node_id == anchor_node_id(case["selected"]):
        return NODE_ADDR + ANCHOR_NODE_OFFSET
    offset = FIXED_NODE_OFFSETS.get(node_id)
    return 0 if offset is None else NODE_ADDR + offset


def build_work(case: dict) -> bytes:
    page = bytearray(WORK_SIZE)
    for index in range(WORK_SIZE):
        page[index] = (index * 29 + 7) & 0xFF
    struct.pack_into("<H", page, REGION_COUNT, u16(case["previous"]))
    page[REGION_HANDLES:REGION_HANDLES + 8] = b"\xa5" * 8
    page[LIST_CURSOR:LIST_CURSOR + 0x64] = b"\x3c" * 0x64
    return bytes(page)


def put_node(page: bytearray, offset: int, values: tuple) -> None:
    x, y, width, height = values
    struct.pack_into("<H", page, offset + 8, u16(x))
    struct.pack_into("<H", page, offset + 0xA, u16(y))
    struct.pack_into("<H", page, offset + 4, u16(width))
    struct.pack_into("<H", page, offset + 6, u16(height))


def build_nodes(case: dict) -> bytes:
    page = bytearray(NODE_SIZE)
    for index in range(NODE_SIZE):
        page[index] = (index * 17 + 3) & 0xFF

    put_node(page, ANCHOR_NODE_OFFSET, case["anchor"])
    for node_id, offset in FIXED_NODE_OFFSETS.items():
        put_node(page, offset, case["nodes"][node_id])

    dims_pointer = case["dims_pointer"]
    if dims_pointer is None:
        dims_pointer = NODE_ADDR + DIMS_OFFSET
    struct.pack_into("<I", page, NODE_33_OFFSET + 0xC, dims_pointer & 0xFFFFFFFF)
    struct.pack_into("<h", page, DIMS_OFFSET, case["dims"][0])
    struct.pack_into("<h", page, DIMS_OFFSET + 2, case["dims"][1])
    return bytes(page)


def read_s16(page: bytes, offset: int) -> int:
    return struct.unpack_from("<h", page, offset)[0]


class Machine:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.mem_map(0, ZERO_SIZE)
        self.uc.mem_map(IMAGE_ADDR, IMAGE_SIZE)
        self.uc.mem_map(WORK_ADDR, WORK_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)
        self.uc.mem_write(IMAGE_ADDR, image_bytes())

        self.orig_code = get_orig_bytes()
        self.call_log: list = []
        self.case: dict = {}
        self.region_calls = 0
        self._install_stubs()

    def _install_stubs(self) -> None:
        bx_lr = struct.pack("<I", 0xE12FFF1E)
        for address, hook in (
            (STUB_2B9008, self._on_release),
            (STUB_27EDF8, self._on_fill_pair),
            (STUB_29F248, self._on_selected_row),
            (STUB_2BF6D0, self._on_resolve_node),
            (STUB_29E2F4, self._on_register_rect),
        ):
            self.uc.mem_write(address, bx_lr)
            self.uc.hook_add(unicorn.UC_HOOK_CODE, hook, begin=address, end=address)

    # -- stub bodies ------------------------------------------------------
    def _on_release(self, uc, address, size, user_data) -> None:
        self.call_log.append(("camp_func_002b9008",))

    def _on_fill_pair(self, uc, address, size, user_data) -> None:
        dst = uc.reg_read(arm.UC_ARM_REG_R0)
        value = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("UiConfig_FillPair", dst, value & 0xFFFFFFFF))
        # Original body of 0x0027EDF8, which this routine consumes verbatim.
        replicated = (value & 0xFF) * 0x01010101
        uc.mem_write(dst, struct.pack("<II", replicated, replicated))

    def _on_selected_row(self, uc, address, size, user_data) -> None:
        slot = uc.reg_read(arm.UC_ARM_REG_R0)
        self.call_log.append(("camp_func_0029f248", slot))
        uc.reg_write(arm.UC_ARM_REG_R0, self.case["selected"] & 0xFFFFFFFF)

    def _on_resolve_node(self, uc, address, size, user_data) -> None:
        group = uc.reg_read(arm.UC_ARM_REG_R0)
        node_id = uc.reg_read(arm.UC_ARM_REG_R1)
        self.call_log.append(("UiLayout_ResolveNode", group, node_id))
        uc.reg_write(arm.UC_ARM_REG_R0, node_address(self.case, node_id))

    def _on_register_rect(self, uc, address, size, user_data) -> None:
        args = tuple(
            uc.reg_read(reg)
            for reg in (
                arm.UC_ARM_REG_R0,
                arm.UC_ARM_REG_R1,
                arm.UC_ARM_REG_R2,
                arm.UC_ARM_REG_R3,
            )
        )
        self.call_log.append(("UiTouch_RegisterRectRegion",) + args)
        results = self.case["region_results"]
        value = results[min(self.region_calls, len(results) - 1)]
        self.region_calls += 1
        # s16 return value, sign-extended by the ARM ABI.
        uc.reg_write(arm.UC_ARM_REG_R0, s16(value) & 0xFFFFFFFF)

    # -- execution --------------------------------------------------------
    def run(self, candidate: bytes | None, case: dict) -> dict:
        uc = self.uc
        self.case = case
        self.call_log = []
        self.region_calls = 0

        uc.mem_write(WORK_ADDR, build_work(case))
        uc.mem_write(NODE_ADDR, build_nodes(case))
        uc.mem_write(0, b"\x00" * ZERO_SIZE)
        uc.mem_write(GLOBAL_ADDR, struct.pack("<I", WORK_ADDR))
        uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        uc.mem_write(FUNC_ADDR, self.orig_code if candidate is None else candidate)
        uc.ctl_flush_tb()

        uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for index, reg in enumerate(
            [arm.UC_ARM_REG_R0, arm.UC_ARM_REG_R1, arm.UC_ARM_REG_R2, arm.UC_ARM_REG_R3]
        ):
            uc.reg_write(reg, 0xA0000000 + index)
        for index, reg in enumerate(CALLEE_SAVED):
            uc.reg_write(reg, 0x11110000 + index * 0x1111)

        try:
            uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as exc:  # pragma: no cover - diagnostic path
            raise RuntimeError(
                f"Crash at PC=0x{uc.reg_read(arm.UC_ARM_REG_PC):08x}: {exc}"
            ) from exc
        finally:
            uc.ctl_flush_tb()

        sp = uc.reg_read(arm.UC_ARM_REG_SP)
        return {
            "call_log": list(self.call_log),
            "r0": uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": sp,
            "callee_saved": [uc.reg_read(reg) for reg in CALLEE_SAVED],
            "work": bytes(uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "nodes": bytes(uc.mem_read(NODE_ADDR, NODE_SIZE)),
            "zero": bytes(uc.mem_read(0, ZERO_SIZE)),
            "global_page": bytes(uc.mem_read(GLOBAL_PAGE, GLOBAL_PAGE_SIZE)),
            "stack_below": bytes(uc.mem_read(STACK_ADDR, sp - 0x40 - STACK_ADDR)),
            "stack_above": bytes(uc.mem_read(sp, STACK_ADDR + STACK_SIZE - sp)),
        }


# ---------------------------------------------------------------------------
# Independent expected model
# ---------------------------------------------------------------------------
def expected_case(case: dict) -> dict:
    work = bytearray(build_work(case))
    nodes = bytearray(build_nodes(case))
    zero = bytearray(ZERO_SIZE)
    log: list = []

    def read_half(addr: int, offset: int) -> int:
        if addr < ZERO_SIZE:
            return struct.unpack_from("<H", zero, addr + offset)[0]
        return struct.unpack_from("<H", nodes, addr - NODE_ADDR + offset)[0]

    def read_signed(addr: int, offset: int) -> int:
        if addr < ZERO_SIZE:
            return struct.unpack_from("<h", zero, addr + offset)[0]
        return struct.unpack_from("<h", nodes, addr - NODE_ADDR + offset)[0]

    def read_word(addr: int, offset: int) -> int:
        if addr < ZERO_SIZE:
            return struct.unpack_from("<I", zero, addr + offset)[0]
        return struct.unpack_from("<I", nodes, addr - NODE_ADDR + offset)[0]

    log.extend([("camp_func_002b9008",)] * max(0, s16(case["previous"])))

    log.append(("UiConfig_FillPair", WORK_ADDR + REGION_HANDLES, 0xFFFFFFFF))
    work[REGION_HANDLES:REGION_HANDLES + 8] = b"\xff" * 8
    struct.pack_into("<H", work, REGION_COUNT, 0)

    log.append(("camp_func_0029f248", WORK_ADDR + LIST_CURSOR))
    selected = case["selected"] & 0xFFFFFFFF

    def resolve(node_id: int) -> int:
        log.append(("UiLayout_ResolveNode", NODE_GROUP, node_id & 0xFFFFFFFF))
        return node_address(case, node_id & 0xFFFFFFFF)

    def register(anchor: int, node: int) -> None:
        x = u16(read_half(anchor, 8) + read_half(node, 8))
        y = u16(read_half(anchor, 0xA) + read_half(node, 0xA))
        width = read_half(node, 4) & 0x7FFF
        height = read_half(node, 6) & 0x7FFF
        args = (
            (s16(x) & 0xFFFFFFFF),
            (s16(y) & 0xFFFFFFFF),
            width,
            height,
        )
        log.append(("UiTouch_RegisterRectRegion",) + args)
        results = case["region_results"]
        index = len([entry for entry in log if entry[0] == "UiTouch_RegisterRectRegion"]) - 1
        return results[min(index, len(results) - 1)]

    anchor = resolve(anchor_node_id(selected))
    base_node = resolve(0x1B)
    struct.pack_into("<H", work, REGION_HANDLES, u16(register(anchor, base_node)))

    struct.pack_into(
        "<H", work, REGION_COUNT,
        u16(struct.unpack_from("<H", work, REGION_COUNT)[0] + 1),
    )

    node_34 = resolve(0x34)
    struct.pack_into("<H", work, REGION_HANDLES + 2, u16(register(anchor, node_34)))

    node_38 = resolve(0x38)
    struct.pack_into("<H", work, REGION_HANDLES + 4, u16(register(anchor, node_38)))

    node_33 = resolve(0x33)
    x = u16(read_half(anchor, 8) + read_half(node_33, 8))
    y = u16(read_half(anchor, 0xA) + read_half(node_33, 0xA))
    extents = read_word(node_33, 0xC)
    args = (
        s16(x) & 0xFFFFFFFF,
        s16(y) & 0xFFFFFFFF,
        read_signed(extents, 0) & 0xFFFFFFFF,
        read_signed(extents, 2) & 0xFFFFFFFF,
    )
    log.append(("UiTouch_RegisterRectRegion",) + args)
    results = case["region_results"]
    index = len([entry for entry in log if entry[0] == "UiTouch_RegisterRectRegion"]) - 1
    struct.pack_into(
        "<H", work, REGION_HANDLES + 6, u16(results[min(index, len(results) - 1)])
    )

    count = u16(struct.unpack_from("<H", work, REGION_COUNT)[0] + 3)
    struct.pack_into("<H", work, REGION_COUNT, count)

    return {
        "call_log": log,
        "r0": count,
        "work": bytes(work),
        "nodes": bytes(nodes),
        "zero": bytes(zero),
    }


# ---------------------------------------------------------------------------
# Cases
# ---------------------------------------------------------------------------
def make_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "previous": 0,
        "selected": 0,
        "anchor": (0x0100, 0x0200, 0x0010, 0x0020),
        "nodes": {
            0x1B: (0x0001, 0x0002, 0x0030, 0x0040),
            0x34: (0x0003, 0x0004, 0x0050, 0x0060),
            0x38: (0x0005, 0x0006, 0x0070, 0x0080),
            0x33: (0x0007, 0x0008, 0x0090, 0x00A0),
        },
        "dims": (0x0011, 0x0022),
        "dims_pointer": None,
        "null_ids": set(),
        "region_results": (0, 1, 2, 3),
    }
    case.update(overrides)
    return case


def build_cases() -> list[dict]:
    cases: list[dict] = []

    # --- previous-region release loop and its signed bound ---------------
    cases.append(make_case("previous count 0 -> no release calls"))
    cases.append(make_case("previous count 1 -> one release call", previous=1))
    cases.append(make_case("previous count 5 -> five release calls", previous=5,
                           selected=1))
    cases.append(make_case("previous 0xffff (-1) -> skipped", previous=0xFFFF))
    cases.append(make_case("previous 0x8000 (-32768) -> skipped", previous=0x8000))
    cases.append(make_case("previous 0x0001 selected 2", previous=1, selected=2))

    # --- selected-row / anchor node id -----------------------------------
    cases.append(make_case("selected 0 -> anchor id 0x1f", selected=0))
    cases.append(make_case("selected 2 -> anchor id 0x21", selected=2))
    cases.append(make_case("selected -1 -> anchor id 0x1e", selected=-1))
    cases.append(make_case("selected -4 collides with 0x1b", selected=-4))
    cases.append(make_case("selected 0x7fffffff wraps", selected=0x7FFFFFFF))
    cases.append(make_case("selected 0xfffffff1 -> 0x10", selected=-15))
    cases.append(make_case("selected 0x80000000 wraps", selected=-0x80000000))

    # --- null helper results read the zero page --------------------------
    cases.append(make_case("anchor lookup null", null_ids={0x1F}))
    cases.append(make_case("base 0x1b lookup null", null_ids={0x1B}))
    cases.append(make_case("tail 0x33 lookup null", null_ids={0x33}))
    cases.append(make_case("all fixed lookups null",
                           null_ids={0x1F, 0x1B, 0x34, 0x38, 0x33}))

    # --- halfword boundaries and signed coordinate sums ------------------
    cases.append(make_case(
        "anchor 0x7fff + node 0x7fff wraps to -2",
        anchor=(0x7FFF, 0x7FFF, 0xFFFF, 0xFFFF),
        nodes={0x1B: (0x7FFF, 0x7FFF, 0xFFFF, 0xFFFF),
               0x34: (0x7FFF, 0x7FFF, 0x8000, 0x8001),
               0x38: (0x7FFF, 0x7FFF, 0xFFFF, 0x0000),
               0x33: (0x7FFF, 0x7FFF, 0x0000, 0x0000)},
        previous=2,
    ))
    cases.append(make_case(
        "anchor 0x8000 + node 0x8000 wraps to 0",
        anchor=(0x8000, 0x8000, 0x0000, 0x0000),
        nodes={0x1B: (0x8000, 0x8000, 0x8000, 0xFFFF),
               0x34: (0x0001, 0x0002, 0x7FFF, 0x8000),
               0x38: (0xFFFF, 0xFFFE, 0x0001, 0x0002),
               0x33: (0x0003, 0x0004, 0x0000, 0x0000)},
    ))
    cases.append(make_case(
        "extent bit 15 masked on every record",
        nodes={0x1B: (0x0001, 0x0002, 0x8000, 0x8001),
               0x34: (0x0003, 0x0004, 0xC000, 0xFFFF),
               0x38: (0x0005, 0x0006, 0x8000, 0x0000),
               0x33: (0x0007, 0x0008, 0x7FFF, 0x8000)},
        anchor=(0x0000, 0x0000, 0x8000, 0x8000),
    ))

    # --- tail extents are signed halfwords behind [node+0xc] -------------
    cases.append(make_case("tail dims negative/positive", dims=(-0x8000, 0x7FFF)))
    cases.append(make_case("tail dims both negative", dims=(-1, -2)))
    cases.append(make_case("tail dims both zero", dims=(0, 0)))
    cases.append(make_case("tail dims pointer is null", dims_pointer=0))
    cases.append(make_case("tail dims pointer into zero page", dims_pointer=4,
                           dims=(-0x1234, 0x5678)))

    # --- region handle results, including negatives and 16-bit wrap ------
    cases.append(make_case("region results negative", region_results=(-1, -2, 0x7FFF, 0x8000)))
    cases.append(make_case("region results wrap 0xffff", region_results=(0xFFFF, 0x10000, 0, -0x8000)))
    cases.append(make_case("single region result repeated", region_results=(0x1234,)))

    # --- combined boundary case used by the loop/mask mutants ------------
    cases.append(make_case(
        "all records at halfword boundaries",
        previous=3,
        selected=0x7FFFFFFF,
        anchor=(0x7FFF, 0x8000, 0x0000, 0xFFFF),
        nodes={0x1B: (0x8001, 0x7FFF, 0xFFFF, 0x8000),
               0x34: (0xFFFF, 0x0001, 0x8001, 0x7FFF),
               0x38: (0x8000, 0x8000, 0xFFFF, 0xFFFF),
               0x33: (0x0002, 0xFFFE, 0x8000, 0x0001)},
        dims=(-0x8000, 0x7FFF),
        region_results=(-1, 0x7FFF, -0x8000),
    ))

    return cases


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("r0", "pc", "sp", "callee_saved", "work", "nodes", "zero",
                "global_page", "stack_below", "stack_above"):
        if orig[key] != cand[key]:
            problems.append(f"{key} differs")
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig=" + repr(orig["call_log"])
            + "\n    cand=" + repr(cand["call_log"])
        )
    return problems


def check_against_model(case: dict, result: dict) -> None:
    model = expected_case(case)
    assert result["call_log"] == model["call_log"], (
        f"model call log mismatch on {case['name']}:\n"
        f"  Expected: {model['call_log']}\n  Actual:   {result['call_log']}"
    )
    assert result["r0"] == model["r0"], (
        f"model return mismatch on {case['name']}: "
        f"0x{result['r0']:08x} != 0x{model['r0']:08x}"
    )
    assert result["work"] == model["work"], f"model work mismatch on {case['name']}"
    assert result["nodes"] == model["nodes"], f"model node mismatch on {case['name']}"
    assert result["zero"] == model["zero"], f"model zero-page mismatch on {case['name']}"


def main() -> None:
    print("Testing camp_func_0025a0d0 (0x0025a0d0)...")
    cand = compile_candidate()
    print(f"  original: {FUNC_SIZE} B, candidate: {len(cand)} B")

    machine = Machine()
    cases = build_cases()
    passed = 0

    for case in cases:
        res_orig = machine.run(None, case)
        res_cand = machine.run(cand, case)
        problems = compare(res_orig, res_cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        check_against_model(case, res_cand)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(res_orig['call_log'])} calls)")

    print("\nNegative controls:")
    mutants = [
        (
            "anchor_node_id_offset",
            "static_cast<u32>(selected_row) + 0x1Fu",
            "static_cast<u32>(selected_row) + 0x20u",
        ),
        (
            "extent_mask_keeps_bit15",
            "LoadHalfword(node, kExtentOffset) & ~kExtentSizeBit",
            "LoadHalfword(node, kExtentOffset)",
        ),
        (
            "region_count_step_two",
            "LoadHalfword(work, kRegionCountOffset) + 1u",
            "LoadHalfword(work, kRegionCountOffset) + 2u",
        ),
        (
            "tail_node_id",
            "UiLayout_ResolveNode(kNodeGroup, 0x33u)",
            "UiLayout_ResolveNode(kNodeGroup, 0x35u)",
        ),
        (
            "release_loop_inclusive",
            "index < previous_count",
            "index <= previous_count",
        ),
        (
            "final_count_step_two",
            "LoadHalfword(work, kRegionCountOffset) + 3u",
            "LoadHalfword(work, kRegionCountOffset) + 2u",
        ),
    ]
    for name, old, new in mutants:
        mutant = compile_mutant(name, old, new)
        detected = False
        for case in cases:
            res_orig = machine.run(None, case)
            res_mut = machine.run(mutant, case)
            if compare(res_orig, res_mut):
                detected = True
                break
        assert detected, f"negative control not detected: {name}"
        print(f"  [PASS] mutant detected: {name}")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
