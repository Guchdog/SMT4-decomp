#!/usr/bin/env python3
"""Differential test for engine_func_002a399c (0x002a399c).

`AsdPart_SetScale(part, scale)` stores the new scale and walks the part's child
list, dispatching each child into the 0x00464110 type table (0x44-byte entries).
This runner compiles src/engine/leaf_batch45_a.cpp, extracts that one function,
and executes the pinned original (extracted/exefs/code.bin) and the candidate in
separate Unicorn ARM machines with identical fixtures.

Compared:
  * continuation PC, final SP and the callee-saved integer registers r4-r11;
  * the callee-saved VFP registers s16-s31 (the original saves d8 because it
    uses s16/s17 for the inherited factor);
  * the ordered hook log: kind, type index, hook context (r0), and either the
    16 raw bytes of the quad passed by pointer or the raw s0 bits of the
    scalar hook;
  * the full self/node/instance page, the 0x00464110 type-table page, the
    0x004EA81C render-state page and the stub capture page;
  * any emulated write outside the stack, self page, render page or capture.

The +0x20/+0x2C hook implementations read only r1 (a pointer to the quad), and
the +0x28 hook reads only s0, which is how the indirect argument contract was
recovered from the table targets (e.g. 0x00318DE0, 0x002197AC, 0x002F9F44).
The unrelated s0/s1 leftovers in the original at the pointer hooks are not part
of that contract.  The function returns void; r0 is compared only for the empty
child list, where the original provably leaves `self` in r0.

Coverage: empty list; flag combinations 0 / 0x100 / 0x80 / 0x100|0x80 plus the
unrelated bits; null hooks at each of +0x20/+0x28/+0x2C; several type indices
(table stride); two- and three-node chains (call order and next-pointer reload);
zero, negative and non-finite scale/factor boundaries; signed-zero and large
quad components.  Negative controls mutate each flag constant, the Y override,
the type-table base, the render-state base and the factor operation.
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
OUT_DIR = ROOT / "build/test_leaf_002a399c"

FUNC_ADDR = 0x002A399C
FUNC_SIZE = 604

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00200000  # covers the function and the stub block at 0x310000

SELF_ADDR = 0x00700000
SELF_SIZE = 0x00010000
TABLE_ADDR = 0x00464000  # contains the 0x00464110 type table
TABLE_SIZE = 0x00010000
RENDER_ADDR = 0x004EA000  # contains 0x004EA81C
RENDER_SIZE = 0x00001000
CAPTURE_ADDR = 0x00720000
CAPTURE_SIZE = 0x00010000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

TYPE_TABLE_BASE = 0x00464110
TYPE_STRIDE = 0x44
TYPE_COUNT = 35  # the real table at 0x00464110 has 35 entries

# Distinct stub triples per type index: a wrong entry/stride is visible in the
# logged hook address as well as in the arguments.
STUB_BASE = 0x00310000
STUB_STRIDE = 0x30
KIND_QUAD = 0  # hook +0x20
KIND_SCALE = 1  # hook +0x28
KIND_QUAD_REF = 2  # hook +0x2C
CAPTURE_STRIDE = 0x20

SELF_OBJECT = SELF_ADDR + 0x100
NODE_BASE = SELF_ADDR + 0x200
NODE_STRIDE = 0x100
INSTANCE_BASE = SELF_ADDR + 0x1000
INSTANCE_STRIDE = 0x100
CONTEXT_BASE = SELF_ADDR + 0x1800
CONTEXT_STRIDE = 0x40

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
VFP_SAVED = {f"s{i}": getattr(arm, f"UC_ARM_REG_S{i}") for i in range(16, 32)}
VFP_SAVED_START = {f"s{i}": 0x3F000000 + i for i in range(16, 32)}


def stub_address(type_index: int, kind: int) -> int:
    return STUB_BASE + type_index * STUB_STRIDE + kind * 0x10


def bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


ZERO = 0x00000000
NEG_ZERO = 0x80000000
ONE = 0x3F800000
NEG_ONE = 0xBF800000
HALF = 0x3F000000
TWO = 0x40000000
THREE = 0x40400000
FOUR = 0x40800000
NEG_TWO = 0xC0000000
FIVE = 0x40A00000
POS_INF = 0x7F800000
NEG_INF = 0xFF800000
BIG = 0x7F7FFFFF  # largest finite float


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def extract_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002a399c" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"engine_func_002a399c not found in {obj_file}: {sorted(funcs)}"
        )
    raw, relocs = candidate
    if relocs:
        raise RuntimeError(
            "candidate unexpectedly has relocations: "
            f"{[(r.offset, r.relocation_type, r.symbol_name) for r in relocs]}"
        )
    return raw


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    res = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if res.returncode != 0:
        raise RuntimeError(f"Compilation failed: {res.stderr}")
    return extract_candidate(obj_file)


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
    return extract_candidate(obj_file)


def pack_words(words) -> bytes:
    return struct.pack("<4I", *(w & 0xFFFFFFFF for w in words))


def build_self(case: dict) -> bytes:
    page = bytearray(SELF_SIZE)
    self_case = case["self"]
    base_self = SELF_OBJECT - SELF_ADDR
    page[base_self + 0x00:base_self + 0x10] = pack_words(
        self_case.get("position", [ONE, TWO, 0, 0])
    )
    page[base_self + 0x40:base_self + 0x50] = pack_words(
        self_case.get("quad_40", [ZERO, ZERO, ZERO, ZERO])
    )
    struct.pack_into("<I", page, base_self + 0x60,
                     self_case.get("local_scale", ONE))
    struct.pack_into("<I", page, base_self + 0x74,
                     self_case.get("scale_unit", ONE))

    nodes = case.get("nodes", [])
    struct.pack_into("<I", page, base_self + 0x8C, NODE_BASE if nodes else 0)

    for index, node in enumerate(nodes):
        base = (NODE_BASE - SELF_ADDR) + index * NODE_STRIDE
        page[base + 0x00:base + 0x10] = pack_words(
            node.get("position", [ZERO, ZERO, ZERO, ZERO])
        )
        page[base + 0x20:base + 0x30] = pack_words(
            node.get("quad_20", [ONE, TWO, 3, 4])
        )
        page[base + 0x40:base + 0x50] = pack_words(
            node.get("quad_40", [HALF, NEG_ONE, 0, ONE])
        )
        struct.pack_into("<I", page, base + 0x60, node.get("local_scale", TWO))
        struct.pack_into("<I", page, base + 0x68, node.get("flags", 0))
        struct.pack_into("<I", page, base + 0x74, node.get("field_74", ZERO))
        struct.pack_into("<I", page, base + 0x84, node.get("scale_flags", 0))
        # Children of a child are not traversed by this routine; keep a marker.
        struct.pack_into("<I", page, base + 0x8C, 0xDEAD0000 | index)
        struct.pack_into(
            "<I", page, base + 0x90, INSTANCE_BASE + index * INSTANCE_STRIDE
        )
        next_ptr = (
            NODE_BASE + (index + 1) * NODE_STRIDE if index + 1 < len(nodes) else 0
        )
        struct.pack_into("<I", page, base + 0xAC, next_ptr)

        inst = (INSTANCE_BASE - SELF_ADDR) + index * INSTANCE_STRIDE
        struct.pack_into("<H", page, inst + 0x04, node.get("type", 0) & 0xFFFF)
        struct.pack_into("<I", page, inst + 0x08, CONTEXT_BASE + index * CONTEXT_STRIDE)
        # Context objects carry a distinct sentinel at +0 so a wrong context is
        # visible in memory as well as in the call log.
        context = (CONTEXT_BASE - SELF_ADDR) + index * CONTEXT_STRIDE
        struct.pack_into("<I", page, context, 0xC0DE0000 | index)
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(TABLE_SIZE)
    disabled = case.get("disabled_hooks", {})
    for type_index in range(TYPE_COUNT):
        entry = TYPE_TABLE_BASE - TABLE_ADDR + type_index * TYPE_STRIDE
        flags = disabled.get(type_index, (True, True, True))
        if flags[0]:
            struct.pack_into("<I", page, entry + 0x20,
                             stub_address(type_index, KIND_QUAD))
        if flags[1]:
            struct.pack_into("<I", page, entry + 0x28,
                             stub_address(type_index, KIND_SCALE))
        if flags[2]:
            struct.pack_into("<I", page, entry + 0x2C,
                             stub_address(type_index, KIND_QUAD_REF))
    return bytes(page)


def read_c_stringless(uc, address: int, size: int) -> bytes:
    return bytes(uc.mem_read(address, size))


class ScaleRunner:
    """One Unicorn ARM machine with a deterministic stub triple per type."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Enable VFP (CP10/CP11); the routine saves d8 and scales with VFP.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(RENDER_ADDR, RENDER_SIZE)
        self.uc.mem_map(CAPTURE_ADDR, CAPTURE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for type_index in range(TYPE_COUNT):
            for kind in (KIND_QUAD, KIND_SCALE, KIND_QUAD_REF):
                address = stub_address(type_index, kind)
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
                self.uc.hook_add(
                    unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
                )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.capture_cursor = 0

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        offset = address - STUB_BASE
        type_index = offset // STUB_STRIDE
        kind = (offset % STUB_STRIDE) // 0x10
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)

        capture = bytearray(CAPTURE_STRIDE)
        struct.pack_into("<I", capture, 0, kind)
        struct.pack_into("<I", capture, 4, type_index)
        struct.pack_into("<I", capture, 8, r0)

        if kind == KIND_SCALE:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            struct.pack_into("<I", capture, 12, s0)
            self.call_log.append(("scale", type_index, r0, s0))
        else:
            quad = read_c_stringless(uc, r1, 16)
            capture[16:32] = quad
            self.call_log.append(
                ("quad" if kind == KIND_QUAD else "quad_ref",
                 type_index, r0, struct.unpack("<4I", quad))
            )

        self.uc.mem_write(
            CAPTURE_ADDR + self.capture_cursor * CAPTURE_STRIDE, bytes(capture)
        )
        self.capture_cursor += 1
        # Return a deliberate non-zero value: callers must not consume it.
        uc.reg_write(arm.UC_ARM_REG_R0, 0x5A5A0000 | offset)

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.capture_cursor = 0

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, build_self(case))
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(RENDER_ADDR, b"\x00" * RENDER_SIZE)
        self.uc.mem_write(CAPTURE_ADDR, b"\x00" * CAPTURE_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_OBJECT)
        self.uc.reg_write(arm.UC_ARM_REG_S0, case.get("scale", ONE))
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
        for address, size, _value in self.writes:
            if not (STACK_ADDR <= address < STACK_ADDR + STACK_SIZE):
                in_self = SELF_ADDR <= address < SELF_ADDR + SELF_SIZE
                in_render = RENDER_ADDR <= address < RENDER_ADDR + RENDER_SIZE
                in_capture = CAPTURE_ADDR <= address < CAPTURE_ADDR + CAPTURE_SIZE
                if not (in_self or in_render or in_capture):
                    unexpected_writes.append((address, size))

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "vfp_saved": {
                name: self.uc.reg_read(reg) for name, reg in VFP_SAVED.items()
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "self": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
                "table": bytes(self.uc.mem_read(TABLE_ADDR, TABLE_SIZE)),
                "render": bytes(self.uc.mem_read(RENDER_ADDR, RENDER_SIZE)),
                "capture": bytes(self.uc.mem_read(CAPTURE_ADDR, CAPTURE_SIZE)),
            },
            "unexpected_writes": unexpected_writes,
        }


