#!/usr/bin/env python3
"""Differential test for script_vm_func_00338f30 (0x00338F30) using Unicorn ARM.

Compiles src/engine/leaf_batch45_a.cpp, extracts the script_vm_func_00338f30
body, resolves its direct calls to deterministic stubs placed at the original
addresses, and runs the pinned original (extracted/exefs/code.bin) against the
candidate in separate Unicorn machines with identical fixtures.

Compared outputs:
  * continuation PC, final SP, callee-saved r4-r11 and d8-d15;
  * the ordered call log, with every meaningful argument, of:
      - 0x0023EC3C (script_vm_func_0023ec3c: rng)
      - 0x002B9364 (camp_func_002b9364: tag lookup)
      - 0x002B66EC (script_vm_func_002b66ec: vm info)
      - 0x002A8A08 (camp_func_002a8a08: camp base)
      - 0x0025452C (script_vm_func_0025452c: party slot record)
      - 0x002B087C (battle_func_002b087c: enemy record)
      - 0x0023EBF0 (camp_func_0023ebf0: camp multiplier info)
      - 0x00297688 (camp_func_00297688: override gate)
  * every byte of state, vm_info, camp, party records, enemy records, lookup,
    and camp_info pages;
  * the sorted list of every emulated written byte outside the private stack.
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
OUT_DIR = ROOT / "build/test_leaf_00338f30"

FUNC_ADDR = 0x00338F30
FUNC_SIZE = 692

CODE_ADDR = 0x001F0000
CODE_SIZE = 0x00160000  # covers stubs at 0x0023EBF0..0x002B9364 and 0x00338F30
STATE_ADDR = 0x00700000
STATE_SIZE = 0x00005000
CAMP_ADDR = 0x00710000
CAMP_SIZE = 0x00010000
VM_INFO_ADDR = 0x00720000
VM_INFO_SIZE = 0x00001000
PARTY_ADDR = 0x00730000
PARTY_SIZE = 0x00001000
ENEMY_ADDR = 0x00740000
ENEMY_SIZE = 0x00001000
LOOKUP_ADDR = 0x00750000
LOOKUP_SIZE = 0x00001000
CAMP_INFO_ADDR = 0x00760000
CAMP_INFO_SIZE = 0x00001000
STACK_ADDR = 0x08000000
STACK_SIZE = 0x00010000
TRAP_ADDR = 0x90000000

ENTRY_SP = STACK_ADDR + STACK_SIZE - 0x100

STUB_23EC3C = 0x0023EC3C  # script_vm_func_0023ec3c
STUB_2B9364 = 0x002B9364  # camp_func_002b9364
STUB_2B66EC = 0x002B66EC  # script_vm_func_002b66ec
STUB_2A8A08 = 0x002A8A08  # camp_func_002a8a08
STUB_25452C = 0x0025452C  # script_vm_func_0025452c
STUB_2B087C = 0x002B087C  # battle_func_002b087c
STUB_23EBF0 = 0x0023EBF0  # camp_func_0023ebf0
STUB_297688 = 0x00297688  # camp_func_00297688

STUB_NAMES = {
    STUB_23EC3C: "script_vm_func_0023ec3c",
    STUB_2B9364: "camp_func_002b9364",
    STUB_2B66EC: "script_vm_func_002b66ec",
    STUB_2A8A08: "camp_func_002a8a08",
    STUB_25452C: "script_vm_func_0025452c",
    STUB_2B087C: "battle_func_002b087c",
    STUB_23EBF0: "camp_func_0023ebf0",
    STUB_297688: "camp_func_00297688",
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

MEM_REGIONS = (
    ("state", STATE_ADDR, STATE_SIZE),
    ("camp", CAMP_ADDR, CAMP_SIZE),
    ("vm_info", VM_INFO_ADDR, VM_INFO_SIZE),
    ("party", PARTY_ADDR, PARTY_SIZE),
    ("enemy", ENEMY_ADDR, ENEMY_SIZE),
    ("lookup", LOOKUP_ADDR, LOOKUP_SIZE),
    ("camp_info", CAMP_INFO_ADDR, CAMP_INFO_SIZE),
)


def s32(value: int) -> int:
    value &= 0xFFFFFFFF
    return value - 0x100000000 if value & 0x80000000 else value


def relocate_candidate(obj_file: Path) -> bytes:
    funcs = extract_elf_functions_detailed(obj_file)
    candidate = funcs.get("script_vm_func_00338f30")
    if candidate is None:
        raise RuntimeError(f"script_vm_func_00338f30 not found in {obj_file}")

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
            (STATE_ADDR, STATE_SIZE),
            (CAMP_ADDR, CAMP_SIZE),
            (VM_INFO_ADDR, VM_INFO_SIZE),
            (PARTY_ADDR, PARTY_SIZE),
            (ENEMY_ADDR, ENEMY_SIZE),
            (LOOKUP_ADDR, LOOKUP_SIZE),
            (CAMP_INFO_ADDR, CAMP_INFO_SIZE),
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
            begin=STUB_23EBF0,
            end=STUB_2B9364 + 4,
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
        self.gate_idx = 0

    def _on_write(self, uc, access, address, size, value, user_data) -> None:
        if STACK_ADDR <= address < STACK_ADDR + STACK_SIZE:
            return
        self.writes.append((address, size, value))

    def _on_stub(self, uc, address, size, user_data) -> None:
        if address not in STUB_NAMES:
            return
        r0 = uc.reg_read(arm.UC_ARM_REG_R0)

        if address == STUB_23EC3C:
            self.call_log.append(("rng", s32(r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, self.case["rng_val"] & 0xFFFFFFFF)
        elif address == STUB_2B9364:
            self.call_log.append(("lookup", r0))
            tag = self.case["lookup_tags"].get(r0)
            if tag is None:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
            else:
                slot_addr = LOOKUP_ADDR + (r0 & 0xFF) * 8
                self.uc.mem_write(slot_addr + 2, struct.pack("<B", tag))
                uc.reg_write(arm.UC_ARM_REG_R0, slot_addr)
        elif address == STUB_2B66EC:
            self.call_log.append(("vm_info",))
            uc.reg_write(arm.UC_ARM_REG_R0, VM_INFO_ADDR)
        elif address == STUB_2A8A08:
            self.call_log.append(("camp_base",))
            uc.reg_write(arm.UC_ARM_REG_R0, CAMP_ADDR)
        elif address == STUB_25452C:
            self.call_log.append(("party_rec", s32(r0)))
            uc.reg_write(arm.UC_ARM_REG_R0, PARTY_ADDR + r0 * 0x80)
        elif address == STUB_2B087C:
            self.call_log.append(("enemy_rec", r0))
            if r0 in self.case["enemies"]:
                uc.reg_write(arm.UC_ARM_REG_R0, ENEMY_ADDR + (r0 & 0xF) * 0x40)
            else:
                uc.reg_write(arm.UC_ARM_REG_R0, 0)
        elif address == STUB_23EBF0:
            self.call_log.append(("camp_info",))
            uc.reg_write(arm.UC_ARM_REG_R0, CAMP_INFO_ADDR)
        elif address == STUB_297688:
            self.call_log.append(("gate",))
            vals = self.case["gate_vals"]
            val = vals[self.gate_idx] if self.gate_idx < len(vals) else vals[-1]
            self.gate_idx += 1
            uc.reg_write(arm.UC_ARM_REG_R0, val & 0xFFFFFFFF)

    def run(self, code: bytes, case: dict) -> dict:
        self.case = case
        self.call_log = []
        self.writes = []
        self.gate_idx = 0

        self.uc.mem_write(FUNC_ADDR, b"\x00" * 0x1000)
        self.uc.mem_write(FUNC_ADDR, code)
        for _name, addr, sz in MEM_REGIONS:
            self.uc.mem_write(addr, b"\x00" * sz)
        self.uc.mem_write(STACK_ADDR, b"\xCC" * STACK_SIZE)

        # Populate state
        self.uc.mem_write(STATE_ADDR + 0xE0, struct.pack("<I", case["flags_e0"]))
        self.uc.mem_write(STATE_ADDR + 0x14C, struct.pack("<B", case["sub_mode"]))
        self.uc.mem_write(STATE_ADDR + 0x44A0, struct.pack("<I", case["flags_44a0"]))
        self.uc.mem_write(STATE_ADDR + 0x44A8, struct.pack("<I", case["flags_44a8"]))
        self.uc.mem_write(STATE_ADDR + 0x44AC, struct.pack("<I", case["flags_44ac"]))
        for i, val in enumerate(case["slots"]):
            self.uc.mem_write(STATE_ADDR + 0xC8 + i * 4, struct.pack("<I", val))

        # Populate vm_info
        self.uc.mem_write(VM_INFO_ADDR + 0x72, struct.pack("<H", case["vm_flags"]))
        self.uc.mem_write(
            VM_INFO_ADDR + 0x26, struct.pack("<hh", case["vm_a"], case["vm_b"])
        )

        # Populate camp slots
        for i, s in enumerate(case["camp_slots"]):
            self.uc.mem_write(CAMP_ADDR + 0x9108 + i, struct.pack("<b", s))

        # Populate party records
        for i, (rflags, a, b) in enumerate(case["party_recs"]):
            base = PARTY_ADDR + i * 0x80
            self.uc.mem_write(base + 0x44, struct.pack("<H", rflags))
            self.uc.mem_write(base + 0x18, struct.pack("<hh", a, b))

        # Populate enemy records
        for eid, (ea, eb) in case["enemies"].items():
            base = ENEMY_ADDR + (eid & 0xF) * 0x40
            self.uc.mem_write(base + 0x12, struct.pack("<HH", ea, eb))

        # Populate camp_info multiplier
        self.uc.mem_write(CAMP_INFO_ADDR + 0x1C, struct.pack("<f", case["camp_mult"]))

        self.uc.reg_write(arm.UC_ARM_REG_R0, STATE_ADDR)
        self.uc.reg_write(arm.UC_ARM_REG_R1, case["mode"] & 0xFFFFFFFF)
        self.uc.reg_write(arm.UC_ARM_REG_SP, ENTRY_SP)
        self.uc.reg_write(arm.UC_ARM_REG_LR, TRAP_ADDR)
        for name, reg in CALLEE_SAVED.items():
            self.uc.reg_write(reg, CALLEE_SAVED_START[name])
        for _name, reg, val in VFP_CALLEE_SAVED:
            self.uc.reg_write(reg, val)

        self.uc.emu_start(FUNC_ADDR, TRAP_ADDR, count=50000)

        mem_snapshot = {
            name: bytes(self.uc.mem_read(addr, sz)) for name, addr, sz in MEM_REGIONS
        }
        return {
            "pc": self.uc.reg_read(arm.UC_ARM_REG_PC),
            "sp": self.uc.reg_read(arm.UC_ARM_REG_SP),
            "callee_saved": {name: self.uc.reg_read(reg) for name, reg in CALLEE_SAVED.items()},
            "vfp_saved": {name: self.uc.reg_read(reg) for name, reg, _v in VFP_CALLEE_SAVED},
            "call_log": list(self.call_log),
            "writes": sorted(self.writes),
            "mem": mem_snapshot,
        }


def base_case(**overrides) -> dict:
    case = {
        "name": "base",
        "mode": 0,
        "sub_mode": 0,
        "flags_44a0": 0x107,
        "flags_44a8": 0,
        "flags_44ac": 0,
        "flags_e0": 0,
        "slots": [0x10001, 2, 0, 0, 0, 0],
        "lookup_tags": {1: 0x10, 2: 0x27},
        "vm_flags": 0,
        "vm_a": 10,
        "vm_b": 20,
        "camp_slots": [0, -1, 1],
        "party_recs": [(0, 15, 25), (0, 5, 5), (0x2, 100, 100)],
        "enemies": {1: (10, 10), 2: (5, 5)},
        "camp_mult": 1.0,
        "gate_vals": [0],
        "rng_val": 50,
    }
    case.update(overrides)
    return case


def make_cases() -> list[dict]:
    return [
        base_case(name="gate_44ac_bit5", flags_44ac=0x20),
        base_case(name="gate_44a8_bit14", flags_44a8=0x4000),
        base_case(name="gate_44a8_bit15", flags_44a8=0x8000),
        base_case(name="gate_44a0_bit9", flags_44a0=0x206),
        base_case(name="gate_e0_bit16", flags_e0=0x10000),
        base_case(name="gate_e0_bit17", flags_e0=0x20000),
        base_case(name="mode_nonzero_low_rng", mode=1, rng_val=0x45),
        base_case(name="mode_nonzero_high_rng", mode=1, rng_val=0x46),
        base_case(name="submode1_no_match", sub_mode=1, lookup_tags={1: 0x10, 2: 0x26}),
        base_case(name="submode1_match_0x27", sub_mode=1, rng_val=99),
        base_case(name="submode2_set_flags", sub_mode=2),
        base_case(name="submode3_early_ret", sub_mode=3),
        base_case(name="vm_flag_bit1_set", vm_flags=2, party_recs=[(0, -5, -5), (0, 0, 0), (0, 0, 0)], rng_val=10),
        base_case(name="party_skip_bits_0x400_0x4", party_recs=[(0x400, 99, 99), (0x4, 99, 99), (0, 1, 2)], rng_val=50),
        base_case(name="enemy_missing_and_high", slots=[1, 99, 0, 0, 0, 0], enemies={1: (200, 100)}, rng_val=30),
        base_case(name="diff_scale_boundary", rng_val=50),
        base_case(name="base_chance_boundary", rng_val=49),
        base_case(name="clamp_min_boundary_eq", vm_a=-200, vm_b=0, camp_slots=[-1, -1, -1], rng_val=0x1E),
        base_case(name="clamp_min_boundary_gt", vm_a=-200, vm_b=0, camp_slots=[-1, -1, -1], rng_val=0x1F),
        base_case(name="clamp_max_boundary_eq", vm_a=500, vm_b=0, camp_slots=[-1, -1, -1], enemies={}, rng_val=0x46),
        base_case(name="clamp_max_boundary_gt", vm_a=500, vm_b=0, camp_slots=[-1, -1, -1], enemies={}, rng_val=0x47),
        base_case(name="override_gate_1_1_eq", gate_vals=[1, 1], rng_val=0x50),
        base_case(name="override_gate_1_1_gt", gate_vals=[1, 1], rng_val=0x51),
        base_case(name="override_gate_1_2_unclamped", vm_a=500, vm_b=0, enemies={}, camp_mult=1.5, gate_vals=[1, 2], rng_val=100),
    ]


def compare_results(orig: dict, cand: dict) -> list[str]:
    diffs: list[str] = []
    for key in ("pc", "sp", "callee_saved", "vfp_saved", "call_log", "writes", "mem"):
        if orig[key] != cand[key]:
            diffs.append(f"{key} mismatch")
    return diffs


def main() -> int:
    raw_bin = ORIG_BIN.read_bytes()
    off = FUNC_ADDR - 0x00100000
    orig_code = raw_bin[off : off + FUNC_SIZE]

    cand_code = compile_candidate_baseline()
    print(f"script_vm_func_00338f30: orig {len(orig_code)} B, cand {len(cand_code)} B")

    cases = make_cases()
    for case in cases:
        orig_res = Runner().run(orig_code, case)
        cand_res = Runner().run(cand_code, case)
        diffs = compare_results(orig_res, cand_res)
        if diffs:
            print(f"FAIL [{case['name']}]: {diffs}")
            print("  orig log:", orig_res["call_log"])
            print("  cand log:", cand_res["call_log"])
            print("  orig writes:", orig_res["writes"])
            print("  cand writes:", cand_res["writes"])
            return 1
        print(f"PASS [{case['name']}]")

    mutants = [
        ("mode_thresh", "constexpr s32 kModeNonZeroThreshold = 0x46;", "constexpr s32 kModeNonZeroThreshold = 0x45;"),
        ("lookup_tag", "constexpr u8 kSpecialLookupTag = 0x27;", "constexpr u8 kSpecialLookupTag = 0x26;"),
        ("skip_mask", "constexpr u16 kSlotSkipMask = 0x406;", "constexpr u16 kSlotSkipMask = 0x006;"),
        ("diff_scale", "constexpr f32 kLevelDiffScale = 0.2f;", "constexpr f32 kLevelDiffScale = 0.25f;"),
        ("base_chance", "constexpr s32 kBaseChance = 0x2D;", "constexpr s32 kBaseChance = 0x2C;"),
        ("min_chance", "constexpr s32 kMinChance = 0x1E;", "constexpr s32 kMinChance = 0x1F;"),
        ("max_chance", "constexpr s32 kMaxChance = 0x46;", "constexpr s32 kMaxChance = 0x45;"),
        ("override_chance", "constexpr s32 kOverrideChance = 0x50;", "constexpr s32 kOverrideChance = 0x51;"),
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
