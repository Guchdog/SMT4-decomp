#!/usr/bin/env python3
"""Differential test for func_003e4ebc (0x003E4EBC) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the func_003e4ebc body,
resolves its direct calls to deterministic stubs placed at the original
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
OUT_DIR = ROOT / "build/test_leaf_003e4ebc"

FUNC_ADDR = 0x003E4EBC
FUNC_SIZE = 712

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00210000  # covers 0x0024C1CC..0x003E4EBC
NODE_ADDR = 0x00700000
NODE_SIZE = 0x00001000
OUT_ADDR = 0x00710000
OUT_SIZE = 0x00001000
ANIM_ADDR = 0x00720000
ANIM_SIZE = 0x00001000
FALLBACK_ADDR = 0x00730000
FALLBACK_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_380D3C = 0x00380D3C
STUB_381084 = 0x00381084
STUB_380F14 = 0x00380F14
STUB_24C1CC = 0x0024C1CC
STUB_3811CC = 0x003811CC

STUB_NAMES = {
    STUB_380D3C: "func_00380d3c",
    STUB_381084: "func_00381084",
    STUB_380F14: "func_00380f14",
    STUB_24C1CC: "engine_func_0024c1cc",
    STUB_3811CC: "func_003811cc",
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
    candidate = funcs.get("func_003e4ebc")
    if candidate is None:
        raise RuntimeError(f"func_003e4ebc not found in {obj_file}")

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
            (NODE_ADDR, NODE_SIZE),
            (OUT_ADDR, OUT_SIZE),
            (ANIM_ADDR, ANIM_SIZE),
            (FALLBACK_ADDR, FALLBACK_SIZE),
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
            begin=STUB_24C1CC,
            end=STUB_3811CC + 4,
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

        if address in (STUB_380D3C, STUB_381084, STUB_380F14):
            flags_val = struct.unpack("<I", uc.mem_read(r1, 4))[0]
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            self.call_log.append((STUB_NAMES[address], r0, flags_val, r2, s0))
            uc.mem_write(r1, struct.pack("<I", flags_val | 1))
        elif address == STUB_24C1CC:
            s0 = uc.reg_read(arm.UC_ARM_REG_S0)
            s1 = uc.reg_read(arm.UC_ARM_REG_S1)
            s2 = uc.reg_read(arm.UC_ARM_REG_S2)
            self.call_log.append(("24c1cc", r0, s0, s1, s2))
        elif address == STUB_3811CC:
            self.call_log.append(("3811cc", r0, r1))

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        self.uc.mem_write(NODE_ADDR, b"\x00" * NODE_SIZE)
        self.uc.mem_write(OUT_ADDR, b"\x00" * OUT_SIZE)
        self.uc.mem_write(ANIM_ADDR, b"\x00" * ANIM_SIZE)
        self.uc.mem_write(FALLBACK_ADDR, b"\x00" * FALLBACK_SIZE)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        self.uc.mem_write(NODE_ADDR + 0x5B, bytes(case["node_flags"]))
        self.uc.mem_write(OUT_ADDR + 0x3C, struct.pack("<I", case["out_flags"]))
        self.uc.mem_write(ANIM_ADDR + 0x00, struct.pack("<I", case["anim_flags"]))
        self.uc.mem_write(
            ANIM_ADDR + 0x0C,
            struct.pack("<iii", *case["rel_offsets"]),
        )
        self.uc.mem_write(
            FALLBACK_ADDR,
            struct.pack("<9f", *case["scale"], *case["rot"], *case["trans"]),
        )
        self.uc.mem_write(ENTRY_SP, struct.pack("<i", case["reset"]))

        self.uc.reg_write(arm.UC_ARM_REG_R0, NODE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, OUT_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R2, ANIM_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R3, FALLBACK_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_S0, f32_bits(case["time"]))
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
            "written_addrs": sorted({addr for addr, _sz, _val in self.writes}),
            "out_mem": bytes(self.uc.mem_read(OUT_ADDR, OUT_SIZE)),
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "node_flags": (1, 1, 1),
        "out_flags": 0x40000780,
        "anim_flags": 0,
        "rel_offsets": (0x20, 0x30, 0x40),
        "scale": (1.0, 1.0, 1.0),
        "rot": (0.0, 0.0, 0.0),
        "trans": (0.0, 0.0, 0.0),
        "time": 12.5,
        "reset": 0,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="all_tracks_active_reset0"),
        base_case(name="all_tracks_zero_time_null_rel", anim_flags=0x7, rel_offsets=(0, 0, 0), reset=1, node_flags=(0, 0, 0)),
        base_case(name="all_disabled_reset0", anim_flags=0x38, reset=0),
        base_case(name="all_disabled_reset1_zero_unit", anim_flags=0x38, reset=1),
        base_case(name="all_disabled_reset1_equal_nonunit", anim_flags=0x38, reset=1, scale=(2.0, 2.0, 2.0), rot=(0.1, 0.0, 0.0), trans=(0.0, 1.0, 0.0)),
        base_case(name="all_disabled_reset1_unequal_scale", anim_flags=0x38, reset=1, scale=(1.0, 2.0, 3.0)),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "call_log", "written_addrs", "out_mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"func_003e4ebc: orig {len(orig_code)} B, cand {len(cand_code)} B")

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
        ("rot_gate", "(anim_flags & 0x10u) == 0", "(anim_flags & 0x40u) == 0"),
        ("trans_gate", "(anim_flags & 0x08u) == 0", "(anim_flags & 0x40u) == 0"),
        ("scale_gate", "(anim_flags & 0x20u) == 0", "(anim_flags & 0x40u) == 0"),
        ("unit_scale", "scale_u[0] == 0x3F800000u", "scale_u[0] == 0x40000000u"),
        ("clear_bit30", "& ~0x40000000u", "& ~0x20000000u"),
        ("node_5b", "out_flags |= 8u;", "out_flags |= 16u;"),
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
