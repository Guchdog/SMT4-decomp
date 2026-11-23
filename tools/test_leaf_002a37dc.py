#!/usr/bin/env python3
"""Differential test for engine_func_002a37dc (0x002a37dc).

`AsdPart_SetColor(part, color)` publishes the packed 0xAABBGGRR color at
part+0x64, stages its four normalized channels (A, B, G, R) in the
0x004EA81C render block, then walks the part's child list at +0x8C.  For every
child it multiplies the child's normalized color by the parent tint and passes
the truncating re-quantization to the per-type hook at 0x00464110 entry +0x30.

This runner compiles src/engine/leaf_batch41_c.cpp, extracts that one function,
and executes the pinned original (extracted/exefs/code.bin) and the candidate
in separate Unicorn ARM machines with identical fixtures.

Compared per case:
  * return r0, continuation PC, final SP and the callee-saved r4-r11;
  * the callee-saved VFP registers s16-s31 (the original saves d8-d10);
  * the ordered hook log: type index, context (r0), packed color (r1) and the
    16 bytes of the render vector at call time;
  * the full self page, the 0x00464110 type-table page, the 0x004EA81C
    render-state page and the stub capture page;
  * any emulated write outside the private stack, self page, render page or
    capture page.

The function returns void, but both paths leave `part`, the instance pointer or
the hook's return value in r0, so r0 is compared as well: the stubs return a
deliberate poison value that must be ignored by the loop.

Coverage: empty child list; one to three nodes; every channel order and the
0x00/0x01/0x7F/0x80/0xFF byte boundaries; truncation-sensitive channel pairs;
zero, white and high-bit packed colors; null hook slots; type indices 0, 1, 3,
34, 0x7F, 0xFF and 0x200 (past the 35 real entries but still inside the mapped
page); a hook that terminates the list and a hook that skips a node, both
proving the +0xAC reload after the call; a child +0x8C marker that must never
be traversed.  Negative controls mutate the 1/255 factor, the 255.0f scale, the
table base, the entry stride, the render base, both channel shifts, the parent
tint store, the null-slot test and the hook context argument.
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
OUT_DIR = ROOT / "build/test_leaf_002a37dc"

FUNC_NAME = "engine_func_002a37dc"
FUNC_ADDR = 0x002A37DC
FUNC_SIZE = 448

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

STUB_BASE = 0x00310000
STUB_STRIDE = 0x10
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

RENDER_PATTERN = 0xA5


def stub_address(type_index: int) -> int:
    return STUB_BASE + type_index * STUB_STRIDE


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def extract_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    for name, value in funcs.items():
        if FUNC_NAME in name:
            raw, relocs = value
            if relocs:
                raise RuntimeError(
                    "candidate unexpectedly has relocations: "
                    f"{[(r.offset, r.relocation_type, r.symbol_name) for r in relocs]}"
                )
            return raw
    raise RuntimeError(f"{FUNC_NAME} not found in {obj_file}: {sorted(funcs)}")


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch41_c.o"
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
    base_self = SELF_OBJECT - SELF_ADDR
    # The routine must overwrite this with the argument, so a marker is enough.
    struct.pack_into("<I", page, base_self + 0x64, 0xDEADBEEF)

    nodes = case.get("nodes", [])
    struct.pack_into("<I", page, base_self + 0x8C, NODE_BASE if nodes else 0)

    for index, node in enumerate(nodes):
        base = (NODE_BASE - SELF_ADDR) + index * NODE_STRIDE
        struct.pack_into("<I", page, base + 0x64, node["color"] & 0xFFFFFFFF)
        # Untraversed child list marker: a wrong child list read is visible.
        struct.pack_into("<I", page, base + 0x8C, 0xDEAD0000 | index)
        struct.pack_into(
            "<I", page, base + 0x90, INSTANCE_BASE + index * INSTANCE_STRIDE
        )
        next_ptr = (
            NODE_BASE + (index + 1) * NODE_STRIDE if index + 1 < len(nodes) else 0
        )
        struct.pack_into("<I", page, base + 0xAC, next_ptr)

        inst = (INSTANCE_BASE - SELF_ADDR) + index * INSTANCE_STRIDE
        struct.pack_into("<H", page, inst + 0x04, node["type"] & 0xFFFF)
        struct.pack_into("<I", page, inst + 0x08, CONTEXT_BASE + index * CONTEXT_STRIDE)
        context = (CONTEXT_BASE - SELF_ADDR) + index * CONTEXT_STRIDE
        struct.pack_into("<I", page, context, 0xC0DE0000 | index)
    return bytes(page)


def build_table(case: dict) -> bytes:
    page = bytearray(TABLE_SIZE)
    disabled = set(case.get("disabled_hooks", ()))
    for type_index in range(TYPE_COUNT):
        if type_index in disabled:
            continue
        entry = TYPE_TABLE_BASE - TABLE_ADDR + type_index * TYPE_STRIDE
        struct.pack_into("<I", page, entry + 0x30, stub_address(type_index))
    return bytes(page)


class ColorRunner:
    """One Unicorn ARM machine with a deterministic stub per type."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(SELF_ADDR, SELF_SIZE)
        self.uc.mem_map(TABLE_ADDR, TABLE_SIZE)
        self.uc.mem_map(RENDER_ADDR, RENDER_SIZE)
        self.uc.mem_map(CAPTURE_ADDR, CAPTURE_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for type_index in range(TYPE_COUNT + 1):
            address = stub_address(type_index)
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_WRITE, self._on_write)

        self.call_log: list = []
        self.writes: list = []
        self.capture_cursor = 0
        self.next_override: dict = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        type_index = (address - STUB_BASE) // STUB_STRIDE
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        vector = bytes(uc.mem_read(RENDER_ADDR + 0x91C, 16))

        record = bytearray(CAPTURE_STRIDE)
        struct.pack_into("<I", record, 0, type_index)
        struct.pack_into("<I", record, 4, r0)
        struct.pack_into("<I", record, 8, r1)
        record[16:32] = vector
        self.uc.mem_write(
            CAPTURE_ADDR + self.capture_cursor * CAPTURE_STRIDE, bytes(record)
        )
        self.capture_cursor += 1
        self.call_log.append(
            ("hook", type_index, r0, r1, struct.unpack("<4I", vector))
        )

        # Prove the +0xAC link is reloaded after the hook.
        if CONTEXT_BASE <= r0 < CONTEXT_BASE + CONTEXT_STRIDE * 8:
            node_index = (r0 - CONTEXT_BASE) // CONTEXT_STRIDE
            if node_index in self.next_override:
                struct.pack_into(
                    "<I",
                    self._self_page,
                    (NODE_BASE - SELF_ADDR) + node_index * NODE_STRIDE + 0xAC,
                    self.next_override[node_index] & 0xFFFFFFFF,
                )
                self.uc.mem_write(SELF_ADDR, bytes(self._self_page))

        # Deliberate non-zero return value; the routine must ignore it.
        uc.reg_write(arm.UC_ARM_REG_R0, 0x5A5A0000 | (type_index << 8))

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []
        self.capture_cursor = 0
        self.next_override = dict(case.get("next_override", {}))

        self._self_page = bytearray(build_self(case))
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(SELF_ADDR, bytes(self._self_page))
        self.uc.mem_write(TABLE_ADDR, build_table(case))
        self.uc.mem_write(RENDER_ADDR, bytes([RENDER_PATTERN]) * RENDER_SIZE)
        self.uc.mem_write(CAPTURE_ADDR, b"\x00" * CAPTURE_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_OBJECT)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["color"] & 0xFFFFFFFF)
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
        "color": 0xFFFFFFFF,
        "nodes": [],
    }
    case.update(overrides)
    return case


