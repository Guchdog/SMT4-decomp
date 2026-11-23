#!/usr/bin/env python3
"""Differential test for camp_func_0033d164 (0x0033d164) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the camp_func_0033d164 body,
resolves its direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP, callee-saved r4-r11;
  * the ordered call log with every argument of both helpers (the resolver's
    (group, node_index) and the zero-fill's (pointer, size));
  * the full panel page and the read-only layout-node page;
  * any emulated write outside the panel page and the private stack.

Coverage: every one of the 18 resolver node indices, sign-extension boundaries
(s16 0x0000/0x0001/0xFFFF/0x7FFF/0x8000) for each of the six value groups
(icons, title, tabs, item positions, both labels), the tab extrapolation with
positive and negative boundaries, four panel prefill patterns and a resolver
null result (both sides must fault identically on the first load). Negative
controls mutate a node index, the extrapolation sign, an idle count, the label
field selection and the clear length; each mutant must be detected.
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
OUT_DIR = ROOT / "build/test_leaf_0033d164"

FUNC_ADDR = 0x0033D164
FUNC_SIZE = 448

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and every stub below 0x3F0000
PANEL_ADDR = 0x00710000
PANEL_SIZE = 0x00010000
NODE_ADDR = 0x00720000
NODE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

# Original direct-call targets; stubs are placed at the same addresses so both
# the original bytes and the relocated candidate resolve to them.
STUB_2BF6D0 = 0x002BF6D0
STUB_2C4B30 = 0x002C4B30

STUB_NAMES = {
    STUB_2BF6D0: "camp_func_002bf6d0",
    STUB_2C4B30: "engine_func_002c4b30",
}

# Node indices requested by the routine: 0x59..0x60 (icons), 0x61 (title),
# 0x62..0x64 (tabs), 0x65..0x68 (item positions), 0x69/0x6A (label Y values).
NODE_INDEX_MIN = 0x59
NODE_INDEX_MAX = 0x6A
NODE_STRIDE = 0x40
NODE_BASE = 0x100
NODE_UNKNOWN = 0xC00

# Panel layout written by the routine (all offsets from ARM evidence).
OFF_ITEM_COUNT = 0x2F4
OFF_COLUMN_A = 0x2F8
OFF_COLUMN_B = 0x2FC
OFF_TITLE = 0x300
OFF_TABS = 0x308       # three Vec2 (0x64, 0x63, 0x62)
OFF_TAB_END = 0x320
OFF_ICONS = 0x328      # four ItemIcon (two Vec2 each)
OFF_ITEM_POS = 0x368   # four Vec2 (0x65..0x68)
OFF_LABEL = 0x388      # two floats: +0x388 node 0x69, +0x38C node 0x6A
OFF_STATE = 0x390
OFF_SCALE = 0x394
OFF_FADE = 0x398
OFF_PROGRESS = 0x39C
OFF_OFFSET = 0x3A0
CLEAR_LENGTH = 0x2F4

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
        if "0033d164" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_0033d164 not found in {obj_file}: {sorted(funcs)}"
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
            displacement = (target - (FUNC_ADDR + rel.offset + 8)) >> 2
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into(
                "<I", code, rel.offset, cond | (displacement & 0x00FFFFFF)
            )
        elif rel.relocation_type == 2:  # R_ARM_ABS32
            # The candidate keeps its 0.0f/4.0f literals in a local PC-relative
            # pool, so no ABS32 relocation is expected.
            raise RuntimeError(
                f"unexpected ABS32 relocation for {rel.symbol_name}"
            )
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
def node_offset(index: int) -> int:
    if NODE_INDEX_MIN <= index <= NODE_INDEX_MAX:
        return NODE_BASE + (index - NODE_INDEX_MIN) * NODE_STRIDE
    return NODE_UNKNOWN


def default_pair(index: int) -> tuple[int, int]:
    k = index - NODE_INDEX_MIN
    x = ((k * 0x111) & 0x7FFF) - 0x0800
    y = 0x0600 - ((k * 0x171) & 0x1FFF)
    return x, y


def build_node(case: dict) -> bytes:
    page = bytearray([0xA5] * NODE_SIZE)
    overrides = case.get("nodes", {})
    for index in range(NODE_INDEX_MIN, NODE_INDEX_MAX + 1):
        x, y = overrides.get(index, default_pair(index))
        offset = node_offset(index)
        struct.pack_into("<I", page, offset + 0x0, 0x59000000 | index)
        struct.pack_into("<I", page, offset + 0x4, 0x5D000000 | index)
        struct.pack_into("<h", page, offset + 0x8, x)
        struct.pack_into("<h", page, offset + 0xA, y)
        # Elements 6/7 and the rest of the stride are never read; keep
        # sentinels so an unintended wider load would change no fixture but a
        # wider store would be caught.
        struct.pack_into("<h", page, offset + 0xC, 0x1234 + index)
        struct.pack_into("<h", page, offset + 0xE, 0x2345 - index)
    # Explicit unknown slot for an out-of-range resolver index.
    struct.pack_into("<h", page, NODE_UNKNOWN + 0x8, 0x1111)
    struct.pack_into("<h", page, NODE_UNKNOWN + 0xA, 0x2222)
    return bytes(page)


def build_panel(case: dict) -> bytes:
    page = bytearray([case.get("panel_fill", 0xA5)] * PANEL_SIZE)
    # Preload the geometry fields with a different pattern so a missing store
    # (rather than an overwritten one) is visible; the clear length is also
    # checked against these bytes.
    for offset in range(0x2F4, 0x3A4, 4):
        struct.pack_into("<I", page, offset, 0xDEAD0000 | offset)
    for offset, value in case.get("panel_words", {}).items():
        struct.pack_into("<I", page, offset, value)
    return bytes(page)


class D164Runner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Enable the VFP coprocessor (CP10/CP11) for vcvt/vmov/vldr/vstr.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(PANEL_ADDR, PANEL_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
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

    # ------------------------------------------------------------------ stubs
    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        if address == STUB_2BF6D0:
            self.call_log.append((STUB_NAMES[address], r0, r1))
            if self.case.get("resolve_null", False):
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, NODE_ADDR + node_offset(r1))
        elif address == STUB_2C4B30:
            self.call_log.append((STUB_NAMES[address], r0, r1))
            if r1:
                uc.mem_write(r0, b"\x00" * r1)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    # -------------------------------------------------------------- execution
    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(PANEL_ADDR, build_panel(case))
        self.uc.mem_write(NODE_ADDR, build_node(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, PANEL_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        faulted = None
        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError as error:
            faulted = (self.uc.reg_read(arm.UC_ARM_REG_PC), str(error))

        panel = bytes(self.uc.mem_read(PANEL_ADDR, PANEL_SIZE))
        node = bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE))

        unexpected_writes = []
        for address, size in self.writes:
            in_panel = PANEL_ADDR <= address < PANEL_ADDR + PANEL_SIZE
            in_stack = STACK_ADDR <= address < STACK_ADDR + STACK_SIZE
            if size == 0:
                in_panel = in_stack = True
            elif not (in_panel or in_stack):
                unexpected_writes.append((address, size))

        return {
            "faulted": faulted is not None,
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "panel": panel,
            "node": node,
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if orig["faulted"] != cand["faulted"]:
        problems.append(f"faulted: orig={orig['faulted']} cand={cand['faulted']}")
        return problems
    if orig["call_log"] != cand["call_log"]:
        problems.append(
            "call_log:\n    orig="
            + repr(orig["call_log"])
            + "\n    cand="
            + repr(cand["call_log"])
        )
        return problems
    if orig["faulted"]:
        # Fault path: only the identical ordered prefix is meaningful.
        return problems
    for key in ("ret", "pc", "sp", "callee_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if orig["panel"] != cand["panel"]:
        for offset in range(0, PANEL_SIZE, 4):
            left = orig["panel"][offset : offset + 4]
            right = cand["panel"][offset : offset + 4]
            if left != right:
                problems.append(
                    f"panel word +0x{offset:03X}: orig={left.hex()} cand={right.hex()}"
                )
    if orig["node"] != cand["node"]:
        problems.append("node page was modified differently")
    if orig["unexpected_writes"] or cand["unexpected_writes"]:
        problems.append(
            "unexpected writes orig="
            f"{orig['unexpected_writes']} cand={cand['unexpected_writes']}"
        )
    return problems


def base_case(name: str, **overrides) -> dict:
    case = {"name": name, "panel_fill": 0xA5}
    case.update(overrides)
    return case


ALL_NODES = range(NODE_INDEX_MIN, NODE_INDEX_MAX + 1)


def all_nodes(pair: tuple[int, int]) -> dict:
    return {index: pair for index in ALL_NODES}


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- baseline and panel prefill patterns.
    cases.append(base_case("baseline default layout"))
    for fill in (0x00, 0x5A, 0xFF):
        cases.append(base_case(f"panel prefill 0x{fill:02X}", panel_fill=fill))

    # --- every resolver value group at the signed 16-bit boundaries.
    for x, y in (
        (0x0000, 0x0000),
        (1, -1),
        (-1, 1),
        (2, -2),
        (0x7FFF, 0x7FFF),
        (-0x8000, -0x8000),
        (0x7FFF, -0x8000),
        (-0x8000, 0x7FFF),
    ):
        cases.append(
            base_case(f"all nodes x={x} y={y}", nodes=all_nodes((x, y)))
        )

    # --- per-group boundaries so each field is exercised independently.
    cases.append(
        base_case(
            "icons boundary",
            nodes={
                0x59: (0x7FFF, -0x8000),
                0x5A: (-0x8000, 0x7FFF),
                0x5B: (-1, 1),
                0x5C: (1, -1),
                0x5D: (-0x8000, -0x8000),
                0x5E: (0x7FFF, 0x7FFF),
                0x5F: (0x0000, 0x0000),
                0x60: (0x4000, -0x4000),
            },
        )
    )
    cases.append(
        base_case("title boundary", nodes={0x61: (-0x8000, 0x7FFF)})
    )
    cases.append(
        base_case(
            "tabs boundary positive",
            nodes={0x64: (0x7FFF, 0x7FFF), 0x63: (-0x8000, -0x8000),
                   0x62: (0x0000, 0x0000)},
        )
    )
    cases.append(
        base_case(
            "tabs boundary negative",
            nodes={0x64: (-0x8000, 0x0000), 0x63: (0x7FFF, 0x0000),
                   0x62: (-0x8000, 0x7FFF)},
        )
    )
    cases.append(
        base_case(
            "tabs extrapolation wide",
            nodes={0x64: (0x7FFF, 0x0001), 0x63: (-0x8000, 0x0002),
                   0x62: (0x7FFF, 0x0003)},
        )
    )
    cases.append(
        base_case(
            "item positions boundary",
            nodes={0x65: (0x7FFF, -0x8000), 0x66: (-0x8000, 0x7FFF),
                   0x67: (-1, 0x0000), 0x68: (1, -1)},
        )
    )
    cases.append(
        base_case(
            "labels boundary",
            nodes={0x69: (0x7FFF, -1), 0x6A: (-0x8000, -0x8000)},
        )
    )
    cases.append(
        base_case(
            "labels ignore element 4",
            nodes={0x69: (0x1234, 0x0002), 0x6A: (0x5678, 0x0003)},
        )
    )

    # --- one distinct value per node to pin the exact index mapping/order.
    cases.append(
        base_case(
            "distinct accent per node",
            nodes={
                index: (((index * 37) & 0x7FF) - 0x400,
                        (((index * 53) & 0x7FF) - 0x400))
                for index in ALL_NODES
            },
        )
    )

    # --- resolver returns null: both sides must fault on the first load.
    cases.append(base_case("resolver null faults", resolve_null=True))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = D164Runner().run(orig_code, case)
        cand = D164Runner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        state = "faulted" if orig["faulted"] else f"{len(orig['call_log'])} calls"
        print(f"  [PASS] {case['name']}  ({state})")
    return passed


def main() -> None:
    print("Testing camp_func_0033d164 (0x0033d164)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(relocations resolved)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("icon_node_index", "layout_node(i + 0x59u)", "layout_node(i + 0x5Au)"),
        ("tab_extrapolation_sign",
         "self->tab_end.x = (last_x - middle_x) + last_x;",
         "self->tab_end.x = (last_x - middle_x) - last_x;"),
        ("idle_item_count", "self->item_count = 0;", "self->item_count = 1;"),
        ("label_node_x_field",
         "self->label_origin.x = static_cast<f32>(label_a[5]);",
         "self->label_origin.x = static_cast<f32>(label_a[4]);"),
        ("clear_length", "engine_func_002c4b30(self, kPanelSize);",
         "engine_func_002c4b30(self, 0x2F0u);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            if case.get("resolve_null"):
                continue
            orig = D164Runner().run(orig_code, case)
            bad = D164Runner().run(mutant_code, case)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
