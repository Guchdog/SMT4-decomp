#!/usr/bin/env python3
"""Differential test for ui_func_0015a7c0 (0x0015A7C0) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the ui_func_0015a7c0 body,
resolves its direct calls (including BLX into Thumb 0x002C00D4) to
deterministic stubs placed at the original addresses, and runs the pinned
original (extracted/exefs/code.bin) against the candidate in separate Unicorn
machines with identical fixtures.
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
OUT_DIR = ROOT / "build/test_leaf_0015a7c0"

FUNC_ADDR = 0x0015A7C0
FUNC_SIZE = 720

CODE_ADDR = 0x00150000
CODE_SIZE = 0x00180000  # covers 0x0015A7C0..0x002C00D4
GLOBAL1_ADDR = 0x00460000
GLOBAL1_SIZE = 0x00020000  # covers 0x004652A0 and 0x0047662C
GLOBAL2_ADDR = 0x004E0000
GLOBAL2_SIZE = 0x00010000  # covers 0x004EFD38
CTX_ADDR = 0x00700000
CTX_SIZE = 0x00004000
SRC_ADDR = 0x00710000
SRC_SIZE = 0x00001000
DATA_ADDR = 0x00720000
DATA_SIZE = 0x00001000
CMD_ADDR = 0x00800000
CMD_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2A1A08 = 0x002A1A08
STUB_2A198C = 0x002A198C
STUB_2B73A4 = 0x002B73A4
STUB_2C00D4 = 0x002C00D4  # Thumb

THUMB_STUBS = {STUB_2C00D4}

STUB_NAMES = {
    STUB_2A1A08: "func_002a1a08",
    STUB_2A198C: "func_002a198c",
    STUB_2B73A4: "ui_func_002b73a4",
    STUB_2C00D4: "engine_func_002c00d4",
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


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("ui_func_0015a7c0")
    if candidate is None:
        raise RuntimeError(f"ui_func_0015a7c0 not found in {obj_file}")

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
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (GLOBAL1_ADDR, GLOBAL1_SIZE),
            (GLOBAL2_ADDR, GLOBAL2_SIZE),
            (CTX_ADDR, CTX_SIZE),
            (SRC_ADDR, SRC_SIZE),
            (DATA_ADDR, DATA_SIZE),
            (CMD_ADDR, CMD_SIZE),
            (STACK_ADDR, STACK_SIZE),
            (TRAP_ADDR, 0x1000),
        ):
            self.uc.mem_map(addr, size)

        self.uc.mem_write(TRAP_ADDR, struct.pack("<I", 0xE7FFDEFE))
        for address in STUB_NAMES:
            if address in THUMB_STUBS:
                self.uc.mem_write(address, struct.pack("<H", 0x4770))
            else:
                self.uc.mem_write(address, struct.pack("<I", 0xE12FFF1E))

        self.uc.hook_add(
            unicorn.UC_HOOK_CODE,
            self._on_stub,
            begin=STUB_2A198C,
            end=STUB_2C00D4 + 4,
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

        if address == STUB_2A1A08:
            vec = bytes(uc.mem_read(r1, 16))
            self.call_log.append(("2a1a08", r0, vec))
            uc.mem_write(r0, vec)
        elif address == STUB_2A198C:
            in_vec = struct.unpack("<4f", uc.mem_read(r3, 16))
            self.call_log.append(("2a198c", r0, r2, in_vec))
            out_vec = (in_vec[0] + 1.0, in_vec[1] + 2.0, in_vec[2] + 3.0, in_vec[3] + 4.0)
            uc.mem_write(r1, struct.pack("<4f", *out_vec))
        elif address == STUB_2B73A4:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append(("2b73a4", s0))
            val = struct.unpack("<f", struct.pack("<I", s0))[0]
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(val * 0.5))
        elif address == STUB_2C00D4:
            self.call_log.append(("2c00d4", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["c00d4_ret"])

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(0x004652A0, struct.pack("<I", CMD_ADDR))
        self.uc.mem_write(0x0047662C, struct.pack("<I", case["g_47662c"]))
        self.uc.mem_write(0x004EFD38, struct.pack("<4f", 9.0, 8.0, 7.0, 6.0))

        self.uc.mem_write(CTX_ADDR, b"\x00" * CTX_SIZE)
        self.uc.mem_write(CTX_ADDR + 0x08, struct.pack("<I", CTX_ADDR + 0x1000))
        self.uc.mem_write(CTX_ADDR + 0x1008, struct.pack("<I", CTX_ADDR + 0x2000))
        self.uc.mem_write(CTX_ADDR + 0x2068, struct.pack("<ii", case["max_count"], 0x100))
        self.uc.mem_write(CTX_ADDR + 0xA4, struct.pack("<I", CTX_ADDR + 0x3000))

        self.uc.mem_write(SRC_ADDR, b"\x00" * SRC_SIZE)
        self.uc.mem_write(SRC_ADDR + 0x08, struct.pack("<I", DATA_ADDR))
        self.uc.mem_write(SRC_ADDR + 0x98, struct.pack("<f", 1.5))
        self.uc.mem_write(SRC_ADDR + 0xA8, struct.pack("<f", 2.5))
        self.uc.mem_write(SRC_ADDR + 0xB8, struct.pack("<f", 3.5))
        self.uc.mem_write(SRC_ADDR + 0x17C, struct.pack("<3f", -1.0, -2.0, -3.0))

        self.uc.mem_write(DATA_ADDR, b"\x00" * DATA_SIZE)
        self.uc.mem_write(DATA_ADDR + 0xB8, struct.pack("<I", case["mode"]))
        self.uc.mem_write(DATA_ADDR + 0xBC, struct.pack("<4f", 1.0, 0.1, 0.2, 0.3))
        self.uc.mem_write(DATA_ADDR + 0xCC, struct.pack("<4f", 2.0, 0.4, 0.5, 0.6))
        self.uc.mem_write(DATA_ADDR + 0xE8, struct.pack("<4f", 3.0, 0.7, 0.8, 0.9))
        self.uc.mem_write(DATA_ADDR + 0xF8, struct.pack("<2f", 5.0, case["f_fc"]))

        self.uc.mem_write(CMD_ADDR, b"\x00" * CMD_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.reg_write(arm.UC_ARM_REG_R0, CTX_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["index"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_R2, SRC_ADDR)
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
            "cmd_mem": bytes(self.uc.mem_read(CMD_ADDR, 0x100)),
            "cmd_ptr": struct.unpack("<I", self.uc.mem_read(0x004652A0, 4))[0],
            "g_4efd38": bytes(self.uc.mem_read(0x004EFD38, 16)),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "index": 2,
        "max_count": 4,
        "mode": 0,
        "f_fc": 1.0,
        "g_47662c": 0,
        "c00d4_ret": 1,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="oob_index_early_exit", index=4, max_count=4),
        base_case(name="mode_0_directional"),
        base_case(name="mode_1_g47662c_bit0_clear_c00d4_1", mode=1, g_47662c=0, c00d4_ret=1),
        base_case(name="mode_1_g47662c_bit0_set", mode=1, g_47662c=1, c00d4_ret=1),
        base_case(name="mode_2_spot_in_range", mode=2, f_fc=1.5),
        base_case(name="mode_2_spot_zero", mode=2, f_fc=0.0),
        base_case(name="mode_2_spot_ge_pi", mode=2, f_fc=3.5),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "call_log", "cmd_mem", "cmd_ptr", "g_4efd38"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"ui_func_0015a7c0: orig {len(orig_code)} B, cand {len(cand_code)} B")

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
        ("stride6", "index * 6", "index * 5"),
        ("header", "cmd[1] = 0x804F02C0u;", "cmd[1] = 0x804F02C1u;"),
        ("reg13", "base_reg + 0x13", "base_reg + 0x12"),
        ("pi_scale", "f_fc * 40.7436638f", "f_fc * 41.0f"),
        ("zero_spot", "spot[1] = 1.00001001f;", "spot[1] = 2.0f;"),
        ("g47662c_bit", "(*g_47662c & 1u) == 0", "(*g_47662c & 2u) == 0"),
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
