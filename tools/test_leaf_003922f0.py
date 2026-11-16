#!/usr/bin/env python3
"""Differential test for engine_func_003922f0 (0x003922F0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_003922f0
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
OUT_DIR = ROOT / "build/test_leaf_003922f0"

FUNC_ADDR = 0x003922F0
FUNC_SIZE = 728

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x001C0000  # covers 0x002337A0..0x003922F0
GLOBAL_ADDR = 0x00430000
GLOBAL_SIZE = 0x00010000  # covers 0x00432FC8
CAND_RODATA_ADDR = 0x00600000
CAND_RODATA_SIZE = 0x00010000
SELF_ADDR = 0x00700000
SELF_SIZE = 0x00001000
ROOT_ADDR = 0x00710000
ROOT_SIZE = 0x00001000
TABLE_ADDR = 0x00720000
TABLE_SIZE = 0x00004000
SRC_ADDR = 0x00730000
SRC_SIZE = 0x00001000
VTBL_ADDR = 0x00740000
VTBL_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_234278 = 0x00234278
STUB_234160 = 0x00234160
STUB_2337A0 = 0x002337A0
STUB_234004 = 0x00234004
STUB_27EC84 = 0x0027EC84
STUB_2A17C0 = 0x002A17C0
STUB_2342B8 = 0x002342B8
STUB_234368 = 0x00234368
STUB_2A1578 = 0x002A1578
STUB_VTBL1 = 0x002D0000
STUB_VTBL3 = 0x002D0010

STUB_NAMES = {
    STUB_234278: "engine_func_00234278",
    STUB_234160: "engine_func_00234160",
    STUB_2337A0: "shop_func_002337a0",
    STUB_234004: "engine_func_00234004",
    STUB_27EC84: "camp_func_0027ec84",
    STUB_2A17C0: "engine_func_002a17c0",
    STUB_2342B8: "func_002342b8",
    STUB_234368: "engine_func_00234368",
    STUB_2A1578: "engine_func_002a1578",
    STUB_VTBL1: "vtbl1",
    STUB_VTBL3: "vtbl3",
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
    return result, abs32_targets, func_val


def relocate_candidate(obj_file: Path) -> tuple[bytes, dict[int, bytes]]:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("engine_func_003922f0")
    if candidate is None:
        raise RuntimeError(f"engine_func_003922f0 not found in {obj_file}")

    sections, abs32_targets, func_val = elf_sections_and_abs32_targets(obj_file, "engine_func_003922f0")
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
            addend = struct.unpack_from("<I", code, rel.offset)[0]
            if sec_name == ".text":
                struct.pack_into("<I", code, rel.offset, (FUNC_ADDR - func_val) + addend)
            else:
                if sec_name not in rodata_map:
                    rodata_map[sec_name] = next_addr
                    rodata_chunks[next_addr] = sections[sec_name]
                    next_addr += (len(sections[sec_name]) + 0xFFF) & ~0xFFF
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
        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL_ADDR, GLOBAL_SIZE),
            (CAND_RODATA_ADDR, CAND_RODATA_SIZE),
            (SELF_ADDR, SELF_SIZE),
            (ROOT_ADDR, ROOT_SIZE),
            (TABLE_ADDR, TABLE_SIZE),
            (SRC_ADDR, SRC_SIZE),
            (VTBL_ADDR, VTBL_SIZE),
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
            begin=STUB_2337A0,
            end=STUB_VTBL3 + 4,
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

        if address == STUB_234278:
            self.call_log.append(("234278",))
            uc.mem_write(r0, b"\x00" * 20)
        elif address == STUB_234160:
            self.call_log.append(("234160", r0, r1))
            uc.mem_write(SRC_ADDR + 0x100, struct.pack("<I", VTBL_ADDR))
            uc.reg_write(arm.UC_ARM_REG_R0, SRC_ADDR + 0x100)
        elif address == STUB_2337A0:
            self.call_log.append(("2337a0", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["sel"])
        elif address == STUB_234004:
            self.call_log.append(("234004", r0, r1, r2))
        elif address == STUB_27EC84:
            words = struct.unpack("<5I", uc.mem_read(r0, 20))
            self.call_log.append(("27ec84", words))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["ec84_ret"])
        elif address == STUB_2A17C0:
            words = struct.unpack("<5I", uc.mem_read(r0, 20))
            self.call_log.append(("2a17c0", words))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["a17c0_ret"])
        elif address == STUB_2342B8:
            words = struct.unpack("<5I", uc.mem_read(r1, 20))
            self.call_log.append(("2342b8", r0, words))
        elif address == STUB_234368:
            self.call_log.append(("234368", r1))
            uc.mem_write(r0, struct.pack("<II", 0x11112222, 0x33334444))
        elif address == STUB_2A1578:
            pair = struct.unpack("<II", uc.mem_read(r0, 8))
            self.call_log.append(("2a1578", pair))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["a1578_ret"])
        elif address == STUB_VTBL1:
            self.call_log.append(("vtbl1", r0))
        elif address == STUB_VTBL3:
            self.call_log.append(("vtbl3", r1))
            uc.mem_write(r0, struct.pack("<5I", *self.case["msg"]))

    def run(self, code: bytes, rodata: dict[int, bytes], case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        if rodata:
            for addr, chunk in rodata.items():
                self.uc.mem_write(addr, chunk)
        self.uc.mem_write(0x00432FC8, struct.pack("<I", ROOT_ADDR))
        self.uc.mem_write(ROOT_ADDR, b"\x00" * ROOT_SIZE)
        self.uc.mem_write(ROOT_ADDR + 0x678, struct.pack("<I", TABLE_ADDR))
        self.uc.mem_write(TABLE_ADDR, b"\x00" * TABLE_SIZE)
        self.uc.mem_write(
            TABLE_ADDR + case["sel"] * (0x139 * 8) + 0x9AA,
            struct.pack("<H", 0x4321),
        )

        self.uc.mem_write(VTBL_ADDR, b"\x00" * VTBL_SIZE)
        self.uc.mem_write(VTBL_ADDR + 0x04, struct.pack("<I", STUB_VTBL1))
        self.uc.mem_write(VTBL_ADDR + 0x0C, struct.pack("<I", STUB_VTBL3))

        self.uc.mem_write(SRC_ADDR, b"\x00" * SRC_SIZE)
        self.uc.mem_write(SRC_ADDR, struct.pack("<I", VTBL_ADDR))

        self.uc.mem_write(SELF_ADDR, b"\x00" * SELF_SIZE)
        self.uc.mem_write(SELF_ADDR + 0x08, struct.pack("<i", case["state"]))
        self.uc.mem_write(SELF_ADDR + 0x0C, struct.pack("<i", case["countdown"]))
        self.uc.mem_write(
            SELF_ADDR + 0x208,
            struct.pack("<I", SRC_ADDR if case["has_src"] else 0),
        )
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_R0, SELF_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)

        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "call_log": list(self.call_log),
            "writes": sorted(self.writes),
            "self_mem": bytes(self.uc.mem_read(SELF_ADDR, SELF_SIZE)),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "state": 0,
        "countdown": 2,
        "has_src": True,
        "sel": 2,
        "msg": (0x67, 1, 2, 3, 4),
        "ec84_ret": 0,
        "a17c0_ret": 1,
        "a1578_ret": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="state_0"),
        base_case(name="state_1_ec84", state=1, ec84_ret=1),
        base_case(name="state_1_a17c0_0", state=1, a17c0_ret=0),
        base_case(name="state_1_tag66", state=1, msg=(0x66, 10, 20, 30, 40)),
        base_case(name="state_1_tag67", state=1, msg=(0x67, 10, 20, 30, 40)),
        base_case(name="state_1_tag_other", state=1, msg=(0x55, 10, 20, 30, 40)),
        base_case(name="state_2_with_prev", state=2, has_src=True),
        base_case(name="state_2_no_prev", state=2, has_src=False),
        base_case(name="state_3_ec84", state=3, ec84_ret=1),
        base_case(name="state_3_tag66", state=3, msg=(0x66, 1, 2, 3, 4)),
        base_case(name="state_3_tag67", state=3, msg=(0x67, 1, 2, 3, 4)),
        base_case(name="state_3_tag_other", state=3, msg=(0x55, 1, 2, 3, 4)),
        base_case(name="state_4_bit31_set", state=4, a1578_ret=0x80000000),
        base_case(name="state_4_bit31_clr", state=4, a1578_ret=0x7FFFFFFF),
        base_case(name="state_5_countdown_gt0", state=5, countdown=2),
        base_case(name="state_5_countdown_0", state=5, countdown=1),
        base_case(name="state_270f", state=0x270F),
        base_case(name="state_default", state=99),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "call_log", "writes", "self_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code, cand_rodata = compile_candidate_baseline()
    print(f"engine_func_003922f0: orig {len(orig_code)} B, cand {len(cand_code)} B, rodata_chunks {len(cand_rodata)}")

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
        ("table_off", "table + sel * (0x139u * 8u) + 0x9AAu", "table + sel * (0x139u * 8u) + 0x9ACu"),
        ("state3_out4", "*reinterpret_cast<s32*>(self + 0x04) = 0x0A;", "*reinterpret_cast<s32*>(self + 0x04) = 0x0B;"),
        ("state4_tag", "self[0x210] = 0x64;", "self[0x210] = 0x65;"),
        ("state5_out4", "*reinterpret_cast<s32*>(self + 0x04) = 6;", "*reinterpret_cast<s32*>(self + 0x04) = 7;"),
        ("state_270f", "engine_func_00234004(self, 5, 3);", "engine_func_00234004(self, 5, 4);"),
        ("bit31", "(engine_func_002a1578(pair) >> 31) != 0", "(engine_func_002a1578(pair) >> 30) != 0"),
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