def node(color: int, type_index: int = 0) -> dict:
    return {"color": color, "type": type_index}


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # Empty child list: only the +0x64 store and the parent vector staging.
    cases.append(base_case("empty list, white", color=0xFFFFFFFF))
    cases.append(base_case("empty list, zero", color=0x00000000))
    cases.append(base_case("empty list, high-bit channels", color=0xF0E0D0C0))
    cases.append(base_case("empty list, 0x80808080", color=0x80808080))

    # Single node: channel order and simple scaling.
    cases.append(base_case("white parent, normal child",
                           nodes=[node(0x80A0C0E0)]))
    cases.append(base_case("alpha-only parent",
                           color=0xFF000000, nodes=[node(0x00FFFFFF)]))
    cases.append(base_case("zero parent", color=0x00000000,
                           nodes=[node(0xFFFFFFFF)]))
    cases.append(base_case("zero child", nodes=[node(0x00000000)]))
    cases.append(base_case("both zero", color=0x00000000,
                           nodes=[node(0x00000000)]))
    cases.append(base_case("channel rotation 0x01020304 x 0x04030201",
                           color=0x01020304, nodes=[node(0x04030201)]))
    cases.append(base_case("alpha zero, rgb full", color=0x00FFFFFF,
                           nodes=[node(0xFFFFFFFF)]))
    cases.append(base_case("rgb zero, alpha full", color=0xFF000000,
                           nodes=[node(0xFF000000)]))
    cases.append(base_case("high-bit pair 0x7F808080 x 0x80807F7F",
                           color=0x7F808080, nodes=[node(0x80807F7F)]))
    cases.append(base_case("0x7F7F7F7F x 0x80808080",
                           color=0x7F7F7F7F, nodes=[node(0x80808080)]))

    # Truncation-sensitive channel products (a*b/255 is not integral).
    for parent, child in (
        (0xC8C8C8C8, 0xC8C8C8C8),   # 200*200/255 = 156.86...
        (0x64646464, 0xC8C8C8C8),   # 100*200/255 = 78.43...
        (0x80808080, 0x7F7F7F7F),   # 128*127/255 = 63.75...
        (0x01010101, 0x81818181),   # 1*129/255 = 0.50...
        (0x7E7E7E7E, 0x81818181),   # 126*129/255 = 63.74...
        (0xFEFEFEFE, 0x01010101),   # 254*1/255 = 0.99...
        (0xFFFF0000, 0x0000FFFF),   # only R/B channels contribute
    ):
        cases.append(
            base_case(f"truncation pair 0x{parent:08X} x 0x{child:08X}",
                      color=parent, nodes=[node(child)])
        )

    # Type-index and null-slot coverage.
    for type_index in (0, 1, 2, 3, 7, 20, 34):
        cases.append(
            base_case(f"type index {type_index:#04x}",
                      color=0xFFFFFFFF, nodes=[node(0x80402010, type_index)])
        )
    cases.append(base_case("null hook type 3", color=0xFFFFFFFF,
                           nodes=[node(0x80402010, 3)],
                           disabled_hooks=(3,)))
    cases.append(base_case("null hook type 0", color=0xFFFFFFFF,
                           nodes=[node(0x80402010, 0)],
                           disabled_hooks=(0,)))
    cases.append(base_case("null hook type 34", color=0xFFFFFFFF,
                           nodes=[node(0x80402010, 34)],
                           disabled_hooks=(34,)))
    for type_index in (0x7F, 0xFF, 0x200):
        # Past the 35 real entries but inside the mapped table page: the hook
        # word is zero, so the routine must not call anything.
        cases.append(
            base_case(f"past-table type {type_index:#06x}",
                      color=0xFFFFFFFF,
                      nodes=[node(0x80402010, type_index)])
        )
    cases.append(base_case("null hook on second of three nodes",
                           color=0xFFFFFFFF,
                           nodes=[node(0x10203040, 1),
                                  node(0x50607080, 4),
                                  node(0x90A0B0C0, 5)],
                           disabled_hooks=(4,)))

    # Linked-list traversal and call ordering.
    cases.append(base_case("two nodes",
                           color=0xFF00FF00,
                           nodes=[node(0x00FF00FF, 0), node(0x80808080, 1)]))
    cases.append(base_case("three nodes mixed",
                           color=0x80402010,
                           nodes=[node(0x10203040, 2),
                                  node(0x20304050, 3),
                                  node(0x30405060, 4)]))
    cases.append(base_case("three nodes, same child color",
                           color=0x40C08020,
                           nodes=[node(0x00FFFFFF, 1),
                                  node(0x00FFFFFF, 2),
                                  node(0x00FFFFFF, 3)]))

    # Hook-driven link rewrite: the +0xAC reload must be honoured.
    cases.append(base_case("hook terminates the list",
                           color=0xFFFFFFFF,
                           nodes=[node(0x10203040, 1),
                                  node(0x50607080, 2),
                                  node(0x90A0B0C0, 3)],
                           next_override={0: 0}))
    cases.append(base_case("hook skips the middle node",
                           color=0xFFFFFFFF,
                           nodes=[node(0x10203040, 1),
                                  node(0x50607080, 2),
                                  node(0x90A0B0C0, 3)],
                           next_override={0: NODE_BASE + 2 * NODE_STRIDE}))

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for case in cases:
        orig = ColorRunner().run(orig_code, case)
        cand = ColorRunner().run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {case['name']}  ({len(orig['call_log'])} hooks)")
    return passed


