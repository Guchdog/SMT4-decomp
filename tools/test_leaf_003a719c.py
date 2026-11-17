#!/usr/bin/env python3
"""Differential test for script_vm_func_003a719c (0x003A719C) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the script_vm_func_003a719c
body, resolves its direct calls (including tail calls) to deterministic stubs
placed at the original addresses, and runs the pinned original
(extracted/exefs/code.bin) against the candidate in separate Unicorn machines
with identical fixtures.
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
OUT_DIR = ROOT / "build/test_leaf_003a719c"

FUNC_ADDR = 0x003A719C
FUNC_SIZE = 724

CODE_ADDR = 0x00220000
CODE_SIZE = 0x001A0000  # covers 0x002329DC..0x003A719C
GLOBAL_ADDR = 0x00430000
GLOBAL_SIZE = 0x00010000  # covers 0x0043D9CC
WORK_ADDR = 0x00700000
WORK_SIZE = 0x0000C000
STR_ADDR = 0x00710000
STR_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_276550 = 0x00276550
STUB_27F10C = 0x0027F10C
STUB_24C48C = 0x0024C48C
STUB_256750 = 0x00256750
STUB_26C8A8 = 0x0026C8A8
STUB_29E2B0 = 0x0029E2B0
STUB_2333D4 = 0x002333D4
STUB_29CEE4 = 0x0029CEE4
STUB_2339E8 = 0x002339E8
STUB_2339AC = 0x002339AC
STUB_2337A0 = 0x002337A0
STUB_2BD25C = 0x002BD25C
STUB_2BF86C = 0x002BF86C
STUB_295904 = 0x00295904
STUB_2BD020 = 0x002BD020
STUB_2971E4 = 0x002971E4
STUB_2A0F68 = 0x002A0F68
STUB_232A48 = 0x00232A48
STUB_29F10C = 0x0029F10C
STUB_29CCF8 = 0x0029CCF8
STUB_2329DC = 0x002329DC
STUB_26C7E8 = 0x0026C7E8
STUB_2B8B78 = 0x002B8B78
STUB_29DA10 = 0x0029DA10
STUB_29DCD4 = 0x0029DCD4
STUB_2B0824 = 0x002B0824

STUB_NAMES = {
    STUB_276550: "script_vm_func_00276550",
    STUB_27F10C: "script_vm_func_0027f10c",
    STUB_24C48C: "ui_func_0024c48c",
    STUB_256750: "shop_func_00256750",
    STUB_26C8A8: "Status_GetFlag1E63",
    STUB_29E2B0: "camp_func_0029e2b0",
    STUB_2333D4: "shop_func_002333d4",
    STUB_29CEE4: "camp_func_0029cee4",
    STUB_2339E8: "shop_func_002339e8",
    STUB_2339AC: "shop_func_002339ac",
    STUB_2337A0: "shop_func_002337a0",
    STUB_2BD25C: "script_vm_func_002bd25c",
    STUB_2BF86C: "engine_func_002bf86c",
    STUB_295904: "script_vm_func_00295904",
    STUB_2BD020: "script_vm_func_002bd020",
    STUB_2971E4: "script_vm_func_002971e4",
    STUB_2A0F68: "camp_func_002a0f68",
    STUB_232A48: "shop_func_00232a48",
    STUB_29F10C: "camp_func_0029f10c",
    STUB_29CCF8: "script_vm_func_0029ccf8",
    STUB_2329DC: "shop_func_002329dc",
    STUB_26C7E8: "camp_func_0026c7e8",
    STUB_2B8B78: "script_vm_func_002b8b78",
    STUB_29DA10: "camp_func_0029da10",
    STUB_29DCD4: "camp_func_0029dcd4",
    STUB_2B0824: "camp_func_002b0824",
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


def read_cstr(uc: unicorn.Uc, addr: int, limit: int = 128) -> bytes:
    raw = bytes(uc.mem_read(addr, limit))
    end = raw.find(0)
    return raw[:end] if end != -1 else raw


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("script_vm_func_003a719c")
    if candidate is None:
        raise RuntimeError(f"script_vm_func_003a719c not found in {obj_file}")

    code_raw, relocs = candidate
    code = bytearray(code_raw)
    for rel in relocs:
        if rel.relocation_type not in (28, 29):
            raise RuntimeError(
                f"unhandled relocation type {rel.relocation_type} "
                f"for {rel.symbol_name}"
            )
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
    return bytes(code)


def compile_candidate_baseline() -> bytes:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    obj_file = OUT_DIR / "leaf_batch45_a.o"
    result = compile_tu_armv6k(SOURCE, obj_file, ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"compile failed:\n{result.stderr}")
    return relocate_candidate(obj_file)


def compile_candidate_mutant(name: str, old: str, new: str) -> bytes:
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
            (WORK_ADDR, WORK_SIZE),
            (STR_ADDR, STR_SIZE),
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
            begin=STUB_2329DC,
            end=STUB_2BF86C + 4,
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

        if address == STUB_276550:
            self.call_log.append(("276550",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["a"])
        elif address == STUB_27F10C:
            self.call_log.append(("27f10c",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["b_ret"])
        elif address == STUB_24C48C:
            self.call_log.append(("24c48c",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["c"])
        elif address == STUB_256750:
            self.call_log.append(("256750",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["d"])
        elif address == STUB_26C8A8:
            self.call_log.append(("26c8a8",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["flag1e63"])
        elif address == STUB_29E2B0:
            self.call_log.append(("29e2b0",))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["e2b0"])
        elif address == STUB_2333D4:
            self.call_log.append(("2333d4", r0, s32(r1)))
        elif address == STUB_29CEE4:
            self.call_log.append(("29cee4", s32(r0)))
        elif address == STUB_2339E8:
            self.call_log.append(("2339e8", r0))
        elif address == STUB_2339AC:
            self.call_log.append(("2339ac", r0))
        elif address == STUB_2337A0:
            self.call_log.append(("2337a0", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 1)
        elif address == STUB_2BD25C:
            self.call_log.append(("2bd25c", r0 & 0xFFFF))
            self.uc.mem_write(STR_ADDR, b"ItemName\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, STR_ADDR)
        elif address == STUB_2BD020:
            self.call_log.append(("2bd020", r0 & 0xFFFF, s32(r1)))
            self.uc.mem_write(STR_ADDR + 0x100, b"ItemDesc\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, STR_ADDR + 0x100)
        elif address == STUB_2BF86C:
            src_str = read_cstr(uc, r1)
            self.call_log.append(("2bf86c", src_str))
            uc.mem_write(r0, src_str + b"\x00")
        elif address == STUB_295904:
            self.call_log.append(("295904", r0, read_cstr(uc, r1)))
        elif address == STUB_2971E4:
            self.call_log.append(("2971e4", r0, s32(r1)))
        elif address == STUB_2A0F68:
            self.call_log.append(("2a0f68", s32(r0)))
        elif address == STUB_29F10C:
            self.call_log.append(("29f10c", r0, r1))
        elif address == STUB_2B8B78:
            self.call_log.append(("2b8b78", r0))
        elif address == STUB_2B0824:
            self.call_log.append(("2b0824", r0 & 0xFFFF))
            self.uc.mem_write(STR_ADDR + 0x200, b"Tab1Desc\x00")
            uc.reg_write(arm.UC_ARM_REG_R0, STR_ADDR + 0x200)
        elif address == STUB_29DA10:
            self.call_log.append(("29da10", r0 & 0xFFFF))
            uc.mem_write(r1, b"Tab0Desc\x00")
        elif address == STUB_29DCD4:
            arg3 = read_cstr(uc, r3) if STACK_ADDR <= r3 < STACK_ADDR + STACK_SIZE else r3
            self.call_log.append(("29dcd4", r0, r1, r2, arg3))
        else:
            self.call_log.append((STUB_NAMES[address],))

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(0x0043D9CC, struct.pack("<I", 0))
        self.uc.mem_write(WORK_ADDR, b"\x00" * WORK_SIZE)
        self.uc.mem_write(STR_ADDR, b"\x00" * STR_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.mem_write(WORK_ADDR + 0x55C + 0x12, struct.pack("<b", case["panel_12"]))
        self.uc.mem_write(WORK_ADDR + 0x590, struct.pack("<I", 0x00750000))
        self.uc.mem_write(WORK_ADDR + 0x5A0, struct.pack("<I", 0x00760000))
        self.uc.mem_write(WORK_ADDR + 0x5A4, struct.pack("<BB", case["w5a4"], case["w5a5"]))
        self.uc.mem_write(WORK_ADDR + 0x5A8, struct.pack("<h", case["count"]))
        self.uc.mem_write(WORK_ADDR + 0x5A8 + 1 * 0x20 + 4, struct.pack("<H", 0x0123))

        self.uc.reg_write(arm.UC_ARM_REG_R0, WORK_ADDR)
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
            "written_addrs": sorted({addr for addr, _sz, _val in self.writes}),
            "work_mem": bytes(self.uc.mem_read(WORK_ADDR, WORK_SIZE)),
            "g_43d9cc": struct.unpack("<i", self.uc.mem_read(0x0043D9CC, 4))[0],
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "count": 2,
        "panel_12": 0,
        "w5a4": 0,
        "w5a5": 0,
        "a": 0,
        "b_ret": 0,
        "c": 0,
        "d": 0,
        "flag1e63": 0,
        "e2b0": 1,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="flag1e63_e2b0_1", flag1e63=1, e2b0=1, w5a4=0),
        base_case(name="flag1e63_e2b0_0_w5a4_1", flag1e63=1, e2b0=0, w5a4=1),
        base_case(name="b_from_27f10c", b_ret=1),
        base_case(name="b_from_panel12", count=1, panel_12=1),
        base_case(name="a_nonzero", a=1, w5a4=0),
        base_case(name="c_nonzero_tab0_to_1", c=1, w5a5=0),
        base_case(name="c_nonzero_tab1_to_0", c=1, w5a5=1),
        base_case(name="d_nonzero", d=1),
        base_case(name="all_zero_noop", count=0),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "call_log", "written_addrs", "work_mem", "g_43d9cc"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"script_vm_func_003a719c: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner().run(cand_code, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]: {diffs}")
            print("  orig log:", orig_res["call_log"])
            print("  cand log:", cand_res["call_log"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("e2b0_idx", "(camp_func_0029e2b0() == 1) ? 1 : 5", "(camp_func_0029e2b0() == 1) ? 2 : 5"),
        ("color", "camp_func_0029f10c(0, 0x323232FFu);", "camp_func_0029f10c(0, 0x323232FEu);"),
        ("req_tab", "work[0x5A5] == 1 ? 0x4Cu : 0x4Du", "work[0x5A5] == 1 ? 0x4Du : 0x4Cu"),
        ("state_b", "*reinterpret_cast<u32*>(work + 0x14) = 7;", "*reinterpret_cast<u32*>(work + 0x14) = 6;"),
        ("state_d", "*reinterpret_cast<u32*>(work + 0x14) = 8;", "*reinterpret_cast<u32*>(work + 0x14) = 6;"),
        ("g_43d9cc", "if (c != 0) {\n        *reinterpret_cast<s32*>(0x0043D9CCu) = -1;", "if (c != 0) {\n        *reinterpret_cast<s32*>(0x0043D9CCu) = 0;"),
    ]
    for name, old, new in mutants:
        m_code = compile_candidate_mutant(name, old, new)
        detected = False
        for case in cases:
            orig_res = Runner().run(orig_code, case)
            bad_res = Runner().run(m_code, case)
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
