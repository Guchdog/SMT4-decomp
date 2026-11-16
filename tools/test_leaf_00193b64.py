#!/usr/bin/env python3
"""Differential test for battle_func_00193b64 (0x00193B64) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the battle_func_00193b64 body,
resolves its direct calls (including the tail call to 0x00203198) to
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
OUT_DIR = ROOT / "build/test_leaf_00193b64"

FUNC_ADDR = 0x00193B64
FUNC_SIZE = 712

CODE_ADDR = 0x00190000
CODE_SIZE = 0x00130000  # covers 0x00193B64..0x002A84BC
DST_ADDR = 0x00700000
DST_SIZE = 0x00001000
SRC_ADDR = 0x00710000
SRC_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2A84BC = 0x002A84BC
STUB_1CA504 = 0x001CA504
STUB_2918C4 = 0x002918C4
STUB_1AD1D8 = 0x001AD1D8
STUB_1DD86C = 0x001DD86C
STUB_1DD938 = 0x001DD938
STUB_1EE114 = 0x001EE114
STUB_1EE2F0 = 0x001EE2F0
STUB_1EE1D0 = 0x001EE1D0
STUB_202F58 = 0x00202F58
STUB_203078 = 0x00203078
STUB_203198 = 0x00203198

STUB_NAMES = {
    STUB_2A84BC: "battle_func_002a84bc",
    STUB_1CA504: "func_001ca504",
    STUB_2918C4: "ui_func_002918c4",
    STUB_1AD1D8: "func_001ad1d8",
    STUB_1DD86C: "func_001dd86c",
    STUB_1DD938: "func_001dd938",
    STUB_1EE114: "func_001ee114",
    STUB_1EE2F0: "func_001ee2f0",
    STUB_1EE1D0: "func_001ee1d0",
    STUB_202F58: "func_00202f58",
    STUB_203078: "func_00203078",
    STUB_203198: "func_00203198",
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


def f32_bits(value: float) -> int:
    return struct.unpack("<I", struct.pack("<f", value))[0]


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("battle_func_00193b64")
    if candidate is None:
        raise RuntimeError(f"battle_func_00193b64 not found in {obj_file}")

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
        self.uc.reg_write(arm.UC_ARM_REG_C1_C0_2, 0x00F00000)
        self.uc.reg_write(arm.UC_ARM_REG_FPEXC, 0x40000000)

        for addr, size in (
            (CODE_ADDR, CODE_SIZE),
            (DST_ADDR, DST_SIZE),
            (SRC_ADDR, SRC_SIZE),
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
            begin=STUB_1AD1D8,
            end=STUB_2A84BC + 4,
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

        if address == STUB_2A84BC:
            self.call_log.append(("2a84bc", r0))
        elif address == STUB_1CA504:
            self.call_log.append(("1ca504", r0, r1))
            uc.mem_write(r0 + 0x50, struct.pack("<I", self.case["dst_50"]))
            uc.mem_write(
                r0 + 0x3C,
                struct.pack("<H", self.case["dst_stats"][0]),
            )
            uc.mem_write(
                r0 + 0x48,
                struct.pack("<HHH", *self.case["dst_stats"][1:]),
            )
        elif address == STUB_2918C4:
            self.call_log.append(("2918c4", s32(r0), r1, s32(r2)))
            uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(self.case["delta"]))
        else:
            self.call_log.append((STUB_NAMES[address], r0, r1))

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(DST_ADDR, b"\xAA" * DST_SIZE)
        self.uc.mem_write(SRC_ADDR, b"\x00" * SRC_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.mem_write(SRC_ADDR + 0x34, bytes(case["bytes_34"]))
        self.uc.mem_write(SRC_ADDR + 0x38, struct.pack("<I", case["w38"]))
        self.uc.mem_write(SRC_ADDR + 0x3C, struct.pack("<h", case["s3c"]))
        self.uc.mem_write(SRC_ADDR + 0x40, struct.pack("<II", case["w40"], case["w44"]))
        self.uc.mem_write(SRC_ADDR + 0x48, struct.pack("<hhh", *case["s48_4c"]))

        self.uc.reg_write(arm.UC_ARM_REG_R0, DST_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, SRC_ADDR)
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
            "dst_mem": bytes(self.uc.mem_read(DST_ADDR, DST_SIZE)),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "bytes_34": (10, 20, 30, 255),
        "w38": 0x11223344,
        "s3c": -12,
        "w40": 0x55667788,
        "w44": 0x99AABBCC,
        "s48_4c": (100, -50, 200),
        "dst_50": 0x42,
        "dst_stats": (50, 10, 20, 30),
        "delta": 15.75,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="dst50_nonzero_all_stats"),
        base_case(name="dst50_zero_skip_adjust", dst_50=0),
        base_case(name="dst50_nonzero_partial_zero_stats", dst_stats=(0, 5, 0, 8), delta=12.0),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "call_log", "writes", "dst_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"battle_func_00193b64: orig {len(orig_code)} B, cand {len(cand_code)} B")

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
        ("ptr_2e1", "dst + 0x2E1", "dst + 0x2E0"),
        ("zero_end", "off <= 0x338", "off <= 0x334"),
        ("dst50", "*reinterpret_cast<const u32*>(dst + 0x50) != 0", "*reinterpret_cast<const u32*>(dst + 0x54) != 0"),
        ("stat_3c", "adjust_stat_00193b64(dst, 0x3C, -1, 0x200);", "adjust_stat_00193b64(dst, 0x3E, -1, 0x200);"),
        ("mirror_48", "adjust_stat_00193b64(dst, 0x48, 0x04, 0x204);", "adjust_stat_00193b64(dst, 0x48, -1, 0x204);"),
        ("mirror_4a", "adjust_stat_00193b64(dst, 0x4A, 0x08, 0x208);", "adjust_stat_00193b64(dst, 0x4A, -1, 0x208);"),
        ("mirror_4c", "adjust_stat_00193b64(dst, 0x4C, 0x0C, 0x20C);", "adjust_stat_00193b64(dst, 0x4C, -1, 0x20C);"),
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