def compare(orig: dict, cand: dict, compare_ret: bool) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved"):
        if orig[key] != cand[key]:
            problems.append(f"{key}:\n    orig={orig[key]!r}\n    cand={cand[key]!r}")
    if compare_ret and orig["ret"] != cand["ret"]:
        problems.append(f"ret:\n    orig={orig['ret']!r}\n    cand={cand['ret']!r}")
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
        "scale": ONE,
        "self": {
            "position": [HALF, NEG_ONE, ZERO, ONE],
            "quad_40": [TWO, NEG_TWO, HALF, ZERO],
            "local_scale": ONE,
            "scale_unit": TWO,
        },
        "nodes": [],
    }
    case.update(overrides)
    return case


def make_node(**overrides) -> dict:
    node = {
        "flags": 0,
        "quad_20": [ONE, TWO, THREE, FOUR],
        "quad_40": [HALF, NEG_ONE, ZERO, ONE],
        "local_scale": TWO,
        "scale_flags": 0,
        "type": 0,
        "field_74": ZERO,
    }
    node.update(overrides)
    return node


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Empty child list: immediate return, r0 is provably `self`.
    cases.append(base_case("empty child list"))

    # Scalar (+0x28) path only.
    cases.append(base_case("flags 0 -> +0x28 hook", nodes=[make_node()]))
    cases.append(
        base_case("flags 0, inherit bit -> +0x28 hook",
                  nodes=[make_node(scale_flags=1)])
    )
    cases.append(
        base_case("flags 0, inherit bit, type 3",
                  nodes=[make_node(scale_flags=1, type=3)])
    )

    # Scaled-quad (+0x2C) path.
    cases.append(base_case("flags 0x100 -> +0x2C hook",
                           nodes=[make_node(flags=0x100)]))
    cases.append(
        base_case("flags 0x100, inherit bit -> +0x2C hook",
                  nodes=[make_node(flags=0x100, scale_flags=1)])
    )
    cases.append(
        base_case("flags 0x100, type 5",
                  nodes=[make_node(flags=0x100, type=5)])
    )

    # Composition (+0x20) path, with and without the Y override.
    cases.append(base_case("flags 0x80 -> +0x28 and +0x20",
                           nodes=[make_node(flags=0x80)]))
    cases.append(
        base_case("flags 0x80|4 -> Y override",
                  nodes=[make_node(flags=0x80 | 4)])
    )
    cases.append(
        base_case("flags 0x100|0x80 -> +0x2C and +0x20",
                  nodes=[make_node(flags=0x100 | 0x80, type=7)])
    )
    cases.append(
        base_case("flags 0x100|0x80|4, inherit bit",
                  nodes=[make_node(flags=0x100 | 0x80 | 4, scale_flags=1,
                                   type=2)])
    )

    # Unrelated flag bits must not change the selected paths.
    cases.append(
        base_case("unrelated flag bits",
                  nodes=[make_node(flags=0x80000000 | 0x202 | 0x18 | 0x2)])
    )
    cases.append(
        base_case("unrelated flag bits with compose",
                  nodes=[make_node(flags=0x200 | 0x80 | 0x10)])
    )

    # Null hook slots, one at a time.
    cases.append(
        base_case("null +0x28 hook", nodes=[make_node(type=1)],
                  disabled_hooks={1: (True, False, True)})
    )
    cases.append(
        base_case("null +0x2C hook", nodes=[make_node(flags=0x100, type=1)],
                  disabled_hooks={1: (True, True, False)})
    )
    cases.append(
        base_case("null +0x20 hook", nodes=[make_node(flags=0x80, type=1)],
                  disabled_hooks={1: (False, True, True)})
    )
    cases.append(
        base_case("all hooks null, compose path",
                  nodes=[make_node(flags=0x100 | 0x80, type=6)],
                  disabled_hooks={6: (False, False, False)})
    )

    # Linked-list traversal and hook ordering.
    cases.append(
        base_case("two nodes: +0x2C then +0x80",
                  nodes=[make_node(flags=0x100, type=0),
                         make_node(flags=0x80, type=1)])
    )
    cases.append(
        base_case("three nodes mixed",
                  nodes=[make_node(flags=0x80, type=2),
                         make_node(flags=0x100, type=3),
                         make_node(flags=0, type=4, scale_flags=1)])
    )
    cases.append(
        base_case("two nodes, second null list tail",
                  nodes=[make_node(flags=0x100 | 0x80, type=7),
                         make_node(flags=0x100 | 0x80 | 4, type=0)])
    )

    # Scale/factor boundaries.
    for scale in (ZERO, NEG_ZERO, HALF, NEG_TWO, POS_INF, NEG_INF, BIG):
        cases.append(
            base_case(f"scale 0x{scale:08x}", scale=scale,
                      nodes=[make_node(flags=0x100),
                             make_node(flags=0x80, scale_flags=1)])
        )
    for unit in (ZERO, NEG_ZERO, NEG_ONE, POS_INF, HALF):
        cases.append(
            base_case(f"self scale unit 0x{unit:08x}",
                      self={"position": [ONE, ZERO, NEG_ZERO, ONE],
                            "quad_40": [ZERO, ONE, NEG_ONE, ZERO],
                            "local_scale": NEG_TWO,
                            "scale_unit": unit},
                      nodes=[make_node(flags=0x100 | 0x80, scale_flags=1)])
        )
    for local in (ZERO, NEG_ZERO, POS_INF, NEG_INF, BIG):
        cases.append(
            base_case(f"child local scale 0x{local:08x}",
                      nodes=[make_node(flags=0x100,
                                       local_scale=local,
                                       scale_flags=1)])
        )
    for scale_flags in (0x1, 0x2, 0xFFFFFFFF, 0x80000001):
        cases.append(
            base_case(f"child scale_flags 0x{scale_flags:08x}",
                      nodes=[make_node(flags=0x80, scale_flags=scale_flags)])
        )

    # Signed-zero / large composition inputs exercise the two add passes.
    cases.append(
        base_case("signed-zero composition",
                  self={"position": [NEG_ZERO, ZERO, NEG_ZERO, ONE],
                        "quad_40": [ZERO, NEG_ZERO, ONE, NEG_ZERO],
                        "local_scale": ONE,
                        "scale_unit": ZERO},
                  nodes=[make_node(flags=0x80 | 4, quad_40=[NEG_ZERO, NEG_ZERO,
                                                           ZERO, ZERO])])
    )
    cases.append(
        base_case("large composition values",
                  self={"position": [BIG, NEG_INF, BIG, NEG_ZERO],
                        "quad_40": [NEG_INF, BIG, ONE, TWO],
                        "local_scale": HALF,
                        "scale_unit": TWO},
                  nodes=[make_node(flags=0x100 | 0x80,
                                   quad_20=[BIG, NEG_INF, NEG_ZERO, TWO],
                                   quad_40=[BIG, BIG, NEG_INF, NEG_ZERO])])
    )

    # Type index coverage (table stride / zero-extension of the u16 type).
    # Index 0xFF is past the 35 real entries, so its hook words are zero and no
    # call may happen; it proves the u16 type is used as a plain unsigned index.
    for type_index in (0, 1, 2, 4, 7, 20, 34, 8, 0xFF):
        cases.append(
            base_case(f"type index {type_index:#06x}",
                      nodes=[make_node(flags=0x100 | 0x80,
                                       type=type_index)])
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = ScaleRunner().run(orig_code, case)
        cand = ScaleRunner().run(cand_code, case)
        problems = compare(orig, cand, compare_ret=not case.get("nodes"))
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} hooks)")
    return passed