def main() -> None:
    print(f"Testing {FUNC_NAME} (0x{FUNC_ADDR:08x})...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate_baseline()
    print(f"Original {len(orig_code)} B, candidate {len(cand_code)} B.")

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("inv255_factor",
         "constexpr f32 kColorInv255  = 1.0f / 255.0f;",
         "constexpr f32 kColorInv255  = 1.0f / 256.0f;"),
        ("scale255_factor",
         "constexpr f32 kColorScale255 = 255.0f;",
         "constexpr f32 kColorScale255 = 256.0f;"),
        ("type_table_base",
         "constexpr u32 kTypeTableBase = 0x00464110u;",
         "constexpr u32 kTypeTableBase = 0x00464150u;"),
        ("type_entry_stride",
         "constexpr u32 kTypeStride = 0x44;",
         "constexpr u32 kTypeStride = 0x40;"),
        ("render_state_base",
         "constexpr u32 kRenderStateBase = 0x004EA81Cu;",
         "constexpr u32 kRenderStateBase = 0x004EA80Cu;"),
        ("second_lane_shift",
         "out.value[1] = static_cast<f32>((color >> 16) & kColorByteMask) *",
         "out.value[1] = static_cast<f32>((color >> 8) & kColorByteMask) *"),
        ("third_lane_shift",
         "out.value[2] = static_cast<f32>((color >> 8) & kColorByteMask) *",
         "out.value[2] = static_cast<f32>((color >> 16) & kColorByteMask) *"),
        ("parent_tint_store",
         "state.color = parent;",
         "state.color = state.vector;"),
        ("null_slot_test",
         "if (type->set_color != nullptr) {",
         "if (type->set_color == nullptr) {"),
        ("hook_context_argument",
         "type->set_color(instance->context, packed);",
         "type->set_color(nullptr, packed);"),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig = ColorRunner().run(orig_code, case)
            try:
                bad = ColorRunner().run(mutant_code, case)
            except RuntimeError as error:
                print(f"  [PASS] {name} mutant faults: {error}")
                detected = True
                break
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
