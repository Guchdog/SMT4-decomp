#!/usr/bin/env python3
"""Differential test for camp_func_00204d6c (0x00204D6C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the camp_func_00204d6c body,
resolves its direct calls (including BLX into the Thumb formatter at 0x002BE7FC)
and .rodata string relocations to deterministic stubs placed at the original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the ordered call log, with every meaningful register/stack/VFP argument and
    formatted buffer string, of:
      - 0x002BF6D0 (camp_func_002bf6d0: layout node lookup)
      - 0x002BF558 (func_002bf558: panel draw)
      - 0x002BCFF0 (engine_func_002bcff0: demon name lookup)
      - 0x002BE7FC (ui_func_002be7fc: Thumb text formatter)
      - 0x002BE77C (ui_func_002be77c: scaled text draw, s0..s4 VFP args)
      - 0x002B6F74 (camp_func_002b6f74: demon bars draw, sxth demon_id)
      - 0x0028D498 (camp_func_0028d498: demon level lookup)
      - 0x002BE16C (engine_func_002be16c: level/dash text draw)
  * every byte of the layout node fixture page and demon name fixture page;
  * the sorted list of every emulated written byte outside the private stack.

Negative controls mutate:
  * the layout group (0x1A -> 0x1B)
  * the slot background panel id (0x19 -> 0x18)
  * the name node id (0x40F -> 0x410)
  * the bars node id (0x40E -> 0x40D)
  * the level node id (0x521 -> 0x522)
  * the priority (0xB5 -> 0xB4)
  * the name X scale (0.29296875f -> 0.5f)
  * the empty slot text color (0x5A5A5AFF -> 0x5A5A5AFE)
  * the empty slot dash string ("---" -> "--")
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
OUT_DIR = ROOT / "build/test_leaf_00204d6c"

FUNC_ADDR = 0x00204D6C
FUNC_SIZE = 692

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00100000  # covers 0x00204D6C and all stubs up to 0x002BF6D0
RODATA_ADDR = 0x00600000
RODATA_SIZE = 0x00010000
NODES_ADDR = 0x00700000
NODES_SIZE = 0x00004000
NAMES_ADDR = 0x00710000
NAMES_SIZE = 0x00004000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2BF6D0 = 0x002BF6D0  # camp_func_002bf6d0
STUB_2BF558 = 0x002BF558  # func_002bf558
STUB_2BCFF0 = 0x002BCFF0  # engine_func_002bcff0
STUB_2BE7FC = 0x002BE7FC  # ui_func_002be7fc (Thumb)
STUB_2BE77C = 0x002BE77C  # ui_func_002be77c
STUB_2B6F74 = 0x002B6F74  # camp_func_002b6f74
STUB_28D498 = 0x0028D498  # camp_func_0028d498
STUB_2BE16C = 0x002BE16C  # engine_func_002be16c

THUMB_STUBS = {STUB_2BE7FC}

STUB_NAMES = {
    STUB_2BF6D0: "camp_func_002bf6d0",
    STUB_2BF558: "func_002bf558",
    STUB_2BCFF0: "engine_func_002bcff0",
    STUB_2BE7FC: "ui_func_002be7fc",
    STUB_2BE77C: "ui_func_002be77c",
    STUB_2B6F74: "camp_func_002b6f74",
    STUB_28D498: "camp_func_0028d498",
    STUB_2BE16C: "engine_func_002be16c",
}
SYMBOL_TO_ADDRESS = {name: address for address, name in STUB_NAMES.items()}

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
VFP_CALLEE_SAVED = (
    ("d8", arm.UC_ARM_REG_D8, 0x3FF1111122222222),
    ("d9", arm.UC_ARM_REG_D9, 0x3FF3333344444444),
    ("d10", arm.UC_ARM_REG_D10, 0x3FF5555566666666),
    ("d11", arm.UC_ARM_REG_D11, 0x3FF7777788888888),
    ("d12", arm.UC_ARM_REG_D12, 0x3FF99999AAAAAAAA),
    ("d13", arm.UC_ARM_REG_D13, 0x3FFBBBBBCCCCCCCC),
    ("d14", arm.UC_ARM_REG_D14, 0x3FFDDDDDEEEEEEEE),
    ("d15", arm.UC_ARM_REG_D15, 0x3FFFFFFFFFFFFFFF),
)

S_REGS = (
    arm.UC_ARM_REG_S0,
    arm.UC_ARM_REG_S1,
    arm.UC_ARM_REG_S2,
    arm.UC_ARM_REG_S3,
    arm.UC_ARM_REG_S4,
)


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def s16(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


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
        if section[1] != 8:  # skip SHT_NOBITS
            result[name] = data[section[4] : section[4] + section[5]]
    return result


def relocate_candidate(obj_file: Path) -> tuple[bytes, bytes]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("camp_func_00204d6c")
    if candidate is None:
        raise RuntimeError(f"camp_func_00204d6c not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            target = SYMBOL_TO_ADDRESS.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(
                    f"unresolved relocation type {rel.relocation_type} "
                    f"for {rel.symbol_name}"
                )
            pc = FUNC_ADDR + rel.offset + 8
            offset = target - pc
            if target in THUMB_STUBS:
                if offset & 3:
                    raise RuntimeError(f"unaligned Thumb target 0x{target:08x}")
                instruction = (
                    0xFA000000
                    | ((offset >> 2) & 0x00FFFFFF)
                    | ((offset & 2) << 23)
                )
                struct.pack_into("<I", code, rel.offset, instruction)
            else:
                if offset & 3:
                    raise RuntimeError(f"unaligned ARM target 0x{target:08x}")
                original = struct.unpack_from("<I", code, rel.offset)[0]
                cond = original & 0xFF000000
                struct.pack_into(
                    "<I", code, rel.offset, cond | ((offset >> 2) & 0x00FFFFFF)
                )
        elif rel.relocation_type == 2:  # R_ARM_ABS32 into .rodata.str1.1
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, RODATA_ADDR + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    rodata = elf_sections(obj_file).get(".rodata.str1.1", b"")
    return bytes(code), rodata


def compile_candidate_baseline() -> tuple[bytes, bytes]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compile failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, bytes]:
    text = SOURCE.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutant {name}: expected 1 match for {old!r}")
    mutant_src = OUT_DIR / f"mutant_{name}.cpp"
    mutant_obj = OUT_DIR / f"mutant_{name}.o"
    mutant_src.write_text(text.replace(old, new, 1), encoding="utf-8")
    result = compile_tu_armv6k(mutant_src, mutant_obj, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"mutant {name} compile failed:\n{result.stderr}")
    return relocate_candidate(mutant_obj)


def read_cstr(uc: unicorn.Uc, addr: int, limit: int = 128) -> bytes:
    raw = bytes(uc.mem_read(addr, limit))
    end = raw.find(0)
    return raw[:end] if end != -1 else raw


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (RODATA_ADDR, RODATA_SIZE),
            (NODES_ADDR, NODES_SIZE),
            (NAMES_ADDR, NAMES_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(addr, size)

        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))

        # Place BX LR stubs (ARM: 0xE12FFF1E, Thumb: 0x4770).
        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_28D498,
            end=STUB_2BF6D0 + 4,
        )
        self.uc.hook_add(
            unicorn.UC_HOOK_MEM_WRITE,
            self._on_write,
            begin=0,
            end=0xFFFFFFFF,
        )

        self.case: dict = {}
        self.call_log: list[tuple] = []
        self.writes: list[tuple[int, int, int]] = []
        self.node_slots: dict[tuple[int, int], int] = {}

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address, size, user_data) -> None:
        if address not in STUB_NAMES:
            return

        r0 = uc.reg_read(arm.UC_ARM_REG_R0)
        r1 = uc.reg_read(arm.UC_ARM_REG_R1)
        r2 = uc.reg_read(arm.UC_ARM_REG_R2)
        r3 = uc.reg_read(arm.UC_ARM_REG_R3)
        sp = uc.reg_read(arm.UC_ARM_REG_SP)

        if address == STUB_2BF6D0:
            self.call_log.append(("node", r0, r1))
            node_addr = self.node_slots.get((r0, r1), NODES_ADDR + 0x3F00)
            uc.reg_write(arm.UC_ARM_REG_R0, node_addr)
        elif address == STUB_2BF558:
            arg4 = s32(struct.unpack("<I", uc.mem_read(sp, 4))[0])
            arg5 = s32(struct.unpack("<I", uc.mem_read(sp + 4, 4))[0])
            self.call_log.append(("panel", r0, r1, r2, s32(r3), arg4, arg5))
        elif address == STUB_2BCFF0:
            self.call_log.append(("name", s32(r0)))
            name_bytes = self.case["demon_name"]
            uc.mem_write(NAMES_ADDR, name_bytes + b"\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, NAMES_ADDR)
        elif address == STUB_2BE7FC:
            fmt = read_cstr(uc, r1)
            if fmt == b"%s":
                arg_str = read_cstr(uc, r2)
                formatted = arg_str + b"\x00"
                self.call_log.append(("fmt", fmt, arg_str))
            elif fmt == b"%d":
                val = s32(r2)
                formatted = str(val).encode("ascii") + b"\x00"
                self.call_log.append(("fmt", fmt, val))
            else:
                formatted = fmt + b"\x00"
                self.call_log.append(("fmt", fmt))
            uc.mem_write(r0, formatted)
            uc.reg_write(arm.UC_ARM_REG_R0, len(formatted) - 1)
        elif address == STUB_2BE77C:
            text = read_cstr(uc, r2)
            floats = tuple(uc.reg_read(reg) for reg in S_REGS)
            self.call_log.append(("draw_text", r0, r1, text, floats))
        elif address == STUB_2B6F74:
            arg4 = s32(struct.unpack("<I", uc.mem_read(sp, 4))[0])
            arg5 = s32(struct.unpack("<I", uc.mem_read(sp + 4, 4))[0])
            self.call_log.append(("bars", s32(r0), s32(r1), s32(r2), s32(r3), arg4, arg5))
        elif address == STUB_28D498:
            self.call_log.append(("level", s32(r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["demon_level"] & 0xFFFFFFFF)
        elif address == STUB_2BE16C:
            width = s32(struct.unpack("<I", uc.mem_read(sp, 4))[0])
            prio = s32(struct.unpack("<I", uc.mem_read(sp + 4, 4))[0])
            text_ptr = struct.unpack("<I", uc.mem_read(sp + 8, 4))[0]
            text = read_cstr(uc, text_ptr)
            self.call_log.append(("draw_lv", r0, s32(r1), s32(r2), s32(r3), width, prio, text))

    def run(self, code: bytes, rodata: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []
        self.node_slots = {}

        self.uc.mem_write(CODE_ADDR, b"\x00" * (FUNC_ADDR - CODE_ADDR))
        self.uc.mem_write(FUNC_ADDR, code)
        if rodata:
            self.uc.mem_write(RODATA_ADDR, rodata)
        self.uc.mem_write(NODES_ADDR, b"\x00" * NODES_SIZE)
        self.uc.mem_write(NAMES_ADDR, b"\x00" * NAMES_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        # Populate node records at 0x20-byte offsets in NODES_ADDR.
        for idx, ((group, node_id), (nx, ny)) in enumerate(case["nodes"].items()):
            addr = NODES_ADDR + idx * 0x20
            self.node_slots[(group, node_id)] = addr
            self.uc.mem_write(addr + 0x08, struct.pack("<hh", nx, ny))

        # Place 5th argument (text_color) at [ENTRY_SP].
        self.uc.mem_write(ENTRY_SP, struct.pack("<I", case["text_color"] & 0xFFFFFFFF))

        self.uc.reg_write(arm.UC_ARM_REG_R0, case["x"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["y"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, case["demon_id"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R3, case["panel_id"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])
        for _name, reg, val in VFP_CALLEE_SAVED:
            self.uc.reg_write(reg, val)

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "vfp_saved": {name: self.uc.reg_read(reg) for name, reg, _v in VFP_CALLEE_SAVED},
            "call_log": list(self.call_log),
            "writes": sorted(self.writes),
            "nodes_mem": bytes(self.uc.mem_read(NODES_ADDR, NODES_SIZE)),
            "names_mem": bytes(self.uc.mem_read(NAMES_ADDR, NAMES_SIZE)),
        }


def make_cases() -> list[dict]:
    default_nodes = {
        (0x1A, 0x414): (10, 20),
        (0x1A, 0x415): (-30, 45),
        (0x1A, 0x40F): (12, 4),
        (0x1A, 0x40E): (100, -8),
        (0x1A, 0x521): (140, 18),
    }
    return [
        {
            "name": "demon_basic",
            "x": 16,
            "y": 32,
            "demon_id": 42,
            "panel_id": 0x414,
            "text_color": 0xFFFFFFFF,
            "demon_name": b"Pixie",
            "demon_level": 7,
            "nodes": default_nodes,
        },
        {
            "name": "demon_negative_coords",
            "x": -100,
            "y": -50,
            "demon_id": 123,
            "panel_id": 0x415,
            "text_color": 0x12345678,
            "demon_name": b"Jack Frost",
            "demon_level": 99,
            "nodes": default_nodes,
        },
        {
            "name": "demon_sxth_boundary_0x8000",
            "x": 0,
            "y": 0,
            "demon_id": 0x8000,
            "panel_id": 0x414,
            "text_color": 0x00FF00FF,
            "demon_name": b"Metatron",
            "demon_level": -1,
            "nodes": default_nodes,
        },
        {
            "name": "demon_sxth_boundary_0x7fff",
            "x": 5,
            "y": -5,
            "demon_id": 0x7FFF,
            "panel_id": 0x414,
            "text_color": 0xAABBCCDD,
            "demon_name": b"Alice",
            "demon_level": 0,
            "nodes": default_nodes,
        },
        {
            "name": "empty_slot_demon_0",
            "x": 24,
            "y": 48,
            "demon_id": 0,
            "panel_id": 0x414,
            "text_color": 0xFFFFFFFF,
            "demon_name": b"Unused",
            "demon_level": 1,
            "nodes": default_nodes,
        },
        {
            "name": "empty_slot_negative_xy",
            "x": -40,
            "y": -12,
            "demon_id": 0,
            "panel_id": 0x415,
            "text_color": 0x000000FF,
            "demon_name": b"Unused",
            "demon_level": 1,
            "nodes": default_nodes,
        },
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "call_log", "writes", "nodes_mem", "names_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch:\n  orig={orig[key]!r}\n  cand={cand[key]!r}")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code, cand_rodata = compile_candidate_baseline()
    print(
        f"camp_func_00204d6c: orig {len(orig_code)} B, "
        f"cand {len(cand_code)} B, rodata {len(cand_rodata)} B"
    )

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, b"", case)
        cand_res = Runner().run(cand_code, cand_rodata, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]:")
            for d in diffs:
                print(" ", d)
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("group", "constexpr u32 kCampLayoutGroup = 0x1A;", "constexpr u32 kCampLayoutGroup = 0x1B;"),
        ("bg_panel", "constexpr u32 kSlotBgPanelId = 0x19;", "constexpr u32 kSlotBgPanelId = 0x18;"),
        ("name_node", "constexpr u32 kNameNodeId = 0x40F;", "constexpr u32 kNameNodeId = 0x410;"),
        ("bars_node", "constexpr u32 kBarsNodeId = 0x40E;", "constexpr u32 kBarsNodeId = 0x40D;"),
        ("level_node", "constexpr u32 kLevelNodeId = 0x521;", "constexpr u32 kLevelNodeId = 0x522;"),
        ("prio", "constexpr s32 kSlotPriority = 0xB5;", "constexpr s32 kSlotPriority = 0xB4;"),
        ("scale_x", "constexpr f32 kNameScaleX = 0.29296875f;", "constexpr f32 kNameScaleX = 0.5f;"),
        ("empty_color", "constexpr u32 kEmptyTextColor = 0x5A5A5AFFu;", "constexpr u32 kEmptyTextColor = 0x5A5A5AFEu;"),
        ("dash_str", 'ui_func_002be7fc(text, "---");', 'ui_func_002be7fc(text, "--");'),
    ]
    for name, old, new in mutants:
        m_code, m_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, b"", case)
            bad_res = Runner().run(m_code, m_rodata, case)
            if compare_results(orig_res, bad_res):
                detected = True
                break
        if not detected:
            print(f"FAIL [mutant {name}]: not detected!")
            return 1
        print(f"PASS [mutant {name} detected]")

    print(f"ALL PASS: {len(cases)} cases + {len(mutants)} negative controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
