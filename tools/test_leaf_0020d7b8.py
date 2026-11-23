#!/usr/bin/env python3
"""Differential test for script_vm_func_0020d7b8 (0x0020d7b8) using Unicorn ARM.

Compiles src/engine/leaf_batch41_c.cpp, extracts the script_vm_func_0020d7b8
body, resolves its six direct calls to deterministic stubs, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP and callee-saved r4-r11;
  * the ordered call log with every register/float argument of each helper,
    including the three words read through the transform-vector pointer;
  * the full slot table, node flags, sub-node pose word, visual-node visibility
    bytes, the VM-object page and the 0x0049F91C instance page;
  * every emulated write outside the private stack.

r0 is not compared: the original is a `void` function whose epilogue leaves r0
as whatever the last helper happened to return, so it is not part of the
contract (documented in the function record).

Coverage: VM mode != 0x16 (0, 0x15, 0x17, 0xFFFF); the instance-active byte
0x00/0x01/0xFF; every branch of the visibility toggle (pending 0/non-zero,
direction 0/non-zero, node flags bit 1 set/clear); the 0x38-vs-0x14 pose
comparison equal and unequal with signed/unsigned boundary words; all nine
primary slots and all three secondary slots (including the final index of each
group); and transform-vector/float round-tripping.
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
OUT_DIR = ROOT / "build/test_leaf_0020d7b8"

FUNC_ADDR = 0x0020D7B8
FUNC_SIZE = 500

CODE_ADDR = 0x00100000
CODE_SIZE = 0x00300000  # covers 0x1E2C94 and every stub up to 0x2A5A54
GLOBAL_ADDR = 0x00440000  # holds the 0x00447E10 pointer slot
GLOBAL_SIZE = 0x00020000
INSTANCE_ADDR = 0x00490000  # holds 0x0049F91C
INSTANCE_SIZE = 0x00020000
SLOT_ADDR = 0x00500000  # VM object + 12 slots of 44 bytes
SLOT_SIZE = 0x00004000
NODE_ADDR = 0x00510000  # 12 node records (flags word, sub pointer)
NODE_SIZE = 0x00002000
SUB_ADDR = 0x00520000  # 12 sub-nodes (visual pointer +0x2C, word +0x38)
SUB_SIZE = 0x00002000
VIS_ADDR = 0x00530000  # 12 visual nodes (visibility byte +0x1F6)
VIS_SIZE = 0x00004000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

GLOBAL_POINTER_SLOT = 0x00447E10
INSTANCE_BLOCK = 0x0049F91C
INSTANCE_ACTIVE_OFFSET = 0x22
MODE_OFFSET = 0x0C

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

SLOT_STRIDE = 44
GROUP0_OFFSET = 0x1114
GROUP0_COUNT = 9
GROUP1_OFFSET = 0x12A0
GROUP1_COUNT = 3
SLOT_COUNT = GROUP0_COUNT + GROUP1_COUNT
NODE_STRIDE = 0x20
SUB_STRIDE = 0x40
VIS_STRIDE = 0x200

STUB_1E2C94 = 0x001E2C94
STUB_29BDB4 = 0x0029BDB4
STUB_28C8A8 = 0x0028C8A8
STUB_28C880 = 0x0028C880
STUB_2A5A54 = 0x002A5A54

STUB_NAMES = {
    STUB_1E2C94: "script_vm_func_001e2c94",
    STUB_29BDB4: "ui_func_0029bdb4",
    STUB_28C8A8: "engine_func_0028c8a8",
    STUB_28C880: "engine_func_0028c880",
    STUB_2A5A54: "engine_func_002a5a54",
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
CALLEE_SAVED_START_REG = {
    arm.UC_ARM_REG_R4: 0x44444444,
    arm.UC_ARM_REG_R5: 0x55555555,
    arm.UC_ARM_REG_R6: 0x66666666,
    arm.UC_ARM_REG_R7: 0x77777777,
    arm.UC_ARM_REG_R8: 0x88888888,
    arm.UC_ARM_REG_R9: 0x99999999,
    arm.UC_ARM_REG_R10: 0xAAAAAAAA,
    arm.UC_ARM_REG_R11: 0xBBBBBBBB,
}
FP_CALLEE_SAVED_START = {
    arm.UC_ARM_REG_D8: 0x1111222233334444,
    arm.UC_ARM_REG_D9: 0x5555666677778888,
}


def get_orig_bytes() -> bytes:
    with open(ORIG_BIN, "rb") as f:
        f.seek(FUNC_ADDR - 0x00100000)
        return f.read(FUNC_SIZE)


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = None
    for name, value in funcs.items():
        if "0020d7b8" in name:
            candidate = value
            break
    if candidate is None:
        raise RuntimeError(
            f"script_vm_func_0020d7b8 not found in {obj_file}: {sorted(funcs)}"
        )

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):  # R_ARM_CALL / R_ARM_JUMP24
            target = None
            for address, name in STUB_NAMES.items():
                if rel.symbol_name == name:
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
                f"for {rel.symbol_name!r}"
            )
    return bytes(code)


def compile_candidate() -> bytes:
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
def slot_offset(index: int) -> int:
    if index < GROUP0_COUNT:
        return GROUP0_OFFSET + index * SLOT_STRIDE
    return GROUP1_OFFSET + (index - GROUP0_COUNT) * SLOT_STRIDE


def default_slot() -> dict:
    return {
        "active": 0,
        "pending": 0,
        "direction": 0,
        "vec": (0x11110000, 0x22220000, 0x33330000),
        "float_bits": 0x3F800000,
        "index": 0,
        "flags": 0,
        "pose": 0,
    }


def build_slot_page(case: dict) -> bytes:
    page = bytearray([0xA5] * SLOT_SIZE)
    struct.pack_into("<H", page, MODE_OFFSET, case.get("mode", 0x16) & 0xFFFF)
    # Unrelated object words around the mode so a wild write is visible.
    struct.pack_into("<I", page, 0x00, 0x0BADF00D)
    struct.pack_into("<I", page, 0x08, 0x0BADF00D)
    struct.pack_into("<I", page, 0x10, 0x0BADF00D)

    specs = case.get("slots", {})
    for index in range(SLOT_COUNT):
        spec = default_slot()
        spec.update(specs.get(index, {}))
        base = slot_offset(index)
        page[base + 0] = spec["active"] & 0xFF
        page[base + 1] = spec["pending"] & 0xFF
        page[base + 2] = spec["direction"] & 0xFF
        page[base + 3] = 0xA5
        for i, word in enumerate(spec["vec"]):
            struct.pack_into("<I", page, base + 4 + i * 4, word & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x10, spec["float_bits"] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x14, spec["index"] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x20, (NODE_ADDR + index * NODE_STRIDE))
        struct.pack_into("<I", page, base + 0x24, 0xA5A5A5A5)
        struct.pack_into("<I", page, base + 0x28, 0xA5A5A5A5)
    return bytes(page)


def build_node_page(case: dict) -> bytes:
    page = bytearray([0x5A] * NODE_SIZE)
    specs = case.get("slots", {})
    for index in range(SLOT_COUNT):
        spec = default_slot()
        spec.update(specs.get(index, {}))
        base = index * NODE_STRIDE
        struct.pack_into("<I", page, base + 0, spec["flags"] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 4, 0x5A5A5A5A)
        struct.pack_into("<I", page, base + 8, SUB_ADDR + index * SUB_STRIDE)
        struct.pack_into("<I", page, base + 12, 0x5A5A5A5A)
    return bytes(page)


def build_sub_page(case: dict) -> bytes:
    page = bytearray([0x3C] * SUB_SIZE)
    specs = case.get("slots", {})
    for index in range(SLOT_COUNT):
        spec = default_slot()
        spec.update(specs.get(index, {}))
        base = index * SUB_STRIDE
        struct.pack_into("<I", page, base + 0x00, 0x3C3C3C3C)
        struct.pack_into("<I", page, base + 0x2C, VIS_ADDR + index * VIS_STRIDE)
        struct.pack_into("<I", page, base + 0x38, spec["pose"] & 0xFFFFFFFF)
        struct.pack_into("<I", page, base + 0x3C, 0x3C3C3C3C)
    return bytes(page)


def build_vis_page() -> bytes:
    page = bytearray([0xC3] * VIS_SIZE)
    for index in range(SLOT_COUNT):
        base = index * VIS_STRIDE
        page[base + 0x1F6] = 0x77
    return bytes(page)


def build_instance_page(case: dict) -> bytes:
    page = bytearray([0x69] * INSTANCE_SIZE)
    base = INSTANCE_BLOCK - INSTANCE_ADDR
    page[base + INSTANCE_ACTIVE_OFFSET] = case.get("instance_active", 0) & 0xFF
    # Keep the neighbouring bytes distinct so an off-by-one offset is caught.
    page[base + INSTANCE_ACTIVE_OFFSET + 1] = 0x2C
    page[base + INSTANCE_ACTIVE_OFFSET - 1] = 0x2B
    return bytes(page)


def build_global_page() -> bytes:
    page = bytearray(GLOBAL_SIZE)
    struct.pack_into("<I", page, GLOBAL_POINTER_SLOT - GLOBAL_ADDR, SLOT_ADDR)
    struct.pack_into("<I", page, GLOBAL_POINTER_SLOT - GLOBAL_ADDR + 4, 0x11223344)
    return bytes(page)


def slot_spec(**overrides) -> dict:
    spec = default_slot()
    spec.update(overrides)
    return spec


def case(name: str, **overrides) -> dict:
    result = {"name": name}
    result.update(overrides)
    return result


# ------------------------------------------------------------------ relocatable
class LeafRunner:
    """One Unicorn machine with deterministic stubs at the original targets."""

    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        # Both bodies use VFP (vpush/vldr/vmov): enable CP10/CP11 and FPEXC.EN.
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)
        self.uc.mem_map(CODE_ADDR, CODE_SIZE)
        self.uc.mem_map(GLOBAL_ADDR, GLOBAL_SIZE)
        self.uc.mem_map(INSTANCE_ADDR, INSTANCE_SIZE)
        self.uc.mem_map(SLOT_ADDR, SLOT_SIZE)
        self.uc.mem_map(NODE_ADDR, NODE_SIZE)
        self.uc.mem_map(SUB_ADDR, SUB_SIZE)
        self.uc.mem_map(VIS_ADDR, VIS_SIZE)
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

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        self.writes.append((address, size, value))

    def _words(self, address: int, count: int) -> tuple:
        raw = self.uc.mem_read(address, 4 * count)
        return struct.unpack(f"<{count}I", raw)

    def _on_stub(self, uc, address: int, size: int, user_data) -> None:
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)

        if address == STUB_1E2C94:
            # Argument-free helper: the original arrives with incidental r0/r1.
            self.call_log.append((STUB_NAMES[address],))
        elif address == STUB_29BDB4:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append((STUB_NAMES[address], r0, s0))
        elif address == STUB_28C8A8:
            vec = self._words(r2, 3)
            self.call_log.append((STUB_NAMES[address], r0, r1, r2, vec))
        elif address == STUB_28C880:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc.reg_read(arm.UC_ARM_REG_S2)
            self.call_log.append((STUB_NAMES[address], r0, r1, s0, s1, s2))
        elif address == STUB_2A5A54:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append((STUB_NAMES[address], r0, r1, s0))
        else:  # pragma: no cover - guarded by hook registration
            raise AssertionError(f"unexpected stub address 0x{address:08x}")

    def run(self, code: bytes, case: dict) -> dict:
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(GLOBAL_ADDR, build_global_page())
        self.uc.mem_write(INSTANCE_ADDR, build_instance_page(case))
        self.uc.mem_write(SLOT_ADDR, build_slot_page(case))
        self.uc.mem_write(NODE_ADDR, build_node_page(case))
        self.uc.mem_write(SUB_ADDR, build_sub_page(case))
        self.uc.mem_write(VIS_ADDR, build_vis_page())
        self.uc.mem_write(STACK_ADDR, b"\x00" * STACK_SIZE)
        self.writes = []

        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for reg, value in CALLEE_SAVED_START_REG.items():
            self.uc.reg_write(reg, value)
        for reg, value in FP_CALLEE_SAVED_START.items():
            self.uc.reg_write(reg, value)
        for reg, value in (
            (arm.UC_ARM_REG_R0, 0xDEADBEEF),
            (arm.UC_ARM_REG_R1, 0xCAFEBABE),
            (arm.UC_ARM_REG_R2, 0x01234567),
            (arm.UC_ARM_REG_R3, 0x89ABCDEF),
        ):
            self.uc.reg_write(reg, value)

        try:
            self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, timeout=5_000_000)
        except Exception as error:  # pragma: no cover - diagnostic path
            pc = self.uc.reg_read(arm.UC_ARM_REG_PC)
            raise RuntimeError(f"Crash at PC=0x{pc:08x}: {error}") from error

        writes = []
        for address, size, value in self.writes:
            if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
                continue
            writes.append((address, size, value))

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {
                name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()
            },
            "fp_callee_saved": {
                name: self.uc.reg_read(reg)
                for name, reg in (("d8", arm.UC_ARM_REG_D8), ("d9", arm.UC_ARM_REG_D9))
            },
            "call_log": list(self.call_log),
            "fixtures": {
                "global": bytes(self.uc.mem_read(GLOBAL_ADDR, GLOBAL_SIZE)),
                "instance": bytes(self.uc.mem_read(INSTANCE_ADDR, INSTANCE_SIZE)),
                "slots": bytes(self.uc.mem_read(SLOT_ADDR, SLOT_SIZE)),
                "nodes": bytes(self.uc.mem_read(NODE_ADDR, NODE_SIZE)),
                "subs": bytes(self.uc.mem_read(SUB_ADDR, SUB_SIZE)),
                "visuals": bytes(self.uc.mem_read(VIS_ADDR, VIS_SIZE)),
            },
            "writes": writes,
        }


def compare(orig: dict, cand: dict) -> list[str]:
    problems = []
    for key in ("pc", "sp", "callee_saved", "fp_callee_saved"):
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
    if orig["writes"] != cand["writes"]:
        problems.append(
            "ordered non-stack writes:\n    orig="
            + repr(orig["writes"])
            + "\n    cand="
            + repr(cand["writes"])
        )
    return problems


def make_cases() -> list[dict]:
    cases: list[dict] = []

    # --- VM mode gate: only 0x16 runs the body.
    for mode in (0x0000, 0x0015, 0x0017, 0xFFFF):
        cases.append(
            case(
                f"mode 0x{mode:04x} returns early",
                mode=mode,
                instance_active=0,
                slots={0: slot_spec(active=1, pending=1, direction=1)},
            )
        )
    cases.append(case("mode 0x16, instance 0, no active slots", slots={}))
    cases.append(
        case(
            "mode 0x16, instance 1, no active slots",
            instance_active=1,
            slots={},
        )
    )

    # --- instance-active branch over every slot: odd flags already hidden.
    all_slots = {}
    for index in range(SLOT_COUNT):
        all_slots[index] = slot_spec(
            active=1,
            pending=1,
            direction=index & 1,
            flags=2 if index & 1 else 0,
            index=0x100 + index,
            pose=0x100 + index,
        )
    cases.append(
        case(
            "instance 1, all 12 slots (set path / already hidden)",
            instance_active=1,
            slots=all_slots,
        )
    )
    cases.append(
        case(
            "instance 0xFF, all 12 slots",
            instance_active=0xFF,
            slots=all_slots,
        )
    )
    cases.append(
        case(
            "instance 1, extra flag bits preserved",
            instance_active=1,
            slots={0: slot_spec(active=1, flags=0x80000003), 8: slot_spec(active=1)},
        )
    )

    # --- instance-inactive branch: pending gate.
    cases.append(
        case(
            "pending 0 skips the whole update",
            instance_active=0,
            slots={0: slot_spec(active=1, pending=0, direction=1, flags=2)},
        )
    )
    cases.append(
        case(
            "pending 0xFF, direction 0xFF treated as non-zero",
            instance_active=0,
            slots={
                0: slot_spec(active=0xFF, pending=0xFF, direction=0xFF, flags=0),
                3: slot_spec(active=1, pending=0xFF, direction=0xFF, flags=3),
            },
        )
    )

    # --- toggle paths: direction != 0 clears bit 1; direction == 0 sets it.
    cases.append(
        case(
            "direction 1, flags bit1 set -> clear, pose equal",
            instance_active=0,
            slots={
                0: slot_spec(
                    active=1,
                    pending=1,
                    direction=1,
                    flags=2,
                    index=0x1234,
                    pose=0x1234,
                )
            },
        )
    )
    cases.append(
        case(
            "direction 1, flags bit1 set -> clear, pose differs",
            instance_active=0,
            slots={
                1: slot_spec(
                    active=1,
                    pending=1,
                    direction=1,
                    flags=0x0000000A,
                    index=0xFFFFFFFF,
                    pose=0x7FFFFFFF,
                )
            },
        )
    )
    cases.append(
        case(
            "direction 1, flags bit1 clear -> skip toggle",
            instance_active=0,
            slots={
                2: slot_spec(
                    active=1,
                    pending=1,
                    direction=1,
                    flags=0x00000001,
                    index=0,
                    pose=1,
                )
            },
        )
    )
    cases.append(
        case(
            "direction 0, flags bit1 clear -> set",
            instance_active=0,
            slots={
                3: slot_spec(
                    active=1,
                    pending=1,
                    direction=0,
                    flags=0xFFFFFFFC,
                    index=0x80000000,
                    pose=0x80000000,
                )
            },
        )
    )
    cases.append(
        case(
            "direction 0, flags bit1 set -> skip toggle",
            instance_active=0,
            slots={
                4: slot_spec(
                    active=1,
                    pending=1,
                    direction=0,
                    flags=0x00000002,
                    index=-1 & 0xFFFFFFFF,
                    pose=0x00000000,
                )
            },
        )
    )

    # --- every slot independently, alternating toggle branch, pose match.
    for index in range(SLOT_COUNT):
        cases.append(
            case(
                f"slot {index} only (group {'0' if index < 9 else '1'})",
                instance_active=0,
                slots={
                    index: slot_spec(
                        active=1,
                        pending=1,
                        direction=index & 1,
                        flags=(2 if index & 1 else 1),
                        index=0x7000 + index,
                        pose=(0x7000 + index) if index % 3 else 0x4000 + index,
                    )
                },
            )
        )

    # --- last slot of each group with all fields at their boundaries.
    for index in (8, 11):
        cases.append(
            case(
                f"boundary slot {index}",
                instance_active=0,
                slots={
                    index: slot_spec(
                        active=1,
                        pending=1,
                        direction=1,
                        flags=2,
                        vec=(0xFFFFFFFF, 0x80000000, 0x00000001),
                        float_bits=0x80000000,  # -0.0f
                        index=0x7FFFFFFF,
                        pose=0x80000000,
                    )
                },
            )
        )

    # --- float/int round-trip through the transform helpers.
    for bits in (0x00000000, 0x3F800000, 0xC2C80000, 0x7F7FFFFF):
        cases.append(
            case(
                f"transform float bits 0x{bits:08x}",
                instance_active=0,
                slots={
                    5: slot_spec(
                        active=1,
                        pending=1,
                        direction=0,
                        flags=0,
                        vec=(bits, bits ^ 0x55555555, bits ^ 0xAAAAAAAA),
                        float_bits=bits,
                        index=0x10,
                        pose=0x11,
                    )
                },
            )
        )

    return cases


def run_case_set(orig_code, cand_code, cases) -> int:
    passed = 0
    for item in cases:
        orig = LeafRunner().run(orig_code, item)
        cand = LeafRunner().run(cand_code, item)
        problems = compare(orig, cand)
        if problems:
            print(f"  [FAIL] {item['name']}")
            for problem in problems:
                print(f"    {problem}")
            raise SystemExit(1)
        passed += 1
        print(f"  [PASS] {item['name']}  ({len(orig['call_log'])} calls)")
    return passed


def main() -> None:
    print("Testing script_vm_func_0020d7b8 (0x0020d7b8)...")
    orig_code = get_orig_bytes()
    cand_code = compile_candidate()
    print(
        f"Original {len(orig_code)} B, candidate {len(cand_code)} B "
        "(six calls relocated)."
    )

    cases = make_cases()
    passed = run_case_set(orig_code, cand_code, cases)

    print("\nNegative controls:")
    for name, old, new in (
        ("mode_constant", "constexpr u16 kActiveMode = 0x16u;",
         "constexpr u16 kActiveMode = 0x17u;"),
        ("hidden_flag", "constexpr u32 kHiddenFlag = 2u;",
         "constexpr u32 kHiddenFlag = 4u;"),
        ("instance_offset", "constexpr u32 kInstanceActiveOffset = 0x22u;",
         "constexpr u32 kInstanceActiveOffset = 0x23u;"),
        ("group1_offset", "const u32 slot_offset = (group == 0) ? 0x1114u : 0x12A0u;",
         "const u32 slot_offset = (group == 0) ? 0x1114u : 0x12A4u;"),
        ("shown_volume", "ui_func_0029bdb4(slots::backend_of(slot), 1.0f);",
         "ui_func_0029bdb4(slots::backend_of(slot), 0.0f);"),
        ("pose_offset", "+ 0x38) !=", "+ 0x3C) !="),
    ):
        mutant_code = compile_candidate_mutant(name, old, new)
        detected = False
        for item in cases:
            orig = LeafRunner().run(orig_code, item)
            bad = LeafRunner().run(mutant_code, item)
            if compare(orig, bad):
                detected = True
                break
        assert detected, f"negative control failed: {name} was not detected"
        print(f"  [PASS] {name} mutant is detected")

    print(f"\nAll {passed}/{len(cases)} differential cases PASSED.")


if __name__ == "__main__":
    main()