def main() -> None:
    print("Testing engine_func_002a399c (0x002a399c)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("use_scaled_quad_flag",
         "constexpr u32 kFlagUseScaledQuad = 0x100u;",
         "constexpr u32 kFlagUseScaledQuad = 0x200u;"),
        ("compose_quad_flag",
         "constexpr u32 kFlagComposeQuad   = 0x080u;",
         "constexpr u32 kFlagComposeQuad   = 0x020u;"),
        ("override_y_flag",
         "constexpr u32 kFlagOverrideY     = 0x004u;",
         "constexpr u32 kFlagOverrideY     = 0x002u;"),
        ("inherit_scale_flag",
         "constexpr u32 kFlagInheritScale  = 0x001u;",
         "constexpr u32 kFlagInheritScale  = 0x002u;"),
        ("overridden_y_value",
         "constexpr f32 kOverriddenY       = 5.0f;",
         "constexpr f32 kOverriddenY       = 4.0f;"),
        ("type_table_base",
         "return reinterpret_cast<TypeEntry*>(0x00464110u);",
         "return reinterpret_cast<TypeEntry*>(0x00464150u);"),
        ("render_state_base",
         "return *reinterpret_cast<RenderState*>(0x004EA81Cu);",
         "return *reinterpret_cast<RenderState*>(0x004EA80Cu);"),
        ("factor_operation",
         "node->local_scale * inherited",
         "node->local_scale + inherited"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ScaleRunner().run(orig_code, case)
            try:
                bad = ScaleRunner().run(mutant_code, case)
            except RuntimeError as error:
                print(f"  [PASS] {name} mutant faults: {error}")
                detected = True
                break
            if compare(orig, bad, compare_ret=not case.get("nodes")):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
