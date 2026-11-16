#!/usr/bin/env python3
"""Differential test for engine_func_00107208 (0x00107208) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the engine_func_00107208
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
OUT_DIR = ROOT / "build/test_leaf_00107208"

FUNC_ADDR = 0x00107208
FUNC_SIZE = 724

CODE_ADDR = 0x00100000
CODE_SIZE = 0x001D0000  # covers 0x00107208..0x002C0E84
TABLE_ADDR = 0x00700000
TABLE_SIZE = 0x00001000
SLOTS_ADDR = 0x00710000
SLOTS_SIZE = 0x00001000
TBL_ADDR = 0x00720000
TBL_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_2C0E84 = 0x002C0E84
STUB_2C0E34 = 0x002C0E34
STUB_2C0C5C = 0x002C0C5C
STUB_2C0C04 = 0x002C0C04
STUB_111968 = 0x00111968
STUB_2C0BCC = 0x002C0BCC
STUB_2C0BA8 = 0x002C0BA8
STUB_10F474 = 0x0010F474
STUB_10F4B0 = 0x0010F4B0

STUB_NAMES = {
    STUB_2C0E84: "Tbb_GetDefaultTable18Payload",
    STUB_2C0E34: "camp_func_002c0e34",
    STUB_2C0C5C: "ui_func_002c0c5c",
    STUB_2C0C04: "engine_func_002c0c04",
    STUB_111968: "camp_func_00111968",
    STUB_2C0BCC: "engine_func_002c0bcc",
    STUB_2C0BA8: "script_vm_func_002c0ba8",
    STUB_10F474: "func_0010f474",
    STUB_10F4B0: "func_0010f4b0",
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


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("engine_func_00107208")
    if candidate is None:
        raise RuntimeError(f"engine_func_00107208 not found in {obj_file}")

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
            (TABLE_ADDR, TABLE_SIZE),
            (SLOTS_ADDR, SLOTS_SIZE),
            (TBL_ADDR, TBL_SIZE),
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
            begin=STUB_10F474,
            end=STUB_2C0E84 + 4,
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
        self.slot_map: dict[tuple[int, int, int], int] = {}

        self.state_idx = 0

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

        if address == STUB_2C0E84:
            self.call_log.append(("2c0e84",))
            uc.reg_write(arm.UC_ARM_REG_R0, TABLE_ADDR)
        elif address == STUB_2C0E34:
            self.call_log.append(("2c0e34",))
            uc.reg_write(arm.UC_ARM_REG_R0, len(self.case["entries"]))
        elif address == STUB_2C0C5C:
            self.call_log.append(("2c0c5c",))
            val = self.case["state_vals"][self.state_idx]
            self.state_idx += 1
            uc.reg_write(arm.UC_ARM_REG_R0, val)
        elif address == STUB_2C0C04:
            key = (r0 & 0xFF, r1 & 0xFF, r2 & 0xFFFF)
            self.call_log.append(("2c0c04", *key))
            uc.reg_write(arm.UC_ARM_REG_R0, self.slot_map.get(key, SLOTS_ADDR + 0xF00))
        elif address == STUB_111968:
            key = (r0 & 0xFF, r1 & 0xFF, r2 & 0xFFFF)
            self.call_log.append(("111968", *key))
            uc.reg_write(arm.UC_ARM_REG_R0, TBL_ADDR)
        elif address == STUB_2C0BCC:
            self.call_log.append(("2c0bcc", s32(r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["rng_val"])
        elif address == STUB_2C0BA8:
            self.call_log.append(("2c0ba8", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, 1 if r0 in self.case["true_flags"] else 0)
        elif address == STUB_10F474:
            self.call_log.append(("10f474", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["f474_ret"])
        elif address == STUB_10F4B0:
            self.call_log.append(("10f4b0", r0))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["f4b0_ret"])

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []
        self.slot_map = {}
        self.state_idx = 0

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(TABLE_ADDR, b"\x00" * TABLE_SIZE)
        self.uc.mem_write(SLOTS_ADDR, b"\x00" * SLOTS_SIZE)
        self.uc.mem_write(TBL_ADDR, b"\x00" * TBL_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        for idx, e in enumerate(case["entries"]):
            self.uc.mem_write(
                TABLE_ADDR + idx * 0x94,
                struct.pack("<BBH", e["slot_id"], e["is_demon"], e["sub_idx"]),
            )
            eff_sub = e["sub_idx"]
            if e["is_demon"] != 0:
                if eff_sub == 6:
                    eff_sub = 0
                elif eff_sub == 7:
                    eff_sub = 1
            elif eff_sub == 7:
                eff_sub = 6
            key = (e["is_demon"], e["slot_id"], eff_sub)
            s_addr = SLOTS_ADDR + idx * 0x10
            self.slot_map[key] = s_addr
            self.uc.mem_write(s_addr, struct.pack("<HBB", e["cur_id"], e["mask"], e["b3"]))

        for k, (rid, rkey, rdur) in enumerate(case["tbl_recs"]):
            self.uc.mem_write(TBL_ADDR + 4 + k * 6, struct.pack("<HHH", rid, rkey, rdur))

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
            "slots_mem": bytes(self.uc.mem_read(SLOTS_ADDR, SLOTS_SIZE)),
        }


def make_cases() -> list[dict]:
    tbl = [
        (0, 0, 0),
        (10, 50, 5),
        (20, 1200, 7),
        (30, 1300, 0x19),
        (40, 1000, 3),
    ]
    return [
        {
            "name": "empty_count",
            "entries": [],
            "state_vals": [],
            "tbl_recs": tbl,
            "rng_val": 10,
            "true_flags": set(),
            "f474_ret": 0,
            "f4b0_ret": 0,
        },
        {
            "name": "sub_remap_timers_and_lt3e8",
            "entries": [
                {"slot_id": 1, "is_demon": 1, "sub_idx": 6, "cur_id": 0, "mask": 0xFF, "b3": 0x43},
                {"slot_id": 2, "is_demon": 1, "sub_idx": 7, "cur_id": 0, "mask": 0, "b3": 0x41},
                {"slot_id": 3, "is_demon": 0, "sub_idx": 7, "cur_id": 99, "mask": 0, "b3": 0x40},
            ],
            "state_vals": [0, 1, 0],
            "tbl_recs": tbl,
            "rng_val": 40,
            "true_flags": set(),
            "f474_ret": 1,
            "f4b0_ret": 1,
        },
        {
            "name": "group_weight_ge3e8_and_flag_gate",
            "entries": [
                {"slot_id": 8, "is_demon": 0, "sub_idx": 2, "cur_id": 5, "mask": 0, "b3": 0x60},
                {"slot_id": 9, "is_demon": 1, "sub_idx": 2, "cur_id": 5, "mask": 0, "b3": 0x60},
                {"slot_id": 4, "is_demon": 0, "sub_idx": 2, "cur_id": 0, "mask": 0, "b3": 0x00},
                {"slot_id": 5, "is_demon": 0, "sub_idx": 2, "cur_id": 0, "mask": 0, "b3": 0x00},
            ],
            "state_vals": [3, 3, 3, 4],
            "tbl_recs": tbl,
            "rng_val": 100,
            "true_flags": {0x668},
            "f474_ret": 0,
            "f4b0_ret": 1,
        },
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "call_log", "writes", "slots_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"engine_func_00107208: orig {len(orig_code)} B, cand {len(cand_code)} B")

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
        ("stride", "constexpr u32 kTableEntryStride = 0x94;", "constexpr u32 kTableEntryStride = 0x90;"),
        ("thresh", "constexpr u32 kWeightGroupThreshold = 0x3E8;", "constexpr u32 kWeightGroupThreshold = 0x3E9;"),
        ("flaga", "constexpr u32 kFlagGateA = 0x668;", "constexpr u32 kFlagGateA = 0x669;"),
        ("flagb", "constexpr u32 kFlagGateB = 0x1D7;", "constexpr u32 kFlagGateB = 0x1D8;"),
        ("dur_mask", "(dur & 0x1Fu)", "(dur & 0x0Fu)"),
        ("bit20", "slot[3] |= 0x20u;", "slot[3] |= 0x40u;"),
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
