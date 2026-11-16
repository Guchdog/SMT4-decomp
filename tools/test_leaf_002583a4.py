#!/usr/bin/env python3
"""Differential test for camp_func_002583a4 (0x002583a4) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts camp_func_002583a4, resolves
its three direct calls to deterministic stubs, and runs the pinned original
(extracted/exefs/code.bin) against the candidate with identical fixtures.

Compared outputs:
  * return r0, continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every helper argument (stack pointers normalised);
  * the whole camp arena: manager fields, relative-offset tables, object/child
    flags, element records, float pairs, phase-2 group and its 0x2B0 reset;
  * the fault address for negative controls that must fail identically.

Coverage: signed loop bounds (0, positive, negative), object required-flag bit
masks, active-child flag, child counts, empty and multi-entry element lists,
matching and non-matching keys, negative/zero/inside/edge/beyond data indices,
negative and positive s16 selectors, null offset-table entries, null data base,
phase-2 count 0/1/2, both phase-2 selectors, and the original's dead
`selected + 8` read (a null selection must fault at address 8). Mutants of the
required-flag mask, the y offset pair index and the 0x2B0 clear target must be
detected by these cases.
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
OUT_DIR = ROOT / "build/test_leaf_002583a4"

FUNC_ADDR = 0x002583A4
FUNC_SIZE = 664

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00300000  # covers the function, its global and every stub
ARENA_ADDR = 0x00700000
ARENA_SIZE = 0x00040000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_340C30 = 0x00340C30
STUB_2A2DDC = 0x002A2DDC
STUB_2C25F0 = 0x002C25F0
STUB_NAMES = {
    STUB_340C30: "camp_func_00340c30",
    STUB_2A2DDC: "camp_func_002a2ddc",
    STUB_2C25F0: "engine_func_002c25f0",
}
CALL_RELOC_TYPES = (28, 29, 10)  # R_ARM_CALL / R_ARM_JUMP24 / R_ARM_THM_CALL

# ---------------------------------------------------------------- arena layout
MANAGER = ARENA_ADDR + 0x0000
KEY = ARENA_ADDR + 0x0800
SELF = ARENA_ADDR + 0x1000
ROOT_A = ARENA_ADDR + 0x2000
ROOT_B = ARENA_ADDR + 0x2100
ROOT_C = ARENA_ADDR + 0x2200
ROOT_D = ARENA_ADDR + 0x2300
OBJ_LOOKUP = ARENA_ADDR + 0x2500
LOOKUP2 = ARENA_ADDR + 0x2800
ENTRY2 = ARENA_ADDR + 0x2A00
GROUP = ARENA_ADDR + 0x2C00
SELECTED0 = ARENA_ADDR + 0x2F00
SELECTED1 = ARENA_ADDR + 0x2F80
OBJ0 = ARENA_ADDR + 0x3000
CHILD_ARRAY = ARENA_ADDR + 0x3300
CHILD0 = ARENA_ADDR + 0x3400
CHILD1 = ARENA_ADDR + 0x3500
ELEM0 = ARENA_ADDR + 0x3600
ELEM1 = ARENA_ADDR + 0x3640
ELEM_ARRAY0 = ARENA_ADDR + 0x3700
ELEM_ARRAY1 = ARENA_ADDR + 0x3740
DATA0 = ARENA_ADDR + 0x3800
DATA1 = ARENA_ADDR + 0x3820

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
    with open(ORIG_BIN, "rb") as handle:
        handle.seek(FUNC_ADDR - 0x00100000)
        return handle.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "002583a4" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"camp_func_002583a4 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in CALL_RELOC_TYPES:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
        target = None
        for address, name in STUB_NAMES.items():
            if name in rel.symbol_name:
                target = address
                break
        if target is None:
            raise RuntimeError(f"unresolved call relocation: {rel.symbol_name}")
        pc = FUNC_ADDR + rel.offset + 8
        displacement = target - pc
        if displacement & 3:
            raise RuntimeError(f"unaligned call target 0x{target:08x}")
        original = struct.unpack_from("<I", code, rel.offset)[0]
        cond = original & 0xFF000000
        struct.pack_into(
            "<I",
            code,
            rel.offset,
            cond | ((displacement >> 2) & 0x00FFFFFF),
        )
    return bytes(code)


def compile_candidate() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Compilation failed: {result.stderr}")
    return relocate_candidate(obj_file)


def compile_mutant(name: str, old: str, new: str) -> bytes:
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


# ------------------------------------------------------------------- fixtures
def default_child(data_addr: int, elem_array: int, keys, indices, **overrides):
    spec = {
        "flags": 0x40000001,
        "data": data_addr,
        "elem_array": elem_array,
        "keys": list(keys),
        "indices": list(indices),
        "span": 16,
        "stride": 8,
        "element_count": 2,
        "data_offset": None,
        "table_null": False,
        "selectors_zero": False,
    }
    spec.update(overrides)
    return spec


def default_case(name: str, **overrides) -> dict:
    case = {
        "name": name,
        "count1": 1,
        "count2": 1,
        "idx0": 0,
        "key_sel": 0x10,
        "idx1": 0,
        "idx2": 0,
        "object_flags": 0x10000001,
        "object_table_zero": False,
        "object_entry_zero": False,
        "child_count": 1,
        "child_table_zero": False,
        "children": [
            default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99], [0, 0]),
            default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0]),
        ],
        "offset": (0.25, -0.75),
        "selected_null_m0": False,
        "selected_null_m1": False,
    }
    case.update(overrides)
    return case


def build_arena(case: dict) -> bytes:
    arena = bytearray(b"\xCC" * ARENA_SIZE)

    def put32(address: int, value: int) -> None:
        struct.pack_into("<I", arena, address - ARENA_ADDR, value & 0xFFFFFFFF)

    def put16(address: int, value: int) -> None:
        struct.pack_into("<h", arena, address - ARENA_ADDR, value)

    def putf(address: int, value: float) -> None:
        struct.pack_into("<f", arena, address - ARENA_ADDR, value)

    def rel(target: int, field_address: int) -> int:
        return (target - field_address) & 0xFFFFFFFF

    put32(MANAGER + 0x84, ROOT_A)
    put32(MANAGER + 0x194, case["count1"])
    put32(MANAGER + 0x298, case["count2"])
    put16(MANAGER + 0x94, case["idx0"])
    put16(MANAGER + 0x96, case["key_sel"])
    put16(MANAGER + 0x198, case.get("idx1", 0))
    put16(MANAGER + 0x19A, case.get("idx2", 0))
    put16(MANAGER + 0x19C, case.get("idx1_m1", 1))
    put16(MANAGER + 0x19E, case.get("idx2_m1", 1))

    put32(ROOT_A + 8, ROOT_B)
    put32(ROOT_B + 0x2C, ROOT_C)
    put32(ROOT_C + 8, ROOT_D)

    if case["object_table_zero"]:
        put32(ROOT_D + 0xC8, 0)
    else:
        put32(ROOT_D + 0xC8, rel(OBJ_LOOKUP, ROOT_D + 0xC8))
    for index in (-1, 0, 1):
        slot = OBJ_LOOKUP + index * 4
        put32(slot, 0 if case["object_entry_zero"] else rel(OBJ0, slot))

    put32(OBJ0 + 0x00, case["object_flags"])
    put32(OBJ0 + 0x38, case["child_count"])
    if case["child_table_zero"]:
        put32(OBJ0 + 0x3C, 0)
    else:
        put32(OBJ0 + 0x3C, rel(CHILD_ARRAY, OBJ0 + 0x3C))

    for index, (child_addr, spec) in enumerate(
        zip((CHILD0, CHILD1), case["children"])
    ):
        slot = CHILD_ARRAY + index * 4
        put32(slot, 0 if spec["table_null"] else rel(child_addr, slot))

        put32(child_addr + 0x00, spec["flags"])
        put32(child_addr + 0x14, spec["span"])
        put32(child_addr + 0x24, spec["stride"])
        put32(child_addr + 0x28, spec["element_count"])
        if spec["data_offset"] is None:
            put32(child_addr + 0x18, rel(spec["data"], child_addr + 0x18))
        else:
            put32(child_addr + 0x18, spec["data_offset"])
        put32(
            child_addr + 0x2C,
            rel(spec["elem_array"], child_addr + 0x2C),
        )

        for elem_index in range(2):
            dest = ELEM0 if elem_index == 0 else ELEM1
            slot_address = spec["elem_array"] + elem_index * 4
            if spec["selectors_zero"] and elem_index == 0:
                put32(slot_address, 0)
            else:
                put32(slot_address, rel(dest, slot_address))
            put32(dest + 0x04, spec["keys"][elem_index])
            put32(dest + 0x30, spec["indices"][elem_index])

    for index in range(2):
        putf(DATA0 + index * 8, 1.0 + index)
        putf(DATA0 + index * 8 + 4, 10.0 + index)
        putf(DATA1 + index * 8, 3.0 + index)
        putf(DATA1 + index * 8 + 4, 30.0 + index)

    put32(ROOT_C + 0x164, LOOKUP2)
    for index in (-1, 0, 1):
        put32(LOOKUP2 + index * 4, ENTRY2)
    put32(ENTRY2 + 0x3C, GROUP)
    for index in (-1, 0, 1):
        slot = GROUP + 0x274 + index * 4
        target = SELECTED1 if index == 1 else SELECTED0
        put32(slot, rel(target, slot))
    put32(GROUP + 0x2B0, 0xDEADBEEF)
    put32(SELECTED0 + 0x00, 0x0BADF00D)
    put32(SELECTED1 + 0x00, 0x12345678)
    if case["selected_null_m0"]:
        put32(GROUP + 0x274, 0)
    if case["selected_null_m1"]:
        put32(GROUP + 0x278, 0)

    put32(SELF + 0x0C, KEY)
    put32(KEY, 0x5A5A5A5A)
    return bytes(arena)


def read_arena(uc) -> bytes:
    return bytes(uc.mem_read(ARENA_ADDR, ARENA_SIZE))


class CampRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Unicorn boots with VFP/NEON disabled; enable CP10/CP11 and FPEXC.
        cpacr = self.uc.reg_read(arm.UC_ARM_REG_C1_C0_2)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, cpacr | (0xF << 20))
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(ARENA_ADDR, ARENA_SIZE)
        self.uc.mem_map(STACK_ADDR, STACK_SIZE)
        self.uc.mem_map(TRAP_ADDR, 0x1000)

        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))  # bx lr
            self.uc.hook_add(
                unicorn.UC_HOOK_CODE, self._on_stub, begin=address, end=address
            )
        self.uc.hook_add(unicorn.UC_HOOK_MEM_UNMAPPED, self._on_unmapped)

        self.call_log = []
        self.fault = None
        self.case = {}

    def _normalise(self, value: int) -> object:
        if STACK_ADDR <= value < STACK_ADDR + STACK_SIZE:
            return "<stack>"
        return value

    def _on_unmapped(
        self, uc, access, address, size, value, user_data
    ) -> bool:
        if self.fault is None:
            self.fault = (address, size, access)
        return False

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        if address == STUB_340C30:
            dx, dy = self.case["offset"]
            uc.mem_write(r1, struct.pack("<ff", 111.0, 222.0))
            uc.mem_write(r2, struct.pack("<ff", dx, dy))
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    r0,
                    self._normalise(r1),
                    self._normalise(r2),
                    dx,
                    dy,
                )
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA340C30)
        elif address == STUB_2A2DDC:
            slot_value, key_value = struct.unpack(
                "<II", uc.mem_read(r0, 4) + uc.mem_read(r1, 4)
            )
            self.call_log.append(
                (
                    STUB_NAMES[address],
                    self._normalise(r0),
                    slot_value,
                    r1,
                    key_value,
                )
            )
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA2A2DDC)
        elif address == STUB_2C25F0:
            self.call_log.append((STUB_NAMES[address], r0, r1))
            uc.reg_write(arm.UC_ARM_REG_R0, 0xA2C25F0)
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.fault = None
        self.case = case

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(ARENA_ADDR, build_arena(case))
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.uc.mem_write(0x0043DD90, struct.pack("<I", ARENA_ADDR))
        self.uc.mem_write(0x0043DD8C, struct.pack("<I", 0xA5A5A5A5))

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, 0x11111111)
        self.uc.reg_write(arm.UC_ARM_REG_R2, 0x22222222)
        self.uc.reg_write(arm.UC_ARM_REG_R3, 0x33333333)
        for name, value in CALLEE_SAVED_START.items():
            self.uc.reg_write(CALLEE_SAVED[name], value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except unicorn.UcError:
            if self.fault is None:
                raise

        return {
            "ret": self.uc.reg_read(arm.UC_ARM_REG_R0),
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "call_log": list(self.call_log),
            "arena": read_arena(self.uc),
            "fault": self.fault,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    if (orig["fault"] is None) != (cand["fault"] is None):
        problems.append(f"fault presence: orig={orig['fault']} cand={cand['fault']}")
    if orig["fault"] is not None:
        if orig["fault"][0] != cand["fault"][0]:
            problems.append(
                f"fault address: orig=0x{orig['fault'][0]:08x} "
                f"cand=0x{cand['fault'][0]:08x}"
            )
        if orig["call_log"] != cand["call_log"]:
            problems.append(
                "call_log before fault:\n    orig="
                + repr(orig["call_log"])
                + "\n    cand="
                + repr(cand["call_log"])
            )
        return problems

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
    if orig["arena"] != cand["arena"]:
        first = next(
            index
            for index, (left, right) in enumerate(zip(orig["arena"], cand["arena"]))
            if left != right
        )
        problems.append(
            f"arena mismatch at 0x{ARENA_ADDR + first:08x}: "
            f"orig=0x{orig['arena'][first]:02x} cand=0x{cand['arena'][first]:02x}"
        )
    return problems


def make_cases() -> list[dict]:
    cases = []

    # Loop-bound branches: signed zero / positive / negative.
    cases.append(default_case("one entry in each phase"))
    cases.append(default_case("both counts zero", count1=0, count2=0))
    cases.append(default_case("both counts negative", count1=-1, count2=-1))
    cases.append(default_case("phase 2 count zero", count2=0))
    cases.append(default_case("phase 1 count zero", count1=0))
    cases.append(default_case("phase 2 count negative", count1=1, count2=-2))

    # Object required-flag mask: all 0x10000001 bits required; extras ignored.
    cases.append(default_case("object flags exact", object_flags=0x10000001))
    cases.append(default_case("object flags extra accepted", object_flags=0xFFFFFFFF))
    cases.append(default_case("object flags missing low bit", object_flags=0))
    cases.append(default_case("object flags missing high bit", object_flags=1))
    cases.append(default_case("object flags high only", object_flags=0x10000000))
    cases.append(default_case("object entry null", object_entry_zero=True))

    # Child active flag and child count branches.
    cases.append(
        default_case(
            "child inactive",
            children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99], [0, 0],
                                    flags=0x40000000),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )
    cases.append(
        default_case(
            "child active without flag",
            children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99], [0, 0],
                                    flags=0x00000001),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )
    cases.append(default_case("child count zero", child_count=0))
    cases.append(default_case("child count negative", child_count=-1))
    cases.append(default_case("child entry null",
                              children=[default_child(DATA0, ELEM_ARRAY0,
                                                      [0x14, 0x99], [0, 0],
                                                      table_null=True),
                                        default_child(DATA1, ELEM_ARRAY1,
                                                      [0x14, 0x99], [0, 0])]))
    cases.append(
        default_case(
            "two children first inactive",
            child_count=2,
            children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99], [0, 0],
                                    flags=0x00000000),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )
    cases.append(default_case("two children both active", child_count=2))

    # Element list and key matching.
    cases.append(
        default_case(
            "element count zero",
            children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99], [0, 0],
                                    element_count=0),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )
    cases.append(
        default_case(
            "first element mismatched",
            children=[default_child(DATA0, ELEM_ARRAY0, [0x99, 0x14], [0, 0]),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )
    cases.append(
        default_case(
            "both elements match",
            children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x14], [0, 0]),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )
    cases.append(default_case("negative key selector", key_sel=-3))

    # Element data index boundaries: negative, zero, inside, edge, beyond.
    for index in (-1, 0, 8, 12, 16, 20):
        cases.append(
            default_case(
                f"data index {index}",
                children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99],
                                        [index, 0]),
                          default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99],
                                        [0, 0])],
            )
        )
    cases.append(
        default_case(
            "null data base with empty span",
            children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99], [0, 0],
                                    data_offset=0, span=0),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )

    # Signed s16 selectors: negative and positive resolve through the same table.
    cases.append(default_case("object selector -1", idx0=-1))
    cases.append(default_case("object selector +1", idx0=1))
    cases.append(default_case("phase2 selector -1", idx1=-1, count2=1))
    cases.append(default_case("phase2 selector +1", idx1=1, count2=1))
    cases.append(default_case("phase2 slot selector +1", idx2=1, count2=1))

    # Phase 2: two manager entries use +0x198/+0x19A and +0x19C/+0x19E.
    cases.append(default_case("phase2 two entries", count2=2))
    cases.append(
        default_case("phase2 two entries swapped",
                     count2=2, idx1=1, idx2=1, idx1_m1=0, idx2_m1=1)
    )

    # Fault-negative controls: identical fault addresses, different code PCs.
    cases.append(default_case("object table offset zero", object_table_zero=True))
    cases.append(default_case("null element selector", 
                              children=[default_child(DATA0, ELEM_ARRAY0,
                                                      [0x14, 0x99], [0, 0],
                                                      selectors_zero=True),
                                        default_child(DATA1, ELEM_ARRAY1,
                                                      [0x14, 0x99], [0, 0])]))
    cases.append(default_case("null selected record", selected_null_m0=True))
    cases.append(
        default_case(
            "null data base dereferenced",
            children=[default_child(DATA0, ELEM_ARRAY0, [0x14, 0x99], [0, 0],
                                    data_offset=0, span=8),
                      default_child(DATA1, ELEM_ARRAY1, [0x14, 0x99], [0, 0])],
        )
    )

    return cases


def main() -> None:
    print("Testing camp_func_002583a4 (0x002583a4)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()

    runner_orig = CampRunner()
    runner_cand = CampRunner()
    cases = make_cases()

    failures = 0
    for case in cases:
        orig = runner_orig.run(orig_code, case)
        cand = runner_cand.run(cand_code, case)
        problems = compare(orig, cand)
        if problems:
            failures += 1
            print(f"  [FAIL] {case['name']}")
            for problem in problems:
                print(f"    {problem}")
        else:
            suffix = ""
            if orig["fault"] is not None:
                suffix = f" (both fault at 0x{orig['fault'][0]:08x})"
            print(f"  [PASS] {case['name']}{suffix}")

    # Mutants must be detected by at least one case.
    mutants = [
        (
            "required_flags",
            "constexpr u32 kObjectRequiredFlags = 0x10000001;",
            "constexpr u32 kObjectRequiredFlags = 0x10000000;",
        ),
        (
            "y_offset_pair",
            "x = x + offset_pair[0];\n                        y = y + offset_pair[1];",
            "x = x + offset_pair[0];\n                        y = y + offset_pair[0];",
        ),
        (
            "group_clear_offset",
            "*reinterpret_cast<u32*>(group + 0x2B0) = 0;",
            "*reinterpret_cast<u32*>(group + 0x2B4) = 0;",
        ),
    ]
    for name, old, new in mutants:
        try:
            mutant_code = compile_mutant(name, old, new)
        except RuntimeError as error:
            print(f"  [FAIL] mutant {name} could not be built: {error}")
            failures += 1
            continue
        detected = False
        mutant_runner = CampRunner()
        for case in cases:
            orig = runner_orig.run(orig_code, case)
            mutant = mutant_runner.run(mutant_code, case)
            if compare(orig, mutant):
                detected = True
                break
        if detected:
            print(f"  [PASS] mutant {name} detected")
        else:
            print(f"  [FAIL] mutant {name} was not detected")
            failures += 1

    total = len(cases) + len(mutants)
    if failures:
        print(f"\n{failures}/{total} differential checks FAILED")
        raise SystemExit(1)
    print(f"\nAll {total}/{total} differential checks PASSED!")


if __name__ == "__main__":
    main()
