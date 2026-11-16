#!/usr/bin/env python3
"""Differential test for script_vm_func_0023187c (0x0023187C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the script_vm_func_0023187c
body, resolves its direct calls to deterministic stubs placed at the original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.
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
OUT_DIR = ROOT / "build/test_leaf_0023187c"

FUNC_ADDR = 0x0023187C
FUNC_SIZE = 700

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00100000  # covers 0x00231628..0x002C0BA8
CAND_RODATA_ADDR = 0x00600000
CAND_RODATA_SIZE = 0x00010000
WORK_ADDR = 0x00700000
WORK_SIZE = 0x00008000
RECS_ADDR = 0x00710000
RECS_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_231664 = 0x00231664  # camp_func_00231664
STUB_231628 = 0x00231628  # camp_func_00231628
STUB_2C0BA8 = 0x002C0BA8  # script_vm_func_002c0ba8
STUB_24C3F8 = 0x0024C3F8  # engine_func_0024c3f8

STUB_NAMES = {
    STUB_231664: "camp_func_00231664",
    STUB_231628: "camp_func_00231628",
    STUB_2C0BA8: "script_vm_func_002c0ba8",
    STUB_24C3F8: "engine_func_0024c3f8",
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


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def elf_sections_and_abs32_targets(path: Path, func_name: str) -> tuple[dict[str, bytes], dict[int, str]]:
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
    sec_names: list[str] = []
    result: dict[str, bytes] = {}
    for section in sections:
        end = shstrtab.find(b"\x00", section[0])
        name = shstrtab[section[0] : end].decode("ascii", errors="replace")
        sec_names.append(name)
        if section[1] != 8:
            result[name] = data[section[4] : section[4] + section[5]]

    symtab_sec = next(s for n, s in zip(sec_names, sections) if n == ".symtab")
    sym_data = data[symtab_sec[4] : symtab_sec[4] + symtab_sec[5]]
    syms = [struct.unpack_from("<IIIBBH", sym_data, i) for i in range(0, len(sym_data), 16)]

    strtab_data = result[".strtab"]
    func_shndx = None
    func_val = 0
    for st_name, st_val, _sz, _info, _other, st_shndx in syms:
        end = strtab_data.find(b"\x00", st_name)
        if strtab_data[st_name:end].decode("ascii", errors="replace") == func_name:
            func_shndx = st_shndx
            func_val = st_val
            break

    abs32_targets: dict[int, str] = {}
    for _name, sec in zip(sec_names, sections):
        if sec[1] == 9 and sec[7] == func_shndx:
            rel_data = data[sec[4] : sec[4] + sec[5]]
            for i in range(0, len(rel_data), 8):
                r_offset, r_info = struct.unpack_from("<II", rel_data, i)
                if (r_info & 0xFF) == 2:
                    sym_idx = r_info >> 8
                    target_shndx = syms[sym_idx][5]
                    abs32_targets[r_offset - func_val] = sec_names[target_shndx]
    return result, abs32_targets


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("script_vm_func_0023187c")
    if candidate is None:
        raise RuntimeError(f"script_vm_func_0023187c not found in {obj_file}")

    sections, abs32_targets = elf_sections_and_abs32_targets(obj_file, "script_vm_func_0023187c")
    rodata_map: dict[str, int] = {}
    rodata_chunks: dict[int, bytes] = {}
    next_addr = CAND_RODATA_ADDR

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type in (28, 29):
            target = SYMBOL_TO_ADDRESS.get(rel.symbol_name)
            if target is None:
                raise RuntimeError(f"unresolved relocation {rel.symbol_name}")
            pc = FUNC_ADDR + rel.offset + 8
            offset = target - pc
            if offset & 3:
                raise RuntimeError(f"unaligned ARM target 0x{target:08x}")
            original = struct.unpack_from("<I", code, rel.offset)[0]
            cond = original & 0xFF000000
            struct.pack_into("<I", code, rel.offset, cond | ((offset >> 2) & 0x00FFFFFF))
        elif rel.relocation_type == 2:
            sec_name = abs32_targets[rel.offset]
            if sec_name not in rodata_map:
                rodata_map[sec_name] = next_addr
                rodata_chunks[next_addr] = sections[sec_name]
                next_addr += (len(sections[sec_name]) + 0xFFF) & ~0xFFF
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            struct.pack_into("<I", code, rel.offset, rodata_map[sec_name] + addend)
        else:
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
    return bytes(code), rodata_chunks


def compile_candidate_baseline() -> tuple[bytes, dict[int, bytes]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compile failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> tuple[bytes, dict[int, bytes]]:
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


class Runner:
    def __init__(self) -> None:
        self.uc = unicorn.Uc(unicorn.UC_ARCH_ARM, unicorn.UC_MODE_ARM)
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (CAND_RODATA_ADDR, CAND_RODATA_SIZE),
            (WORK_ADDR, WORK_SIZE),
            (RECS_ADDR, RECS_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(addr, size)

        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        for address in STUB_NAMES:
            self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_231628,
            end=STUB_2C0BA8 + 4,
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

        if address == STUB_231664:
            self.call_log.append(("231664",))
            uc.reg_write(arm.UC_ARM_REG_R0, len(self.case["records"]))
        elif address == STUB_231628:
            idx = s32(r1)
            self.call_log.append(("231628", idx))
            uc.reg_write(arm.UC_ARM_REG_R0, RECS_ADDR + idx * 0x20)
        elif address == STUB_2C0BA8:
            self.call_log.append(("2c0ba8", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if r0 in self.case["true_flags"] else 0)
        elif address == STUB_24C3F8:
            self.call_log.append(("24c3f8", r0, r1))
            w, h = self.case["sprite_dims"].get(r1, (16, 16))
            uc.mem_write(r2, struct.pack("<ii", w, 0))
            uc.mem_write(r3, struct.pack("<ii", h, 0))
            uc.mem_write(r2, struct.pack("<i", w))
            uc.mem_write(r3, struct.pack("<i", h))

    def run(self, code: bytes, rodata: dict[int, bytes], case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        if rodata:
            for addr, chunk in rodata.items():
                self.uc.mem_write(addr, chunk)
        self.uc.mem_write(WORK_ADDR, b"\x00" * WORK_SIZE)
        self.uc.mem_write(RECS_ADDR, b"\x00" * RECS_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        for idx, rec in enumerate(case["records"]):
            base = RECS_ADDR + idx * 0x20
            self.uc.mem_write(base + 0x00, struct.pack("<bBB", rec["map_id"], rec["b1"], rec["b2"]))
            self.uc.mem_write(base + 0x04, struct.pack("<HHh", rec["flag_on"], rec["flag_off"], rec["kind"]))
            self.uc.mem_write(base + 0x0E, struct.pack("<hh", rec["x"], rec["y"]))

        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["map_id"] & 0xFFFFFFFF)
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
            "work_mem": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
        }


def rec(map_id=0x65, b1=1, b2=2, flag_on=0, flag_off=0, kind=5, x=0, y=0) -> dict:
    return {
        "map_id": map_id,
        "b1": b1,
        "b2": b2,
        "flag_on": flag_on,
        "flag_off": flag_off,
        "kind": kind,
        "x": x,
        "y": y,
    }


def make_cases() -> list[dict]:
    dims = {0x1BC3: (16, 20), 0x1BC4: (24, 18), 0x1BC5: (12, 14)}
    return [
        {
            "name": "empty_records",
            "map_id": 0x65,
            "records": [],
            "true_flags": set(),
            "sprite_dims": dims,
        },
        {
            "name": "map_0x65_all_kinds_and_filters",
            "map_id": 0x65,
            "records": [
                rec(map_id=0x66, kind=5, x=100, y=200),
                rec(map_id=0x65, flag_on=10, kind=5, x=100, y=200),
                rec(map_id=0x65, flag_on=11, flag_off=12, kind=5, x=-1000, y=500),
                rec(map_id=0x65, flag_on=11, flag_off=13, kind=6, x=2000, y=-3000),
                rec(map_id=0x65, kind=9, x=0, y=0),
            ],
            "true_flags": {11, 12},
            "sprite_dims": dims,
        },
        {
            "name": "map_0x66_bounds",
            "map_id": 0x66,
            "records": [
                rec(map_id=0x66, kind=5, x=-5000, y=4000),
                rec(map_id=0x66, kind=6, x=10000, y=-10000),
            ],
            "true_flags": set(),
            "sprite_dims": dims,
        },
        {
            "name": "map_0x67_bounds",
            "map_id": 0x67,
            "records": [
                rec(map_id=0x67, kind=5, x=3000, y=-2000),
                rec(map_id=0x67, kind=7, x=-8000, y=7000),
            ],
            "true_flags": set(),
            "sprite_dims": dims,
        },
        {
            "name": "map_other_no_match",
            "map_id": 0x64,
            "records": [rec(map_id=0x65, kind=5, x=100, y=200)],
            "true_flags": set(),
            "sprite_dims": dims,
        },
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "call_log", "writes", "work_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code, cand_rodata = compile_candidate_baseline()
    print(f"script_vm_func_0023187c: orig {len(orig_code)} B, cand {len(cand_code)} B, rodata_chunks {len(cand_rodata)}")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, {}, case)
        cand_res = Runner().run(cand_code, cand_rodata, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]: {diffs}")
            print("  orig log:", orig_res["call_log"])
            print("  cand log:", cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("min_x_65", "min_x = -25500.0f;", "min_x = -25400.0f;"),
        ("width_x_66", "width_x = 31000.0f;", "width_x = 31100.0f;"),
        ("min_y_67", "min_y = -19000.0f;", "min_y = -18900.0f;"),
        ("sprite_5", "sprite_id = 0x1BC3;", "sprite_id = 0x1BC6;"),
        ("sprite_6", "sprite_id = 0x1BC4;", "sprite_id = 0x1BC6;"),
        ("stride", "work + 0xE88 + count * 0x4C", "work + 0xE88 + count * 0x48"),
        ("count_off", "work + 0x5A88", "work + 0x5A84"),
    ]
    for name, old, new in mutants:
        m_code, m_rodata = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, {}, case)
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
